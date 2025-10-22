{
	'name': "Vacaciones - Genera Excel - CENS",

	'summary': """
		Permite Exportar a Excel los datos de las Vacaciones""",

    'description': """
		Permite generar una WorkSheet Excel con los datos de las vacaciones - CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Time Off',
 	'version': '16.0.1.02',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_holidays', 'base', 'hr'],

	'data': [
        'views/cens_vacaciones_excel_01.xml',
        ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

