# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_code = fields.Many2one('product.product', string="Code")
    x_type = fields.Char(string="Type")
    x_width_m = fields.Float(string="Width (m)")
    x_height_m = fields.Float(string="Height (m)")
    x_quantity_units = fields.Integer(string="Quantity (Units)")
    x_unit_area_m2 = fields.Float(string="Unit Area (m²)")
    x_total_area_m2 = fields.Float(string="Total Area (m²)")
    x_price_per_m2 = fields.Float(string="Price per m²") # هذا الحقل ما زال يتم نقله من الـ SO، يمكنك استخدامه أو تركه يعتمد على price_unit

    x_total_price = fields.Monetary(
        string="Total Purchase Price",
        compute='_compute_x_total_purchase_price',
        store=True,
        currency_field='currency_id'
    )

    @api.depends('x_total_area_m2', 'price_unit', 'product_qty') # يعتمد الآن على سعر الوحدة وكمية الـ PO
    def _compute_x_total_purchase_price(self):
        for line in self:
            # استخدام x_total_area_m2 إذا كانت الـ PO مرتبطة بـ Area، وإلا استخدام product_qty * price_unit
            if line.x_total_area_m2 > 0 and line.x_price_per_m2 > 0:
                line.x_total_price = line.x_total_area_m2 * line.price_unit # أو line.x_price_per_m2 إذا كان هذا هو سعر الشراء per m2
            else:
                line.x_total_price = line.product_qty * line.price_unit
            # ملاحظة: تم تعديل هذا السطر ليستخدم price_unit من الـ PO وليس x_price_per_m2 من الـ SO مباشرةً
            # إذا كنت تريد أن يكون سعر الشراء هو x_price_per_m2 مضروباً في x_total_area_m2، يجب ضبط price_unit في الـ PO بناءً عليه.
            # حالياً، price_unit سيأتي من Product Supplierinfo.
            # لذا، إذا كان x_total_area_m2 هو الكمية الأساسية للشراء، فكر في ضبط product_qty = x_total_area_m2.

    # تجاوز الدالة القياسية لنقل الحقول المخصصة من sale.order.line
    @api.model
    def _prepare_purchase_order_line_from_sale_line(self, sale_line, product_id, product_qty, product_uom, company_id, supplier):
        """
        تجاوز هذه الدالة لنقل الحقول المخصصة من سطر أمر البيع إلى سطر أمر الشراء.
        """
        values = super()._prepare_purchase_order_line_from_sale_line(sale_line, product_id, product_qty, product_uom, company_id, supplier)
        
        # نقل الحقول المخصصة
        values.update({
            'x_code': sale_line.x_code.id,
            'x_type': sale_line.x_type,
            'x_width_m': sale_line.x_width_m,
            'x_height_m': sale_line.x_height_m,
            'x_quantity_units': sale_line.x_quantity_units,
            'x_unit_area_m2': sale_line.x_unit_area_m2,
            'x_total_area_m2': sale_line.x_total_area_m2,
            'x_price_per_m2': sale_line.x_price_per_m2,
            # 'x_total_price' سيتم حسابه تلقائياً
        })
        return values