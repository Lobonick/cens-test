{
	'name': "Nómina-bbss-04",

	'summary': """
		Agrega BOTÓN para NUEVO Reporte CTS Intermitentes""",

    'description': """
		REPORTE que muestra personal INTERMITENTE con el cálculo de CTS. Estos cambios incluyen nuevos 
        campos y métodos. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
 	'version': '16.0.1.01',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'hr', 'web', 'base_setup'],

	'data': [
        'views/cens_nomina_payslip_bbss_04.xml',
        ],

    
    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

