# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_width_m = fields.Float(string='Width (m)')
    x_height_m = fields.Float(string='Height (m)')
    x_unit_area_m2 = fields.Float(
        string='Unit Area (m²)',
        compute='_compute_unit_area',
        store=True
    )

    @api.depends('x_width_m', 'x_height_m')
    def _compute_unit_area(self):
        for line in self:
            if line.x_width_m and line.x_height_m:
                area = line.x_width_m * line.x_height_m
                if area < 2:
                    line.x_unit_area_m2 = 2
                else:
                    line.x_unit_area_m2 = area
            else:
                line.x_unit_area_m2 = 2
