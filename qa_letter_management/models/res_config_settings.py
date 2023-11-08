from odoo import fields, models, _

class Company(models.Model):
	_inherit = 'res.company'

	advanced_journal_id = fields.Many2one('account.journal', string='Advanced journal')


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	advanced_journal_id = fields.Many2one('account.journal', string='Advanced Journal',
									 related="company_id.advanced_journal_id", readonly=False)
