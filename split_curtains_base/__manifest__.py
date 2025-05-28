# -*- coding: utf-8 -*-
{
    'name': 'Split Curtains Base',
    'version': '18.0.1.0.0',
    'summary': 'حساب أوتوماتيكي للمقاسات والسعر في الكوتيشن',
    'category': 'Sales',
    'author': 'Split Curtains',
    'depends': ['sale'],
    'data': [
        'views/sale_order_custom_view.xml',
        'views/sale_order_line_form_view.xml',
        'views/sale_order_line_tree_view.xml',
    ],
    'installable': True,
    'application': False,
}
