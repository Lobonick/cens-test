# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)


class CobrarFactoring(models.TransientModel):
	_name = "solse.factoring.cobrar.wizard"
	_description = "Cobrar Factoring"

	cobrar_con = fields.Many2one("account.journal", domain=[('type', 'in', ['cash', 'bank'])])
	monto_cobrar = fields.Float("Monto a cobrar")
	fecha = fields.Date("Fecha")

	@api.model
	def default_get(self, fields_list):
		# OVERRIDE
		res = super().default_get(fields_list)
		modelo_planilla_factoring = self.env['solse.factoring.planillas']
		planilla_ids = self.env.context.get('active_ids', [])
		if planilla_ids:
			planilla_id = planilla_ids[0]
			planilla = modelo_planilla_factoring.browse(planilla_id)
			res['monto_cobrar'] = planilla.monto_factoring_pendiente

		return res

	@api.constrains('cobrar_con')
	def check_metodo_cobro(self):
		if not self.cobrar_con:
			raise exceptions.ValidationError("Se debe seleccionar una forma de cobro")

	@api.constrains('monto_cobrar')
	def check_monto_cobrar(self):
		if not self.monto_cobrar:
			raise exceptions.ValidationError("Se debe ingresar un monto a cobrar")

	def registrar_cobro(self):
		modelo_planilla_factoring = self.env['solse.factoring.planillas']
		planilla_ids = self.env.context.get('active_ids', [])
		if planilla_ids:
			planilla_id = planilla_ids[0]
			planilla = modelo_planilla_factoring.browse(planilla_id)
			self.cobrar_factoring(planilla)
			_logging.info("proceso de cobrar factoring")
			_logging.info(planilla)
			
		return {
			'type': 'ir.actions.act_window_close',
		}

	def cobrar_factoring(self, planilla):
		cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factorign_id = int(cuenta_factorign_id)

		cuenta_gastos_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_gastos')
		cuenta_gastos_id = int(cuenta_gastos_id)

		cuenta_comision_fija_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_comision')
		cuenta_comision_fija_id = int(cuenta_comision_fija_id)

		cuenta_pagar = self.cobrar_con.default_account_id.id

		#porc_garantia = planilla.porc_garantia_factoring
		porc_gastos = planilla.porc_cobro_factoring
		amount_total_signed = self.monto_cobrar

		if self.monto_cobrar > planilla.monto_factoring_pendiente:
			raise exceptions.ValidationError("El monto a cobrar es mayor al saldo restante")

		#monto_garantia = amount_total_signed * (porc_garantia / 100.00)
		#monto_garantia = round(monto_garantia, 3)
		monto_factoring = amount_total_signed# - monto_garantia
		monto_factoring = round(monto_factoring, 2)
		monto_gastos = monto_factoring * (porc_gastos / 100.00)
		monto_gastos = round(monto_gastos, 2)

		if planilla.comision_fija_restante >= monto_gastos:
			raise UserError("El monto fijo de comision no puede ser mayor o igual a al monto de gasto cobrado en este asiento (%s > %s)" % (str(planilla.comision_fija_restante), str(monto_gastos)))
		

		monto_cobrar = monto_factoring - monto_gastos
		monto_gastos = monto_gastos - planilla.comision_fija_restante
		monto_cobrar = round(monto_cobrar, 2)

		datos_asiento = {
			'move_type': 'entry',
			'date': self.fecha,
			'planilla_fact_n2': planilla.id,
			'ref': 'Por la cancelacion de la planilla (%s) con %s' % (planilla.name, self.cobrar_con.name),
			'glosa': 'Por la cancelacion de la planilla (%s) con %s'% (planilla.name, self.cobrar_con.name),
			'es_x_factoring': True,
			'partner_id': planilla.empresa_factoring.id,
			'line_ids': [
				(0, None, {
					'name': 'Factoring',
					'account_id': cuenta_factorign_id,
					'debit': 0.0,
					'credit': monto_factoring,
					'partner_id': planilla.empresa_factoring.id,
				}),
				(0, None, {
					'name': 'Gastos en Factoring',
					'account_id': cuenta_gastos_id,
					'debit': monto_gastos,
					'credit': 0.0,
					'partner_id': planilla.empresa_factoring.id,
				}),
				(0, None, {
					'name': self.cobrar_con.name,
					'account_id': cuenta_pagar,
					'debit': monto_cobrar,
					'credit': 0.0,
					'partner_id': planilla.empresa_factoring.id,
				}),
			]
		}

		if planilla.comision_fija_restante:
			datos_asiento['line_ids'].append((0, None, {
				'name': 'Comision por Factoring',
				'account_id': cuenta_comision_fija_id,
				'debit': planilla.comision_fija_restante,
				'credit': 0.0,
				'partner_id': planilla.empresa_factoring.id,
			}))

		_logging.info("asiento total :::::::::::::::::::::::::::::::::::::::")
		_logging.info(datos_asiento)

		asiento_cancelacion = self.env['account.move'].create(datos_asiento)
		asiento_cancelacion.action_post()

		datos_actualizar = {}
		if planilla.monto_factoring_pendiente == 0 and planilla.asiento_garantia_ids:
			datos_actualizar['estado'] = 'finalizado'
		else:
			datos_actualizar['estado'] = 'cobrando'

		if planilla.comision_fija_restante:
			datos_actualizar['comision_fija_cobrada'] = planilla.comision_fija_restante

		planilla.write(datos_actualizar)


