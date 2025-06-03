# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_downpayment = fields.Monetary(
        string='العربون',  # Down Payment
        compute='_compute_downpayment',
        store=True,
        currency_field='currency_id',
    )
    x_remaining = fields.Monetary(
        string='المتبقي',  # Remaining
        compute='_compute_remaining',
        store=True,
    )

    @api.depends('invoice_ids.invoice_line_ids')
    def _compute_downpayment(self):
        for order in self:
            total = 0.0
            # نجمع كل خطوط الفواتير التي تحتوي على "down payment" في الاسم
            for invoice in order.invoice_ids:
                if invoice.move_type == 'out_invoice' and invoice.state != 'cancel':
                    for line in invoice.invoice_line_ids:
                        label = (line.name or "").lower()
                        if 'down payment' in label:
                            total += abs(line.price_total)
            # نتحقق إن كل الفواتير المرتبطة مدفوعة بالكامل
            paid = all(
                inv.payment_state == 'paid'
                for inv in order.invoice_ids
                if inv.move_type == 'out_invoice' and inv.state != 'cancel'
            )
            order.x_downpayment = 0.0 if paid else total

    @api.depends('amount_total', 'x_downpayment', 'invoice_ids.payment_state', 'invoice_ids.state')
    def _compute_remaining(self):
        for order in self:
            invs = order.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel')
            # إذا كل الفواتير مدفوعة، المتبقي = 0
            if invs and all(inv.payment_state == 'paid' for inv in invs):
                order.x_remaining = 0.0
            else:
                order.x_remaining = order.amount_total - abs(order.x_downpayment or 0.0)
