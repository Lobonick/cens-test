# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

{
	'name': "SOLSE: Personalización para CENS",

	'summary': """
		Personalización para CENS""",

	'description': """
		* Personalización para CENS

	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_rate_api',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_accountant',
	],
	'data': [
		'wizard/account_payment_register_views.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}