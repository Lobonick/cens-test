{
	'name': "Nómina-bbss-liquidac-01",

	'summary': """
		Upgrade en las Boletas de Pago de la Nómina con el registro de Liquidaciones""",

    'description': """
		Permite agregar carcaterísticas y funcionalidad para el cálculo de los Beneficios 
        Sociales de Cese, en la Boletas de Pago de la Nómina. Estos cambios incluyen nuevos 
        campos y métodos. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources',
 	'version': '16.0.1.69',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['hr_payroll', 'base', 'hr', 'web', 'base_setup', 'cens_nomina_excel_01'],

	'data': [
        'views/cens_nomina_payslip_bbss.xml',
        ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

