# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Extension CPE para Enterprise",

	'summary': """
		Extension CPE para Enterprise""",

	'description': """
		Extension CPE para Enterprise
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.1',

	'depends': [
		'account',
		'solse_pe_cpe',
	],
	
	'data': [
		#'security/ir.model.access.csv',
		'report/report_invoice.xml',
		'report/report_invoice_p2.xml',
	],
	'assets': {
		'web.report_assets_common': [
			'/solse_fercor/static/src/css/reportes.css',
		],
	},
	'installable': True,
	'price': 15,
	'currency': 'USD',
}