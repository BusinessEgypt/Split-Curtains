# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.state == 'posted'):
            # جمع كل sale.order.line المرتبطة بالفاتورة
            sale_lines = inv.invoice_line_ids.mapped('sale_line_ids')
            if not sale_lines:
                continue
            # تحضير سطور الـ PO بنفس مواصفات الـ SO بسسعر الشراء
            po_lines = []
            for sl in sale_lines:
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
                    'x_price_per_m2': sl.x_price_per_m2,
                    'x_total_price': sl.x_total_price,
                }))
            # إنشاء الـ Purchase Order وتأكده
            po = self.env['purchase.order'].create({
                'partner_id': inv.partner_id.id,
                'origin': inv.invoice_origin or inv.name,
                'order_line': po_lines,
            })
            po.button_confirm()
        return res
