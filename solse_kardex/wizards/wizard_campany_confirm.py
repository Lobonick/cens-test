# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning
import pytz

tz = pytz.timezone('America/Lima')

class CompanyConfirmStok(models.TransientModel):
	_name = "solse.company.confirm.stock"
	_description = "Wizard stock"

	operation_time = fields.Datetime('Tiempo de operación', required=True, default=lambda a: fields.Datetime.now(tz))

	def recalculate_stock(self):
		products = self.env['product.product'].search([('product_tmpl_id.type', 'in', ['product']), ('active', '=', True)])
		for record in products:
			self.calculate_stock_product(record)
		
		return {'type': 'ir.actions.act_window_close'}

	def calculate_stock_product(self, product):
		record = self.env['stock.move.line'].search([('product_id', '=', product.id), ('date', '<', self.operation_time), ('state', 'not in', ['draft', 'cancel'])], 
			order='date desc, order_number desc', limit=1)
		if len(record) == 1:
			record.force_update()
		else:
			record = self.env['stock.move.line'].search([('product_id', '=', product.id), ('date', '>=', self.operation_time), ('state', 'not in', ['draft', 'cancel'])], 
			order='date, order_number', limit=1)
			if len(record) == 1:
				record.force_update()