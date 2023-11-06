{
	'name': "Ausencias - CENS",

	'summary': """
		Actualizaciones adicionales para el módulo AUSENCIAS""",

    'description': """
		Agrega nuevo campo para el correlativo interno (AU-000000).
        CENS-PERÚ 
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Human Resources/Time-Off',
 	'version': '1.0.2.10',
	'depends': ['base','hr','hr_holidays','calendar','resource'],
	'data': ['views/hr_leave_view_form_cens.xml'],
 	'installable': True,
	'application': True,
	'auto_install': False,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
}
