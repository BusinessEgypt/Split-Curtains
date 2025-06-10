# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('payment_state')
    def _check_and_create_po_manual(self):
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'):
            so = inv.invoice_origin and self.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
            if not so or so.x_po_created_from_invoice:
                continue

            # إنشاء PO مباشرة (Manual Creation)
            po = self.env['purchase.order'].create({
                'origin': so.name,
                'partner_id': so.partner_id.id,
                'currency_id': self.env.ref('base.EGP').id,
                'date_order': fields.Date.context_today(self),
                'company_id': so.company_id.id,
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.display_name,
                    'product_qty': line.x_total_area_m2 or 1,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.x_price_per_m2 or line.product_id.standard_price,
                    'x_code': line.x_code.id,
                    'x_width_m': line.x_width_m,
                    'x_height_m': line.x_height_m,
                    'x_quantity_units': line.x_quantity_units,
                    'x_unit_area_m2': line.x_unit_area_m2,
                    'x_total_area_m2': line.x_total_area_m2,
                    'x_price_per_m2': line.x_price_per_m2,
                }) for line in so.order_line.filtered(lambda l: l.product_id.type == 'product')]
            })

            po.button_confirm()
            so.x_po_created_from_invoice = True
            _logger.info(f'PO {po.name} created manually after invoice {inv.name} payment')
            po.message_post(body=f'✅ PO auto-created from SO {so.name} after invoice {inv.name} payment')
