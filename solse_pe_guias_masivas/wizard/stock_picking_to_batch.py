# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockPickingToBatch(models.TransientModel):
	_inherit = 'stock.picking.to.batch'

	pe_is_eguide = fields.Boolean("Es Guía Electrónica", copy=False)
	pe_transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Modo de transporte", copy=False)
	pe_carrier_id = fields.Many2one(comodel_name="res.partner", string="Transportista", copy=False)
	fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")

	@api.model
	def _get_pe_transport_mode(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

	def attach_pickings(self):
		self.ensure_one()
		pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
		if self.mode == 'new':
			company = pickings.company_id
			if len(company) > 1:
				raise UserError(_("The selected pickings should belong to an unique company."))
			batch = self.env['stock.picking.batch'].create({
				'user_id': self.user_id.id,
				'company_id': company.id,
				'picking_type_id': pickings[0].picking_type_id.id,
				'pe_is_eguide': self.pe_is_eguide,
				'pe_transport_mode': self.pe_transport_mode,
				'pe_carrier_id': self.pe_carrier_id.id,
				'fleet_id': self.fleet_id.id,
			})
		else:
			batch = self.batch_id

		pickings.write({'batch_id': batch.id})