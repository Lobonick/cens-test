{
	'name': "CRM - CENS",

	'summary': """
		Actualizaciones adicionales para el módulo CRM""",

    'description': """
		Traslada lo hecho en Odoo Studio a código CENS.
        CENS-PERÚ 
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Sales/CRM',
 	'version': '16.0.2.32',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ], 
    'depends': [
        'crm',
        'base',
        'base_setup',
    ],

	'data': [
        'views/crm_form_cens.xml',
        ],

    'assets': {
            'web.assets_backend': [
                'cens_crm/static/src/js/popup_message.js',
                'cens_crm/static/src/css/custom_styles.css',
            ],
        },

    'images': [
        'static/description/comentario.png',
        'static/description/cens-qrcode.jpg',
        'static/description/logo-modulos.png'
    ],
 	'installable': True,
	'application': True,
	'auto_install': False,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}
