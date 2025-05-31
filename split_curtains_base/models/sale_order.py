# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_downpayment = fields.Monetary(
        string='Down Payment',
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

    def update_downpayment_from_invoice(self):
        # هتلف على كل الفواتير المربوطة بالأوردر وتلقط أي فاتورة Down Payment وتجمع قيمتها
        for order in self:
            downpayment_total = 0
            for invoice in order.invoice_ids:
                # ممكن تظبط هنا الشروط حسب نوع الفاتورة لو عندك أنواع تانية
                if invoice.state != 'cancel' and invoice.invoice_payment_state != 'not_paid':
                    for line in invoice.invoice_line_ids:
                        if line.product_id and 'down' in (line.product_id.name or '').lower():
                            downpayment_total += line.price_total
            order.x_downpayment = downpayment_total

@api.onchange('invoice_ids')
def _onchange_invoice_ids(self):
    self.update_downpayment_from_invoice()

