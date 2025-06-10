# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.state == 'posted'):
            _logger.info(f"Processing invoice: {inv.name} (ID: {inv.id})")
            _logger.info(f"Invoice lines: {inv.invoice_line_ids}")

            # جمع كل sale.order.line المرتبطة بسطور الفاتورة
            sale_lines = inv.invoice_line_ids.mapped('sale_line_ids')

            # في حال وجود منتج الدفعة المقدمة في الفاتورة فقط، قد لا يكون هناك sale_line_ids
            # لذا نحتاج للتعامل مع هذا السيناريو أو التأكد من أن الفاتورة تحتوي على سطور منتجات فعلية
            if not sale_lines:
                _logger.warning(f"No sale lines found for invoice {inv.name}. Skipping PO creation for this invoice.")
                continue

            # تحضير سطور الـ PO بنفس مواصفات الـ SO بسعر الشراء
            po_lines = []
            for sl in sale_lines:
                # التأكد من أن المنتج موجود وله standard_price
                if not sl.product_id:
                    _logger.warning(f"Product missing for sale line {sl.name}. Skipping this line for PO creation.")
                    continue
                
                # يمكنك تحديد مورد افتراضي هنا إذا لم يكن هناك مورد مرتبط بالمنتج
                # أو التأكد من أن inv.partner_id هو المورد الصحيح
                # For simplicity, we'll use the invoice's partner_id as the PO vendor.
                # If specific vendors are needed per product, that logic would be more complex.

                po_lines.append((0, 0, {
                    'product_id': sl.product_id.id,
                    'name': sl.name,
                    'product_qty': sl.product_uom_qty,
                    'product_uom': sl.product_uom.id,
                    'price_unit': sl.product_id.standard_price or 0.0,
                    'x_code': sl.x_code.id,
                    'x_type': sl.x_type,
                    'x_width_m': sl.x_width_m,
                    'x_height_m': sl.x_height_m,
                    'x_unit_area_m2': sl.x_unit_area_m2,
                    'x_quantity_units': sl.x_quantity_units,
                    'x_total_area_m2': sl.x_total_area_m2,
                    'x_price_per_m2': sl.x_price_per_m2, # هذا مازال ينقل من الـ SO، ولكن الـ x_total_price في الـ PO سيتم حسابه بناءً على price_unit الجديد
                    # 'x_total_price': sl.x_total_price, # تم إزالة هذا، حيث سيتم حسابه في purchase_order_line
                }))
            
            if not po_lines:
                _logger.warning(f"No valid PO lines generated for invoice {inv.name}. Skipping PO creation.")
                continue

            # إنشاء الـ Purchase Order وتأكيده
            # استخدام inv.partner_id كمورد افتراضي للـ PO
            po_partner = inv.partner_id
            if not po_partner.supplier_rank > 0: # التأكد من أن الشريك هو مورد
                _logger.warning(f"Invoice partner {inv.partner_id.name} is not a vendor. Cannot create PO.")
                continue

            po = self.env['purchase.order'].create({
                'partner_id': po_partner.id,
                'origin': inv.invoice_origin or inv.name,
                'order_line': po_lines,
            })
            po.button_confirm()
            _logger.info(f"Purchase Order {po.name} created and confirmed for invoice {inv.name}.")
        return res