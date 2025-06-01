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

    @api.depends('invoice_ids.invoice_line_ids')
    def _compute_downpayment(self):
        for order in self:
            total = 0.0
            for invoice in order.invoice_ids:
                if invoice.move_type == 'out_invoice' and invoice.state != 'cancel':
                    for line in invoice.invoice_line_ids:
                        label = (line.name or "").lower()
                        if 'down payment' in label:
                            total += line.price_total
            order.x_downpayment = total
