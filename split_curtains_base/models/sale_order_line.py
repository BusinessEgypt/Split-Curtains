from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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

    @api.depends('x_total_area_m2', 'x_price_per_m2', 'product_id', 'price_unit', 'product_uom_qty', 'price_subtotal')
def _compute_total_price(self):
    for line in self:
        if line.product_id and (
            'down' in (line.product_id.name or '').lower()
            or 'down' in (line.product_id.default_code or '').lower()
        ):
            # يظهر بالسالب
            line.x_total_price = -abs(line.price_subtotal or 0)
        else:
            line.x_total_price = line.x_total_area_m2 * line.x_price_per_m2


    @api.onchange('x_width_m', 'x_height_m', 'x_quantity_units', 'x_code', 'product_id')
    def _onchange_manual_fields(self):
        for line in self:
            # لو المنتج Down Payment
            if line.product_id and (
                line.product_id.name == 'Down Payment'
                or line.product_id.default_code == 'Down Payment'
            ):
                line.x_code = line.product_id
                # مفيش تغيير في الأسعار أو الكميات هنا (سابها زي ما هي)
                return
            else:
                area = max((line.x_width_m or 0) * (line.x_height_m or 0), 2)
                total_area = area * (line.x_quantity_units or 0)
                price_per_m2 = line.x_code.list_price or 0

                line.product_id = line.x_code.id
                line.price_unit = price_per_m2
                line.product_uom_qty = total_area
