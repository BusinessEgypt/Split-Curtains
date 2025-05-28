from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_code = fields.Many2one('product.product', string='Code', ...)
    # باقي الحقول هنا
