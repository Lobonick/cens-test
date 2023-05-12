# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "CPE Stock",

	'summary': """
		Permite enlazar facturas diramente con las guias""",

	'description': """
		Facturación electrónica - Perú 
		Permite enlazar facturas diramente con las guias sin pasar por cotizaciones.
		Permite retornar stock al anular una factura
		Permite retornar stock al generar nota de credito
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.5',
	'license': 'Other proprietary',
	'depends': [
		'stock',
		'stock_account',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_cpe_guias',
	],
	'data': [
		'data/tareas_programadas.xml',
		'views/account_move_view.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}