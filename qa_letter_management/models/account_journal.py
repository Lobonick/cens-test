from odoo import models, fields, api

class AccountJournal(models.Model):
	_inherit = "account.journal"

	responsibility_account_id = fields.Many2one('account.account', string='Reponsibility Account')
	letter_type = fields.Boolean('Is letter type?')
	bank_partner_id = fields.Many2one('res.partner', string='Bank Partner')