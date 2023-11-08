# -*- coding: utf-8 -*-
{
    'name': "QA Gestión de Letras por Pagar Perú",

    'summary': """ complemento del módulo Gestión de Letras """,

    'description': """
        Campos, tablas y funcionalidades de la gestión de letras estándar, para proveedores - Perú
    """,

    'author': "GRUPO QUANAM S.A.C.",
    'website': "https://www.grupoquanam.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'sequence': 0,
    'category': 'Development',
    'version': '14.0.1',
    'application': True,
    'installable': True,
    'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': [
        'qa_letter_management'
        ],

    # always loaded
    'data': [
        'views/letter_management_view.xml',
        'views/account_move_view.xml',
        'views/menu.xml',
        ],
    }