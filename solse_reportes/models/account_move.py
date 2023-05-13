# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import Warning
import pytz

tz = pytz.timezone('America/Lima')

class AccountMove(models.Model):
	_inherit = 'account.move'

	def _default_invoice_hour(self):
		reg_datetime = datetime.now(tz)
		return reg_datetime.strftime("%H:%M:%S")
		
	invoice_hour = fields.Char(string="Hora", required=True, default=_default_invoice_hour)
	
	invoice_time = fields.Datetime('Fecha/hora factura', readonly=False, compute="_compute_invoice_time", store=True)
	invoice_time_move = fields.Datetime(compute='_compute_datetime_operation_move', store=True)

	@api.depends('invoice_date', 'invoice_hour')
	def _compute_invoice_time(self):
		for reg in self:
			if reg.invoice_date and reg.invoice_hour:
				reg_datetime = str(reg.invoice_date)+" "+reg.invoice_hour
				datetime_obj_naive = datetime.strptime(reg_datetime, "%Y-%m-%d %H:%M:%S")
				
				datetime_obj_lima = pytz.timezone('America/Lima').localize(datetime_obj_naive)
				reg.invoice_time = datetime_obj_lima.strftime("%Y-%m-%d %H:%M:%S")

	#@api.one
	@api.depends('move_type', 'invoice_time', 'journal_id', 'currency_id', 'amount_total', 'state', 'partner_id')
	def _compute_datetime_operation_move(self):
		#self.ensure_one()
		for reg_self in self:
			movement_type = 'S'
			partner_type = 'customer'
			if reg_self.move_type in ['out_refund', 'in_refund']:
				movement_type = 'E'
			if reg_self.move_type in ['in_invoice', 'in_refund']:
				partner_type = 'supplier'
			account_balance = {
				"invoice_origin": reg_self.id,
				"journal_mov": reg_self.journal_id and reg_self.journal_id.id,
				"movement_type": movement_type,
				"amount": reg_self.amount_total,
				"state": reg_self.state,
				"operation_time": reg_self.invoice_time,
				"currency_id": reg_self.currency_id.id,
				"partner_id": reg_self.partner_id.id,
				"partner_type": partner_type
			}
			movements_balance = self.env['solse.account.balances'].search([('invoice_origin','=', reg_self.id)])
			total_records = len(movements_balance)
			if total_records == 0:
				self.env['solse.account.balances'].create(account_balance)
			elif total_records == 1:
				movements_balance.write(account_balance)
			elif total_records > 1:
				position = 1
				for reg in movements_balance:
					if position == 1:
						reg.amount = reg_self.amount_total
						reg.state = reg_self.state
						reg.journal_mov = reg_self.journal_id and reg_self.journal_id.id,
						reg.movement_type = movement_type
						reg.operation_time = reg_self.invoice_time
						reg.currency_id = reg_self.currency_id.id
						reg.partner_id = reg_self.partner_id.id
						reg.partner_type = partner_type
					else:
						reg.state = 'cancelled'
					position += 1
			else:
				raise Warning('No se pudo modificar los registros')
			
			reg_self.invoice_time_move = datetime.now()