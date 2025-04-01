{
	'name': "Nómina - Edita Excel 01 - CENS",

	'summary': """
		Permite generar la PLANILLA GENERAL de la Nómina""",

    'description': """
		Permite generar una WorkSheet Excel con los datos de LOTE Nómina y permite actualizar
        el las Boletas del LOTE con los datos importados desde el WorkSheet. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources',
 	'version': '16.0.3.41',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['base', 'hr', 'hr_payroll', 'web', 'base_setup'],

	'data': [
        'views/nomina_list_excel_cens.xml',
        ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

