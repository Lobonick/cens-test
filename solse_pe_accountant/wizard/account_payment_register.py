# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class AccountPaymentRegister(models.TransientModel):
	_inherit = 'account.payment.register'

	es_detraccion_retencion = fields.Boolean("Es por Detracción/Retención", help="Marcar si el pago es por la detracción o retención")
	tipo = fields.Selection([("normal", "Normal"), ("detraccion", "Detracción"), ("retencion", "Retención")], default="normal", string="Tipo pago")
	communication = fields.Char(string="Memo", store=True, readonly=False, compute='_compute_communication_2')
	transaction_number = fields.Char(string='Número de operación')
	mostrar_check = fields.Boolean("Mostrar check", compute="_compute_mostrar_check", store=True)

	@api.depends('line_ids', 'line_ids.move_id')
	def _compute_mostrar_check(self):
		for reg in self:
			factura = reg.line_ids[0].move_id
			mostrar_check = True
			if factura.pago_detraccion:
				mostrar_check = False
			if not factura.tiene_detraccion and not factura.tiene_retencion:
				mostrar_check = False
			reg.mostrar_check = mostrar_check

	@api.depends('can_edit_wizard', 'line_ids')
	def _compute_communication_2(self):
		for wizard in self:
			if wizard.can_edit_wizard:
				factura = wizard.line_ids[0].move_id
				if factura:
					dato = factura.name
					partes = dato.split(" ")
					dato = partes[1] if len(partes) == 2 else partes[0]
					wizard.communication = dato
				else:
					batches = wizard._get_batches()
					wizard.communication = wizard._get_batch_communication(batches[0])

			else:
				factura = wizard.line_ids[0].move_id
				if factura:
					dato = factura.name
					partes = dato.split(" ")
					dato = dato if len(partes) == 1 else dato[1]
					wizard.communication = dato
				else:
					wizard.communication = False

	@api.onchange('es_detraccion_retencion', 'journal_id', 'currency_id')
	def _onchange_detraccion_retencion(self):
		factura = self.line_ids[0].move_id
		self.payment_difference_handling = "open"
		#self._compute_currency_id()
		if self.es_detraccion_retencion and not factura.pago_detraccion:
			if self.tipo == 'normal':
				self.tipo = 'detraccion'
			self.currency_id = self.env.ref('base.PEN')
			self.amount = factura.monto_detraccion + factura.monto_retencion
		elif factura.tiene_detraccion and factura.pago_detraccion:
			source_amount_currency = self.source_amount_currency
			if source_amount_currency + 1 > factura.monto_neto_pagar_base:
				total_descontar = factura.monto_neto_pagar_base
				
			else:
				total_descontar = source_amount_currency
				
			self.amount = total_descontar
		elif factura.company_id.currency_id.id == self.currency_id.id:
			source_amount = self.source_amount
			self.amount = source_amount - factura.monto_detraccion - factura.monto_retencion
		else:
			source_amount_currency = self.source_amount_currency
			self.amount = source_amount_currency - factura.monto_detraccion_base - factura.monto_retencion_base

	@api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
	def _compute_amount(self):
		for wizard in self:
			wizard._onchange_detraccion_retencion()
			"""if wizard.source_currency_id == wizard.currency_id:
				# Misma moneda.
				wizard.amount = wizard.source_amount_currency
			elif wizard.currency_id == wizard.company_id.currency_id:
				# Pago expresado en la moneda de la empresa.
				wizard.amount = wizard.source_amount
			else:
				# Moneda extranjera de pago diferente a la fijada en los asientos de diario.
				amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
				wizard.amount = amount_payment_currency"""

	
	@api.onchange('amount')
	def _onchange_amount(self):
		payment_difference_handling = 'open'
		factura = self.line_ids[0].move_id
		if self.tipo == 'detraccion' and factura.move_type == 'in_invoice':
			cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
			cuenta_det_id = int(cuenta_det_id)
			#payment_vals['destination_account_id'] = cuenta_det_id
			monto_detraccion = abs(factura.amount_total_signed) - factura.monto_neto_pagar
			diferencia = monto_detraccion - self.amount
			if diferencia:
				payment_difference_handling = 'reconcile'

		self.payment_difference_handling = payment_difference_handling

	@api.onchange('payment_difference_handling')
	def _onchange_payment_difference_handling(self):

		if self.payment_difference_handling == 'reconcile':
			cuenta_diferencia = False
			if self.payment_difference > 0:
				cuenta_diferencia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detrac_ganancias')
				cuenta_diferencia = int(cuenta_diferencia)
			else:
				cuenta_diferencia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detrac_perdidas')
				cuenta_diferencia = int(cuenta_diferencia)
			self.writeoff_account_id = cuenta_diferencia

	def _create_payment_vals_from_wizard(self, batch_result):
		payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
		payment_vals['transaction_number'] = self.transaction_number
		factura = self.line_ids[0].move_id

		crear_diferencia = False
		if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
			crear_diferencia = True

		if self.tipo == 'detraccion' and factura.move_type == 'in_invoice':
			cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
			cuenta_det_id = int(cuenta_det_id)
			payment_vals['destination_account_id'] = cuenta_det_id
			monto_detraccion = abs(factura.amount_total_signed) - factura.monto_neto_pagar
			diferencia = monto_detraccion - self.amount
			
			if diferencia and not crear_diferencia:
				if diferencia > 0:
					cuenta_diferencia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detrac_ganancias')
					cuenta_diferencia = int(cuenta_diferencia)
				else:
					cuenta_diferencia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detrac_perdidas')
					cuenta_diferencia = int(cuenta_diferencia)

				payment_vals['write_off_line_vals'] = {
					'name': 'Diferencia por decimales en la detracción',
					'amount': round(diferencia, 3),
					'account_id': cuenta_diferencia,
				}

		if self.tipo == 'retencion' and factura.move_type == 'in_invoice':
			cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
			cuenta_det_id = int(cuenta_det_id)
			payment_vals['destination_account_id'] = cuenta_det_id

		#self.payment_difference_handling = 'reconcile'
		return payment_vals

	def _create_payments(self):
		self.ensure_one()
		batches = self._get_batches()
		first_batch_result = batches[0]
		edit_mode = self.can_edit_wizard and (len(first_batch_result['lines']) == 1 or self.group_payment)
		to_process = []

		if edit_mode:
			payment_vals = self._create_payment_vals_from_wizard(first_batch_result)
			to_process.append({
				'create_vals': payment_vals,
				'to_reconcile': first_batch_result['lines'],
				'batch': first_batch_result,
			})
		else:
			# Don't group payments: Create one batch per move.
			if not self.group_payment:
				new_batches = []
				for batch_result in batches:
					for line in batch_result['lines']:
						new_batches.append({
							**batch_result,
							'payment_values': {
								**batch_result['payment_values'],
								'payment_type': 'inbound' if line.balance > 0 else 'outbound'
							},
							'lines': line,
						})
				batches = new_batches

			for batch_result in batches:
				to_process.append({
					'create_vals': self._create_payment_vals_from_batch(batch_result),
					'to_reconcile': batch_result['lines'],
					'batch': batch_result,
				})

		payments = self._init_payments(to_process, edit_mode=edit_mode)
		self._post_payments(to_process, edit_mode=edit_mode)
		self._reconcile_payments(to_process, edit_mode=edit_mode)
		return payments

	def _create_payments(self):
		self.ensure_one()
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
		cuenta_det_id = int(cuenta_det_id)

		cuenta_ret_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
		cuenta_ret_id = int(cuenta_ret_id)

		batches = self._get_batches()
		batch_result = batches[0]
		factura = self.line_ids[0].move_id

		if self.tipo == 'detraccion':
			if factura.pago_detraccion:
				raise UserError('Ya existe un pago por detracción')
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] == cuenta_det_id:
					batch_result = lot
					break

		elif self.tipo == 'retencion':
			if factura.pago_detraccion:
				raise UserError('Ya existe un pago por detracción')
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] == cuenta_ret_id:
					batch_result = lot
					break

		else:
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] != cuenta_det_id:
					batch_result = lot
					break

		edit_mode = self.can_edit_wizard and (len(batch_result['lines']) == 1 or self.group_payment)
		to_process = []

		if edit_mode:
			payment_vals = self._create_payment_vals_from_wizard(batch_result)
			to_process.append({
				'create_vals': payment_vals,
				'to_reconcile': batch_result['lines'],
				'batch': batch_result,
			})
		else:
			# Don't group payments: Create one batch per move.
			if not self.group_payment:
				new_batches = []
				for batch_result in batches:
					for line in batch_result['lines']:
						new_batches.append({
							**batch_result,
							'lines': line,
						})
				batches = new_batches

			for batch_result in batches:
				to_process.append({
					'create_vals': self._create_payment_vals_from_batch(batch_result),
					'to_reconcile': batch_result['lines'],
					'batch': batch_result,
				})

		payments = self._init_payments(to_process, edit_mode=edit_mode)
		self._post_payments(to_process, edit_mode=edit_mode)
		self._reconcile_payments(to_process, edit_mode=edit_mode)

		if payments and self.tipo == 'detraccion':
			factura.pago_detraccion = payments[0].id

		return payments

	@api.depends('line_ids')
	def _compute_from_lines(self):
		''' Load initial values from the account.moves passed through the context. '''
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
		cuenta_det_id = int(cuenta_det_id)

		cuenta_ret_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
		cuenta_ret_id = int(cuenta_ret_id)

		for wizard in self:
			batches = wizard._get_batches()
			factura = self.line_ids[0].move_id
			if factura.move_type == 'in_invoice':
				batch_result = batches[0]
				if self.tipo == 'detraccion':
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_det_id:
							batch_result = lot
							break

				elif self.tipo == 'retencion':
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_ret_id:
							batch_result = lot
							break
				else:
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] != cuenta_det_id:
							batch_result = lot
							break
				
				wizard_values_from_batch = wizard._get_wizard_values_from_batch(batch_result)
				if len(batches) > 1:
					for indice in range(1, len(batches)):
						temp = batches[indice]
						temp = wizard._get_wizard_values_from_batch(temp)
						wizard_values_from_batch['source_amount'] = wizard_values_from_batch['source_amount'] + temp['source_amount']
						wizard_values_from_batch['source_amount_currency'] = wizard_values_from_batch['source_amount_currency'] + temp['source_amount_currency']
				wizard.update(wizard_values_from_batch)
				wizard.can_edit_wizard = True
				wizard.can_group_payments = len(batch_result['lines']) != 1
			else:
				batch_result = batches[0]
				wizard_values_from_batch = wizard._get_wizard_values_from_batch(batch_result)
				if len(batches) == 1:
					# == Single batch to be mounted on the view ==
					wizard.update(wizard_values_from_batch)
					wizard.can_edit_wizard = True
					wizard.can_group_payments = len(batch_result['lines']) != 1
				else:
					# == Multiple batches: The wizard is not editable  ==
					wizard.update({
						'company_id': batches[0]['lines'][0].company_id.id,
						'partner_id': False,
						'partner_type': False,
						'payment_type': wizard_values_from_batch['payment_type'],
						'source_currency_id': False,
						'source_amount': False,
						'source_amount_currency': False,
					})

					wizard.can_edit_wizard = False
					wizard.can_group_payments = any(len(batch_result['lines']) != 1 for batch_result in batches)