{
	'name': "Nómina-Liquidación BBSS - CENS",

	'summary': """
		Liquidación de Beneficios Sociales (BBSS) perteneciente al módulo NÓMINAS""",

    'description': """
		Adiciona la funcionalidad de controlar la automatización y control de las
        liquidaciones de Beneficios Sociales del personal CESADO.
        CENS-PERÚ   
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.1.01',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'hr', 'web', 'mail', 'base_setup'],

	'data': [
        'security/ir.model.access.csv',
        'views/nomina_liquidaciones_bbss.xml',
        'views/menu_items.xml',
        'reports/liquidacion_bbss_report.xml',
        'reports/liquidacion_bbss_template.xml',
        ],

    'images': [
        'static/description/barra_progreso.gif',
        'static/description/cens-qrcode.jpg',
        'static/description/firma_cens.jpg',
        'static/description/sello_agua.png',
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
