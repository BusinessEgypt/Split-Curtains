# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_downpayment = fields.Monetary(
        string='Down Payment',
        compute='_compute_downpayment',
        store=True,
        currency_field='currency_id',
    )
    x_remaining = fields.Monetary(
        string='Remaining',
        compute='_compute_remaining',
        store=True,
    )

    @api.depends('amount_total', 'x_downpayment')
    def _compute_remaining(self):
        for order in self:
            order.x_remaining = order.amount_total - (order.x_downpayment or 0.0)

    @api.depends('invoice_ids.invoice_line_ids', 'invoice_ids.state', 'invoice_ids.payment_state')
    def _compute_downpayment(self):
        for order in self:
            downpayment_total = 0.0
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
                ('invoice_origin', '=', order.name)
            ])
            for invoice in invoices:
                if invoice.payment_state != 'not_paid':
                    for line in invoice.invoice_line_ids:
                        if line.product_id and 'down' in (line.product_id.name or '').lower():
                            downpayment_total += line.price_total
            order.x_downpayment = downpayment_total
