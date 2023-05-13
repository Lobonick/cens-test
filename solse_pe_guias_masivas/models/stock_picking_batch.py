# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logging = logging.getLogger(__name__)

class StockPickingBatch(models.Model):
	_inherit = "stock.picking.batch"
	
	pe_is_eguide = fields.Boolean("Es Guía Electrónica", copy=False)
	pe_transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Modo de transporte", copy=False)
	pe_carrier_id = fields.Many2one(comodel_name="res.partner", string="Transportista", copy=False)
	fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")

	@api.model
	def _get_pe_transport_mode(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

	def action_confirm(self):
		"""Sanity checks, confirm the pickings and mark the batch as confirmed."""
		self.ensure_one()
		if not self.picking_ids:
			raise UserError(_("You have to set some pickings to batch."))
		self.picking_ids.action_confirm()
		self.crear_guias_electronicas()
		self._check_company()
		self.state = 'in_progress'
		return True

	def crear_guias_electronicas(self):
		for guia in self.picking_ids:
			datos = {
				'pe_is_eguide': self.pe_is_eguide,
				'pe_transport_mode': self.pe_transport_mode,
			}
			if self.pe_transport_mode == '01':
				datos['pe_carrier_id'] = self.pe_carrier_id.id

			if self.pe_transport_mode == '02':
				datos_tipo_privado = {
					'picking_id': guia.id,
					'fleet_id': self.fleet_id.id,
					'name': self.fleet_id.license_plate,
					'driver_id': self.fleet_id.driver_id.id,
				}
				registro = self.env['pe.stock.fleet'].create(datos_tipo_privado)
				if not registro:
					raise UserError("No se pudo crear la linea del vehiculo")
				#registro.onchange_fleet_id()

			guia.write(datos)

	def generar_guias(self):
		for guia in self.picking_ids:
			if guia.pe_guide_number == False or guia.pe_guide_number == "/":
				guia.action_generate_eguide()

	def do_imprimir_guia(self):
		return self.env.ref('stock.action_report_delivery').report_action(self.picking_ids)
