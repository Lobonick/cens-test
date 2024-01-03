# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp
import logging
_logging = logging.getLogger(__name__)


class CobrarGarantiaFactoring(models.TransientModel):
	_name = "solse.factoring.garantia.wizard"
	_description = "Cobrar Garantia"

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
			res['monto_cobrar'] = planilla.monto_garantia_factoring

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
			self.cobrar_garantia(planilla)
			
		return {
			'type': 'ir.actions.act_window_close',
		}

	def cobrar_garantia(self, planilla):
		cuenta_factorign_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factorign_id = int(cuenta_factorign_id)

		cuenta_garantia_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring_garantia')
		cuenta_garantia_id = int(cuenta_garantia_id)

		cuenta_pagar = self.cobrar_con.default_account_id.id

		porc_garantia = planilla.empresa_factoring.porc_garantia_factoring
		porc_gastos = planilla.empresa_factoring.porc_cobro_factoring
		amount_total_signed = planilla.monto_total_factoring

		monto_garantia = planilla.monto_garantia_factoring

		datos_asiento = {
			'move_type': 'entry',
			'date': self.fecha,
			'planilla_fact_n3': planilla.id,
			'ref': 'Por la cobro de garantia retenida (%s) con %s' % (planilla.name, self.cobrar_con.name),
			'glosa': 'Por la cobro de garantia retenida (%s) con %s' % (planilla.name, self.cobrar_con.name),
			'es_x_factoring': True,
			'line_ids': [
				(0, None, {
					'name': 'Garantia de Factoring',
					'account_id': cuenta_garantia_id,
					'debit': 0.0,
					'credit': monto_garantia,
					'partner_id': planilla.empresa_factoring.id,
				}),
				(0, None, {
					'name': self.cobrar_con.name,
					'account_id': cuenta_pagar,
					'debit': monto_garantia,
					'credit': 0.0,
					'partner_id': planilla.empresa_factoring.id,
				}),
			]
		}

		asiento_garantia = self.env['account.move'].create(datos_asiento)
		asiento_garantia.action_post()

		if planilla.monto_factoring_pendiente == 0:
			planilla.write({'estado': 'finalizado'})
		else:
			planilla.write({'estado': 'cobrando'})

		return
