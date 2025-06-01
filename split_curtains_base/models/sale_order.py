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

    @api.depends('invoice_ids')
    def _compute_downpayment(self):
        # ❗️ده ID المنتج الخاص بالدفعة المقدمة داخل النظام
        downpayment_product_id = 2  # عدّله لو اتغير في البيئة عندك

        for order in self:
            total = 0.0
            for invoice in order.invoice_ids:
                if invoice.move_type == 'out_invoice' and invoice.state != 'cancel':
                    for line in invoice.invoice_line_ids:
                        if line.product_id.id == downpayment_product_id:
                            total += line.price_total
            order.x_downpayment = total
