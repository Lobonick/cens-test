# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models, _
import logging
import json
_logging = logging.getLogger(__name__)

INCLUIDOS = ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']

class AccountMoveSunat(models.Model):
	_inherit = 'account.move'

	@api.model
	def _get_default_fecha_factura(self):
		move_type = self._context.get('default_move_type', 'entry')
		if move_type == 'in_invoice':
			return fields.Date.context_today(self)
		else:
			return False

	invoice_date = fields.Date(string='Invoice/Bill Date', default=_get_default_fecha_factura, readonly=True, index=True, copy=False, states={'draft': [('readonly', False)]})
	fecha_tipo_cambio = fields.Date("Fecha tipo de cambio", compute="_compute_fecha_tipo_cambio", help="Fecha que se toma para el tipo de cambio.\nPara compras toma la fecha de factura y para los demás movimientos la fecha contable")

	@api.depends('move_type', 'date', 'invoice_date')
	def _compute_fecha_tipo_cambio(self):
		for reg in self:
			fecha = reg.invoice_date
			if reg.state in ['posted', 'cancel', 'annull']:
				reg.fecha_tipo_cambio = reg.date
				continue
			if reg.move_type == 'in_invoice': # Facturas proveedor
				fecha = reg.invoice_date
			elif reg.move_type == 'in_refund': # Notas de credito proveedor
				fecha = reg.reversed_entry_id.invoice_date
			elif reg.move_type == 'out_refund': # Notas de credito cliente
				fecha = reg.reversed_entry_id.invoice_date
			elif reg.move_type == 'out_invoice' and reg.es_x_apertura: # Facturas de cliente
				fecha = reg.invoice_date
			else:
				fecha = reg.date

			reg.fecha_tipo_cambio = fecha
			

	@api.depends('invoice_date', 'company_id')
	def _compute_date(self):
		self._compute_fecha_tipo_cambio()
		for move in self:
			if not move.invoice_date:
				if not move.date:
					move.date = fields.Date.context_today(self)
				continue
			accounting_date = move.invoice_date
			if not move.is_sale_document(include_receipts=True):
				accounting_date = move._get_accounting_date(move.invoice_date, move._affect_tax_report())
			if accounting_date and accounting_date != move.date:
				fecha_apertura = move.fecha_apertura or accounting_date
				move.date = fecha_apertura if move.es_x_apertura else accounting_date
				# might be protected because `_get_accounting_date` requires the `name`
				self.env.add_to_compute(self._fields['name'], move)

	def _compute_payments_widget_to_reconcile_info(self):
		for move in self:
			move.invoice_outstanding_credits_debits_widget = False
			move.invoice_has_outstanding = False

			if move.state != 'posted' \
					or move.payment_state not in ('not_paid', 'partial') \
					or not move.is_invoice(include_receipts=True):
				continue

			pay_term_lines = move.line_ids\
				.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

			domain = [
				('account_id', 'in', pay_term_lines.account_id.ids),
				('parent_state', '=', 'posted'),
				('partner_id', '=', move.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]

			payments_widget_vals = {'outstanding': True, 'content': [], 'move_id': move.id}

			if move.is_inbound():
				domain.append(('balance', '<', 0.0))
				payments_widget_vals['title'] = _('Outstanding credits')
			else:
				domain.append(('balance', '>', 0.0))
				payments_widget_vals['title'] = _('Outstanding debits')

			for line in self.env['account.move.line'].search(domain):

				if line.currency_id == move.currency_id:
					# Same foreign currency.
					amount = abs(line.amount_residual_currency)
				else:
					# Different foreign currencies.
					fecha_tipo_cambio = line.date if move.move_type not in INCLUIDOS else move.fecha_tipo_cambio
					amount = line.company_currency_id._convert(
						abs(line.amount_residual),
						move.currency_id,
						move.company_id,
						fecha_tipo_cambio,
					)

				if move.currency_id.is_zero(amount):
					continue

				payments_widget_vals['content'].append({
					'journal_name': line.ref or line.move_id.name,
					'amount': amount,
					'currency_id': move.currency_id.id,
					'id': line.id,
					'move_id': line.move_id.id,
					'date': fields.Date.to_string(line.date),
					'account_payment_id': line.payment_id.id,
				})

			if not payments_widget_vals['content']:
				continue

			move.invoice_outstanding_credits_debits_widget = payments_widget_vals
			move.invoice_has_outstanding = True

	@api.depends('company_id', 'partner_id', 'tax_totals', 'currency_id')
	def _compute_partner_credit_warning(self):
		for move in self:
			move.with_company(move.company_id)
			move.partner_credit_warning = ''
			show_warning = move.state == 'draft' and \
						   move.move_type == 'out_invoice' and \
						   move.company_id.account_use_credit_limit
			if show_warning:
				fecha_tipo_cambio = move.date if move.move_type not in INCLUIDOS else move.fecha_tipo_cambio
				amount_total_currency = move.currency_id._convert(move.tax_totals['amount_total'], move.company_currency_id, move.company_id, fecha_tipo_cambio)
				updated_credit = move.partner_id.commercial_partner_id.credit + amount_total_currency
				move.partner_credit_warning = self._build_credit_warning_message(move, updated_credit)

	def _inverse_amount_total(self):
		for move in self:
			if len(move.line_ids) != 2 or move.is_invoice(include_receipts=True):
				continue

			to_write = []

			amount_currency = abs(move.amount_total)
			fecha_tipo_cambio = move.date if move.move_type not in INCLUIDOS else move.fecha_tipo_cambio
			balance = move.currency_id._convert(amount_currency, move.company_currency_id, move.company_id, fecha_tipo_cambio)

			for line in move.line_ids:
				if not line.currency_id.is_zero(balance - abs(line.balance)):
					to_write.append((1, line.id, {
						'debit': line.balance > 0.0 and balance or 0.0,
						'credit': line.balance < 0.0 and balance or 0.0,
						'amount_currency': line.balance > 0.0 and amount_currency or -amount_currency,
					}))

			move.write({'line_ids': to_write})

	def _recompute_cash_rounding_lines(self):
		''' Handle the cash rounding feature on invoices.

		In some countries, the smallest coins do not exist. For example, in Switzerland, there is no coin for 0.01 CHF.
		For this reason, if invoices are paid in cash, you have to round their total amount to the smallest coin that
		exists in the currency. For the CHF, the smallest coin is 0.05 CHF.

		There are two strategies for the rounding:

		1) Add a line on the invoice for the rounding: The cash rounding line is added as a new invoice line.
		2) Add the rounding in the biggest tax amount: The cash rounding line is added as a new tax line on the tax
		having the biggest balance.
		'''
		self.ensure_one()
		def _compute_cash_rounding(self, total_amount_currency):
			''' Compute the amount differences due to the cash rounding.
			:param self:                    The current account.move record.
			:param total_amount_currency:   The invoice's total in invoice's currency.
			:return:                        The amount differences both in company's currency & invoice's currency.
			'''
			difference = self.invoice_cash_rounding_id.compute_difference(self.currency_id, total_amount_currency)
			if self.currency_id == self.company_id.currency_id:
				diff_amount_currency = diff_balance = difference
			else:
				diff_amount_currency = difference
				fecha_tipo_cambio = self.date if self.move_type not in INCLUIDOS else self.fecha_tipo_cambio
				diff_balance = self.currency_id._convert(diff_amount_currency, self.company_id.currency_id, self.company_id, self.date)
			return diff_balance, diff_amount_currency

		def _apply_cash_rounding(self, diff_balance, diff_amount_currency, cash_rounding_line):
			''' Apply the cash rounding.
			:param self:                    The current account.move record.
			:param diff_balance:            The computed balance to set on the new rounding line.
			:param diff_amount_currency:    The computed amount in invoice's currency to set on the new rounding line.
			:param cash_rounding_line:      The existing cash rounding line.
			:return:                        The newly created rounding line.
			'''
			rounding_line_vals = {
				'balance': diff_balance,
				'partner_id': self.partner_id.id,
				'move_id': self.id,
				'currency_id': self.currency_id.id,
				'company_id': self.company_id.id,
				'company_currency_id': self.company_id.currency_id.id,
				'display_type': 'rounding',
			}

			if self.invoice_cash_rounding_id.strategy == 'biggest_tax':
				biggest_tax_line = None
				for tax_line in self.line_ids.filtered('tax_repartition_line_id'):
					if not biggest_tax_line or tax_line.price_subtotal > biggest_tax_line.price_subtotal:
						biggest_tax_line = tax_line

				# No tax found.
				if not biggest_tax_line:
					return

				rounding_line_vals.update({
					'name': _('%s (rounding)', biggest_tax_line.name),
					'account_id': biggest_tax_line.account_id.id,
					'tax_repartition_line_id': biggest_tax_line.tax_repartition_line_id.id,
					'tax_tag_ids': [(6, 0, biggest_tax_line.tax_tag_ids.ids)],
					'tax_ids': [Command.set(biggest_tax_line.tax_ids.ids)]
				})

			elif self.invoice_cash_rounding_id.strategy == 'add_invoice_line':
				if diff_balance > 0.0 and self.invoice_cash_rounding_id.loss_account_id:
					account_id = self.invoice_cash_rounding_id.loss_account_id.id
				else:
					account_id = self.invoice_cash_rounding_id.profit_account_id.id
				rounding_line_vals.update({
					'name': self.invoice_cash_rounding_id.name,
					'account_id': account_id,
					'tax_ids': [Command.clear()]
				})

			# Create or update the cash rounding line.
			if cash_rounding_line:
				cash_rounding_line.write(rounding_line_vals)
			else:
				cash_rounding_line = self.env['account.move.line'].create(rounding_line_vals)

		existing_cash_rounding_line = self.line_ids.filtered(lambda line: line.display_type == 'rounding')

		# The cash rounding has been removed.
		if not self.invoice_cash_rounding_id:
			existing_cash_rounding_line.unlink()
			# self.line_ids -= existing_cash_rounding_line
			return

		# The cash rounding strategy has changed.
		if self.invoice_cash_rounding_id and existing_cash_rounding_line:
			strategy = self.invoice_cash_rounding_id.strategy
			old_strategy = 'biggest_tax' if existing_cash_rounding_line.tax_line_id else 'add_invoice_line'
			if strategy != old_strategy:
				# self.line_ids -= existing_cash_rounding_line
				existing_cash_rounding_line.unlink()
				existing_cash_rounding_line = self.env['account.move.line']

		others_lines = self.line_ids.filtered(lambda line: line.account_id.account_type not in ('asset_receivable', 'liability_payable'))
		others_lines -= existing_cash_rounding_line
		total_amount_currency = sum(others_lines.mapped('amount_currency'))

		diff_balance, diff_amount_currency = _compute_cash_rounding(self, total_amount_currency)

		# The invoice is already rounded.
		if self.currency_id.is_zero(diff_balance) and self.currency_id.is_zero(diff_amount_currency):
			existing_cash_rounding_line.unlink()
			# self.line_ids -= existing_cash_rounding_line
			return

		_apply_cash_rounding(self, diff_balance, diff_amount_currency, existing_cash_rounding_line)
	
	
class AccountMoveLineSunat(models.Model):
	_inherit = 'account.move.line'

	parent_move_type = fields.Selection(related='move_id.move_type', store=True, readonly=True)
