# -*- coding: utf-8 -*-
{
	'name': "SOLSE Dev",

	'summary': """
		SOLSE Dev""",

	'description': """
		SOLSE Dev
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Operations',
	'version': '16.0.0.2',

	'depends': [
		'sale_management',
		'account',
		'stock',
		'solse_pe_cpe',
		'solse_pe_cpe_guias',
	],
	'data': [
		'security/ir.model.access.csv',
		'data/tareas_programadas.xml',
		'data/mail_template.xml',
		'views/herramientas_view.xml',
	],
	'qweb': [],
	'installable': True,
}