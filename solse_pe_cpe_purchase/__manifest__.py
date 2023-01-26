# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Perú: Compras",

	'summary': """
		Enlace del modulo de compras con la creacion de facturas usando el tipo de documento correspondiente""",

	'description': """
		Facturación - Perú 
		Enlace del modulo de compras con la creacion de facturas usando el tipo de documento correspondiente
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.2',
	'license': 'Other proprietary',
	'depends': [
		'purchase',
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'views/detalle_compras_view.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}