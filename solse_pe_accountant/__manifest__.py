# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

{
	'name': "Perú - Contabilidad",

	'summary': """
		Contabilidad básica para Perú""",

	'description': """
		* Gestiona asientos de apertura
		* Tipo de cambio segun la fecha correspondiente a las normas de sunat.
		* Gestiona de cuentas contables para detracciones y retenciones
		* Registro del pago de detracciones y retenciones
		* Registro de glosa para los asientos contables

	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.2',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_rate_api',
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'views/res_config_settings_view.xml',
		'views/account_move_view.xml',
		'wizard/account_payment_register_views.xml',
	],
	'installable': True,
	'price': 690,
	'currency': 'USD',
}