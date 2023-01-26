# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form


class AccountAccount(models.Model):
	_inherit = "account.account"
	
	debit_target_account_id = fields.Many2one('account.account', string='Cuenta destino de débito')
	credit_target_account_id = fields.Many2one('account.account', string='Cuenta destino de crédito')
	
	target_account = fields.Boolean(string='Tiene cuenta de destino', default=False)
	target_journal_id = fields.Many2one('account.journal', string='Diario de destino')

	target_line_ids = fields.One2many('solse.target.move', 'account_id', 'Lineas destino')

	@api.constrains('target_line_ids')
	def _check_credit_amount(self):
		for reg in self:
			suma_debe = 0
			suma_haber = 0
			for linea in reg.target_line_ids:
				if linea.type == 'd':
					suma_debe = suma_debe + linea.percent
				elif linea.type == 'h':
					suma_haber = suma_haber + linea.percent
			if suma_debe != 100:
				raise ValidationError('La sumatoria del Debe tiene que ser 100.')

			if suma_haber != 100:
				raise ValidationError('La sumatoria del Haber tiene que ser 100.')


class TargetMove(models.Model):
	_name = "solse.target.move"
	_description = "Asiento de destino"
	_order = "type"

	account_id = fields.Many2one('account.account', 'Cuenta Origen', ondelete='cascade', index=True)
	target_account_id = fields.Many2one('account.account', 'Asiento de destino', ondelete='cascade', index=True)
	type = fields.Selection([('d', 'Debe'), ('h', 'Haber')], string='Tipo', index=True, default='d')
	percent = fields.Float('Porcentaje %')
	
