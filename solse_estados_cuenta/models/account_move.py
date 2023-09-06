# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)



class AccountMove(models.Model):
	_inherit = 'account.move'


	fecha_ini_pago = fields.Date("Fecha inicial de pago", compute="_compute_payments_inter", store=True)
	fecha_fin_pago = fields.Date("Fecha inicial de pago", compute="_compute_payments_inter", store=True)
	payment_move_line_ids = fields.Many2many('account.move.line', string='Payment Move Lines', store=True, compute="_compute_payments_inter")

	@api.depends('line_ids','line_ids.amount_residual','line_ids.account_type')
	def _compute_payments_inter(self):
		for reg in self:
			payment_lines = set()
			lineas = reg.line_ids
			pay_term_lines = lineas.filtered(lambda line: line.account_type in ('asset_receivable', 'liability_payable'))
			for line in pay_term_lines:
			#for line in pay_term_lines:
				payment_lines.update(line.mapped('matched_credit_ids.credit_move_id.id'))
				payment_lines.update(line.mapped('matched_debit_ids.debit_move_id.id'))

			lineas_pago = self.env['account.move.line'].browse(list(payment_lines)).sorted()
			reg.payment_move_line_ids = lineas_pago
			if lineas_pago:
				fecha_ini_pago = lineas_pago[0].date
				fecha_fin_pago = lineas_pago[-1].date
			else:
				fecha_ini_pago = False
				fecha_fin_pago = False

			reg.fecha_ini_pago = fecha_ini_pago
			reg.fecha_fin_pago = fecha_fin_pago


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	factura_pagada = fields.Many2one("account.move", strign="Factura Pagada")