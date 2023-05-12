# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "CPE desde POS",

	'summary': """
		Facturación electronica desde POS""",

	'description': """
		Facturación electronica desde POS
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Operations',
	'version': '16.0.0.9',
	'license': 'Other proprietary',
	'depends': [
		'base_setup',
		'solse_pe_edi',
		'solse_pe_cpe',
		'point_of_sale',
		'sale_management',
		'pos_sale',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/solse_pos_security.xml',
		'wizard/pos_recover_wizard_view.xml',
		'wizard/sale_make_order_advance_view.xml',
		'views/pos_config_view.xml',
		#'views/pos_order_view.xml',
		'views/pos_session_view.xml',
	],
	'assets': {
		'point_of_sale.assets': [
			'solse_pe_cpe_pos/static/src/js/Chrome.js',
			'solse_pe_cpe_pos/static/src/js/screen.js',
			'solse_pe_cpe_pos/static/src/js/PaymentScreen.js',
			'solse_pe_cpe_pos/static/src/js/InvoiceButton.js',
			'solse_pe_cpe_pos/static/src/js/OrderReceipt.js',
			'solse_pe_cpe_pos/static/src/js/TicketScreen.js',
			'solse_pe_cpe_pos/static/src/js/PartnerListScreen.js',
			'solse_pe_cpe_pos/static/src/js/PartnerDetailsEdit.js',
			'solse_pe_cpe_pos/static/src/lib/String.js',
			'solse_pe_cpe_pos/static/src/lib/NumeroALetras.js',
			'solse_pe_cpe_pos/static/src/lib/qrcode.js',
			'solse_pe_cpe_pos/static/src/xml/point_of_sale.xml',
			'solse_pe_cpe_pos/static/src/xml/pos.xml',
			#'solse_pe_cpe_pos/static/src/xml/**/*',
		],
	},
	'installable': True,
	'price': 150,
	'currency': 'USD',
}