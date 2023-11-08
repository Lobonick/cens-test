from odoo import models

class AccountAccount(models.Model):
	_inherit = 'account.account'

	def is_expense_account(self):
		return False
		ma = self.env['account.account'].search([('mooring_account','=', self.id)])
		if ma and self.id:
			return True
		else:
			return False
