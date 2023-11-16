# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

{
	'name': "Factoring - Added",

	'summary': """
		Contabilidad: Planilla de Factoring""",

	'description': """
		Inserta características adicionales al FORM de Planilla Factoring
		
	""",

	'author': "Sistemas ODOO-CENS-PERÚ",
 	"website": "https://www.cens.com.pe",
	'category': 'Financial',
	'version': '16.0.1.03',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_edi',
		'solse_pe_cpe',
		'solse_pe_accountant',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/planillas_factoring_cens_view.xml',
	],
    'installable': True,
	'price': 10,
	'currency': 'USD',
	'application': True,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",

}