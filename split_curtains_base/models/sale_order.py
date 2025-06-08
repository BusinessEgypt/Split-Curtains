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
        raise UserError(_("The line contains an undefined product."))

    width = line.x_width_m or 0
    height = line.x_height_m or 0
    units = line.x_quantity_units or 0
    unit_area = max(width * height, 2)
    total_area = unit_area * units
    price_per_m2 = line.product_id.standard_price or 0
    total_price = total_area * price_per_m2

    return (0, 0, {
        'product_id': line.product_id.id,
        'name': line.name,
        'product_qty': line.product_uom_qty,
        'product_uom': line.product_uom.id,
        'price_unit': price_per_m2,  # سعر الشراء
        'date_planned': Date.today(),

        # ✅ الحقول الفنية كاملة
        'x_code': line.x_code.id if line.x_code else False,
        'x_type': line.x_type,
        'x_width_m': width,
        'x_height_m': height,
        'x_quantity_units': units,
        'x_unit_area_m2': unit_area,
        'x_total_area_m2': total_area,
        'x_price_per_m2': price_per_m2,
        'x_total_price': total_price,
    })

    def action_create_purchase(self):
        PurchaseOrder = self.env['purchase.order']
        for order in self:
            if not order.x_accounts_approval:
                raise UserError(_("Accounts must approve before creating a manufacturing order."))

            _logger.info("✅ Creating PO (named Manufacturing Order) for SO: %s", order.name)
            if not order.order_line:
                raise UserError(_("Cannot proceed without order lines."))

            po = PurchaseOrder.create({
                'partner_id': order.partner_id.id,
                'origin': f'Manufacturing Order from {order.name}',
                'order_line': [self._prepare_purchase_order_line(l) for l in order.order_line],
            })

            po.message_post(body=f'🧰 Auto-created PO (as Manufacturing Order) from {order.name}')
            _logger.info("🆕 Created PO: %s", po.name)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Order',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': po.id,
                'target': 'current',
            }

        return True
