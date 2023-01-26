# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

class Bank(models.Model) :
	_inherit = 'res.bank'
	
	l10n_pe_bank_code = fields.Selection(selection="_get_pe_banco", string='Banco')

	@api.model
	def _get_pe_banco(self):
		return self.env['pe.datas'].get_selection("PE.TABLA03")
