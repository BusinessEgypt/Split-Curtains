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
            # هيظهر 0 لو مدفوع بالكامل، والباقي حسب الحالة
            paid = all(inv.payment_state == 'paid' for inv in order.invoice_ids if inv.move_type == 'out_invoice' and inv.state != 'cancel')
            if paid:
                order.x_remaining = 0.0
            else:
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
                            # ✅ داون بايمنت يظهر دايمًا بالسالب في الكوتيشن
                            total += line.price_total if line.price_total < 0 else -abs(line.price_total)
            # لما الأوردر مدفوع بالكامل، يختفي الداون بايمنت (أو يبقى 0)
            paid = all(inv.payment_state == 'paid' for inv in order.invoice_ids if inv.move_type == 'out_invoice' and inv.state != 'cancel')
            order.x_downpayment = 0.0 if paid else total
