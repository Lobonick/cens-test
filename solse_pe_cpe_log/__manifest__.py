# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

{
	'name': "Log CPE - Perú",

	'summary': """
		Manejo de errores para los cpe's SUNAT - Perú""",

	'description': """
		Manejo de errores para los cpe's SUNAT - Perú
		Manejo de errores para los cpe's SUNAT - Perú
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '16.0.0.2',
	'license': 'Other proprietary',
	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		#'security/solse_pe_cpe_security.xml',
		'data/tareas_programdas.xml',
		'views/solse_cpe_view.xml',
	],
	'installable': True,
	'price': 150,
	'currency': 'USD',
}