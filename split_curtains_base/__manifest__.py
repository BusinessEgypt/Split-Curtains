{
    'name': 'Split Curtains Base',
    'version': '1.0',
    'summary': 'Curtain Customization',
    'description': 'Curtain order lines with area calculation',
    'author': 'Ahmed - Split Curtains',
    'license': 'LGPL-3',
    'depends': ['base', 'sale'],
    'data': [
        'views/sale_order_line_form_view.xml',
        'views/sale_order_custom_view.xml',
        # مش محتاجين الـ ignore view دلوقتي
        # 'views/sale_order_line_view_ignore.xml',
    ],
    'installable': True,
    'application': False,
}
