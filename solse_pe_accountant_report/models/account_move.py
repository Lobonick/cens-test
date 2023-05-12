# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError
import logging
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def _get_cash_flow_lines(self, date_from, date_to):
		"""liquidity_accounts = self.env['account.account'].search([
			('account_type', 'in', ['asset_cash', 'liability_credit_card']),
			('deprecated', '=', False)
		]).ids"""

		liquidity_accounts = self.env['account.account'].search([
			('internal_group', '=', 'asset'),
			('reconcile', '=', True),
			('deprecated', '=', False),
			('company_id', '=', self.env.company.id),
			'|',
			('currency_id', '=', False),
			('currency_id.rate_ids', '=', False),
		])
		other_accounts = self.env['account.account'].search([
			('internal_group', '=', 'asset'),
			('reconcile', '=', False),
			('deprecated', '=', False),
			('company_id', '=', self.env.company.id),
			('account_type', 'not in', ['liability_payable', 'asset_receivable']),
			('currency_id', '=', False),
		])
		cuentas_liquides = liquidity_accounts + other_accounts
		cuentas_liquides = cuentas_liquides.ids


		lines = []
		for account in self.env['account.account'].browse(cuentas_liquides):
			# Filter moves by date and account
			moves = self.env['account.move.line'].search([
				('account_id', '=', account.id),
				('date', '>=', date_from),
				('date', '<=', date_to),
				#('exclude_from_cash_flow', '=', False),
				('move_id.state', '=', 'posted'),
				('move_id.company_id', '=', self.env.company.id)
			])

			# Calculate total inflow and outflow
			inflow = sum(moves.filtered(lambda m: m.debit > 0).mapped('debit'))
			outflow = sum(moves.filtered(lambda m: m.credit > 0).mapped('credit'))
			if not inflow and not outflow:
				continue

			# Append cash flow line to the list
			lines.append({
				'account': account.name,
				'inflow': inflow,
				'outflow': outflow,
				'net_flow': inflow - outflow
			})
		return lines


	
	def _get_cash_flow_lines_2(self, start_date, end_date):
		"""
		Obtener las líneas de flujo de caja para el período dado
		"""
		# obtener todas las cuentas de efectivo y equivalentes de efectivo
		cash_accounts = self.env['account.account'].search([
			('user_type_id.type', 'in', ['liquidity', 'payable', 'receivable'])
		])

		#move_lines = self.line_ids.filtered(lambda x: x.account_id.user_type_id.type in ['liquidity', 'payable', 'receivable'])
		cash_account_ids = tuple(cash_accounts.ids)
		if not cash_account_ids:
			raise UserError(_('No hay cuentas de efectivo y equivalentes de efectivo.'))

		# obtener movimientos de caja para las cuentas de efectivo y equivalentes de efectivo para el período dado
		domain = [
			('account_id', 'in', cash_account_ids),
			('date', '>=', start_date),
			('date', '<=', end_date),
			('move_id.state', '=', 'posted'),
			('account_id.internal_type', 'in', ('liquidity', 'other'))
		]
		cash_flow_lines = self.env['account.move.line'].search(domain)

		# ordenar las líneas por fecha y cuenta
		cash_flow_lines = cash_flow_lines.sorted(key=lambda l: (l.date, l.account_id.code))

		return cash_flow_lines