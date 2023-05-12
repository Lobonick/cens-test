# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

{
	'name': "F&M SOLSE EDI ",

	'summary': """
		F&M SOLSE EDI""",

	'description': """
		F&M SOLSE EDI
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'account',
	'version': '16.0.1.3',
	'license': 'Other proprietary',
	'depends': [
		'base',
		'account',
		'l10n_pe',
		'l10n_latam_invoice_document',
		'solse_pe_catalogo',
	],
	'data': [
		'security/pe_datas_security.xml',
		'security/ir.model.access.csv',
		'data/account_tax_data.xml',
		'data/l10n_latam_document_type_data.xml',
		'data/res_currency_data.xml',
		'views/l10n_latam_document_type_view.xml',
		'views/company_view.xml',
		'views/accoun_move_view.xml',
		'views/product_view.xml',
		'views/res_country_data.xml',
		'views/res_partner_view.xml',
	],
	'qweb': [],
	'installable': True,
}