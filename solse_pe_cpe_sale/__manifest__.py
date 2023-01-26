# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "CPE Ventas",

	'summary': """
		Enlace del modulo de ventas con la creacion de facturas electronicas""",

	'description': """
		Facturación electrónica - Perú 
		Enlace del modulo de ventas con la creacion de facturas electronicas
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.3',
	'license': 'Other proprietary',
	'depends': [
		'sale',
		'sale_management',
		'solse_pe_edi',
		'solse_pe_cpe',
		'sale_discount_total',
	],
	'data': [
		'data/tarea_programada.xml',
		'views/sale_order_view.xml',
		'views/detalle_ventas_view.xml',
		'report/report_sale_ticket.xml',
		'report/report_invoice.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}