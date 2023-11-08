# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api
from contextlib import ExitStack, contextmanager
import logging
from odoo.exceptions import UserError, ValidationError
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'

	con_factoring = fields.Boolean("Pagado con Factoring")
	empresa_factoring = fields.Many2one("res.partner", string="Empresa Factoring")
	factura_factoring = fields.Many2one("account.move", string="Factura afectada (Factoring)")
	asiento_factoring = fields.Many2one("account.move", string="Asiento Factoring (Asignacion)")
	asiento_factoring_cancelacion = fields.Many2one("account.move", string="Asiento Factoring (Cancelación)")
	asiento_factoring_garantia = fields.Many2one("account.move", string="Asiento Factoring (Garantia)")

	factura_enlazada = fields.Many2one("account.move", string="Factura enlazada")
	es_x_factoring = fields.Boolean("Es por factoring")
	es_x_cancelacion = fields.Boolean("Es por cancelacion (Factoring)")
	es_x_cobro_garantia = fields.Boolean("Es por cobro de garantia (Factoring)")

	pagar_con = fields.Many2one("account.journal", domain=[('type', 'in', ['cash', 'bank'])])

	def pagar_factoring(self):
		if not self.pagar_con:
			raise UserError("Seleccione un forma de pago")

		if self.asiento_factoring_cancelacion:
			raise UserError("Ya cuenta con un asiento de cancelación")

		cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factorign_id = int(cuenta_factorign_id)

		cuenta_gastos_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_gastos')
		cuenta_gastos_id = int(cuenta_gastos_id)

		cuenta_pagar = self.pagar_con.default_account_id.id

		porc_garantia = self.empresa_factoring.porc_garantia_factoring
		porc_gastos = self.empresa_factoring.porc_cobro_factoring
		amount_total_signed = self.factura_enlazada.amount_total_signed

		monto_garantia = amount_total_signed * (porc_garantia / 100)
		monto_factoring = amount_total_signed - monto_garantia
		monto_gastos = monto_factoring * (porc_gastos / 100)
		monto_cobrar = monto_factoring - monto_gastos

		datos_asiento = {
			'move_type': 'entry',
			'factura_enlazada': self.factura_enlazada.id,
			'ref': 'Por la cancelacion de facruras factoring (%s)' % self.factura_enlazada.name,
			'glosa': 'Por la cancelacion de facruras factoring (%s)' % self.factura_enlazada.name,
			'es_x_factoring': True,
			'line_ids': [
				(0, None, {
					'name': 'Factoring',
					'account_id': cuenta_factorign_id,
					'debit': 0.0,
					'credit': monto_factoring,
					'partner_id': self.factura_enlazada.partner_id.id,
				}),
				(0, None, {
					'name': 'Gastos en Factoring',
					'account_id': cuenta_gastos_id,
					'debit': monto_gastos,
					'credit': 0.0,
					'partner_id': self.factura_enlazada.partner_id.id,
				}),
				(0, None, {
					'name': self.pagar_con.name,
					'account_id': cuenta_pagar,
					'debit': monto_cobrar,
					'credit': 0.0,
					'partner_id': self.factura_enlazada.partner_id.id,
				}),
			]
		}

		asiento_cancelacion = self.env['account.move'].create(datos_asiento)
		asiento_cancelacion.action_post()
		self.write({'asiento_factoring_cancelacion': asiento_cancelacion.id})
		self.factura_enlazada.write({'asiento_factoring_cancelacion': asiento_cancelacion.id})

		return

	def cobrar_garantia(self):
		if not self.pagar_con:
			raise UserError("Seleccione un forma de pago")

		if self.asiento_factoring_garantia:
			raise UserError("Ya cuenta con un asiento de garantia")

		cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factorign_id = int(cuenta_factorign_id)

		cuenta_garantia_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_garantia')
		cuenta_garantia_id = int(cuenta_garantia_id)

		cuenta_pagar = self.pagar_con.default_account_id.id

		porc_garantia = self.empresa_factoring.porc_garantia_factoring
		porc_gastos = self.empresa_factoring.porc_cobro_factoring
		amount_total_signed = self.factura_enlazada.amount_total_signed

		monto_garantia = amount_total_signed * (porc_garantia / 100)
		monto_factoring = amount_total_signed - monto_garantia
		monto_gastos = monto_factoring * (porc_gastos / 100)
		monto_cobrar = monto_factoring - monto_gastos

		datos_asiento = {
			'move_type': 'entry',
			'factura_enlazada': self.factura_enlazada.id,
			'ref': 'Por la cobro de garantia retenida (%s)' % self.factura_enlazada.name,
			'glosa': 'Por la cobro de garantia retenida (%s)' % self.factura_enlazada.name,
			'es_x_factoring': True,
			'line_ids': [
				(0, None, {
					'name': 'Garantia de Factoring',
					'account_id': cuenta_garantia_id,
					'debit': 0.0,
					'credit': monto_garantia,
					'partner_id': self.factura_enlazada.partner_id.id,
				}),
				(0, None, {
					'name': self.pagar_con.name,
					'account_id': cuenta_pagar,
					'debit': monto_garantia,
					'credit': 0.0,
					'partner_id': self.factura_enlazada.partner_id.id,
				}),
			]
		}

		asiento_garantia = self.env['account.move'].create(datos_asiento)
		asiento_garantia.action_post()
		self.write({'asiento_factoring_garantia': asiento_garantia.id})
		self.factura_enlazada.write({'asiento_factoring_garantia': asiento_garantia.id})

		return