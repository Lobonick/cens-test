# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Reporte Estados de cuenta",

	'summary': """
		Módulo para imprimir Estados de cuenta""",

	'description': """
		Módulo para imprimir Estados de cuenta
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",

	'category': 'Uncategorized',
	'version': '16.0.1.12',

	'depends': [
		'sale_management',
		'stock',
		'html_text',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'report/report_estados_cuenta.xml',
		'report/report_ventas.xml',
		'report/report_pronostico_cobranzas.xml',
		'report/report_cobranzas.xml',
		'report/report_calidad_deuda.xml',
		'wizard/wizard_estados_cuenta.xml',
		'wizard/wizard_reporte_ventas.xml',
		'wizard/wizard_pronostico_cobranzas.xml',
		'wizard/wizard_cobranzas.xml',
		'wizard/wizard_calidad_deuda.xml',
		'views/menu_view.xml',
	],
	'auto_install': False,
	'installable': True,
	'web_preload': True,
	'application': True,
	"sequence": 1,
}