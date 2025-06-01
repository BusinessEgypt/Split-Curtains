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

    @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.payment_state')
    def _compute_downpayment(self):
        for order in self:
            total = 0.0
            for invoice in order.invoice_ids:
                if invoice.state != 'cancel' and invoice.payment_state not in ['not_paid']:
                    for line in invoice.invoice_line_ids:
                        if line.display_type or not line.product_id:
                            continue
                        # الشرط الأساسي: لازم السطر ده يخص Down Payment
                        if invoice.invoice_origin == order.name and line.price_subtotal < order.amount_total:
                            total += line.price_subtotal
            order.x_downpayment = total
