# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            self._create_purchase_orders_from_invoice(inv)
        return res

    def _create_purchase_orders_from_invoice(self, invoice):
        sale_order = invoice.invoice_origin and self.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
        if not sale_order:
            _logger.warning(f"No Sale Order found for invoice {invoice.name}. Skipping PO creation.")
            return
        if sale_order.x_po_created_from_invoice:
            _logger.info(f"POs already created for SO {sale_order.name}. Skipping.")
            return

        lines = sale_order.order_line.filtered(lambda l: l.product_id.type == 'product')
        if not lines:
            _logger.info(f"No product lines in SO {sale_order.name}. Skipping PO creation.")
            return

        partner = lines[0].product_id.seller_ids and lines[0].product_id.seller_ids[0].name.id or sale_order.partner_id.id
        po_vals = {
            'origin': sale_order.name,
            'partner_id': partner,
            'date_order': fields.Date.context_today(self),
            'currency_id': self.env.ref('base.EGP').id,
            'company_id': sale_order.company_id.id,
        }
        po = self.env['purchase.order'].create(po_vals)

        for l in lines:
            po.write({'order_line': [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.display_name,
                'product_qty': l.x_total_area_m2 or 1,
                'product_uom': l.product_uom.id,
                'price_unit': l.x_price_per_m2,
                'x_code': l.x_code.id,
                'x_width_m': l.x_width_m,
                'x_height_m': l.x_height_m,
                'x_quantity_units': l.x_quantity_units,
                'x_unit_area_m2': l.x_unit_area_m2,
                'x_total_area_m2': l.x_total_area_m2,
                'x_price_per_m2': l.x_price_per_m2,
            })]})

        po.button_confirm()
        sale_order.x_po_created_from_invoice = True
        po.message_post(body=f'🧰 Auto-created PO from SO {sale_order.name} via Invoice {invoice.name}')
