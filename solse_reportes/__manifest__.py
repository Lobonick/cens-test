# -*- coding: utf-8 -*-
{
	'name': "Reportes movimientos",

	'summary': """
		Reporte con informacion organizada de los principales movimientos""",

	'description': """
		Reporte con informacion organizada de los principales movimientos
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
	# for the full list
	'category': 'Uncategorized',
	'version': '16.0.0.1',

	# any module necessary for this one to work correctly
	'depends': [
		'account',
	],
	'data': [
		'security/ir.model.access.csv',
		'wizards/wizard_company_balance.xml',
		'wizards/wizard_company_money.xml',
		'views/report_money_movements.xml',
		'views/report_account_balance.xml',
		'views/payments.xml',
		'views/account_move.xml',
		'views/reports.xml',
		'views/account_journal.xml',
		'views/res_partner.xml',
		'views/res_company.xml',
	],
	'license': 'AGPL-3',
	'auto_install': False,
	'installable': True,
	'application': True,
	"sequence": 1,
}