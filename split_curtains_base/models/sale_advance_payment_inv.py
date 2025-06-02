# -*- coding: utf-8 -*-
from odoo import models, api

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()

        for wizard in self:
            if wizard.advance_payment_method == 'percentage':
                for order_id in wizard._context.get('active_ids', []):
                    sale_order = self.env['sale.order'].browse(order_id)
                    amount = sale_order.amount_total * wizard.amount / 100.0

                    for invoice in sale_order.invoice_ids:
                        # نحذف كل السطور اللي فيها كلمة Down payment
                        lines_to_remove = invoice.invoice_line_ids.filtered(lambda l: 'Down payment' in l.name)
                        invoice.write({
                            'invoice_line_ids': [(2, line.id) for line in lines_to_remove]
                        })

                        # نضيف سطر واحد سليم بالسالب
                        invoice.write({
                            'invoice_line_ids': [(0, 0, {
                                'product_id': self.env.ref('sale.advance_product_0').id,
                                'quantity': 1,
                                'price_unit': -amount,
                                'name': f"خصم دفعة مقدمة {wizard.amount:.2f}%",
                                'tax_ids': [(6, 0, [])],
                            })]
                        })

        return res
