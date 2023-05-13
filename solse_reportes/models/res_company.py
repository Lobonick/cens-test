# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
	_inherit = 'res.company'

	calculate_money_balance = fields.Boolean('Calcular saldo dinero', default=False)
	calculate_account_balance = fields.Boolean('Calcular saldo cuenta', default=False)

	money_movement_type = fields.Selection(string='Movimiento dinero', selection=[('s', 'Sumar las entradas / restar las salidas'), ('r', 'Restar las entradas / sumar las salidas')], default='r', required=True)
	account_movement_type = fields.Selection(string='Movimiento saldos', selection=[('s', 'Sumar  el Haber / restar el Debe'), ('r', 'Restar el Haber / sumar el Debe')], default='r', required=True)
	
	
