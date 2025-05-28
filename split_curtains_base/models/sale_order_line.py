from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # 🔍 حقل تجريبي لاختبار الربط
    x_test_field = fields.Char(string="Test Field")
