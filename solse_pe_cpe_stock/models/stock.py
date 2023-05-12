# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError
import logging
_logging = logging.getLogger(__name__)

class Picking(models.Model):
	_inherit = "stock.picking"
	
	factura_id = fields.Many2one("account.move", string="Factura")

	def limpiar_stock_almacen_nombre(self, almacen="Nombre"):
		almacen = self.env['stock.warehouse'].search([("name", "=", almacen)])
		if not almacen:
			raise UserError("No se encontro un almacen con este nombre")
		if len(almacen) > 1:
			raise UserError("Se encontro mas de un almacen con este nombre")

		ubicaciones_ids = [almacen.lot_stock_id.id]
		stock = self.env['stock.quant'].search([('location_id', 'in', ubicaciones_ids)])
		for reg in stock:
			for quant in reg:
				quant.inventory_quantity = 0
			reg.user_id = reg.env.user.id
			reg.inventory_quantity_set = True
			reg.action_apply_inventory()

	@api.model
	def _compute_pe_invoice_ids(self):
		pe_invoice_ids = False
		pe_invoice_name=[]
		for stock_id in self:
			stock_id.sale_id
			pe_invoice_ids = stock_id.sale_id.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			
			if pe_invoice_ids:
				pe_invoice_name = pe_invoice_ids.mapped('l10n_latam_document_number')

			pe_invoice_ids_array = pe_invoice_ids and pe_invoice_ids.ids or []

			if stock_id.factura_id:
				pe_invoice_ids_array.append(stock_id.factura_id.id)
				pe_invoice_name.append(stock_id.factura_id.l10n_latam_document_number)

			stock_id.pe_invoice_ids = pe_invoice_ids_array
			stock_id.pe_invoice_name = ", ".join(pe_invoice_name) or False