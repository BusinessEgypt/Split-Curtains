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
            width = line.x_width_m or 0
            height = line.x_height_m or 0
            area = width * height
            line.x_unit_area_m2 = max(area, 2)
