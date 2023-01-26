# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Perú: Compras",

	'summary': """
		Perú: Compras""",

	'description': """
		Perú: Compras
		Modulo donde se agrega complementos para adaptadar compras a la localización peruana.
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.3',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_catalogo',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/account_move_view.xml',
		'views/afectacion_compra.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}