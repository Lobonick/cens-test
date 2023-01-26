# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"
	
	origin_move_id = fields.Many2one('account.move', string='Entrada de origen', copy=False)
	origin_move_line_id = fields.Many2one('account.move.line', string='Línea de movimiento de origen', copy=False)
	target_move_ids = fields.One2many('account.move', 'origin_move_id', string='Entradas de destino', copy=False)
	target_move_count = fields.Integer('Cant. movimientos de destino', compute='_compute_count_target_move')

	def _compute_count_target_move(self):
		account_move = self.env['account.move']
		for record in self:
			record.target_move_count = account_move.search_count([('origin_move_id', '=', record.id)])

	def generar_asientos_destino_falantes(self):
		facturas = self.env['account.move'].search([("move_type", "=", "in_invoice"), ("state", "=", "posted"), ("target_move_count", "=", 0)])
		for move in facturas:
			move.crear_asiento_destino()

	def crear_asiento_destino(self):
		move = self
		for l in move.line_ids.filtered(lambda r: r.account_id.target_account == True):
			# account_id = l.account_id.id
			if not l.target_move_id:
				move_data = {
					'origin_move_id': move.id,
					'origin_move_line_id': l.id,
					'ref': l.name,
					'date': l.date,
					'journal_id': l.account_id.target_journal_id and l.account_id.target_journal_id.id or False,
					'move_type': 'entry',
				}
				target_move_id = self.env['account.move'].create(move_data)
				l.target_move_id = target_move_id

			line_data = {
				'origin_move_id': move.id,
				'origin_move_line_id': l.id,
				'name': l.name,
				'ref': move.name,
				'partner_id': l.partner_id and l.partner_id.id or False,                                    
				'currency_id': l.currency_id and l.currency_id.id or False,
			}
			
			array_debit_data = []
			array_credit_data = []

			targets = l.account_id.target_line_ids

			if l.debit != False:
				for target in targets:
					debit_data = dict(line_data)
					credit_data = dict(line_data)
					l_monto = (l.debit / (100.000 / target.percent))
					l_amount_currency = (l.amount_currency / (100.000 / target.percent))
					# Debe
					if target.type == 'd':
						debit_data.update(
							account_id = target.target_account_id.id,
							debit = l_monto,
							credit = False,
							amount_currency = l_amount_currency,
						)
						array_debit_data.append((0,0, debit_data))
					# Haber
					else:
						credit_data.update(
							account_id = target.target_account_id.id,
							debit = False,
							credit = l_monto,
							amount_currency = l_amount_currency * -1.0,
						)
						array_credit_data.append((0,0, credit_data))
			else:
				for target in targets:
					debit_data = dict(line_data)
					credit_data = dict(line_data)
					l_monto = (l.credit / (100.000 / target.percent))
					l_amount_currency = (l.amount_currency / (100.000 / target.percent))
					# Debe
					if target.type == 'd':
						debit_data.update(                                   
							account_id = target.target_account_id.id,
							debit = False,
							credit = l_monto,
							amount_currency = l_amount_currency,
						)
						array_debit_data.append((0,0, debit_data))
					# Haber
					else:
						credit_data.update(
							account_id = target.target_account_id.id,
							debit = l_monto,
							credit = False,
							amount_currency = l_amount_currency * -1.0,
						)
						array_credit_data.append((0,0, credit_data))
			
			if not l.target_move_id.line_ids:
				lineas_destino = array_debit_data + array_credit_data
				l.target_move_id.write({
					'line_ids': lineas_destino
				})
			"""else:
				for line in l.target_move_id.line_ids:
					if line.account_id.id == l.account_id.debit_target_account_id.id:
						line.write(debit_data)
					if line.account_id.id == l.account_id.credit_target_account_id.id:
						line.write(credit_data)"""
			# Post Target move
			if l.target_move_id.state == 'draft':
				l.target_move_id._post()

	def _post(self, soft=True):
		datos = super(AccountMove, self)._post(soft=soft)        
		for move in self:
			move.crear_asiento_destino()

		return datos
	
	def button_draft(self):
		super(AccountMove, self).button_draft()  
		for move in self:
			for target in move.target_move_ids:
				target.button_draft()

	def button_cancel(self):
		super(AccountMove, self).button_cancel()  
		for move in self:
			for target in move.target_move_ids:
				target.button_cancel()
	
	def open_target_move_view(self):
		[action] = self.env.ref('account.action_move_line_form').read()
		ids = self.target_move_ids.ids
		action['domain'] = [('id', 'in', ids)]
		action['name'] = 'Entradas de destino'
		return action

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	origin_move_id = fields.Many2one('account.move', string='Entrada de origen', copy=False)
	origin_move_line_id = fields.Many2one('account.move.line', string='Línea de movimiento de origen', ondelete='cascade')
	target_move_id = fields.Many2one('account.move', string='Entradas de destino', copy=False)