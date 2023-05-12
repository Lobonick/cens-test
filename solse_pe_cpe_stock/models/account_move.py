# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _get_stock_type_ids(self):
		company_ids = self.env.context.get('allowed_company_ids', [])
		data = self.env['stock.picking.type'].search([('company_id', 'in', company_ids)])
		if not data:
			data = self.env['stock.picking.type'].search([('company_id', '=', False)])
		
		if self._context.get('default_move_type') in ['out_invoice', 'in_refund']:
			for line in data:
				if line.code == 'outgoing':
					return line

		if self._context.get('default_move_type') in ['in_invoice', 'out_refund']:
			for line in data:
				if line.code == 'incoming':
					return line

	picking_count = fields.Integer(string="Count", copy=False)
	picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', default=_get_stock_type_ids, help="This will determine picking type of incoming shipment")
	invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id", copy=False)
	invoice_picking_cancel_id = fields.Many2one('stock.picking', string="Picking Cancel Id", copy=False)
	devolver_al_anular = fields.Boolean("Devolver stock al anular", default=True)

	def obtener_picking_type_id(self):
		data = self.env['stock.picking.type'].search([('company_id', 'in', [self.company_id.id])])
		if not data:
			data = self.env['stock.picking.type'].search([('company_id', '=', False)])
		
		if self.move_type in ['out_invoice', 'in_refund']:
			for line in data:
				if line.code == 'outgoing':
					return line

		if self.move_type in ['in_invoice', 'out_refund']:
			for line in data:
				if line.code == 'incoming':
					return line

	def asignar_picking_type_id(self):
		self.picking_type_id = self.obtener_picking_type_id().id

	def action_stock_move(self):
		if not self.picking_type_id:
			raise UserError(_(" Please select a picking type"))
			
		for order in self:
			if not self.invoice_picking_id:
				pick = {}
				if self.picking_type_id.code == 'outgoing':
					pick = {
						'picking_type_id': self.picking_type_id.id,
						'partner_id': self.partner_id.id,
						'origin': self.name,
						'factura_id': self.id,
						'location_dest_id': self.partner_id.property_stock_customer.id,
						'location_id': self.picking_type_id.default_location_src_id.id,
						'move_type': 'direct'
					}
				if self.picking_type_id.code == 'incoming':
					pick = {
						'picking_type_id': self.picking_type_id.id,
						'partner_id': self.partner_id.id,
						'origin': self.name,
						'factura_id': self.id,
						'location_dest_id': self.picking_type_id.default_location_dest_id.id,
						'location_id': self.partner_id.property_stock_supplier.id,
						'move_type': 'direct'
					}
				picking = self.env['stock.picking'].create(pick)
				self.invoice_picking_id = picking.id
				self.picking_count = len(picking)
				moves = order.invoice_line_ids.filtered(
					lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
				move_ids = moves._action_confirm()
				move_ids._action_assign()

	def action_view_picking(self):
		# action = self.env.ref('stock.action_picking_tree_ready')
		result = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
		result['context'] = {}
		pick_ids = []
		if self.invoice_picking_id:
			pick_ids.append(self.invoice_picking_id.id)
		if self.invoice_picking_cancel_id:
			pick_ids.append(self.invoice_picking_cancel_id.id)

		# pick_ids = sum([self.invoice_picking_id.id])
		if len(pick_ids) == 1:
			res = self.env.ref('stock.view_picking_form', False)
			result['views'] = [(res and res.id or False, 'form')]
			result['res_id'] = pick_ids[0] or False
		elif len(pick_ids) > 1:
			# result['domain'] = [('id', 'in', pick_ids)]
			res = self.env.ref('stock.vpicktree', False)
			result['views'] = [(res and res.id or False, 'tree')]
			result['domain'] = [('id', 'in', pick_ids)]
			result['res_ids'] = pick_ids

		return result

	def _reverse_moves(self, default_values_list=None, cancel=False):
		if self.picking_type_id.code == 'outgoing':
			data = self.env['stock.picking.type'].search(
				[('company_id', '=', self.company_id.id), ('code', '=', 'incoming')], limit=1)
			self.picking_type_id = data.id
		elif self.picking_type_id.code == 'incoming':
			data = self.env['stock.picking.type'].search(
				[('company_id', '=', self.company_id.id), ('code', '=', 'outgoing')], limit=1)
			self.picking_type_id = data.id
		reverse_moves = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
		return reverse_moves

	def obtener_picking(self, tipo):
		data = self.env['stock.picking.type'].search([('company_id', '=', self.company_id.id), ('code', '=', tipo)], limit=1)
		return data
	
	def button_cancel(self):
		super(AccountMove, self).button_cancel()
		for order in self:
			if not order.invoice_picking_cancel_id and order.devolver_al_anular:
				if not order.invoice_line_ids:
					return
				pick = {}
				picking_type_id = False
				if self.picking_type_id.code == 'outgoing':
					data = self.obtener_picking('incoming')
					picking_type_id = data
				elif self.picking_type_id.code == 'incoming':
					data = self.obtener_picking('outgoing')
					picking_type_id = data

				if not picking_type_id:
					continue

				if picking_type_id.code == 'outgoing':
					pick = {
						'picking_type_id': picking_type_id.id,
						'partner_id': order.partner_id.id,
						'origin': order.name,
						'factura_id': order.id,
						'location_dest_id': order.partner_id.property_stock_customer.id,
						'location_id': picking_type_id.default_location_src_id.id,
						'move_type': 'direct'
					}
				if picking_type_id.code == 'incoming':
					pick = {
						'picking_type_id': picking_type_id.id,
						'partner_id': order.partner_id.id,
						'origin': order.name,
						'factura_id': order.id,
						'location_dest_id': picking_type_id.default_location_dest_id.id,
						'location_id': order.partner_id.property_stock_supplier.id,
						'move_type': 'direct'
					}

				picking = self.env['stock.picking'].create(pick)
				order.invoice_picking_cancel_id = picking.id
				order.picking_count = order.picking_count + len(picking)
				moves = order.invoice_line_ids.filtered(
					lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)

				if not moves:
					raise UserError("No se pudieron cargar los productos a devolver")

				for move_line_id in moves:
					move_line_id.quantity_done = move_line_id.product_uom_qty

				move_ids = moves._action_confirm()
				_logging.info(move_ids)
				move_ids._action_assign()
				picking.action_confirm()
				picking.action_assign()
				wizard = self.env['stock.immediate.transfer'].with_context(
					dict(self.env.context, default_show_transfers=False,
						 default_pick_ids=[(4, picking.id)])).create({})

				if wizard:
					wizard.process()

				picking.button_validate()

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def _create_stock_moves(self, picking):
		moves = self.env['stock.move']
		done = self.env['stock.move'].browse()
		for line in self:
			price_unit = line.price_unit
			if picking.picking_type_id.code == 'outgoing':
				template = {
					'name': line.name or '',
					'product_id': line.product_id.id,
					'product_uom': line.product_uom_id.id,
					'location_id': picking.picking_type_id.default_location_src_id.id,
					'location_dest_id': line.move_id.partner_id.property_stock_customer.id,
					'picking_id': picking.id,
					'state': 'draft',
					'company_id': line.move_id.company_id.id,
					'price_unit': price_unit,
					'picking_type_id': picking.picking_type_id.id,
					'route_ids': 1 and [
						(6, 0, [x.id for x in self.env['stock.rule'].search([('id', 'in', (2, 3))])])] or [],
					'warehouse_id': picking.picking_type_id.warehouse_id.id,
				}
			if picking.picking_type_id.code == 'incoming':
				template = {
					'name': line.name or '',
					'product_id': line.product_id.id,
					'product_uom': line.product_uom_id.id,
					'location_id': line.move_id.partner_id.property_stock_supplier.id,
					'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
					'picking_id': picking.id,
					'state': 'draft',
					'company_id': line.move_id.company_id.id,
					'price_unit': price_unit,
					'picking_type_id': picking.picking_type_id.id,
					'route_ids': 1 and [
						(6, 0, [x.id for x in self.env['stock.rule'].search([('id', 'in', (2, 3))])])] or [],
					'warehouse_id': picking.picking_type_id.warehouse_id.id,
				}
			diff_quantity = line.quantity
			tmp = template.copy()
			tmp.update({
				'product_uom_qty': diff_quantity,
			})
			template['product_uom_qty'] = diff_quantity
			done += moves.create(template)
		return done