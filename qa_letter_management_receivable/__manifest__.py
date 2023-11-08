# -*- coding: utf-8 -*-
{
	'name': "QA Gestión de Letras por Cobrar Perú",

	'summary': """ complemento del módulo Gestión de Letras """,

	'description': """
		Campos, tablas y funcionalidades de la gestión de letras estándar, para clientes - Perú
	""",

	'author': "GRUPO QUANAM S.A.C.",
	'website': "https://www.grupoquanam.com/",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
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
		'security/ir.model.access.csv',
		'views/letter_management_view.xml',
		'views/account_move_view.xml',
		'views/account_payment_register_views.xml',
		'views/res_company_view.xml',
		'views/menu.xml',
		'wizard/get_fees_comissions.xml',
	],
}
