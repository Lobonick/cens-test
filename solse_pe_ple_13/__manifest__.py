# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': 'SUNAT - PLE 13',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'summary': 'Contempla los libros electronicos de inventario - PLE SUNAT',
	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'description': """
		Contempla los libros electronicos de inventario.
	""",
	'depends': [
		'account',
		'stock',
		'l10n_latam_invoice_document',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_cpe_guias',
		'solse_pe_accountant',
		'solse_pe_ple',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/sunat_ple_security.xml',
		'views/account_account_views.xml',
		'views/account_move_views.xml',
		'views/ple_report_views.xml',
		'views/stock_picking_views.xml',
		'views/stock_move_views.xml',
	],
	'external_dependencies': {
		'python': [
			'pandas',
			'xlsxwriter',
			'openpyxl',
		],
	},
	'auto_install': False,
	'installable': True,
	'application': True,
	'sequence': 1,
}
