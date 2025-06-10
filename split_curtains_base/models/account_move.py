# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('payment_state')
    def _check_and_create_purchase_orders(self):
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            _logger.info(f"Processing invoice for PO creation (payment_state is paid): {inv.name} (ID: {inv.id})")

            sale_order = inv.invoice_origin and self.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
            if not sale_order:
                _logger.warning(f"No Sale Order found for invoice {inv.name}. Skipping PO creation.")
                continue

            # حذف أي PO draft طلع قبل كده مرتبط بنفس SO (نظافة نهائية)
            linked_purchase_orders = self.env['purchase.order'].search([('origin', '=', sale_order.name), ('state', '=', 'draft')])
            for po in linked_purchase_orders:
                po.button_cancel()
                po.unlink()

            if sale_order.x_po_created_from_invoice:
                _logger.info(f"POs already created for SO {sale_order.name}. Skipping.")
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
                                po = move.purchase_line_id.order_id
                                # فرض القيم يدويًا
                                po.currency_id = self.env.ref('base.EGP')
                                po.date_order = fields.Date.context_today(po)
                                for line in po.order_line:
                                    # تحديث الحقول المخصصة من الـ Sale Order Line
                                    so_line = sale_order.order_line.filtered(lambda l: l.product_id == line.product_id)
                                    if so_line:
                                        line.x_width_m = so_line.x_width_m
                                        line.x_height_m = so_line.x_height_m
                                        line.x_quantity_units = so_line.x_quantity_units
                                        line.x_unit_area_m2 = so_line.x_unit_area_m2
                                        line.x_total_area_m2 = so_line.x_total_area_m2
                                        line.x_price_per_m2 = so_line.x_price_per_m2
                                        line.price_unit = so_line.x_price_per_m2 or 0.0
                                        line.product_qty = so_line.x_total_area_m2 or 1.0
                                created_purchase_orders |= po

                    except Exception as e:
                        _logger.error(f"Error on stock rule for product {sl.product_id.name}: {e}")
                else:
                    _logger.info(f"Skipping service/downpayment product {sl.product_id.name}")

            if created_purchase_orders:
                sale_order.x_po_created_from_invoice = True
                for po in created_purchase_orders:
                    if po.state == 'draft':
                        po.button_confirm()
                        _logger.info(f"Confirmed PO: {po.name}")
                    po.message_post(body=f'🧰 Auto-created PO from SO {sale_order.name} via Invoice {inv.name}')
