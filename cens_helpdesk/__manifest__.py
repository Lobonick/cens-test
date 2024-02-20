{
	'name': "HelpDesk - CENS",

	'summary': """
		Actualizaciones adicionales para el módulo HELP DESK""",

    'description': """
		Traslada lo hecho en Odoo Studio a código CENS.
        CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Services/Helpdesk',
 	'version': '16.0.1.26',
    'depends': [
        'base',
        'base_setup',
        'mail',
        'helpdesk',
    ],

	'data': [
        'views/helpesk_form_cens.xml',
        ],
 	'installable': True,
	'application': True,
	'auto_install': False,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
     "sequence": 1,
}
