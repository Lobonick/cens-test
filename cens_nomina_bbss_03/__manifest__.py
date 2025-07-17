{
	'name': "Nómina-bbss-liquidac-03",

	'summary': """
		Agrega BOTÓN para Reporte de GRATIFICACIONES""",

    'description': """
		Permite agregar características y funcionalidad para el REPORTE que muestra 
        a todo el personal calculando la GRATIFICACIÓN. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.1.01',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'hr', 'web', 'base_setup', 'cens_nomina_excel_01'],

	'data': [
        'views/cens_nomina_payslip_bbss_03.xml',
        ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

