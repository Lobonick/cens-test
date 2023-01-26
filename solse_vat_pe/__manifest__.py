# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
{
	'name': "Búsqueda RUC/DNI",

	'summary': """
		Obtener datos con RUC o DNI
		""",

	'description': """
		Obtener los datos por RUC o DNI
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",

	'category': 'Uncategorized',
	'version': '16.0.0.3',
	'license': 'Other proprietary',
	'depends': ['base', 'l10n_pe'],

	'data': [
		'security/ir.model.access.csv',
		'data/res_city_data.xml',
		'wizard/busqueda_view.xml',
		'views/company_view.xml',
		'views/res_partner_view.xml',
	],
	'demo': [],
	'installable': True,
	'auto_install': False,
	'application': True,
	"sequence": 1,
}