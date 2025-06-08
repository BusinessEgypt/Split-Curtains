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

    x_accounts_approval = fields.Boolean(
        string='Accounts Approval',
        default=False,
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

    def _prepare_purchase_order_line(self, line):
        if not line.product_id:
            raise UserError(_("السطر يحتوي على منتج غير معروف، تأكد من ربط الكود بالمنتج."))
        return (0, 0, {
            'product_id': line.product_id.id,
            'name': line.name,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'price_unit': line.price_unit,
            'date_planned': Date.today(),
        })

    def action_create_purchase(self):
        PurchaseOrder = self.env['purchase.order']
        for order in self:
            if not order.x_accounts_approval:
                raise UserError(_("لا يمكن إنشاء أمر شراء إلا بعد موافقة الحسابات."))

            _logger.info("✅ بدء إنشاء أمر شراء لـ Order: %s", order.name)
            if not order.order_line:
                raise UserError(_("لا يمكن إنشاء أمر شراء بدون بنود في الطلب."))

            po = PurchaseOrder.create({
                'partner_id': order.partner_id.id,
                'origin': order.name,
                'order_line': [self._prepare_purchase_order_line(l) for l in order.order_line],
            })

            po.message_post(body=f'🆕 تم إنشاء أمر الشراء تلقائيًا من {order.name}')
            _logger.info("🆕 تم إنشاء Purchase Order: %s", po.name)

        return True
