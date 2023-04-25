# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Extension CPE para Empresa: CENS",

	'summary': """
		Extension CPE para Empresa: CENS""",

	'description': """
		Extension CPE para Empresa: CENS
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.1',

	'depends': [
		'account',
		'solse_pe_cpe',
		'solse_pe_cpe_e',
		'l10n_pe_edi',
	],
	
	'data': [],
	'assets': {
		'web.report_assets_common': [],
	},
	'installable': True,
	'price': 15,
	'currency': 'USD',
}