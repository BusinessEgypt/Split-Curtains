# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_code = fields.Many2one('product.product', string="Code")
    x_type = fields.Char(string="Type")
    x_width_m = fields.Float(string="Width (m)")
    x_height_m = fields.Float(string="Height (m)")
    x_quantity_units = fields.Integer(string="Quantity (Units)")
    x_unit_area_m2 = fields.Float(string="Unit Area (m²)")
    x_total_area_m2 = fields.Float(string="Total Area (m²)")
    x_price_per_m2 = fields.Float(string="Price per m²") 

    x_total_price = fields.Monetary(
        string="Total Purchase Price",
        compute='_compute_x_total_purchase_price',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('x_total_area_m2', 'price_unit', 'product_qty') 
    def _compute_x_total_purchase_price(self):
        for line in self:
            if line.x_total_area_m2 and line.x_price_per_m2:
                # إذا كانت الأسعار تعتمد على المتر المربع في الشراء
                line.x_total_price = line.x_total_area_m2 * line.x_price_per_m2
            else:
                # هذا هو الافتراضي إذا لم يكن لديك بيانات المساحة أو السعر بالمتر المربع
                line.x_total_price = line.product_qty * line.price_unit

    @api.model
    def _prepare_purchase_order_line_from_sale_line(self, sale_line, product_id, product_qty, product_uom, company_id, supplier):
        """
        تجاوز هذه الدالة لنقل الحقول المخصصة من سطر أمر البيع إلى سطر أمر الشراء.
        """
        values = super()._prepare_purchase_order_line_from_sale_line(sale_line, product_id, product_qty, product_uom, company_id, supplier)
        
        # نقل الحقول المخصصة
        values.update({
            'x_code': sale_line.x_code.id,
            'x_type': sale_line.x_type,
            'x_width_m': sale_line.x_width_m,
            'x_height_m': sale_line.x_height_m,
            'x_quantity_units': sale_line.x_quantity_units,
            'x_unit_area_m2': sale_line.x_unit_area_m2,
            'x_total_area_m2': sale_line.x_total_area_m2,
            'x_price_per_m2': sale_line.x_price_per_m2,
        })
        return values