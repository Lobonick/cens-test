# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api, _
from contextlib import ExitStack, contextmanager
import logging
from odoo.exceptions import UserError, ValidationError
_logging = logging.getLogger(__name__)

class AccountMoveFactn1(models.Model):
	_inherit = 'account.move'

	planilla_fact_n1 = fields.Many2one("solse.factoring.planillas", string="Planilla Pago")
	planilla_fact_n2 = fields.Many2one("solse.factoring.planillas", string="Planilla Cobro")
	planilla_fact_n3 = fields.Many2one("solse.factoring.planillas", string="Planilla Garantia")

class PlanillasFactoring(models.Model):
	_name = 'solse.factoring.planillas'
	_description = 'Planillas factoring'

	name = fields.Char("Nombre")
	empresa_factoring = fields.Many2one("res.partner", string="Empresa Factoring", domain=[('es_emp_factoring', '=', True)])
	factura_ids = fields.Many2many("account.move", "fact_plani_ids", "fact_ids", "planill_ids", string="Facturas", domain=[('move_type', 'in', ['out_invoice'])])
	fecha = fields.Date("Fecha Solicitud")
	asiento_factoring_ids = fields.One2many("account.move", "planilla_fact_n1", string="Asientos Factoring")
	asiento_cobro_ids = fields.One2many("account.move", "planilla_fact_n2", string="Asientos Cobro")
	asiento_garantia_ids = fields.One2many("account.move", "planilla_fact_n3", string="Asientos Garantia")

	porc_garantia_factoring = fields.Float("% Garantia", related="empresa_factoring.porc_garantia_factoring", store=True, readonly=False)
	porc_cobro_factoring = fields.Float("% Gastos Factoring", related="empresa_factoring.porc_cobro_factoring", store=True, readonly=False)

	monto_total_factoring = fields.Float("Monto total", compute="_compute_monto_factoring", store=True)
	monto_comision_factoring = fields.Float("Monto Comisión", compute="_compute_monto_factoring", store=True)
	monto_garantia_factoring = fields.Float("Monto Garantia", compute="_compute_monto_factoring", store=True)
	monto_comision_fija = fields.Float("Comisión Fija", default=0.00)
	comision_fija_cobrada = fields.Float("Monto fijo cobrado", default=0.00)
	comision_fija_restante = fields.Float("Monto fijo restante", compute="_compute_monto_fijo_restante", store=True)
	monto_neto_cobrar = fields.Float("Monto Neto Cobrar", compute="_compute_monto_factoring")
	#monto cobrar factoring (es el monto menos la garantia)
	monto_factoring_cobrar = fields.Float("Monto Factoring Cobrar", compute="_compute_monto_factoring", store=True)
	monto_factoring_cobrado = fields.Float("Monto Cobrado (Factoring)", compute="_compute_saldos_factoring", store=True)
	monto_factoring_pendiente = fields.Float("Monto pendiente (Factoring)", compute="_compute_saldos_factoring", store=True)

	cobrar_con = fields.Many2one("account.journal", domain=[('type', 'in', ['cash', 'bank'])])
	monto_cobrar = fields.Float("Monto a cobrar")

	estado = fields.Selection([("borrador", "Borrador"), ("asignado", "Generado"), ("cobrando", "Cobrando"), ("finalizado", "Pagado")], default="borrador")

	def unlink(self):
		for record in self:
			if record.estado == 'finalizado':
				raise UserError("No se puede eliminar una planilla ya pagada")
			else:
				record.regresar_borrador()
		super(PlanillasFactoring, self).unlink()

	@api.depends('monto_comision_fija', 'comision_fija_cobrada')
	def _compute_monto_fijo_restante(self):
		for reg in self:
			monto = reg.monto_comision_fija - reg.comision_fija_cobrada
			reg.comision_fija_restante = monto

	@api.depends('factura_ids', 'factura_ids.monto_neto_pagar', 'porc_garantia_factoring', 'porc_cobro_factoring')
	def _compute_monto_factoring(self):
		for reg in self:
			monto_total_factoring  = sum(reg.factura_ids.mapped('monto_neto_pagar'))
			reg.monto_total_factoring = monto_total_factoring

			porc_garantia = reg.porc_garantia_factoring

			monto_garantia = monto_total_factoring * (porc_garantia / 100.00)
			monto_garantia = round(monto_garantia, 2)
			reg.monto_garantia_factoring = monto_garantia

			monto_factoring = monto_total_factoring - monto_garantia

			monto_gastos = monto_factoring * (reg.porc_cobro_factoring / 100.00)
			reg.monto_comision_factoring = monto_gastos
			reg.monto_neto_cobrar = monto_total_factoring - monto_gastos
			reg.monto_factoring_cobrar = monto_factoring

	@api.depends('asiento_cobro_ids', 'asiento_cobro_ids.amount_total_signed', 'monto_factoring_cobrar')
	def _compute_saldos_factoring(self):
		for reg in self:
			monto_cobrado = sum(reg.asiento_cobro_ids.mapped('amount_total_signed'))
			monto_cobrado = abs(monto_cobrado)
			reg.monto_factoring_cobrado = monto_cobrado
			reg.monto_factoring_pendiente = reg.monto_factoring_cobrar - monto_cobrado

	def regresar_borrador(self):
		for asiento in self.asiento_factoring_ids:
			asiento.button_draft()
			asiento.unlink()

		for asiento in self.asiento_cobro_ids:
			asiento.button_draft()
			asiento.unlink()

		for asiento in self.asiento_garantia_ids:
			asiento.button_draft()
			asiento.unlink()
		self.estado = "borrador"
		self.comision_fija_cobrada = 0.00
 
	def obtener_lineas_pago(self, env, factura, pago):
		lineas_pagar = []
		for move in factura:
			move.invoice_outstanding_credits_debits_widget = False
			move.invoice_has_outstanding = False

			if move.state != 'posted' \
					or move.payment_state not in ('not_paid', 'partial') \
					or not move.is_invoice(include_receipts=True):

				continue

			pay_term_lines = move.line_ids.filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

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

				if line.name == "Facturas por Cobrar":
					lineas_pagar.append(line)

		return lineas_pagar

	def procesar_pago_con_factoring(self):
		_logging.info("procesar_pago_con_factoring")


		for factura in self.factura_ids:
			amount_total_signed = factura.monto_neto_pagar
			amount_total_signed = abs(amount_total_signed)

			cuentas = []
			cuenta_det_id = factura.company_id.cuenta_detracciones.id
			cuenta_det_id = int(cuenta_det_id)

			for linea in factura.line_ids:
				if linea.debit == 0:
					continue
				if linea.account_id.id in [cuenta_det_id]:
					continue

				cuentas.append(linea.account_id.id)

			cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
			cuenta_factorign_id = int(cuenta_factorign_id)

			cuenta_garantia_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_garantia')
			cuenta_garantia_id = int(cuenta_garantia_id)

			porc_garantia = self.porc_garantia_factoring

			monto_garantia = amount_total_signed * (porc_garantia / 100.00)
			monto_garantia = round(monto_garantia, 2)
			monto_factoring = amount_total_signed - monto_garantia
			monto_factoring = round(monto_factoring, 2)

			monto_pago_total = monto_garantia + monto_factoring
			monto_pago_total = round(monto_pago_total, 2)

			datos_asiento = {
				'move_type': 'entry',
				'ref': 'Asignacion de factoring (%s)' % factura.name,
				'glosa': 'Asignacion de factoring (%s)' % factura.name,
				'es_x_factoring': True,
				'planilla_fact_n1': self.id,
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
						'credit': monto_pago_total,
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

		self.estado = "asignado"

	def cobrar_factoring(self):
		if not self.cobrar_con:
			raise UserError("Seleccione un forma de pago")

		if not self.monto_cobrar:
			raise UserError("Establesca un monto a cobrar")

		if self.asiento_factoring_cancelacion:
			raise UserError("Ya cuenta con un asiento de cancelación")

		cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factorign_id = int(cuenta_factorign_id)

		cuenta_gastos_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_gastos')
		cuenta_gastos_id = int(cuenta_gastos_id)

		cuenta_comision_fija_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_comision')
		cuenta_comision_fija_id = int(cuenta_comision_fija_id)

		cuenta_pagar = self.pagar_con.default_account_id.id

		porc_garantia = self.empresa_factoring.porc_garantia_factoring
		porc_gastos = self.empresa_factoring.porc_cobro_factoring
		amount_total_signed = self.factura_enlazada.amount_total_signed

		monto_garantia = amount_total_signed * (porc_garantia / 100)
		monto_factoring = amount_total_signed - monto_garantia
		monto_gastos = monto_factoring * (porc_gastos / 100)
		if reg.comision_fija_restante >= monto_gastos:
			raise UserError("El monto fijo de comision no puede ser mayor o igual a al monto de gasto cobrado en este asiento")
		monto_gastos = monto_gastos - reg.comision_fija_restante
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
		if reg.comision_fija_restante:
			datos_asiento['line_ids'].append((0, None, {
				'name': 'Comision por Factoring',
				'account_id': cuenta_comision_fija_id,
				'debit': reg.comision_fija_restante,
				'credit': 0.0,
				'partner_id': self.factura_enlazada.partner_id.id,
			}))

		asiento_cancelacion = self.env['account.move'].create(datos_asiento)
		asiento_cancelacion.action_post()
		self.write({'asiento_factoring_cancelacion': asiento_cancelacion.id, 'comision_fija_cobrada': reg.comision_fija_restante})
		self.factura_enlazada.write({'asiento_factoring_cancelacion': asiento_cancelacion.id})

		return