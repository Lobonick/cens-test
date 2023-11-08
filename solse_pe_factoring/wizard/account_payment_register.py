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
	empresa_factoring = fields.Many2one("res.partner", string="Empresa Factoring")

	def obtener_lineas_pago(self, env, factura, pago):
		lineas_pagar = []
		for move in factura:
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

			lineas_recorrer = env['account.move.line'].sudo().search(domain)
			#return []

			for line in lineas_recorrer:

				if line.currency_id == move.currency_id:
					# Same foreign currency.
					amount = abs(line.amount_residual_currency)
				else:
					# Different foreign currencies.
					amount = line.company_currency_id._convert(
						abs(line.amount_residual),
						move.currency_id,
						move.company_id,
						line.date,
					)

				if move.currency_id.is_zero(amount):
					continue


				"""if line.payment_id.id == pago.id:
					lineas_pagar.append(line)"""
				if line.name == "Facturas por Cobrar":
					lineas_pagar.append(line)

		return lineas_pagar

	def procesar_pago_con_factoring(self):
		_logging.info("procesar_pago_con_factoring")

		amount_total_signed = sum(self.mapped("line_ids.move_id").mapped('amount_total_signed'))
		amount_total_signed = abs(amount_total_signed)
		factura = self.line_ids.move_id[0]

		for wizard in self:
			batches = wizard._get_batches()
			cuentas = []
			for lot in batches:
				payment_values = lot['payment_values']
				cuentas.append(payment_values['account_id'])

			cuentas_cont = self.env['account.account'].search([('id', 'in', cuentas)])

			cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
			cuenta_factorign_id = int(cuenta_factorign_id)

			cuenta_garantia_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_garantia')
			cuenta_garantia_id = int(cuenta_garantia_id)

			porc_garantia = self.empresa_factoring.porc_garantia_factoring

			monto_garantia = amount_total_signed * (porc_garantia / 100)
			monto_factoring = amount_total_signed - monto_garantia

			

			datos_asiento = {
				'move_type': 'entry',
				'ref': 'Asignacion de factoring (%s)' % factura.name,
				'glosa': 'Asignacion de factoring (%s)' % factura.name,
				'es_x_factoring': True,
				'factura_enlazada': factura.id,
				'empresa_factoring': self.empresa_factoring.id,
				'line_ids': [
					(0, None, {
						'name': 'Factoring',
						'account_id': cuenta_factorign_id,
						'debit': monto_factoring,
						'credit': 0.0,
						'partner_id': factura.partner_id.id,
					}),
					(0, None, {
						'name': 'Garantia de Factoring',
						'account_id': cuenta_garantia_id,
						'debit': monto_garantia,
						'credit': 0.0,
						'partner_id': factura.partner_id.id,
					}),
					(0, None, {
						'name': 'Facturas por Cobrar',
						'account_id': cuentas[0],
						'debit': 0,
						'credit': amount_total_signed,
						'partner_id': factura.partner_id.id,
					}),
				]
			}
			asiento_factoring = self.env['account.move'].create(datos_asiento)
			asiento_factoring.action_post()
			factura.write({'factura_factoring': asiento_factoring.id})

			linea_pago = self.obtener_lineas_pago(self.env, factura, asiento_factoring)

			for linea_pagar in linea_pago:
				factura.js_assign_outstanding_line(linea_pagar.id)

			
			return True

	def action_create_payments(self):
		if self.con_factoring:
			return self.procesar_pago_con_factoring()
		payments = self._create_payments()

		if self._context.get('dont_redirect_to_payments'):
			return True

		action = {
			'name': _('Payments'),
			'type': 'ir.actions.act_window',
			'res_model': 'account.payment',
			'context': {'create': False},
		}
		if len(payments) == 1:
			action.update({
				'view_mode': 'form',
				'res_id': payments.id,
			})
		else:
			action.update({
				'view_mode': 'tree,form',
				'domain': [('id', 'in', payments.ids)],
			})
		return action