{
	'name': "CENS-CRM-02",

	'summary': """
		Actualizaciones adicionales para el módulo CRM""",

    'description': """
		- Envía E-mail si detecta un comentario en la ON.
        - Almacena el último filtro usado x usuario
        - Coloca opción para indicar: PREVENTA ENCARGADO.
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Sales/CRM',
 	'version': '16.0.1.02',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ], 
    'depends': [
        'crm',
        'mail',
        'base',
        'base_setup',
    ],

	'data': [
        'views/crm_form_cens_02.xml',
        ],

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

# https://sisac-peru.com/public_html/wp-content/uploads/2024/05cens_homepage.mp4
# https://cens.pe//wp-content//uploads//2024//02//02111.mp4