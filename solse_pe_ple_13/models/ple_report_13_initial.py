# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

class PleReport13Initial(models.Model):
	_name = 'ple.report.13.initial'

	ple_report_13_id = fields.Many2one('ple.report.13', string='Libro de valoración')

	period = fields.Char(string="Periodo")
	product_product_id = fields.Many2one('product.product', string="Producto")
	product_cost = fields.Float(string="Costo unitario")
	quantity_on_hand = fields.Float(string="Cantidad a mano")
	total_value = fields.Float(string='Valor total')

	def ple_13_1_physical_xls(self):
		ple_13_1 = []
		ple_13_1.extend([
			# 1 Periodo
			self.period,
			# 2 Producto
			self.product_product_id.name or '',
			# 3 Fecha de emisión del documento de traslado, comprobante de pago, documento interno o similar
			'',
			# 4 Proveedor
			'',
			# 5 Tipo del documento de traslado, comprobante de pago, documento interno o similar
			'',
			# 6 Número de serie del documento de traslado, comprobante de pago, documento interno o similar
			'',
			# 7 Número del documento de traslado, comprobante de pago, documento interno o similar
			'',
			# 8 Tipo de operación efectuada
		   '',
			# 9 Precio
			str(self.product_product_id.lst_price),
			# 10 Tipo de cambio
			'',
			# 11 Cantidad de unidades físicas del bien ingresado (la primera tupla corresponde al saldo inicial)
			'0',
			# 12 Costo unitario del bien ingresado
			'0',
			# 13 Costo total del bien ingresado
			'0',
			# 14 Cantidad de unidades físicas del bien retirado
			'0',
			# 15 Costo unitario del bien retirado
			'0',
			# 16 Costo total del bien retirado
			'0',
			# 17 Cantidad de unidades físicas del saldo final
			format_positive_value(self.quantity_on_hand, 8, False),
			# 18 Costo unitario del saldo final
			format_positive_value(self.product_cost, 8, True),
			# 19 Costo total del saldo final
			format_positive_value(self.total_value, 2, False),
		])
		return ple_13_1
