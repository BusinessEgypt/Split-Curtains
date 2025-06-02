# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        if self.advance_payment_method != 'percentage':
            return super(SaleAdvancePaymentInv, self).create_invoices()

        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        invoices = self.env['account.move']

        for order in sale_orders:
            amount = order.amount_total * self.amount / 100.0
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': order.partner_id.id,
                'invoice_origin': order.name,
                'invoice_line_ids': [(0, 0, {
                    'product_id': self.env.ref('sale.advance_product_0').id,
                    'name': f"خصم دفعة مقدمة {self.amount:.2f}%",
                    'quantity': 1,
                    'price_unit': -abs(amount),
                    'tax_ids': [(6, 0, [])],  # بدون ضرائب
                })]
            })
            invoice.action_post()
            invoices += invoice

        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'create': False}
        action['domain'] = [('id', 'in', invoices.ids)]

        return action
