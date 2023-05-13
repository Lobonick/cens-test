# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning
import logging
_logging = logging.getLogger(__name__)
import pytz

tz = pytz.timezone('America/Lima')

class CompanyConfirmReports(models.TransientModel):
	_name = "solse.company.confirm.reports"
	_description = "Wizard reports"

	operation_time = fields.Datetime('Tiempo de operación', required=True, default=lambda a: fields.Datetime.now(tz))

	#@api.one
	def recalculate_money(self):
		self.ensure_one()
		record_journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash']), ('active', '=', True)])
		for record in record_journal:
			increase_with_tickets = False # configuracion de calculo segun la compañia
			if record.company_id.money_movement_type == 's':
				increase_with_tickets = True
			self.calculate_money_journal(record, increase_with_tickets)
		
		return {'type': 'ir.actions.act_window_close'}

	def calculate_money_journal(self, journal, increase_with_tickets):
		
		coins = self.env['res.currency'].search([('active', '=', True)])
		for currency in coins:
			previous_temporary = self.env['solse.money.movements'].search([('journal_mov', '=', journal.id), 
				('currency_id', '=', currency.id), ('payment_time', '<', self.operation_time), ('state', 'not in', ['draft', 'cancelled'])], 
				order='payment_time desc, order_number desc', limit=1)
			condition_base = increase_with_tickets and 'E' or 'S'
			previous_temporary_id = previous_temporary.id
			balance = previous_temporary and previous_temporary.balance or 0

			# actualizamos los registros en adelante
			records_onwards = self.env['solse.money.movements'].search([('journal_mov', '=', journal.id), 
				('currency_id', '=', currency.id), ('payment_time', '>=', self.operation_time), ('state', 'not in', ['draft', 'cancelled'])], 
				order='payment_time')
			order_number = 0
			new_balance = 0
			for record in records_onwards:
				order_number += 1
				condition = condition_base == record.movement_type
				new_balance = balance + record.amount if condition else balance - record.amount
				self.env['solse.money.movements'].search([('id', '=', record.id)], limit=1).write({
						"reg_previous": previous_temporary_id,
						"balance": new_balance,
						"order_number": order_number,
						"description": datetime.now(),
						"operation_amount": condition and record.amount or record.amount * -1
					})
				previous_temporary_id = record.id
				balance = new_balance
			
			if previous_temporary or order_number > 0:
				self.env['account.journal'].search([('id', '=', journal.id)], limit=1).write({
						"balance": balance
					})
		
	#@api.one
	def recalculate_balance(self):
		self.ensure_one()
		partners = self.env['res.partner'].search(['|', ('customer_rank', '>', 0), ('supplier_rank', '>', 0), ('active', '=', True)])
		for partner in partners:
			increase_with_tickets = False # configuracion de calculo segun la compañia
			if partner.company_id.account_movement_type == 's':
				increase_with_tickets = True
			if partner.supplier_rank > 0:
				self.calculate_balance_partner(partner, 'supplier', increase_with_tickets)
			if partner.customer_rank > 0:
				self.calculate_balance_partner(partner, 'customer', increase_with_tickets)
		return {'type': 'ir.actions.act_window_close'}

	def calculate_balance_partner(self, partner, partner_type, increase_with_tickets):
		
		coins = self.env['res.currency'].search([('active', '=', True)])
		for currency in coins:
			previous_temporary = self.env['solse.account.balances'].search([('partner_id', '=', partner.id), ('partner_type', '=', partner_type),
				('currency_id', '=', currency.id), ('operation_time', '<', self.operation_time), ('state', 'not in', ['draft', 'cancelled', 'cancel'])], 
			order='operation_time desc, order_number desc', limit=1)
			condition_base = increase_with_tickets and 'E' or 'S'
			previous_temporary_id = previous_temporary.id
			balance = previous_temporary and previous_temporary.balance or 0

			# actualizamos los registros en adelante
			records_onwards = self.env['solse.account.balances'].search([('partner_id', '=', partner.id), ('partner_type', '=', partner_type),
			('currency_id', '=', currency.id), ('operation_time', '>=', self.operation_time), ('state', 'not in', ['draft', 'cancelled', 'cancel'])], 
			order='operation_time')
			order_number = 0
			new_balance = 0
			for record in records_onwards:
				order_number += 1
				condition = condition_base == record.movement_type
				new_balance = balance + record.amount if condition else balance - record.amount
				self.env['solse.account.balances'].search([('id', '=', record.id)], limit=1).write({
						"reg_previous": previous_temporary_id,
						"balance": new_balance,
						"order_number": order_number,
						"description": datetime.now(),
						"operation_amount": condition and record.amount or record.amount * -1
					})
				previous_temporary_id = record.id
				balance = new_balance
			
			if previous_temporary or order_number > 0:
				parm_partner = {}
				if partner_type == 'supplier':
					parm_partner['balance_as_supplier'] = balance
				else:
					parm_partner['balance_as_customer'] = balance
				self.env['res.partner'].search([('id', '=', partner.id)], limit=1).write(parm_partner)