# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning
import pytz

tz = pytz.timezone('America/Lima')

class AccountPayment(models.Model):
	_inherit = 'account.payment'
	
	def _default_payment_hour(self):
		reg_datetime = datetime.now(tz)
		return reg_datetime.strftime("%H:%M:%S")

	payment_hour = fields.Char(string="Hora", required=True, default=_default_payment_hour)
	payment_time = fields.Datetime('Fecha/hora pago', compute="_compute_payment_time", readonly=False, store=True)
	payment_time_move = fields.Datetime(compute='_compute_datetime_payment_move', store=True)

	@api.depends('date', 'payment_hour')
	def _compute_payment_time(self):
		for reg in self:
			if reg.date and reg.payment_hour:
				reg_datetime = str(reg.date)+" "+str(reg.payment_hour)
				"""datetime_obj_naive = datetime.strptime(reg_datetime, "%Y-%m-%d %H:%M:%S")
				
				datetime_obj_lima = pytz.timezone('America/Lima').localize(datetime_obj_naive)
				reg.payment_time = datetime_obj_lima.strftime("%Y-%m-%d %H:%M:%S")"""
				reg.payment_time =  datetime.now()

	#@api.one
	@api.depends('payment_type', 'payment_time', 'journal_id', 'currency_id', 'amount', 'state', 'journal_id')
	def _compute_datetime_payment_move(self):
		for reg in self:
			if reg.payment_type in ['inbound', 'outbound']:
				reg.processMovement()
			elif reg.payment_type == 'transfer':
				reg.proccessTransfer()
			reg.payment_time_move = datetime.now()

	def processMovement(self):
		movement_type = self.payment_type == 'inbound' and 'E' or 'S'
		data_mov = {
			"payment_origin": self.id,
			"journal_mov": self.journal_id and self.journal_id.id,
			"movement_type": movement_type,
			"amount": self.amount,
			"state": self.state
		}

		movement_type_balance = movement_type
		if self.partner_type == 'supplier':
			movement_type_balance = self.payment_type == 'outbound' and 'E' or 'S'
		account_balance = {
			"payment_origin": self.id,
			"journal_mov": self.journal_id and self.journal_id.id,
			"movement_type": movement_type_balance,
			"amount": self.amount,
			"state": self.state,
			"operation_time": self.payment_time,
			"currency_id": self.currency_id.id,
			"partner_id": self.partner_id.id,
			"partner_type": self.partner_type
		}
		# si el pago es por alguna nota de credito cancelamos el movimiento de balance respectivo
		if movement_type == 'E' and self.partner_type == 'supplier' or movement_type == 'S' and self.partner_type == 'customer':
			account_balance['state'] = "cancelled"


		movements = self.env['solse.money.movements'].search([('payment_origin','=', self.id)])
		total_records = len(movements)
		if total_records == 0:
			self.env['solse.money.movements'].create(data_mov)
		elif total_records == 1:
			movements.write(data_mov)
		elif total_records == 2:
			position = 1
			for reg in movements:
				if position == 1:
					reg.amount = self.amount
					reg.state = self.state
					reg.journal_mov = self.journal_id and self.journal_id.id,
					reg.movement_type = movement_type
				else:
					reg.state = 'cancelled'
				position += 1
		else:
			raise Warning('No se pudo modificar los registros')

		movements_balance = self.env['solse.account.balances'].search([('payment_origin','=', self.id)])
		total_records = len(movements_balance)
		if total_records == 0:
			self.env['solse.account.balances'].create(account_balance)
		elif total_records == 1:
			movements_balance.write(account_balance)
		elif total_records == 2:
			position = 1
			for reg in movements_balance:
				if position == 1:
					reg.amount = self.amount
					reg.state = self.state
					reg.journal_mov = self.journal_id and self.journal_id.id,
					reg.movement_type = movement_type_balance
					reg.operation_time = self.payment_time
					reg.currency_id = self.currency_id.id
					reg.partner_id = self.partner_id.id
					reg.partner_type = self.partner_type
				else:
					reg.state = 'cancelled'
				position += 1
		else:
			raise Warning('No se pudo modificar los registros')

	def proccessTransfer(self):
		origin = {
			"payment_origin": self.id,
			"journal_mov": self.journal_id and self.journal_id.id,
			"movement_type": "S",
			"amount": self.amount,
			"state": self.state 
		}
		destination = {
			"payment_origin": self.id,
			"journal_mov": self.journal_id and self.journal_id.id,
			"movement_type": "E",
			"amount": self.amount,
			"state": self.state
		}
		movements = self.env['solse.money.movements'].search([('payment_origin','=', self.id)])
		total_records = len(movements)
		if total_records == 0:
			self.env['solse.money.movements'].create(origin)
			self.env['solse.money.movements'].create(destination)
		elif total_records == 1:
			movements.write(origin)
			self.env['solse.money.movements'].create(destination)
		elif total_records == 2:
			position = 1
			for reg in movements:
				reg.amount = self.amount
				reg.state = self.state
				if position == 1:
					reg.journal_mov = self.journal_id and self.journal_id.id
					reg.movement_type = 'S'
				else:
					reg.journal_mov = self.journal_id and self.journal_id.id
					reg.movement_type = 'E'
				position += 1
		else:
			raise Warning('No se pudo procesar el movimiento')

		# cancelamos los movimientos de balance que puede haber generado
		movements_balance = self.env['solse.account.balances'].search([('payment_origin','=', self.id)])
		for reg in movements_balance:
			reg.state = 'cancelled'