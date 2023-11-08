# -*- coding: utf-8 -*-
{
	'name': "QA Gestión de Letras Perú",

	'summary': """
		Gestión de Letras""",

	'description': """
		Viene con el módulo de Multipagos.
		Campos, tablas y funcionalidades de la gestión de letras estándar - Perú
		
	""",

	'author': "GRUPO QUANAM S.A.C.",
	'website': "https://www.grupoquanam.com/",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
	# for the full list
	'sequence': 0,
	'category': 'Development',
	'version': '16.0.1',
	'application': True,
	'installable': True,
	'auto_install': False,

	# any module necessary for this one to work correctly
	'depends': [
		'base',
		'account',
		'utm',
		'l10n_pe',
		'solse_pe_edi',
		#'qa_standard_locations_account',
		#'qa_invoice_multi_payment',
	],

	# always loaded
	'data': [
		'security/ir.model.access.csv',
		'reports/report_letter_template.xml',
		'views/letter_management_view.xml',
		'views/account_move_view.xml',
		#'views/account_update_view.xml',
		'views/account_journal_view.xml',
		'views/res_company_view.xml',
		'views/menu.xml',
		'views/ubications_master_view.xml',
		'views/paperformat.xml',
		'views/report.xml',
		'views/report_letter_agra.xml',
		'views/res_config_settings.xml',
		'data/mail_template_data.xml',
		'wizard/account_invoice_send_views.xml',
		'wizard/get_post_date_and_rate.xml',
		'data/ir_sequence_data.xml',
		'data/sunat_document_type.xml',
	],
}
