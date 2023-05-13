# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
{
	'name': "Guias Electronicas Masivas (Sunat)",

	'summary': """
		Guias Electronicas Masivas (Sunat)""",

	'description': """
		Guias Electronicas Masivas (Sunat)
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",

	'category': 'Financial',
	'version': '16.0.0.1',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'stock',
		'stock_picking_batch',
		'solse_pe_cpe',
		'solse_pe_cpe_guias',
	],
	'data': [
		'views/stock_picking_batch_views.xml',
		'wizard/stock_picking_to_batch.xml',
	],
	'auto_install': False,
	'installable': True,
	'application': True,
	"sequence": 1,
}