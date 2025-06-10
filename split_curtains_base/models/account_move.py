# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('payment_state')
    def _check_and_create_purchase_orders(self):
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            sale_order = inv.invoice_origin and self.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
            if not sale_order:
                continue

            # Only generate PO if there are actual order lines (not just Down Payment)
            if not sale_order.order_line.filtered(lambda l: l.product_id and l.product_id.type == 'product'):
                continue

            if sale_order.x_po_created_from_invoice:
                continue

            created_purchase_orders = self.env['purchase.order']
            for sl in sale_order.order_line:
                if sl.product_id and sl.product_id.type == 'product':
                    moves = sl._action_launch_stock_rule()
                    for move in moves:
                        if move.purchase_line_id and move.purchase_line_id.order_id:
                            po = move.purchase_line_id.order_id
                            po.currency_id = self.env.ref('base.EGP')
                            po.date_order = fields.Date.context_today(po)
                            created_purchase_orders |= po

            if created_purchase_orders:
                sale_order.x_po_created_from_invoice = True
                for po in created_purchase_orders:
                    if po.state == 'draft':
                        po.button_confirm()
                    po.message_post(body=f'🧰 Auto-created PO from SO {sale_order.name} via Invoice {inv.name}')
