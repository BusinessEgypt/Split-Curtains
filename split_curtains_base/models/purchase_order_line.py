# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_code = fields.Many2one('product.product', string="Product Code")
    x_width_m = fields.Float(string="Width (m)")
    x_height_m = fields.Float(string="Height (m)")
    x_unit_area_m = fields.Float(string="Unit Area (m²)")
    # Alias للحقل في الفيو:
    x_unit_area_m2 = fields.Float(string="Unit Area (m²)", related='x_unit_area_m', store=True)
    x_quantity_units = fields.Float(string="Quantity Units")
    x_area_m = fields.Float(string="Total Area (m²)")
    # Alias للحقل الثاني في الفيو:
    x_total_area_m2 = fields.Float(string="Total Area (m²)", related='x_area_m', store=True)
    x_price_per_m_2 = fields.Float(string="Price per m²")
    x_total = fields.Monetary(string="Total Price", currency_field='currency_id')
    x_type = fields.Selection([
        ('fabric', 'Fabric'),
        ('mechanism', 'Mechanism'),
        ('accessory', 'Accessory'),
    ], string="Type")

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='order_id.currency_id', store=True)

    @api.onchange('x_width_m', 'x_height_m')
    def _compute_unit_area(self):
        for line in self:
            area = (line.x_width_m or 0) * (line.x_height_m or 0)
            line.x_unit_area_m = max(area, 2)

    @api.onchange('x_unit_area_m', 'x_quantity_units')
    def _compute_total_area(self):
        for line in self:
            line.x_area_m = (line.x_unit_area_m or 0) * (line.x_quantity_units or 0)

    @api.onchange('x_area_m', 'x_price_per_m_2')
    def _compute_total_price(self):
        for line in self:
            line.x_total = (line.x_area_m or 0) * (line.x_price_per_m_2 or 0)
