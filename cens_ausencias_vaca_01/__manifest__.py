{
	'name': "Ausencias-Vaca01",

	'summary': """
		Actualizaciones adicionales para el módulo AUSENCIAS que permite crear el reporte de cálculo
         de vacaciones. """,

    'description': """
		Agrega una nueva opción al módulo de ausencias.
        CENS-PERÚ 
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Human Resources/Time-Off',
 	'version': '16.0.1.01',
    'license': 'Other proprietary',
	'depends': ['base','hr','hr_holidays','calendar','resource'],
    'data': [
        'views/hr_leave_vacaciones_01.xml',
        'views/menu_items.xml',
        ],
 	'installable': True,
	'application': True,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
}
