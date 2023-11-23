# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

{
	'name': "Perú - Factoring",

	'summary': """
		Contabilidad: Factoring""",

	'description': """
		* Gestiona de cuentas contables para el control de factoring
		
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.18',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_accountant',
	],
	'data': [
		'security/ir.model.access.csv',
		'wizard/cobrar_factoring.xml',
		'wizard/garantia_factoring.xml',
		'views/res_config_settings_view.xml',
		'views/empresa_factoring_view.xml',
		'views/facturas_factoring_view.xml',
		'views/account_move_view.xml',
		'views/planillas_factoring_view.xml',
		'wizard/account_payment_register_views.xml',
	],
	'installable': True,
	'price': 690,
	'currency': 'USD',
}