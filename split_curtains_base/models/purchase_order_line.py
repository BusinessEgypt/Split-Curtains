# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_width_m = fields.Float(string="Width (m)")
    x_height_m = fields.Float(string="Height (m)")
    x_quantity_units = fields.Integer(string="Quantity (Units)")
    x_total_area_m2 = fields.Float(string="Total Area (m²)")
