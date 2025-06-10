from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            self._create_po_after_payment(inv)
        return res

    def _create_po_after_payment(self, invoice):
        sale_order = invoice.invoice_origin and self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
        if not sale_order or sale_order.x_po_created_from_invoice:
            return

        lines = sale_order.order_line.filtered(lambda l: l.product_id.type == 'product')
        if not lines:
            return

        created_purchase_orders = self.env['purchase.order']
        for line in lines:
            try:
                moves = line._action_launch_stock_rule()
                for move in moves:
                    if move.purchase_line_id and move.purchase_line_id.order_id:
                        po = move.purchase_line_id.order_id
                        created_purchase_orders |= po
            except Exception as e:
                _logger.error(f"Error creating PO for product {line.product_id.name}: {e}")

        if created_purchase_orders:
            sale_order.x_po_created_from_invoice = True
            for po in created_purchase_orders:
                if po.state == 'draft':
                    po.button_confirm()
                po.message_post(body=f'🧰 Auto-created PO from SO {sale_order.name} via Invoice {invoice.name}')
