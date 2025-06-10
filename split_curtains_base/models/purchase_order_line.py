# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_code = fields.Many2one('product.product', string="Product Code")
    x_width_m = fields.Float(string="Width (m)")
    x_height_m = fields.Float(string="Height (m)")
    # الأسماء المطابقة للـ View
    x_unit_area_m2 = fields.Float(string="Unit Area (m²)", compute='_compute_unit_area', store=True)
    x_quantity_units = fields.Float(string="Quantity Units")
    x_total_area_m2 = fields.Float(string="Total Area (m²)", compute='_compute_total_area', store=True)
    x_price_per_m2 = fields.Float(string="Price per m²")
    x_total_price = fields.Monetary(string="Total Price", currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='order_id.currency_id', store=True)

    @api.depends('x_width_m', 'x_height_m')
    def _compute_unit_area(self):
        for line in self:
            area = (line.x_width_m or 0) * (line.x_height_m or 0)
            line.x_unit_area_m2 = max(area, 2)

    @api.depends('x_unit_area_m2', 'x_quantity_units')
    def _compute_total_area(self):
        for line in self:
            line.x_total_area_m2 = (line.x_unit_area_m2 or 0) * (line.x_quantity_units or 0)

    @api.depends('x_total_area_m2', 'x_price_per_m2')
    def _compute_total_price(self):
        for line in self:
            line.x_total_price = (line.x_total_area_m2 or 0) * (line.x_price_per_m2 or 0)
