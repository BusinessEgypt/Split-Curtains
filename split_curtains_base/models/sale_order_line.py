from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # الحقول المخصصة (كما كانت من قبل)
    x_code = fields.Many2one(
        'product.product', string='Code',
        domain=[('sale_ok', '=', True)], ondelete='set null'
    )
    x_type = fields.Char(
        string='Type', related='x_code.categ_id.name',
        store=True, readonly=True
    )
    x_width_m = fields.Float(string='Width (m)')
    x_height_m = fields.Float(string='Height (m)')
    x_unit_area_m2 = fields.Float(
        string='Unit Area (m²)', compute='_compute_unit_area', store=True
    )
    x_quantity_units = fields.Integer(string='Quantity')
    x_total_area_m2 = fields.Float(
        string='Total Area (m²)', compute='_compute_total_area', store=True
    )
    x_price_per_m2 = fields.Float(
        string='Price per m²', compute='_compute_price_per_m2', store=True
    )
    # هنا خففنا النوع ليكون Float لأننا نستخدمه للحسابات
    x_total_price = fields.Float(
        string='Total', compute='_compute_total_price', store=True
    )

    @api.depends('x_width_m', 'x_height_m')
    def _compute_unit_area(self):
        for line in self:
            area = (line.x_width_m or 0) * (line.x_height_m or 0)
            line.x_unit_area_m2 = max(area, 2)

    @api.depends('x_unit_area_m2', 'x_quantity_units')
    def _compute_total_area(self):
        for line in self:
            line.x_total_area_m2 = line.x_unit_area_m2 * (line.x_quantity_units or 0)

    @api.depends('x_code')
    def _compute_price_per_m2(self):
        for line in self:
            line.x_price_per_m2 = line.x_code.list_price or 0

    # هنا جاء التعديل الأكثر أهمية:
    @api.depends('x_total_area_m2', 'x_price_per_m2', 'product_id', 'price_unit', 'product_uom_qty')
    def _compute_total_price(self):
        """
        هذا Compute يُدرك إن سطر الداون بايمنت يولَّد من Invoice Wizard
        لذلك يعتمد على product_id, price_unit, product_uom_qty للتعرّف عليه وإظهار قيمته الصحيحة.
        """
        for line in self:
            if line.product_id:
                prod_name = (line.product_id.name or '').lower()
                # لو اسم المنتج فيه "down payment" (الحرفية بالإنجليزي) تعامل معه
                if 'down payment' in prod_name:
                    # نحسب السعر الفعلي للداون بايمنت
                    line.x_total_price = (line.price_unit or 0.0) * (line.product_uom_qty or 0.0)
                    # (يمكن وضع `-abs(...)` لو أردنا عرضه بالسالب دائماً)
                    continue

            # السطور العادية (حساب الستائر)
            line.x_total_price = (line.x_total_area_m2 or 0.0) * (line.x_price_per_m2 or 0.0)

    @api.onchange('x_width_m', 'x_height_m', 'x_quantity_units', 'x_code')
    def _onchange_manual_fields(self):
        for line in self:
            # لو كان منتج الـ x_code هو الستارة
            if line.product_id and 'down payment' in (line.product_id.name or '').lower():
                # نفترض أنّ سطر الـ Down Payment يأتي من Wizard الفاتورة
                # وبالتالي price_unit و product_uom_qty يكونان مضبوطان من Invoice
                # هنا لا نفعل شيء، لأن Compute سيقوم بالإظهار الصحيح
                continue

            # حساب الستائر العادية (كما كان من قبل)
            area = max((line.x_width_m or 0) * (line.x_height_m or 0), 2)
            total_area = area * (line.x_quantity_units or 0)
            price_per_m2 = line.x_code.list_price or 0

            # ربط المنتج الرسمي بالكود
            line.product_id = line.x_code.id
            line.price_unit = price_per_m2
            line.product_uom_qty = total_area
