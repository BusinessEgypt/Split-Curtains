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
            # إذا جميع الفواتير مدفوعة، نضع remaining = 0
            paid = all(
                inv.payment_state == 'paid'
                for inv in order.invoice_ids
                if inv.move_type == 'out_invoice' and inv.state != 'cancel'
            )
            if paid:
                order.x_remaining = 0.0
            else:
                # نأخذ القيمة المطلقة لـ x_downpayment لكي لا تتحول للزيادة عند طرح سالب - سالب
                order.x_remaining = order.amount_total - abs(order.x_downpayment or 0.0)

    @api.depends('invoice_ids.invoice_line_ids')
    def _compute_downpayment(self):
        for order in self:
            total = 0.0
            # تجمع كل سطور "down payment" من الفواتير المرتبطة بالأوردر
            for invoice in order.invoice_ids:
                if invoice.move_type == 'out_invoice' and invoice.state != 'cancel':
                    for line in invoice.invoice_line_ids:
                        label = (line.name or "").lower()
                        if 'down payment' in label:
                            # نجمع القيمة المطلقة (لأن السعر في الفاتورة يكون بالسالب عند الإنشاء)
                            total += abs(line.price_total)
            # إذا جميع الفواتير مدفوعة، نضع downpayment = 0
            paid = all(
                inv.payment_state == 'paid'
                for inv in order.invoice_ids
                if inv.move_type == 'out_invoice' and inv.state != 'cancel'
            )
            order.x_downpayment = 0.0 if paid else total

    # ملاحظة: إذا أردت إظهار قيمة الداون بايمنت بالسالب فقط في الـ View دون تغيير قيمة الـ store،
    # يمكنك إنشاء حقل _display أو Property في الـ View نفسه أو باستخدام @property method.
