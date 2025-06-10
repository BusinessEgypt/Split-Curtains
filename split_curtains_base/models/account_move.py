# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from collections import defaultdict

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

            # التحقق إذا تم إنشاء أوامر الشراء لهذا الـ SO بالفعل
            if sale_order.x_po_created_from_invoice:
                _logger.info(f"Purchase Orders already created for Sale Order {sale_order.name}. Skipping further PO creation for invoice {inv.name}.")
                continue

            # تجميع سطور أمر الشراء حسب المورد
            po_lines_by_vendor = defaultdict(list)
            
            # جلب الـ routes الأساسية لـ Buy و Dropship
            # استخدام ref لضمان الحصول على الـ ID الصحيح بغض النظر عن الترجمة أو تغيير الاسم
            buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)
            dropship_route = self.env.ref('stock_dropshipping.route_transit_location_dropship', raise_if_not_found=False)
            
            if not (buy_route and dropship_route):
                _logger.warning("Could not find 'Buy' or 'Dropship' routes. PO creation might not work as expected.")

            for sl in sale_order.order_line:
                # تجاهل سطور الدفعات المقدمة أو المنتجات الخدمية
                if sl.product_id and sl.product_id.type != 'service' and not sl.product_id.is_downpayment:
                    
                    product_has_relevant_route = False
                    
                    # 1. التحقق من الـ route المباشر على سطر أمر البيع إذا كان موجودًا
                    if sl.route_id and (sl.route_id == buy_route or sl.route_id == dropship_route):
                        product_has_relevant_route = True
                    # 2. إذا لم يكن هناك route مباشر، تحقق من الـ routes على المنتج أو فئته
                    elif sl.product_id:
                        product_routes = sl.product_id.route_ids | sl.product_id.categ_id.route_ids
                        if (buy_route and buy_route in product_routes) or \
                           (dropship_route and dropship_route in product_routes):
                            product_has_relevant_route = True
                            
                    if product_has_relevant_route and sl.product_id.seller_ids:
                        # الحصول على المورد الافتراضي للمنتج أو أول مورد
                        vendor = sl.product_id.seller_ids[0].partner_id
                        if vendor:
                            po_lines_by_vendor[vendor].append({
                                'product_id': sl.product_id.id,
                                'name': sl.name,
                                'product_qty': sl.product_uom_qty,
                                'product_uom': sl.product_uom.id,
                                'price_unit': sl.product_id.standard_price, # سعر الشراء الافتراضي للمنتج
                                'date_planned': fields.Date.today(),
                                # نقل الحقول المخصصة لـ PO Line
                                'x_code': sl.x_code.id,
                                'x_type': sl.x_type,
                                'x_width_m': sl.x_width_m,
                                'x_height_m': sl.x_height_m,
                                'x_quantity_units': sl.x_quantity_units,
                                'x_unit_area_m2': sl.x_unit_area_m2,
                                'x_total_area_m2': sl.x_total_area_m2,
                                'x_price_per_m2': sl.x_price_per_m2,
                            })
                        else:
                            _logger.warning(f"Product {sl.product_id.name} on SO {sale_order.name} has no vendor configured. Skipping PO line.")
                    else:
                        _logger.info(f"Product {sl.product_id.name} on SO {sale_order.name} is not configured for automatic PO creation (no 'Buy'/'Dropship' route or no vendor). Skipping PO line.")

            created_pos = []
            for vendor, po_lines_data in po_lines_by_vendor.items():
                if po_lines_data:
                    _logger.info(f"Attempting to create PO for vendor {vendor.name} from Sale Order {sale_order.name}.")
                    try:
                        po = self.env['purchase.order'].create({
                            'partner_id': vendor.id,
                            'origin': inv.invoice_origin or inv.name,
                            'order_line': [(0, 0, line_data) for line_data in po_lines_data],
                        })
                        po.button_confirm() # تأكيد أمر الشراء تلقائيا
                        _logger.info(f"Successfully created and confirmed Purchase Order {po.name} for vendor {vendor.name} from Sale Order {sale_order.name}.")
                        po.message_post(body=f'🧰 Auto-created PO (as Manufacturing Order) from Sale Order {sale_order.name} triggered by Invoice {inv.name}.')
                        created_pos.append(po)
                    except Exception as e:
                        _logger.error(f"Error creating PO for vendor {vendor.name} from Sale Order {sale_order.name}: {e}")

            # إذا تم إنشاء أي POs بنجاح، قم بتحديث حقل التتبع في أمر البيع
            if created_pos:
                sale_order.x_po_created_from_invoice = True
                _logger.info(f"Sale Order {sale_order.name} marked as 'PO created from invoice'.")

        return res