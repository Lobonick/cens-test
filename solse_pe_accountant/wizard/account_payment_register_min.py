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
	autodetraccion = fields.Boolean("Autodetracción")
	monto_autodetraccion = fields.Monetary(currency_field='currency_id', string="Importe", default=0.00)

	@api.depends('line_ids', 'line_ids.move_id')
	def _compute_mostrar_check(self):
		for reg in self:
			facturas = reg.mapped("line_ids.move_id")
			mostrar_check = False
			pagadas_detrac = facturas.filtered(lambda r: r.pago_detraccion)
			if len(facturas) == len(pagadas_detrac) and len(pagadas_detrac):
				mostrar_check = False
			else:
				for factura in facturas:
					if factura.tiene_detraccion or factura.tiene_retencion:
						mostrar_check = True
			
			reg.mostrar_check = mostrar_check

	@api.depends('can_edit_wizard', 'line_ids')
	def _compute_communication_2(self):
		for wizard in self:
			if wizard.can_edit_wizard:
				#factura = wizard.line_ids[0].move_id
				facturas = wizard.mapped("line_ids.move_id")
				if facturas:
					dato_array = []
					for factura in facturas:
						dato = factura.name
						partes = dato.split(" ")
						dato = partes[1] if len(partes) == 2 else partes[0]
						dato_array.append(dato)
					wizard.communication = ",".join(dato_array)
				else:
					batches = wizard._get_batches()
					wizard.communication = wizard._get_batch_communication(batches[0])

			else:
				facturas = wizard.mapped("line_ids.move_id")
				if facturas:
					dato_array = []
					for factura in facturas:
						dato = factura.name
						partes = dato.split(" ")
						dato = partes[1] if len(partes) == 2 else partes[0]
						dato_array.append(dato)
					wizard.communication = ",".join(dato_array)
				else:
					wizard.communication = False

	@api.depends('can_edit_wizard', 'amount', 'es_detraccion_retencion')
	def _compute_payment_difference(self):
		factura = self.line_ids[0].move_id
		cuenta_det_id = factura.company_id.cuenta_detracciones_compra.id
		cuenta_det_id = int(cuenta_det_id)

		if factura.move_type == 'out_invoice':
			cuenta_det_id = factura.company_id.cuenta_detracciones.id
			cuenta_det_id = int(cuenta_det_id)

		for wizard in self:
			if wizard.can_edit_wizard and not self.autodetraccion:
				lotes = wizard._get_batches()
				batch_result = lotes[0]
				if self.es_detraccion_retencion and self.tipo == 'detraccion':
					for lot in lotes:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_det_id:
							batch_result = lot
							break

				
				total_amount_residual_in_wizard_currency = wizard\
					._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount=False)[0]
				wizard.payment_difference = total_amount_residual_in_wizard_currency - wizard.amount
			else:
				wizard.payment_difference = 0.0

	#@api.onchange('es_detraccion_retencion', 'currency_id')
	@api.onchange('es_detraccion_retencion', 'tipo', 'autodetraccion')
	def _onchange_detraccion_retencion(self):
		factura = self.line_ids[0].move_id
		self.payment_difference_handling = "open"
		#self._compute_currency_id()
		facturas_con_detraccion = self.mapped("line_ids.move_id").filtered(lambda r: r.tiene_detraccion)
		facturas_con_detra_y_pago_detr = facturas_con_detraccion.filtered(lambda r: r.pago_detraccion)
		if self.es_detraccion_retencion:
			if self.tipo == 'normal':
				self.tipo = 'detraccion'
		else:
			self.tipo = 'normal'

		if self.autodetraccion:
			self.monto_autodetraccion = self.source_amount_currency

		if self.es_detraccion_retencion:
			if self.tipo == 'normal':
				self.tipo = 'detraccion'
			self.currency_id = self.env.ref('base.PEN')

			total_detraccion = sum(self.mapped("line_ids.move_id").filtered(lambda r: not r.pago_detraccion).mapped('monto_detraccion'))
			total_retencion = sum(self.mapped("line_ids.move_id").filtered(lambda r: not r.pago_detraccion).mapped('monto_retencion'))

			self.amount = total_detraccion + total_retencion

		elif len(facturas_con_detraccion) and len(facturas_con_detra_y_pago_detr):
			source_amount_currency = self.source_amount_currency
			monto_comparar = sum(facturas_con_detraccion.mapped('monto_neto_pagar_base'))
			if factura.company_id.currency_id.id == self.currency_id.id:
				monto_comparar = sum(facturas_con_detraccion.mapped('monto_neto_pagar'))
			
			if source_amount_currency + 1 > monto_comparar:
				total_descontar = monto_comparar
			else:
				total_descontar = source_amount_currency

			self.amount = total_descontar

		elif factura.company_id.currency_id.id == self.currency_id.id:# and not self.autodetraccion:
			source_amount = self.source_amount

			total_detraccion = sum(self.mapped("line_ids.move_id").mapped('monto_detraccion'))
			total_retencion = sum(self.mapped("line_ids.move_id").mapped('monto_retencion'))
			total_retencion = 0 # hasta crear lineas contables por retencion
			self.amount = source_amount - total_detraccion - total_retencion
		#elif not self.autodetraccion:
		else:
			source_amount_currency = self.source_amount_currency
			total_detraccion_base = sum(self.mapped("line_ids.move_id").mapped('monto_detraccion_base'))
			total_retencion_base = sum(self.mapped("line_ids.move_id").mapped('monto_retencion_base'))
			total_retencion_base = 0 # hasta crear lineas contables por retencion
			self.amount = source_amount_currency - total_detraccion_base - total_retencion_base
		"""else:
			source_amount_currency = self.source_amount_currency
			_logging.info("source_amount_currency")
			_logging.info(source_amount_currency)
			self.amount = source_amount_currency"""


		#self._compute_from_lines()

	@api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'mostrar_check')
	def _compute_amount(self):
		for wizard in self:
			wizard._onchange_detraccion_retencion()


	@api.onchange('amount')
	def _onchange_amount(self):
		payment_difference_handling = 'open'
		factura = self.line_ids[0].move_id
		if self.tipo == 'detraccion' and factura.move_type == 'in_invoice':# and not self.autodetraccion:
			amount_total_signed = sum(self.mapped("line_ids.move_id").mapped('amount_total_signed'))
			monto_neto_pagar = sum(self.mapped("line_ids.move_id").mapped('monto_neto_pagar'))
			monto_detraccion = abs(amount_total_signed) - monto_neto_pagar
			diferencia = monto_detraccion - self.amount
			if diferencia:
				payment_difference_handling = 'reconcile'
		elif self.tipo == 'detraccion' and factura.move_type == 'out_invoice':# and not self.autodetraccion:
			amount_total_signed = sum(self.mapped("line_ids.move_id").mapped('amount_total_signed'))
			monto_neto_pagar = sum(self.mapped("line_ids.move_id").mapped('monto_neto_pagar'))

			monto_detraccion = abs(amount_total_signed) - monto_neto_pagar
			diferencia = self.amount - monto_detraccion
			if diferencia:
				payment_difference_handling = 'reconcile'

		self.payment_difference_handling = payment_difference_handling

	@api.onchange('payment_difference_handling')
	def _onchange_payment_difference_handling(self):

		if self.payment_difference_handling == 'reconcile':
			cuenta_diferencia = False
			if self.payment_difference > 0:
				cuenta_diferencia = self.company_id.cuenta_detrac_ganancias.id
				cuenta_diferencia = int(cuenta_diferencia)
			else:
				cuenta_diferencia = self.company_id.cuenta_detrac_perdidas.id
				cuenta_diferencia = int(cuenta_diferencia)
			self.writeoff_account_id = cuenta_diferencia

	def _create_payment_vals_from_wizard(self, batch_result):
		payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
		payment_vals['transaction_number'] = self.transaction_number
		factura = self.line_ids[0].move_id

		conversion_rate = self.env['res.currency']._get_conversion_rate(
			self.currency_id,
			self.company_id.currency_id,
			self.company_id,
			self.payment_date,
		)

		crear_diferencia = False
		if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
			crear_diferencia = True

		if self.tipo == 'detraccion' and factura.move_type == 'in_invoice':
			cuenta_det_id = self.company_id.cuenta_detracciones_compra.id
			cuenta_det_id = int(cuenta_det_id)
			payment_vals['destination_account_id'] = cuenta_det_id

			amount_total_signed = sum(self.mapped("line_ids.move_id").mapped('amount_total_signed'))
			monto_neto_pagar = sum(self.mapped("line_ids.move_id").mapped('monto_neto_pagar'))

			monto_detraccion = abs(amount_total_signed) - monto_neto_pagar
			diferencia = monto_detraccion - self.amount
			
			if diferencia and not crear_diferencia:
				if diferencia > 0:
					cuenta_diferencia = self.company_id.cuenta_detrac_ganancias.id
					cuenta_diferencia = int(cuenta_diferencia)
				else:
					cuenta_diferencia = self.company_id.cuenta_detrac_perdidas.id
					cuenta_diferencia = int(cuenta_diferencia)

				if self.payment_type == 'inbound':
					# Receive money.
					write_off_amount_currency = self.payment_difference
				else: # if self.payment_type == 'outbound':
					# Send money.
					write_off_amount_currency = -self.payment_difference

				write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
				dato_json = {
					'account_id': cuenta_diferencia,
					'partner_id': self.partner_id.id,
					'currency_id': self.currency_id.id,
					'amount_currency': write_off_amount_currency,
					'balance': write_off_balance,
				}
				payment_vals['write_off_line_vals'] = [dato_json]

		if self.tipo == 'detraccion' and factura.move_type == 'out_invoice':
			cuenta_det_id = self.company_id.cuenta_detracciones.id
			cuenta_det_id = int(cuenta_det_id)
			payment_vals['destination_account_id'] = cuenta_det_id

			amount_total_signed = sum(self.mapped("line_ids.move_id").mapped('amount_total_signed'))
			monto_neto_pagar = sum(self.mapped("line_ids.move_id").mapped('monto_neto_pagar'))

			monto_detraccion = abs(amount_total_signed) - monto_neto_pagar
			diferencia = monto_detraccion - self.amount
			
			if diferencia and not crear_diferencia:
				if diferencia > 0:
					cuenta_diferencia = self.company_id.cuenta_detrac_ganancias.id
					cuenta_diferencia = int(cuenta_diferencia)
				else:
					cuenta_diferencia = self.company_id.cuenta_detrac_perdidas.id
					cuenta_diferencia = int(cuenta_diferencia)

				if self.payment_type == 'inbound':
					# Receive money.
					write_off_amount_currency = self.payment_difference
				else: # if self.payment_type == 'outbound':
					# Send money.
					write_off_amount_currency = -self.payment_difference

				write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
				dato_json = {
					'account_id': cuenta_diferencia,
					'partner_id': self.partner_id.id,
					'currency_id': self.currency_id.id,
					'amount_currency': write_off_amount_currency,
					'balance': write_off_balance,
				}
				payment_vals['write_off_line_vals'] = [dato_json]

		if self.tipo == 'retencion' and factura.move_type == 'in_invoice':
			cuenta_det_id = self.company_id.cuenta_retenciones.id
			cuenta_det_id = int(cuenta_det_id)
			payment_vals['destination_account_id'] = cuenta_det_id

		#self.payment_difference_handling = 'reconcile'
		return payment_vals

	def _create_payments(self):
		self.ensure_one()


		batches = self._get_batches()
		batch_result = batches[0]
		factura = self.line_ids[0].move_id

		if self.autodetraccion and not factura.company_id.cuenta_detraccion:
			raise UserError("No se ha establecido una cuenta de detracción en la empresa")

		cuenta_det_id = factura.company_id.cuenta_detracciones_compra.id
		cuenta_det_id = int(cuenta_det_id)

		cuenta_ret_id = factura.company_id.cuenta_retenciones.id
		cuenta_ret_id = int(cuenta_ret_id)

		if factura.move_type == 'out_invoice':
			cuenta_det_id = factura.company_id.cuenta_detracciones.id
			cuenta_det_id = int(cuenta_det_id)

		facturas_con_detraccion_con_pago = self.mapped("line_ids.move_id").filtered(lambda r: r.pago_detraccion)

		if self.tipo == 'detraccion':
			if len(facturas_con_detraccion_con_pago):
				raise UserError('Ya existe un pago por detracción')
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] == cuenta_det_id:
					batch_result = lot
					break

		elif self.tipo == 'retencion':
			if len(facturas_con_detraccion_con_pago):
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
				if self.tipo == 'detraccion' and batch_result['payment_values']['account_id'] != cuenta_det_id:
					continue
				if self.tipo == 'normal' and batch_result['payment_values']['account_id'] == cuenta_det_id:
					continue
				to_process.append({
					'create_vals': self._create_payment_vals_from_batch(batch_result),
					'to_reconcile': batch_result['lines'],
					'batch': batch_result,
				})

		batches = self._get_batches()
		if self.autodetraccion and not self.group_payment:
			self.crear_autodetraccion_independiente(cuenta_det_id, batches, to_process, edit_mode)
			#raise UserError("Detener el proceso")

		if self.autodetraccion and self.group_payment:
			raise UserError("Por el momento la autodetracción no se permite cuando se agrupan los pagos")

		payments = self._init_payments(to_process, edit_mode=edit_mode)
		self._post_payments(to_process, edit_mode=edit_mode)
		self._reconcile_payments(to_process, edit_mode=edit_mode)

		if payments and self.tipo == 'detraccion' and not self.autodetraccion and not self.group_payment and len(payments) == 1:
			#raise UserError('procesar pagos')
			factura.pago_detraccion = payments[0].id
		elif payments and self.tipo == 'detraccion' and not self.autodetraccion and not self.group_payment and len(payments) > 1:
			for pago in payments:
				factura_p = self.env['account.move'].search([('name', '=', pago.ref), ('company_id', '=', pago.company_id.id)])
				if factura_p:
					factura_p.pago_detraccion = pago.id

		#raise UserError("terminar proceso")

		return payments

	def crear_autodetraccion_independiente(self, cuenta_det_id, batches, to_process, edit_mode):
		to_process_detraccion = []
		factura = self.line_ids[0].move_id
		if self.autodetraccion:
			lote_detraccion = False
			for lot in batches:
				payment_values = lot['payment_values']
				if payment_values['account_id'] == cuenta_det_id:
					lote_detraccion = lot

			if not lote_detraccion:
				raise UserError("No se pudo establecer el asiento para la detracción")
			monto_pagar_autodetraccion = self.monto_autodetraccion - self.amount
			for linea in lote_detraccion['lines']:
				amount_total_signed = linea.move_id.amount_total_signed
				monto_neto_pagar = linea.move_id.monto_neto_pagar
				monto_detraccion = abs(amount_total_signed) - monto_neto_pagar

				create_vals = {
					'date': to_process[0]['create_vals']['date'], 
					'amount': monto_detraccion, 
					'payment_type': to_process[0]['create_vals']['payment_type'], 
					'partner_type': to_process[0]['create_vals']['partner_type'], 
					'ref': linea.move_id.name, 
					'journal_id': to_process[0]['create_vals']['journal_id'], 
					'currency_id': to_process[0]['create_vals']['currency_id'], 
					'partner_id': to_process[0]['create_vals']['partner_id'], 
					'partner_bank_id': to_process[0]['create_vals']['partner_bank_id'], 
					'payment_method_line_id': to_process[0]['create_vals']['payment_method_line_id'], 
					'destination_account_id': cuenta_det_id, 
					'write_off_line_vals': to_process[0]['create_vals']['write_off_line_vals'], 
					'payment_token_id': to_process[0]['create_vals']['payment_token_id'] if 'payment_token_id' in to_process[0]['create_vals'] else False, 
					'team_id': to_process[0]['create_vals']['team_id'] if 'team_id' in to_process[0]['create_vals'] else False, 
					'transaction_number': to_process[0]['create_vals']['transaction_number'] if 'transaction_number' in to_process[0]['create_vals'] else False
				}
				dato_json_detrac = {
					'create_vals': create_vals,
					'to_reconcile': linea,
					'batch': {
						'lines': linea,
						'payment_values': lote_detraccion['payment_values']
					},
				}
				to_process_detraccion.append(dato_json_detrac)

		if self.autodetraccion and to_process_detraccion and factura.move_type == 'out_invoice':
			payments_detrac = self._init_payments(to_process_detraccion, edit_mode=edit_mode)
			self._post_payments(to_process_detraccion, edit_mode=edit_mode)
			self._reconcile_payments(to_process_detraccion, edit_mode=edit_mode)

			for linea in lote_detraccion['lines']:
				amount_total_signed = linea.move_id.amount_total_signed
				monto_neto_pagar = linea.move_id.monto_neto_pagar
				monto_detraccion = abs(amount_total_signed) - monto_neto_pagar
				datos_pago_pendiente = {
					'is_internal_transfer': True,
					'es_x_autodetraccion': True,
					'payment_type': 'outbound',
					'amount': monto_detraccion,
					'date': to_process[0]['create_vals']['date'],
					'ref': 'Por pago de autodetracción para factura: %s' % linea.move_id.name,
					'journal_id': to_process[0]['create_vals']['journal_id'],
					'destination_journal_id': factura.company_id.cuenta_detraccion.id,
				}
				pago_pendiente = self.env['account.payment'].create(datos_pago_pendiente)
				linea.move_id.write({'pago_detraccion': pago_pendiente.id})

		elif self.autodetraccion and to_process_detraccion and factura.move_type == 'in_invoice':
			payments_detrac = self._init_payments(to_process_detraccion, edit_mode=edit_mode)
			self._post_payments(to_process_detraccion, edit_mode=edit_mode)
			self._reconcile_payments(to_process_detraccion, edit_mode=edit_mode)



	#@api.depends('line_ids', 'tipo')
	@api.depends('line_ids')
	def _compute_from_lines(self):
		''' Load initial values from the account.moves passed through the context. '''
		for wizard in self:
			batches = wizard._get_batches()
			factura = self.line_ids[0].move_id
			cuenta_det_id = factura.company_id.cuenta_detracciones_compra.id
			cuenta_det_id = int(cuenta_det_id)

			cuenta_ret_id = factura.company_id.cuenta_retenciones.id
			cuenta_ret_id = int(cuenta_ret_id)

			facturas_con_detraccion = self.mapped("line_ids.move_id").filtered(lambda r: r.tiene_detraccion)
			facturas_con_retencion = self.mapped("line_ids.move_id").filtered(lambda r: r.tiene_retencion)

			if factura.move_type == 'in_invoice':
				batch_result = batches[0]
				if self.tipo == 'detraccion':
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_det_id:
							batch_result = lot
							break

				elif self.tipo == 'retencion':
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_ret_id:
							batch_result = lot
							break
				#elif facturas_con_detraccion or facturas_con_retencion:
				else:
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] != cuenta_det_id:
							batch_result = lot
							break
				
				wizard_values_from_batch = wizard._get_wizard_values_from_batch(batch_result)
				if len(batches) > 1:
					for indice in range(1, len(batches)):
						temp = batches[indice]
						if temp == batch_result:
								continue

						if temp['payment_values']['account_id'] != cuenta_det_id:
							continue

						temp = wizard._get_wizard_values_from_batch(temp)
						wizard_values_from_batch['source_amount'] = wizard_values_from_batch['source_amount'] + temp['source_amount']
						wizard_values_from_batch['source_amount_currency'] = wizard_values_from_batch['source_amount_currency'] + temp['source_amount_currency']
				wizard.update(wizard_values_from_batch)

				if len(batches) == 1:
					wizard.can_edit_wizard = True
					wizard.can_group_payments = len(batch_result['lines']) != 1
				else:
					wizard.can_edit_wizard = False
					wizard.can_group_payments = any(len(batch_result['lines']) != 1 for batch_result in batches)
			elif factura.move_type == 'out_invoice':
				cuenta_det_id = factura.company_id.cuenta_detracciones.id
				cuenta_det_id = int(cuenta_det_id)
				batch_result = batches[0]
				tiene_detraccion = False
				cuenta_con_detraccion = False
				for lot in batches:
					payment_values = lot['payment_values']
					if payment_values['account_id'] == cuenta_det_id:
						cuenta_con_detraccion=True

				if self.tipo == 'detraccion':
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] == cuenta_det_id:
							batch_result = lot
							tiene_detraccion=True
							break
				else:
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] != cuenta_det_id:
							batch_result = lot
							break

				wizard_values_from_batch = wizard._get_wizard_values_from_batch(batch_result)
				if len(batches) == 1 and not tiene_detraccion:
					wizard.update(wizard_values_from_batch)
					wizard.can_edit_wizard = True
					wizard.can_group_payments = len(batch_result['lines']) != 1
				elif len(batches) == 1 or (len(batches) == 2 and tiene_detraccion):
					if len(batches) > 1:
						for indice in range(1, len(batches)):
							temp = batches[indice]
							if temp == batch_result:
								continue

							if temp['payment_values']['account_id'] != cuenta_det_id:
								continue

							temp = wizard._get_wizard_values_from_batch(temp)
							wizard_values_from_batch['source_amount'] = wizard_values_from_batch['source_amount'] + temp['source_amount']
							wizard_values_from_batch['source_amount_currency'] = wizard_values_from_batch['source_amount_currency'] + temp['source_amount_currency']
					
					wizard.update(wizard_values_from_batch)
					wizard.can_edit_wizard = False
					wizard.can_group_payments = len(batch_result['lines']) != 1
				elif tiene_detraccion:
					if len(batches) > 1:
						for indice in range(0, len(batches)):
							temp = batches[indice]
							if temp == batch_result:
								continue

							if temp['payment_values']['account_id'] != cuenta_det_id:
								continue
							
							temp = wizard._get_wizard_values_from_batch(temp)
							wizard_values_from_batch['source_amount'] = wizard_values_from_batch['source_amount'] + temp['source_amount']
							wizard_values_from_batch['source_amount_currency'] = wizard_values_from_batch['source_amount_currency'] + temp['source_amount_currency']
					
					wizard_values_from_batch['partner_id'] = False
					wizard_values_from_batch['partner_type'] = False
					wizard.update(wizard_values_from_batch)
					wizard.can_edit_wizard = False
					wizard.can_group_payments = any(len(batch_result['lines']) != 1 for batch_result in batches)

				elif len(batches) == 1 or (len(batches) == 2 and cuenta_con_detraccion):
					if len(batches) > 1:
						for indice in range(1, len(batches)):
							temp = batches[indice]
							if temp == batch_result:
								continue

							if temp['payment_values']['account_id'] != cuenta_det_id:
								continue

							temp = wizard._get_wizard_values_from_batch(temp)
							wizard_values_from_batch['source_amount'] = wizard_values_from_batch['source_amount'] + temp['source_amount']
							wizard_values_from_batch['source_amount_currency'] = wizard_values_from_batch['source_amount_currency'] + temp['source_amount_currency']

					wizard.update(wizard_values_from_batch)

					wizard.can_edit_wizard = True
					wizard.can_group_payments = len(batch_result['lines']) != 1
				else:
					source_amount_temp = 0
					source_amount_currency_temp = 0
					for indice in range(0, len(batches)):	
						temp = batches[indice]			
						temp = wizard._get_wizard_values_from_batch(temp)
						source_amount_temp = source_amount_temp + temp['source_amount']
						source_amount_currency_temp = source_amount_currency_temp + temp['source_amount_currency']

					wizard.update({
						'company_id': batches[0]['lines'][0].company_id.id,
						'partner_id': False,
						'partner_type': False,
						'payment_type': wizard_values_from_batch['payment_type'],
						'source_currency_id': False,
						'source_amount': source_amount_temp,
						'source_amount_currency': source_amount_currency_temp,
					})

					cant_batches_val = 0
					for lot in batches:
						payment_values = lot['payment_values']
						if payment_values['account_id'] != cuenta_det_id:
							cant_batches_val += 1

					wizard.can_edit_wizard = True if cant_batches_val == 1 else False
					wizard.can_group_payments = any(len(batch_result['lines']) != 1 for batch_result in batches)

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
