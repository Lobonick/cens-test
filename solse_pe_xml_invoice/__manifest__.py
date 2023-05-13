# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Importar Facturas desde XML",

	'summary': """
		Permite registrar facturas de forma masiva desde los xml""",

	'description': """
		Facturación electrónica - Perú 
		Permite registrar facturas de forma masiva desde los xml
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_cpe_report',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/scpe_pe_purchase_view.xml',
		'views/scpe_pe_invoice_sale_view.xml',
		'views/account_move_view.xml',
		'views/menu_view.xml',
	],
	'installable': True,
	'price': 200,
	'currency': 'USD',
}