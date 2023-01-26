# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	guide_number = fields.Char("Guía de referencia", compute="_get_eguide_name")
	pe_type_operation = fields.Selection("_get_pe_type_operation", "Tipo de operación", help="Tipo de operación efectuada")
	pe_stock_ids = fields.Many2many(comodel_name="stock.picking", string="Guías", compute ="_compute_pe_stock_ids", readonly=True, copy=False)
	pe_stock_name = fields.Char("Número de Guía", compute ="_compute_pe_stock_ids", copy=False)

	@api.model
	def _get_pe_type_operation(self):
		return self.env['pe.datas'].get_selection("PE.TABLA12")

	@api.depends("pe_stock_ids")
	def _get_eguide_name(self):
		for invoice in self:
			name = []
			for pe_stock_id in invoice.pe_stock_ids:
				if pe_stock_id.pe_guide_number and pe_stock_id.pe_guide_number != "/":
					name.append(pe_stock_id.pe_guide_number)
			invoice.guide_number = ", ".join(name) or False


	@api.model
	def invoice_validate(self):
		despatch_numbers = {}
		for invoice in self:
			numbers = []
			for pe_stock_id in invoice.pe_stock_ids:
				if pe_stock_id.pe_guide_number and pe_stock_id.pe_guide_number != "/":
					numbers.append(pe_stock_id.pe_guide_number)
			despatch_numbers[invoice.id] = numbers
		self = self.with_context(despatch_numbers=despatch_numbers)
		return super(AccountInvoice, self).invoice_validate()

	def _compute_pe_stock_ids(self):
		contador = 0
		for invoice in self:
			contador = contador + 1
			if invoice.debit_origin_id or invoice.reversed_entry_id:
				invoice.pe_stock_ids = False
				invoice.pe_stock_name = ""
				continue
			picking_ids =  invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('picking_ids') #self._cr.fetchall()
			pe_stock_ids = []
			pe_stock_name = ""
			numbers=[]
			for picking_id in picking_ids:
				if picking_id.state not in ['draft', 'cancel']: 
					numbers.append(picking_id.name)
					pe_stock_ids.append(picking_id.id)
			if numbers:
				if len(numbers)==1:
					pe_stock_name=numbers[0]
				else:
					pe_stock_name = " - ".join(numbers)
			invoice.pe_stock_ids = False if len(pe_stock_ids) == 0  else pe_stock_ids
			invoice.pe_stock_name = pe_stock_name


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	pack_lot_ids = fields.Many2many(comodel_name="stock.move.line", string="Lotes / Series", compute ="_get_pack_lot_ids", readonly=True, copy=False)
	pack_lot_name = fields.Char("Nombres Lotes / Series", compute ="_get_pack_lot_ids")

	@api.model
	@api.depends("move_id.pe_stock_ids", 'product_id')
	def _get_pack_lot_ids(self):
		for line in self:
			if line.move_id.pe_stock_ids.mapped('move_line_ids').mapped('lot_id'):
				pack_lot_ids = line.move_id.pe_stock_ids.mapped('move_line_ids').filtered(lambda lot: lot.product_id == line.product_id)
				pack_lot_name=[]
				for pack_lot_id in pack_lot_ids:
					name=""
					if line.product_id.tracking=='serial':
						name+="S/N. "
					elif line.product_id.tracking=='lot':
						name+="Lt. "
					name+= (pack_lot_id.lot_id and pack_lot_id.lot_id.name or pack_lot_id.lot_name or "")+" "
					if pack_lot_id.product_qty:
						name+= "Cant. %s" % str(pack_lot_id.product_qty)
					if pack_lot_id.lot_id.life_date:
						name+= "FV. %s" % datetime.strptime(pack_lot_id.lot_id.life_date,'%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y')
					pack_lot_name.append(name)
				line.pack_lot_name= pack_lot_name and "\n".join(pack_lot_name) or False
				line.pack_lot_ids = pack_lot_ids.ids
