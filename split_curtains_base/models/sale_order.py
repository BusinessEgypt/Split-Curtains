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

    def action_create_manufacturing(self):
        MrpProduction = self.env['mrp.production']
        for order in self:
            if not order.x_accounts_approval:
                raise UserError(_("لا يمكن إنشاء أمر تصنيع إلا بعد موافقة الحسابات."))

            _logger.info("✅ بدء إنشاء أمر تصنيع لـ Order: %s", order.name)
            if not order.order_line:
                raise UserError(_("لا يمكن إنشاء أمر تصنيع بدون بنود."))

            # حاليًا هنستخدم أول منتج فقط كنموذج (نقدر نطوره لاحقًا يدعم أكثر من منتج)
            line = order.order_line[0]
            if not line.product_id:
                raise UserError(_("السطر يحتوي على منتج غير معروف."))

            mo = MrpProduction.create({
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom.id,
                'origin': order.name,
                'date_planned_start': Date.today(),
                'location_src_id': line.product_id.property_stock_production.id,
                'location_dest_id': line.product_id.categ_id.property_stock_valuation.id or order.warehouse_id.lot_stock_id.id,
            })

            mo.message_post(body=f'🧰 تم إنشاء أمر تصنيع تلقائيًا من {order.name}')
            _logger.info("🆕 تم إنشاء Manufacturing Order: %s", mo.name)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Order',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'res_id': mo.id,
                'target': 'current',
            }

        return True
