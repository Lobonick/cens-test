{
	'name': "CENS-CRM-04",

	'summary': """
		Actualiza módulo CRM con Usuarios CENS.""",

    'description': """
		- Permite que el móduo LOGEE a Usuarios CENS.
        - Permite habilitar usuarios desde Ficha Empleado.
        - Según el Usuario CENS se filtran las oportunidades que le pertenecen.
	""",

	'author': "Área de Sistemas - CENS-PERÚ",
    "website": "https://www.cens.com.pe",
	'category': 'Sales/CRM',
 	'version': '16.0.1.03',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ], 
    'depends': [
        'crm',
        'hr',
        'base',
        'base_setup',
    ],
        
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/crm_lead_views.xml',
        'wizard/employee_auth_wizard_views.xml',        
    ],

    'images': [
        'static/description/comentario.png',
        'static/description/cens-qrcode.jpg',
        'static/description/logo-modulos.png'
    ],
 	'installable': True,
	'application': True,
	'auto_install': False,
 	'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}

# https://sisac-peru.com/public_html/wp-content/uploads/2024/05cens_homepage.mp4
# https://cens.pe//wp-content//uploads//2024//02//02111.mp4