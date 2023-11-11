# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

{
	'name': "Facturación - Added",

	'summary': """
		Complemento para módulo de Facturación - Contabilidad - Perú""",

	'description': """
		* Agrega botón que inserta número de orden en el detalle de la factura

	""",

	'author': "Sistemas ODOO-CENS-PERÚ",
 	"website": "https://www.cens.com.pe",
    'category': 'accounting',
	'version': '1.0.0.04',
	'license': 'Other proprietary',
	'depends': [
		'account',
		'solse_pe_rate_api',
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'views/account_move_view.xml',
	],
	'installable': True,
	'price': 10,
	'currency': 'USD',
	'application': True,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",

}