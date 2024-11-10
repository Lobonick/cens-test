{
	'name': "Nómina - Edita Excel - CENS",

	'summary': """
		Permite Importar/Exportar Excel los datos de la Nómina""",

    'description': """
		Permite generar una WorkSheet Excel con los datos de LOTE Nómina y permite actualizar
        el las Boletas del LOTE con los datos importados desde el WorkSheet. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.1.03',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base'],

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

