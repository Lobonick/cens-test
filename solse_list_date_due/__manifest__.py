# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "SOLSE: Ver vencimiento de facturas",

	'summary': """
		SOLSE: Ver vencimiento de facturas""",

	'description': """
		SOLSE: Ver vencimiento de facturas
		Adaptaciones para ver vencimiento de facturas
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Operations',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'depends': [
		'base',
		'account',
		'solse_pe_cpe',
	],
	'data': [
		#'security/ir.model.access.csv',
		'views/detalle_vencimiento_facturas.xml',
	],
	'assets': {
		'point_of_sale.assets': [],
	},
	'installable': True,
	'price': 3,
	'currency': 'USD',
}