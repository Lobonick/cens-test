# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning

class MoneyMovemenents(models.Model):
	_name = 'solse.money.movements'
	_description = 'Movimientos de dinero'
	_order = "payment_time desc, order_number desc"
	
	payment_origin = fields.Many2one('account.payment', 'Pago de origen', index=True, readonly=True)
	journal_mov = fields.Many2one('account.journal', 'Diario afectado', index=True, readonly=True)
	company_id = fields.Many2one('res.company', related='journal_mov.company_id', string='Compañia', readonly=True)
	movement_type = fields.Selection(string='Tipo movimiento', selection=[('E', 'Entrada'), ('S', 'Salida')], readonly=True)
	currency_id = fields.Many2one('res.currency', 'Moneda', related='payment_origin.currency_id', store=True, readonly=True)
	amount = fields.Float('Monto', readonly=True)
	operation_amount = fields.Monetary('Monto para operacion', compute='_compute_operation_amount', store=True)
	payment_time = fields.Datetime('Fecha/hora pago', related='payment_origin.payment_time', store=True, readonly=True)
	payment_time_char = fields.Char(string="Fecha/hora pago", compute="_compute_payment_time_char", store=True, readonly=True)
	description = fields.Char('Detalle', readonly=True, compute="_compute_reg_previus", store=True)
	glosa = fields.Char('Glosa', related='payment_origin.ref', store=True)
	balance = fields.Float('Saldo por moneda', readonly=True, compute="_compute_reg_previus", store=True)

	reg_previous = fields.Many2one('solse.money.movements', 'Registro anterior', index=True, ondelete='cascade', compute='_compute_reg_previus', store=True)
	order_number = fields.Integer('Sub orden', default=0, readonly=True) 
	state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Estado")

	@api.depends('payment_time')
	def _compute_payment_time_char(self):
		for reg in self:
			if reg.payment_time:
				#reg.payment_time_char = str(reg.payment_time).split("." )[0]
				record = self.with_context(tz=self.env.user.tz)
				#fecha_hora = reg.payment_time.strftime("%Y/%m/%d %I:%M %p")
				#send_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(record, fecha_hora))
				send_date = fields.Datetime.context_timestamp(record, reg.payment_time).strftime("%Y/%m/%d %I:%M %p")
				reg.payment_time_char = send_date #send_date.
			else:
				reg.payment_time_char = ""
	
	@api.depends('amount', 'movement_type')
	def _compute_operation_amount(self):
		for reg in self:
			increase_with_tickets = False # configuracion de calculo segun la compañia
			if reg.company_id.money_movement_type == 's':
				increase_with_tickets = True
			condition_base = increase_with_tickets and 'E' or 'S'
			condition = condition_base == reg.movement_type
			reg.operation_amount = condition and reg.amount or reg.amount * -1

	#@api.one
	@api.depends('journal_mov', 'payment_time', 'currency_id', 'state', 'movement_type', 'amount')
	def _compute_reg_previus(self):
		for reg in self:
			if reg.company_id.calculate_money_balance:
				rpt = reg.resolvePreviousRecord()
				reg.reg_previous = rpt['reg_previous']
				reg.description = rpt['description']
				reg.balance = rpt['balance']
			else:
				reg.reg_previous = False
				reg.description = ""
				reg.balance = 0

	def resolvePreviousRecord(self):
		self.ensure_one()
		rpt = {}
		increase_with_tickets = False # configuracion de calculo segun la compañia
		if self.company_id.money_movement_type == 's':
			increase_with_tickets = True
		# obtenemos el registro anterior
		reg_previous = self.env['solse.money.movements'].search([('journal_mov', '=', self.journal_mov.id), 
			('currency_id', '=', self.currency_id.id), ('payment_time', '<', self.payment_time), ('state', 'not in', ['draft', 'cancelled'])], 
			order='payment_time desc, order_number desc', limit=1)

		condition_base = increase_with_tickets and 'E' or 'S'
		condition = condition_base == self.movement_type
		previous_temporary_id = self.id
		balance = 0
		if self.state not in ['draft', 'cancelled']:
			# calculalamos y actualizamos el saldo en base al registro anterior
			if reg_previous:
				balance = condition and reg_previous.balance + self.amount or reg_previous.balance - self.amount
			else:
				balance = condition and self.amount or self.amount * -1
		else:
			previous_temporary_id = reg_previous.id
			if reg_previous:
				balance = condition and reg_previous.balance + self.amount or reg_previous.balance - self.amount
		
		rpt['description'] = datetime.now()
		rpt['balance'] = balance
		# actualizamos los registros en adelante
		records_onwards = self.env['solse.money.movements'].search([('journal_mov', '=', self.journal_mov.id), 
			('currency_id', '=', self.currency_id.id), ('payment_time', '>=', self.payment_time), ('id', '!=', self.id), ('state', 'not in', ['draft', 'cancelled'])], 
			order='payment_time')
		order_number = 0
		new_balance = 0
		for record in records_onwards:
			order_number += 1
			condition = condition_base == record.movement_type
			new_balance = condition and balance + record.amount or balance - record.amount
			self.env['solse.money.movements'].search([('id', '=', record.id)], limit=1).write({
					"reg_previous": previous_temporary_id,
					"balance": new_balance,
					"order_number": order_number,
					"description": datetime.now(),
					"operation_amount": condition and record.amount or record.amount * -1
				})
			balance = new_balance
			previous_temporary_id = record.id
		
		self.env['account.journal'].search([('id', '=', self.journal_mov.id)], limit=1).write({
				"balance": balance
			})

		rpt['reg_previous'] = reg_previous.id
		return rpt

	def force_update(self):
		for reg in self:
			if reg.company_id.calculate_money_balance:
				reg.resolvePreviousRecord()
			else:
				raise Warning("La compañía no tiene habilitado el calculo automatico")