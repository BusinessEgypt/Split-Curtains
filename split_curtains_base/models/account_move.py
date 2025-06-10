# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    # سنقوم بتشغيل منطق إنشاء الـ PO عند تغيير payment_state إلى 'paid'
    @api.constrains('payment_state') # هذه الدالة ستُشغل عند كل تغيير لحالة الدفع
    def _check_and_create_purchase_orders(self):
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            _logger.info(f"Processing invoice for PO creation (payment_state is paid): {inv.name} (ID: {inv.id})")
            
            sale_order = inv.invoice_origin and self.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
            
            if not sale_order:
                _logger.warning(f"No Sale Order found for invoice {inv.name}. Skipping PO creation.")
                continue

            if sale_order.x_po_created_from_invoice:
                _logger.info(f"Purchase Orders already created for Sale Order {sale_order.name}. Skipping further PO creation for invoice {inv.name}.")
                continue

            created_purchase_orders = self.env['purchase.order']
            for sl in sale_order.order_line:
                is_downpayment_product = sl.product_id and (
                    'down' in (sl.product_id.name or '').lower() or
                    'down' in (sl.product_id.default_code or '').lower()
                )

                if sl.product_id and sl.product_id.type != 'service' and not is_downpayment_product:
                    try:
                        moves = sl._action_launch_stock_rule()
                        for move in moves:
                            if move.purchase_line_id and move.purchase_line_id.order_id:
                                created_purchase_orders |= move.purchase_line_id.order_id
                                _logger.info(f"Triggered stock rule for {sl.product_id.name} on SO {sale_order.name}. PO: {move.purchase_line_id.order_id.name}")
                            elif move.production_id:
                                _logger.info(f"Triggered manufacturing order for {sl.product_id.name} on SO {sale_order.name}. MO: {move.production_id.name}")
                            else:
                                _logger.info(f"Stock rule for {sl.product_id.name} on SO {sale_order.name} resulted in moves but no PO/MO. Move: {move.name}")

                    except Exception as e:
                        _logger.error(f"Error launching stock rule for product {sl.product_id.name} on SO {sale_order.name}: {e}")
                else:
                    _logger.info(f"Skipping product {sl.product_id.name} (service/downpayment) on SO {sale_order.name} for PO creation.")

            if created_purchase_orders:
                sale_order.x_po_created_from_invoice = True
                _logger.info(f"Sale Order {sale_order.name} marked as 'PO created from invoice'. Created POs: {[po.name for po in created_purchase_orders]}")
                
                for po in created_purchase_orders:
                    if po.state == 'draft':
                        po.button_confirm()
                        _logger.info(f"Confirmed PO: {po.name}")
                    po.message_post(body=f'🧰 Auto-created PO from Sale Order {sale_order.name} triggered by Invoice {inv.name}.')
            elif sale_order.order_line.filtered(lambda l: l.product_id and l.product_id.type != 'service' and not ('down' in (l.product_id.name or '').lower() or 'down' in (l.product_id.default_code or '').lower())):
                _logger.warning(f"No purchase orders were created for Sale Order {sale_order.name} despite having non-service/non-downpayment lines. Check product routes and vendor configurations.")

        # دالة action_post الأصلية يجب أن يتم استدعاؤها في النهاية
        # (إذا كنت لا تزال تريد تشغيلها عند ترحيل الفاتورة لأسباب أخرى)
        # ولكن بما أننا نعتمد على payment_state، فالدالة الأصلية لا تحتاج إلى أي تعديل هنا.
        # super().action_post() لا يجب أن تكون داخل constrains.
        #  الـ `super().action_post()` يجب أن تبقى في دالة `action_post` نفسها.
        #  الـ `_check_and_create_purchase_orders` ستعمل بشكل منفصل عند تغيير `payment_state`.