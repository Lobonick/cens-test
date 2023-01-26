# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

{
	'name': "Catalogo SUNAT ",

	'summary': """
		Catalogo SUNAT""",

	'description': """
		Catalogo SUNAT
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'account',
	'version': '16.0.1.1',
	'license': 'Other proprietary',
	'depends': [
		'base',
		'l10n_pe',
	],
	'data': [
		'security/pe_datas_security.xml',
		'security/ir.model.access.csv',
		'data/pe_datas.xml',
		'data/pe_datas_adicionales.xml',
		'data/pe.datas.csv',
		'views/pe_datas_view.xml',
	],
	'qweb': [],
	'installable': True,
}