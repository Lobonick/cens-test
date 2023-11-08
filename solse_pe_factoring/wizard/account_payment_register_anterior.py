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

	con_factoring = fields.Boolean("Pagado con Factoring")

	def _create_payments(self):
		self.ensure_one()
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
		cuenta_det_id = int(cuenta_det_id)

		cuenta_ret_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
		cuenta_ret_id = int(cuenta_ret_id)

		cuenta_factoring = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factoring = int(cuenta_factoring or 0)

		batches = self._get_batches()
		batch_result = batches[0]
		factura = self.line_ids[0].move_id

		if factura.move_type == 'out_invoice':
			cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
			cuenta_det_id = int(cuenta_det_id)

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

		elif self.con_factoring:
			factura.con_factoring = True
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] == cuenta_factoring:
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
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
		cuenta_det_id = int(cuenta_det_id)

		cuenta_ret_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_retenciones')
		cuenta_ret_id = int(cuenta_ret_id)

		cuenta_factoring = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factoring = int(cuenta_factoring or 0)

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
			elif factura.move_type == 'out_invoice':
				cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
				cuenta_det_id = int(cuenta_det_id)
				batch_result = batches[0]
				if self.tipo == 'detraccion':
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_det_id:
							batch_result = lot
							break
				elif self.con_factoring:
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_factoring:
							batch_result = lot
							break
				else:
					lote = False
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] not in [cuenta_det_id, cuenta_ret_id, cuenta_factoring]:
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

