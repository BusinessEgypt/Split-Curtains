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
    x_price_per_m2 = fields.Float(string="Price per m²") # هذا الحقل ما زال يتم نقله من الـ SO، يمكنك استخدامه أو تركه يعتمد على price_unit

    x_total_price = fields.Monetary(
        string="Total Purchase Price",
        compute='_compute_x_total_purchase_price', # <--- أصبح حقلًا محسوبًا
        store=True, # <--- مازال مخزناً لتخزين القيمة بعد الحساب
        currency_field='currency_id'
    )

    @api.depends('x_total_area_m2', 'price_unit') # <--- يعتمد الآن على سعر الوحدة في الـ PO
    def _compute_x_total_purchase_price(self):
        for line in self:
            line.x_total_price = line.x_total_area_m2 * line.price_unit