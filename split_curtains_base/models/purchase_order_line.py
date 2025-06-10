# -*- coding: utf-8 -*-
from odoo import models, fields

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
    x_total_price = fields.Monetary(string="Total Purchase Price", currency_field='currency_id')
