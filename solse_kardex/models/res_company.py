# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api

class ResCompany(models.Model):
	_inherit = 'res.company'

	calculate_stock_balance = fields.Boolean('Calcular saldo de stock', default=False)
	stock_movement_type = fields.Selection(string='Movimiento stock', selection=[('s', 'Sumar las entradas / restar las salidas'), ('r', 'Restar las entradas / sumar las salidas')], default='s', required=True)