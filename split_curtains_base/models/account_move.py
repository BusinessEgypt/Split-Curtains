# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for inv in self.filtered(lambda m: m.move_type == 'out_invoice' and m.state == 'posted'):
            _logger.info(f"Processing invoice: {inv.name} (ID: {inv.id})")
            
            # البحث عن أمر البيع المرتبط بهذه الفاتورة
            sale_order = inv.invoice_origin and self.env['sale.order'].search([('name', '=', inv.invoice_origin)], limit=1)
            
            if not sale_order:
                _logger.warning(f"No Sale Order found for invoice {inv.name}. Skipping PO creation.")
                continue

            po_lines = []
            # المرور على سطور أمر البيع الأصلي
            for sl in sale_order.order_line:
                # تجاهل سطور الدفعات المقدمة أو المنتجات غير المادية
                if sl.product_id and sl.product_id.type != 'service' and not sl.product_id.is_downpayment:
                    # يمكنك إضافة شرط إضافي هنا لضمان أنه منتج ستائر فقط
                    # مثلاً: if sl.product_id.categ_id.name == 'Curtains'
                    
                    # التأكد أن المنتج قابل للشراء وله سعر شراء
                    if not sl.product_id.purchase_ok or sl.product_id.standard_price is None:
                        _logger.warning(f"Product {sl.product_id.name} is not purchasable or has no standard price. Skipping for PO creation.")
                        continue

                    po_lines.append((0, 0, {
                        'product_id': sl.product_id.id,
                        'name': sl.name,
                        'product_qty': sl.product_uom_qty,
                        'product_uom': sl.product_uom.id,
                        'price_unit': sl.product_id.standard_price, # استخدم standard_price مباشرة
                        'x_code': sl.x_code.id,
                        'x_type': sl.x_type,
                        'x_width_m': sl.x_width_m,
                        'x_height_m': sl.x_height_m,
                        'x_unit_area_m2': sl.x_unit_area_m2,
                        'x_quantity_units': sl.x_quantity_units,
                        'x_total_area_m2': sl.x_total_area_m2,
                        'x_price_per_m2': sl.x_price_per_m2, # هذا مازال ينقل من الـ SO
                    }))
            
            if not po_lines:
                _logger.warning(f"No valid PO lines generated from Sale Order {sale_order.name} for invoice {inv.name}. Skipping PO creation.")
                continue

            # تحديد المورد: يمكن أن يكون الشريك الافتراضي للمنتج أو شريك الفاتورة
            # هنا سنستخدم الشريك الافتراضي لأول منتج في PO lines لضمان أنه مورد
            # أو يمكن استخدام inv.partner_id إذا تأكدنا أنه مورد
            po_partner = po_lines[0][2]['product_id'] and self.env['product.product'].browse(po_lines[0][2]['product_id']).seller_ids[:1].partner_id
            if not po_partner:
                # إذا لم يتم العثور على مورد من المنتج، يمكن العودة إلى شريك الفاتورة إذا كان موردًا
                if inv.partner_id and inv.partner_id.supplier_rank > 0:
                    po_partner = inv.partner_id
                else:
                    _logger.error(f"Could not determine a vendor for Purchase Order from Sale Order {sale_order.name}. Skipping PO creation.")
                    continue


            po = self.env['purchase.order'].create({
                'partner_id': po_partner.id,
                'origin': inv.invoice_origin or inv.name,
                'order_line': po_lines,
            })
            po.button_confirm()
            _logger.info(f"Purchase Order {po.name} created and confirmed for invoice {inv.name} from Sale Order {sale_order.name}.")
        return res