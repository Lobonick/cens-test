# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "SOLSE CPE Guias",

	'summary': """
		Emision de guias electronicos a SUNAT - Perú""",

	'description': """
		Facturación electrónica - Perú 
		Emision de guias electronicos a SUNAT - Perú
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.1.3',
	'license': 'Other proprietary',
	'depends': [
		'stock',
		'fleet',
		'account',
		'account_fleet',
		'product_expiry',
		'solse_pe_cpe',
		'solse_pe_cpe_sale',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/pe_sunat_eguide_view.xml',
		'views/company_view.xml',
		'views/stock_view.xml',
		'views/res_partner.xml',
		'views/cpe_server_view.xml',
		'data/sunat_eguide_data.xml',
		'report/report_guia.xml',
		'report/report_invoice.xml',
	],
	'installable': True,
	'price': 210,
	'currency': 'USD',
}