# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': 'Tipo de cambio para Perú',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'category': 'Extra Tools',
	'summary': 'Automatización de tipo de cambio para Perú',
	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'depends': [
		'base',
		'l10n_pe_currency',
		'solse_vat_pe',
	],
	'data': [
		'security/ir.model.access.csv',
		'data/ir_cron_data.xml',
		'views/account_move_view.xml',
		'views/res_currency_views.xml',
		'wizard/rango_fecha_view.xml',
	],
	'installable': True,
	'sequence': 1,
}
