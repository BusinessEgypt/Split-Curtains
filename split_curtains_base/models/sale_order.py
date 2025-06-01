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

    @api.depends('invoice_ids.invoice_line_ids', 'invoice_ids.origin')
    def _compute_downpayment(self):
        for order in self:
            total = 0.0
            # نبحث عن كل الفواتير اللي مرتبطة بـ order هذا
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '!=', 'cancel'),
                ('partner_id', '=', order.partner_id.id),
                ('origin', '=', order.name)
            ])
            for invoice in invoices:
                for line in invoice.invoice_line_ids:
                    label = (line.name or "").lower()
                    if 'down payment' in label:
                        total += line.price_total
            order.x_downpayment = total

    def _create_invoices(self, final=False, grouped=False):
        invoices = super()._create_invoices(final=final, grouped=grouped)

        for order in self:
            if order.x_downpayment:
                for invoice in order.invoice_ids:
                    if invoice.state != 'cancel' and invoice.move_type == 'out_invoice':
                        already_exists = invoice.invoice_line_ids.filtered(
                            lambda l: 'down payment total' in (l.name or '').lower()
                        )
                        if not already_exists:
                            product = self.env['product.product'].search(
                                [('name', '=', 'Down Payment')], limit=1
                            )
                            if product:
                                invoice.write({
                                    'invoice_line_ids': [(0, 0, {
                                        'name': 'Down Payment Total',
                                        'quantity': 1,
                                        'price_unit': -order.x_downpayment,
                                        'tax_ids': [],
                                        'product_id': product.id,
                                        'account_id': product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id,
                                    })]
                                })

        return invoices
