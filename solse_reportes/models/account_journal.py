# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	balance = fields.Monetary('Saldo', default=0)

	def action_view_money_movement(self):
		self.ensure_one()
		action = self.env.ref('solse_reportes.action_report_money_movements').read()[0]
		action['domain'] = [('state', 'not in', ['cancelled', 'draft']), ('journal_mov.id', 'in', self.ids)]
		action['limit'] = 60
		return action
