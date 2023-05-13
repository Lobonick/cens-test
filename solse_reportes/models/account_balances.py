# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning

class AccountBalances(models.Model):
	_name = 'solse.account.balances'
	_description = 'Cuentas de saldos'   
	_order = "operation_time desc, order_number desc"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
	
	def _default_company(self):
		return self.env['res.company']._company_default_get('res.partner')

	company_id = fields.Many2one('res.company', 'Compañia', index=True, default=_default_company, readonly=True)
	partner_id = fields.Many2one('res.partner', string='Entidad', index=True, readonly=True)
	partner_type = fields.Selection([('customer', 'Cliente'), ('supplier', 'Proveedor')], readonly=True, string='Tipo entidad')
	journal_mov = fields.Many2one('account.journal', 'Diario afectado', index=True, readonly=True)

	payment_origin = fields.Many2one('account.payment', 'Pago origen', index=True, readonly=True)
	invoice_origin = fields.Many2one('account.move', 'Factura origen', index=True, readonly=True)
	# Tipo de movimiento con respecto a la compañia
	movement_type = fields.Selection(string='Tipo movimiento', selection=[('E', 'Haber'), ('S', 'Debe')], readonly=True) 
	currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
	amount = fields.Float('Monto', readonly=True)
	operation_amount = fields.Monetary('Monto operacion', compute='_compute_operation_amount', store=True)
	operation_time = fields.Datetime('Fecha/hora operacion', readonly=True)
	operation_time_char = fields.Char(string='Fecha/hora operacion', compute="_compute_operation_time_char", store=True, readonly=True)
	description = fields.Char('Detalle', compute="_compute_reg_previus", store=True)
	
	state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled'), ('annul', 'Annul'), ('open', 'Open'), ('paid', 'Paid'), ('cancel', 'Cancelled'), ('cancel', 'Cancelled')], readonly=True, default='draft', copy=False, string="Estado")
	
	balance = fields.Float('Saldo por moneda', readonly=True, compute="_compute_reg_previus", store=True) # por compañia->partner_id -> partner_type
	reg_previous = fields.Many2one('solse.account.balances', 'Registro anterior', index=True, ondelete='cascade', compute='_compute_reg_previus', store=True)
	order_number = fields.Integer('Sub orden', default=0, readonly=True) 
	
	@api.depends('operation_time')
	def _compute_operation_time_char(self):
		for reg in self:
			reg.operation_time_char = str(reg.operation_time)
			
	@api.depends('amount', 'movement_type')
	def _compute_operation_amount(self):
		increase_with_tickets = False # configuracion de calculo segun la compañia
		if self.company_id.money_movement_type == 's':
			increase_with_tickets = True
		condition_base = increase_with_tickets and 'E' or 'S'
		
		for reg in self:
			condition = condition_base == reg.movement_type
			reg.operation_amount = condition and reg.amount or reg.amount * -1

	#@api.one
	@api.depends('partner_id', 'partner_type', 'journal_mov', 'operation_time', 'currency_id', 'state', 'movement_type', 'amount')
	def _compute_reg_previus(self):
		for reg in self:
			if reg.company_id.calculate_account_balance:
				rpt = reg.resolvePreviousRecord()
				reg.reg_previous = rpt['reg_previous']
				reg.balance = rpt['balance']
				reg.description = rpt['description']
			else:
				reg.reg_previous = False
				reg.balance = 0
				reg.description = ""

	def resolvePreviousRecord(self):
		self.ensure_one()
		rpt = {}
		increase_with_tickets = False # configuracion de calculo segun la compañia
		if self.company_id.account_movement_type == 's':
			increase_with_tickets = True
		# obtenemos el registro anterior
		reg_previous = self.env['solse.account.balances'].search([('partner_id', '=', self.partner_id.id), ('partner_type', '=', self.partner_type),
			('currency_id', '=', self.currency_id.id), ('operation_time', '<', self.operation_time), ('state', 'not in', ['draft', 'cancelled', 'cancel', 'annul'])], 
			order='operation_time desc, order_number desc', limit=1)

		condition_base = increase_with_tickets and 'E' or 'S'
		condition = condition_base == self.movement_type
		previous_temporary_id = self.id
		balance = 0
		if self.state not in ['draft', 'cancelled', 'annul']:
			# calculalamos y actualizamos el saldo en base al registro anterior
			if reg_previous:
				balance = reg_previous.balance + self.amount if condition else reg_previous.balance - self.amount
			else:
				balance = condition and self.amount or self.amount * -1
		else:
			previous_temporary_id = reg_previous.id
			if reg_previous:
				balance = reg_previous.balance + self.amount if condition else reg_previous.balance - self.amount
		
		rpt['description'] = self.description and self.description + "- 1" or "1 "
		rpt['balance'] = balance

		# actualizamos los registros en adelante
		records_onwards = self.env['solse.account.balances'].search([('partner_id', '=', self.partner_id.id), ('partner_type', '=', self.partner_type),
			('currency_id', '=', self.currency_id.id), ('operation_time', '>=', self.operation_time), ('id', '!=', self.id), ('state', 'not in', ['draft', 'cancelled', 'cancel', 'annul'])], 
			order='operation_time')
		order_number = 0
		new_balance = 0
		for record in records_onwards:
			order_number += 1
			condition = condition_base == record.movement_type
			new_balance = balance + record.amount if condition else balance - record.amount
			
			"""record.reg_previous = previous_temporary_id
			record.balance = new_balance
			record.order_number = order_number
			record.description = datetime.now()"""
			self.env['solse.account.balances'].search([('id', '=', record.id)], limit=1).write({
					"reg_previous": previous_temporary_id,
					"balance": new_balance,
					"order_number": order_number,
					"description": str(datetime.now()) +" * "+ str(balance)+" * "+str(record.amount)+ " * "+str(condition) + " * "+str(new_balance)+" ** "+str(balance + record.amount),
					"operation_amount": condition and record.amount or record.amount * -1
				})
			balance = new_balance
			previous_temporary_id = record.id
		
		parm_partner = {}
		if self.partner_type == 'supplier':
			parm_partner['balance_as_supplier'] = balance
		else:
			parm_partner['balance_as_customer'] = balance
		self.env['res.partner'].search([('id', '=', self.partner_id.id)], limit=1).write(parm_partner) 
		rpt['reg_previous'] = reg_previous.id
		return rpt

	def force_update(self):
		for reg in self:
			if reg.company_id.calculate_account_balance:
				reg.resolvePreviousRecord()
			else:
				raise Warning("La compañía no tiene habilitado el calculo automatico")