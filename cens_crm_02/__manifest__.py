{
	'name': "CENS-CRM-02",

	'summary': """
		Actualizaciones adicionales para el módulo CRM, permite insertar una IMAGEN JPG
        en el áre de comentarios, también envía un Email al crear una nuev ON, también 
        etermina en usuario activo.""",

    'description': """
		Este módulo extiende la funcionalidad del CRM para incluir:
        - Adjuntar imágenes JPG automáticamente en el historial de mensajes
        - Envío automático de correo de alerta al crear una nueva oportunidad
        - Integración con el sistema de actividades (mail.activity)
        - Campos adicionales para control y asignación
        - Funcionalidades específicas para el equipo de ventas
        - Almacena el último filtro usado x usuario
        - Coloca opción para indicar: PREVENTA ENCARGADO.
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Sales/CRM',
 	'version': '16.0.1.64',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ], 

    'depends': [
        'crm',
        'mail',
        'base',
        'base_setup',
        'web',
    ],

	'data': [
        'security/ir.model.access.csv',
        'views/crm_form_cens_02.xml',
        'wizards/whatsapp_info_dialog_views.xml',
        ],

    'images': [
        'static/description/aviso-novedades-01.jpg',
        'static/description/comentario.png',
        'static/description/cens-qrcode.jpg',
        'static/description/logo-modulos.png',
        'static/description/logo-modulos.ico'
    ],
    'external_dependencies': {
        'python': ['requests'],
    },

    'assets': {
        'web.assets_backend': [
            'cens_crm_02/static/src/js/button_effects.js',
            'cens_crm_02/static/src/scss/effects.scss',
        ],
    },
    # 'static/src/scss/effects.scss',
    # 'cens_crm_02/static/src/js/button_effects.js',

 	'installable': True,
	'application': True,
	'auto_install': False,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}
