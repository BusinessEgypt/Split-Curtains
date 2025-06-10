# -*- coding: utf-8 -*-
{
    'name': 'Split Curtains Base',
    'version': '18.0.1.0.0',
    'summary': 'حساب أوتوماتيكي لمساحات الستائر وسعرها داخل عروض الأسعار',
    'description': """
        هذا الموديول يضيف حسابات تلقائية لمساحة الستارة، السعر لكل متر، والمساحة الكلية،
        ويقوم بربطها بالحسابات الرسمية في عرض السعر داخل Odoo.
    """,
    'category': 'Sales',
    'author': 'Split Curtains',
    'website': 'https://www.splitcurtains.com/',
    'depends': ['sale', 'purchase', 'stock_dropshipping', 'purchase_stock'], # تم تصحيح الـ depends
    'data': [
        'views/sale_order_line_form_view.xml',
        'views/sale_order_custom_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}