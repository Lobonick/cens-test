# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Perú: Reportes financieros",

	'summary': """
		Perú: Reportes financieros""",

	'description': """
		Perú: Reportes financieros
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",

	'category': 'Financial',
	'version': '16.0.0.4',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'report_xlsx',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/account_account.xml',
		'wizard/reporte_view.xml',
		'report/reporte_compras_view.xml',
		'report/reporte_ventas_view.xml',
		'report/reporte_perdidas_ganancias_view.xml',
		'report/reporte_balance_general.xml',
		#'report/reporte_flujo_caja_view.xml',
		'views/res_config_settings_view.xml',
		'views/cierre_view.xml',
		'views/menu_view.xml',
	],
	'assets': {
		'web.report_assets_common': [
			'/solse_pe_accountant_report/static/src/css/estilos.css',
		],
	},
	'auto_install': False,
	'installable': True,
	'application': True,
	"sequence": 1,
}