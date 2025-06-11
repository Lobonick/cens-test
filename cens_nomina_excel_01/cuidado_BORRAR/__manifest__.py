{
	'name': "Nómina - E-mails masivos - CENS",

	'summary': """
		Permite enviar los PDF de las Boletas de Pago de la Nómina""",

    'description': """
		Permite generar los PDF de las Boletas de Pago y enviarlas de forma MASIVA por Correo
        Electrónico, según la selección hecha en la vista TREE. CENS-PERÚ 
	""",

	'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources',
 	'version': '16.0.1.43',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['base', 'hr', 'hr_payroll', 'web', 'base_setup', 'cens_nomina_excel_01'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/mail_template.xml',
        'views/hr_payslip_views.xml',
    ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

