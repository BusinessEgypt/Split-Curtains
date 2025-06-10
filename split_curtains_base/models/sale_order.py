# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.fields import Date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_downpayment = fields.Monetary(
        string='Paid Amount',
        compute='_compute_paid_amount_and_remaining',
        store=True,
        currency_field='currency_id',
    )
    x_remaining = fields.Monetary(
        string='Remaining',
        compute='_compute_paid_amount_and_remaining',
        store=True,
    )

    # تم إزالة حقل x_accounts_approval
    # x_accounts_approval = fields.Boolean(...)

    # هذا الحقل مهم لتتبع ما إذا تم إنشاء POs بالفعل
    x_po_created_from_invoice = fields.Boolean(
        string='POs Created from Invoice',
        default=False,
        help="Indicates if purchase orders have been generated for this sale order via invoice payment."
    )

    @api.depends('amount_total', 'invoice_ids.amount_total', 'invoice_ids.state', 'invoice_ids.move_type')
    def _compute_paid_amount_and_remaining(self):
        for order in self:
            paid_total = sum(
                invoice.amount_total
                for invoice in order.invoice_ids
                if invoice.move_type == 'out_invoice' and invoice.state == 'posted'
            )
            order.x_downpayment = paid_total
            order.x_remaining = order.amount_total - paid_total

    # تم إزالة دالة _prepare_purchase_order_line ودالة action_create_purchase هنا
    # لأن إنشاء الـ PO سيتم من خلال AccountMove عند الدفع.