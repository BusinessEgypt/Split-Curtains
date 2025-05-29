from odoo import models, fields, api

class SaleAdvancePaymentInvCustom(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    downpayment_mode = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ], string='Down Payment Type', default='percentage')

    fixed_amount = fields.Float(string='Fixed Amount')

    @api.onchange('downpayment_mode')
    def _onchange_downpayment_mode(self):
        if self.downpayment_mode == 'fixed':
            self.amount = self.fixed_amount

    @api.onchange('fixed_amount')
    def _onchange_fixed_amount(self):
        if self.downpayment_mode == 'fixed':
            self.amount = self.fixed_amount
