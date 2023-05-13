# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "SOLSE: Kardex",

	'summary': """
		Módulo que se integra con Inventario > Productos""",

	'description': """
		Módulo que se integra con Inventario > Productos
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",

	'category': 'Uncategorized',
	'version': '16.0.0.3',
	'license': 'Other proprietary',
	'depends': [
		'sale_management',
		'stock',
	],
	'data': [
		'security/ir.model.access.csv',
		'wizards/wizard_company_confirm.xml',
		'views/product_template_view.xml',
		'views/stock_move_line_view.xml',
		'views/res_company_view.xml',
	],
	'auto_install': False,
	'installable': True,
	'web_preload': True,
	'application': True,
	"sequence": 1,
}