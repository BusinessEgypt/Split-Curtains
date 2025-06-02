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

                    for invoice in sale_order.invoice_ids:
                        # 1. جمع كل سطور الدفعة
                        dp_lines = invoice.invoice_line_ids.filtered(lambda l: 'Down payment' in l.name)
                        total_dp = sum(dp_lines.mapped('price_subtotal'))

                        # 2. حذف كل السطور
                        invoice.write({
                            'invoice_line_ids': [(2, line.id) for line in dp_lines]
                        })

                        # 3. إضافة سطر واحد فقط بالسالب
                        invoice.write({
                            'invoice_line_ids': [(0, 0, {
                                'product_id': self.env.ref('sale.advance_product_0').id,
                                'quantity': 1,
                                'price_unit': -total_dp,
                                'name': f"خصم دفعة مقدمة {wizard.amount:.2f}%",
                                'tax_ids': [(6, 0, [])],  # بدون ضرائب
                            })]
                        })

        return res
