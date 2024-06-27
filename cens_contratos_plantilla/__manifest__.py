{
	'name': "Contratos Plantilla - CENS",

	'summary': """
		Actualizaciones adicionales para el módulo CONTRATOS""",

    'description': """
		Traslada lo hecho en Odoo Studio a código CENS.
        CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources',
 	'version': '16.0.6.05',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['base', 'hr', 'hr_contract', 'web', 'base_setup'],

	'data': [
        'security/ir.model.access.csv',
        'views/contrato_plantilla_form_cens.xml',
        'views/contrato_plantilla_camposinsert.xml',
        'views/contrato_crear.xml',
        ],

    'assets': {
        'web.assets_backend': [
            'cens_contratos_plantilla/static/**/*',
            'cens_contratos_plantilla/static/src/js/custom_script.js',
        ],
    },

    'images': [
        'static/description/barra_progreso.gif',
        'static/description/comentario.png',
        'static/description/cens-qrcode.jpg',
        'static/description/logo-modulos.png'
    ],
    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

# 'assets': {
#        'web.assets_backend': [
#            'cens_contratos_plantilla/static/src/js/text_widget.js',
#       ],
#    },
#        'views/assets.xml',


#    'assets': {
#        'web.assets_backend': [
#            'cens_contratos_plantilla/static/**/*',
#            'cens_contratos_plantilla/static/src/js/highlight_text.js',
#       ],
#    },