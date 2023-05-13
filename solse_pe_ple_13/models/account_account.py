# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountAccount(models.Model):
	_inherit = 'account.account'

	is_inventory_account = fields.Boolean(string='Es cuenta contable de inventario', compute='compute_is_inventory_account',store=True)

	def action_compute_is_inventory_account(self):
		for record in self:
			if record.code and len(record.code) >= 2 and record.code[:2] in ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']:
				is_inventory_account = True
			else:
				is_inventory_account = False
			record.is_inventory_account = is_inventory_account
			
	@api.depends('code')
	def compute_is_inventory_account(self):
		self.action_compute_is_inventory_account()