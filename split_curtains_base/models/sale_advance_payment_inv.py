# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.model
    def _create_invoice_lines(self, order, so_line, amount):
        # Overwrite بالكامل لمنع تقسيم الضرايب
        product = self.env.ref('sale.advance_product_0')
        return [(0, 0, {
            'name': f"خصم دفعة مقدمة {self.amount:.2f}%",
            'product_id': product.id,
            'quantity': 1,
            'price_unit': -abs(amount),
            'tax_ids': [(6, 0, [])],  # بدون أي ضريبة
        })]

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        invoices = self.env['account.move']

        for order in sale_orders:
            if self.advance_payment_method == 'percentage':
                amount = order.amount_total * self.amount / 100.0
                invoice_vals = order._prepare_invoice()
                invoice_vals['invoice_line_ids'] = self._create_invoice_lines(order, None, amount)
                invoice = self.env['account.move'].create(invoice_vals)
                invoice.action_post()
                invoices += invoice
            else:
                raise UserError("Only percentage method is supported.")

        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['context'] = {'create': False}
        action['domain'] = [('id', 'in', invoices.ids)]
        return action
