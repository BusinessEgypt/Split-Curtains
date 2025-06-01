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
            product = self.env['product.product'].search(
                [('name', '=', 'Down Payment')], limit=1
            )
            if product:
                lines = self.env['account.move.line'].search([
                    ('move_id.move_type', '=', 'out_invoice'),
                    ('move_id.state', '!=', 'cancel'),
                    ('move_id.partner_id', '=', order.partner_id.id),
                    ('product_id', '=', product.id),
                ])
                total = sum(lines.mapped('price_total'))
            order.x_downpayment = total
