# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': 'PLE SUNAT - Base',
	'version': '16.0.0.4',
	'license': 'Other proprietary',
	'summary': 'Base para la declaración de PLE a SUNAT',
	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'description': """
		Contempla los libros electronicos de compras, ventas y libro diario.
	""",
	'depends': [
		'l10n_latam_invoice_document',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_accountant',
		'solse_pe_purchase',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/sunat_ple_security.xml',
		'views/product_view.xml',
		'views/res_partner_views.xml',
		'views/account_payment_views.xml',
		'views/account_move_view.xml',
		'views/res_bank_views.xml',
		'views/l10n_latam_document_type_view.xml',
		'views/ple_report_views.xml',
		'views/ple_menu_view.xml',
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
