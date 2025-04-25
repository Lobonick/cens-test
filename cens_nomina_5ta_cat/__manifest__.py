{
	'name': "Nómina-5ta.Categoría - CENS",

	'summary': """
		Control de la Renta 5ta.Categoría para el módulo NÓMINAS""",

    'description': """
		Adiciona la funcionalidad de controlar la automatización y control del
        concepto de Renta de 5ta.categoría SUNAT.
        CENS-PERÚ   
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.4.12',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'web'],

	'data': [
        'security/ir.model.access.csv',
        'views/nomina_5ta_cat_01.xml',
        'views/menu_items.xml',
        ],

    'assets': {
            'web.assets_backend': [
                'cens_nomina_5ta_cat/static/src/js/wide_column.js',
                'cens_nomina_5ta_cat/static/src/css/styles.css',
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
