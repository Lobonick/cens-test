{
    'name': "Nómina - Edita Excel 02 - CENS",

	'summary': """
		Permite Importar/Exportar WORKSHEET de Excel de los datos de la Nómina.""",

    'description': """
		Permite generar una WorkSheet Excel con los datos de LOTE Nómina y permite actualizar
        el las Boletas del LOTE con los datos importados desde el WorkSheet. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.3.08',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'web', 'cens_nomina_excel_01'],
    'assets': {
        'web.assets_backend': [
            'cens_nomina_excel_02/static/src/scss/custom_notebook.scss',
        ],
    },

	'data': [
        'security/ir.model.access.csv',
        'views/nomina_list_excel_cens.xml',
        ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

