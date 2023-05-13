# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
from datetime import datetime
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import Warning
import pytz

tz = pytz.timezone('America/Lima')

import logging
_logger = logging.getLogger(__name__)
_DATOS_JSON = {}

def limpiar():
	_DATOS_JSON = {}

class stockMoveline(models.Model):
	_inherit = 'stock.move.line'
	_order = "date desc, order_number desc, tiempo desc"

	type_move = fields.Selection([
			('in','Movimiento entrada'),
			('out','Movimiento de salida'),
			('internal', 'Movimiento interno')
		], string='Tipo de movimiento ', default="out", index=True, store=True, readonly=True, compute='_compute_type_move', copy=False)

	type_operation = fields.Selection([
			('out','Venta'),
			('return_out','Devolucion de venta'),
			('in', 'Compra'),
			('return_in','Devolución de compra'),
			('internal','Transferencia entre almacenes'),
			('invetory','Ajuste de inventario'),
			('undefined','No definido'),
		], string='Tipo de movimiento ', index=True, store=True, readonly=True, compute='_compute_type_operation', copy=False)

	balance_previous = fields.Float(
		string='Saldo anterior',
		readonly=True,
		compute='_compute_balance_previous',
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)

	categ_id = fields.Many2one("product.category", string="Categoria", related="product_id.categ_id", store=True)

	qty_in = fields.Float(
		string='Ingresos',
		readonly=True,
		compute='_compute_qty_in',
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)
	qty_in_total = fields.Float(
		string='Ingresos Total',
		readonly=True,
		compute='_compute_qty_in_total',
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)

	qty_out = fields.Float(
		string='Salidas',
		readonly=True,
		compute='_compute_qty_out',
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)
	qty_out_total = fields.Float(
		string='Salidas Total',
		readonly=True,
		compute='_compute_qty_out_total',
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)
	operation_amount = fields.Float('Monto operacion', compute='_compute_operation_amount', digits=dp.get_precision('Product Unit of Measure'), store=True)

	description = fields.Char('Detalle', compute="_compute_reg_previus", store=True)
	tiempo = fields.Datetime('Tiempo', required=True, default=lambda a: fields.Datetime.now(tz))
	tiempo2 = fields.Float('Tiempo 2', default=0.0)
	balance = fields.Float(
		string='Saldo',
		readonly=True,
		compute="_compute_reg_previus",
		digits=dp.get_precision('Product Unit of Measure'),
		store=True
	)

	origin = fields.Char(
		string='Origen',
		readonly=True,
		compute='_compute_origin',
		store=True
	)
	calcular = fields.Boolean('Calcular', default=True)

	reg_previous = fields.Many2one('stock.move.line', string="Registro anterior", index=True, ondelete="cascade", compute='_compute_reg_previus', store=True)
	order_number = fields.Integer('Sub orden', default=0, readonly=True)
	id_char = fields.Integer(related='reg_previous.id')

	@api.depends('qty_done', 'type_move')
	def _compute_operation_amount(self):
		for reg in self:
			increase_with_tickets = False # configuracion de calculo segun la compañia
			if reg.move_id.company_id.stock_movement_type == 's':
				increase_with_tickets = True
			condition_base = increase_with_tickets and 'in' or 'out'
			if reg.type_move == 'internal':
				reg.operation_amount = False
			else:
				condition = condition_base == reg.type_move
				reg.operation_amount = condition and reg.qty_done or reg.qty_done * -1

	@api.depends('product_id', 'type_move', 'qty_done', 'state', 'date')
	def _compute_reg_previus(self):
		cantidad = len(self)
		if len(self) > 1:
			for reg in self:
				if reg.move_id.company_id.calculate_stock_balance and reg.product_id.product_tmpl_id.type=='product' and reg.type_move in ['in', 'out', 'internal'] and reg.id in _DATOS_JSON:
					reg.reg_previous = _DATOS_JSON[reg.id]['reg_previous']
					reg.balance = _DATOS_JSON[reg.id]['balance']
					reg.description = _DATOS_JSON[reg.id]['description']
				else:
					reg.reg_previous = False
					reg.balance = 0
					reg.description = ""
			limpiar()
		else:
			for reg in self:
				if reg.move_id.company_id.calculate_stock_balance and reg.product_id.product_tmpl_id.type=='product' and reg.type_move in ['in', 'out', 'internal']:
					try:
						rpt = reg.resolvePreviousRecord(cantidad)
						reg.reg_previous = rpt['reg_previous']
						reg.balance = rpt['balance']
						reg.description = rpt['description']
						_DATOS_JSON[reg.id] = {
							'reg_previous': rpt['reg_previous'] if rpt['reg_previous'] else False,
							'balance': rpt['balance'] if rpt['balance'] else 0,
							'description': rpt['description'] if rpt['description'] else "",
						}
					except Exception as e:
						reg.reg_previous = False
						reg.balance = 0
						reg.description = ""
				else:
					reg.reg_previous = False
					reg.balance = 0
					reg.description = ""

	# hay un incoveniente cuando el producto maneja series y la cantidad es mayor a 1 (27-06-2020)
	def resolvePreviousRecord(self, cantidad):
		rpt = {}
		increase_with_tickets = True # configuracion de calculo segun la compañia
		# obtenemos el registro anterior
		#estados_filtro = ['done', 'assigned', 'confirmed', 'waiting']
		estados_filtro = ['draft', 'cancel']
		condicion = 'not in'
		if cantidad > 1:
			reg_previous = self.env['stock.move.line'].search([('id', '!=', self.id), ('product_id', '=', self.product_id.id), ('date', '=', self.date), ('state', condicion, estados_filtro)], order='date desc, order_number desc')
			if len(reg_previous) > 0:
				reg_previous = self.env['stock.move.line'].search([('id', '!=', self.id), ('product_id', '=', self.product_id.id), ('date', '<=', self.date), ('state', condicion, estados_filtro), ('tiempo2', '<', self.tiempo2)], order='date desc, order_number desc', limit=1)
			else:
				reg_previous = self.env['stock.move.line'].search([('id', '!=', self.id), ('product_id', '=', self.product_id.id), ('date', '<', self.date), ('state', condicion, estados_filtro)], order='date desc, order_number desc', limit=1)
		else:
			reg_previous = self.env['stock.move.line'].search([('id', '!=', self.id), ('product_id', '=', self.product_id.id), ('date', '<', self.date), ('state', condicion, estados_filtro)], order='date desc, order_number desc', limit=1)

		#reg_previous = self.env['stock.move.line'].search([('product_id', '=', self.product_id.id), ('date', '<', self.date), ('state', 'not in', ['draft', 'cancel'])],order='date desc, order_number desc', limit=1)

		movement_type = self.type_move == 'in' and 'E' or 'S'
		condition_base = increase_with_tickets and 'E' or 'S'
		condition = condition_base == movement_type
		previous_temporary_id = self.id
		balance = 0
		quantity = self.qty_done
		"""if self.product_uom_id.uom_type == 'bigger':
			#quantity = quantity * self.product_uom_id.factor
			quantity = quantity / self.product_uom_id.factor
		elif self.product_uom_id.uom_type == 'smaller':
			quantity = quantity / self.product_uom_id.factor"""

		if self.state not in ['draft', 'cancel']:
			# calculalamos y actualizamos el saldo en base al registro anterior
			if reg_previous and self.type_move == "internal":
				balance = reg_previous.balance
			elif reg_previous:
				balance = reg_previous.balance + quantity if condition else reg_previous.balance - quantity
			else:
				balance = condition and quantity or quantity * -1
		else:
			previous_temporary_id = reg_previous.id
			if reg_previous and self.type_move == "internal":
				balance = reg_previous.balance
			elif reg_previous:
				balance = reg_previous.balance + quantity if condition else reg_previous.balance - quantity
		
		rpt['balance'] = balance
		rpt['description'] = datetime.now()

		# actualizamos los registros en adelante
		#records_onwards = self.env['stock.move.line'].search([('product_id', '=', self.product_id.id), ('date', '>=', self.date), ('id', 'not in', [self.id, reg_previous.id]), ('state', 'not in', ['draft', 'cancel'])], order='date')
		records_onwards = []
		if reg_previous:
			records_onwards = self.env['stock.move.line'].search([('product_id', '=', self.product_id.id), ('date', '>=', self.date), ('id', 'not in', [self.id, reg_previous.id]), ('state', condicion, estados_filtro)], order='date')
		else:
			records_onwards = self.env['stock.move.line'].search([('product_id', '=', self.product_id.id), ('date', '>=', self.date), ('id', '!=', self.id), ('state', condicion, estados_filtro)], order='date')
		order_number = 0
		new_balance = 0
		if cantidad > 1:
			rpt['reg_previous'] = reg_previous.id
			return rpt
		for record in records_onwards:
			order_number += 1
			movement_type = record.type_move == 'in' and 'E' or 'S'
			condition = condition_base == movement_type
			quantity = record.qty_done
			"""if record.product_uom_id.uom_type == 'bigger':
				quantity = quantity / record.product_uom_id.factor
			elif record.product_uom_id.uom_type == 'smaller':
				quantity = quantity / record.product_uom_id.factor"""

			if record.type_move == 'internal':
				new_balance = balance
			else:
				new_balance = balance + quantity if condition else balance - quantity
			data_line_onwards = {
					"reg_previous": previous_temporary_id,
					"balance": new_balance,
					"order_number": order_number,
					"description": datetime.now(),
					"tiempo": datetime.now(),
					"tiempo2": round(time.time() * 1000),
					"calcular": False,
				}

			if movement_type == 'E':
				data_line_onwards['qty_in_total'] = quantity
			else:
				data_line_onwards['qty_out_total'] = quantity

			self.env['stock.move.line'].search([('id', '=', record.id)], limit=1).write(data_line_onwards)
			previous_temporary_id = record.id
			balance = new_balance
		
		rpt['reg_previous'] = reg_previous.id
		return rpt

	@api.depends('location_id', 'location_dest_id')
	def _compute_type_move(self):
		for reg in self:
			if not reg.location_id or not reg.location_dest_id:
				reg.type_move = 'internal'
				continue
			if reg.location_id.usage == 'internal' and reg.location_dest_id.usage  == 'internal':
				reg.type_move = 'internal'
			elif reg.location_id.usage == 'internal' and reg.location_dest_id.usage  != 'internal':
				reg.type_move = 'out'
			elif reg.location_id.usage != 'internal' and reg.location_dest_id.usage  == 'internal':
				reg.type_move = 'in'
			else:
				reg.type_move = 'internal'

	@api.depends('location_id', 'location_dest_id')
	def _compute_type_operation(self):
		for reg in self:
			if not reg.location_id or not reg.location_dest_id:
				reg.type_operation = 'undefined'
				continue
			if reg.location_id.usage == 'internal' and reg.location_dest_id.usage  == 'internal':
				reg.type_operation = 'internal'
			elif reg.location_id.usage == 'internal' and reg.location_dest_id.usage  == 'customer':
				reg.type_operation = 'out'
			elif reg.location_id.usage == 'internal' and reg.location_dest_id.usage  == 'supplier':
				reg.type_operation = 'return_in'
			elif reg.location_id.usage == 'internal' and reg.location_dest_id.usage  == 'inventory':
				reg.type_operation = 'invetory'
			elif reg.location_id.usage == 'customer' and reg.location_dest_id.usage  == 'internal':
				reg.type_operation = 'return_out'
			elif reg.location_id.usage == 'supplier' and reg.location_dest_id.usage  == 'internal':
				reg.type_operation = 'in'
			elif reg.location_id.usage == 'inventory' and reg.location_dest_id.usage  == 'internal':
				reg.type_operation = 'invetory'
			else:
				reg.type_operation = 'undefined'

	@api.depends('type_move', 'qty_done')
	def _compute_qty_in(self):
		for reg in self:
			type_move = reg.type_move
			if type_move == 'in':
				reg.qty_in = reg.qty_done
			elif type_move == 'out':
				reg.qty_in = 0
			elif type_move == 'internal':
				reg.qty_in = reg.qty_done

	@api.depends('type_move', 'qty_done')
	def _compute_qty_in_total(self):
		for reg in self:
			quantity = reg.qty_done
			"""if reg.product_uom_id.uom_type == 'bigger':
				quantity = quantity / reg.product_uom_id.factor
			elif reg.product_uom_id.uom_type == 'smaller':
				quantity = quantity / reg.product_uom_id.factor"""
			type_move = reg.type_move
			if type_move == 'in':
				reg.qty_in_total = quantity
			elif type_move == 'out':
				reg.qty_in_total = 0
			elif type_move == 'internal':
				reg.qty_in_total = quantity

	@api.depends('type_move', 'qty_done')
	def _compute_qty_out(self):
		for reg in self:
			type_move = reg.type_move
			if type_move == 'in':
				reg.qty_out = 0
			elif type_move == 'out':
				reg.qty_out = reg.qty_done
			elif type_move == 'internal':
				reg.qty_out = reg.qty_done

	@api.depends('type_move', 'qty_done')
	def _compute_qty_out_total(self):
		for reg in self:
			quantity = reg.qty_done
			"""if reg.product_uom_id.uom_type == 'bigger':
				quantity = quantity / reg.product_uom_id.factor
			elif reg.product_uom_id.uom_type == 'smaller':
				quantity = quantity / reg.product_uom_id.factor"""
			type_move = reg.type_move
			if type_move == 'in':
				reg.qty_out_total = 0
			elif type_move == 'out':
				reg.qty_out_total = quantity
			elif type_move == 'internal':
				reg.qty_out_total = quantity

	@api.depends('reg_previous')
	def _compute_balance_previous(self):
		for reg in self:
			reg.balance_previous = reg.reg_previous.balance

	@api.depends('picking_id')
	def _compute_origin(self):
		for reg in self:
			reg.origin = reg.picking_id.origin

	def force_update(self):
		if self.move_id.company_id.calculate_stock_balance:
			rpt = self.resolvePreviousRecord(1)
			self.reg_previous = rpt['reg_previous']
			self.balance = rpt['balance']
			self.description = rpt['description']
		else:
			raise Warning("La compañía no tiene habilitado el calculo automatico")

	def force_update_sin_filtro(self):
		rpt = self.resolvePreviousRecord(1)
		self.reg_previous = rpt['reg_previous']
		self.balance = rpt['balance']
		self.description = rpt['description']


