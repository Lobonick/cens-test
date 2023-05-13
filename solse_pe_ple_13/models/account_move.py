# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

def format_positive_value(value, decimals, positive):
	if positive:
		value = abs(value)
	formated_value = format(value, '.{}f'.format(decimals))
	return formated_value

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def get_l10n_table_12_operation_type_code(self):
		operation_type_code = self.move_id.stock_move_id.picking_id.pe_type_operation
		if not operation_type_code:
			operation_type_code = '99'
		return operation_type_code     
			
	def ple_13_1_fields(self):
		ple_13_1 = []
		in_product_quantity = self.quantity if self.debit > 0 else 0
		out_product_quantity = -1 * self.quantity if self.credit > 0 else 0
		in_product_cost = 0
		out_product_cost = 0
		balance_cost = 0
		balance_quantity = in_product_quantity if self.debit > 0 else out_product_quantity
		if self.quantity != 0 and balance_quantity != 0:
			in_product_cost = self.debit / self.quantity if self.debit > 0 else 0
			out_product_cost = self.credit / self.quantity if self.credit > 0 else 0
			balance_cost = self.balance / balance_quantity
			
		# 1-4
		ple_13_1.extend([
			# 1 Periodo
			self.date.strftime('%Y%m00'),
			# 2 CUO
			f"{self.move_id.name}-{self.id}",
			# 3 Correlativo
			('M'+str(self.id).rjust(9, '0')),
			# 4 Código de establecimiento anexo
			'9999',
			# 5 Código del catálogo utilizado.
			'1', # TODO l10n_pe_edi_table_13_code
			# 6 Tipo de existencia
			'01', # TODO l10n_pe_edi_table_05_code
			# 7 Código propio de la existencia correspondiente al catálogo señalado en el campo 5.
			'1',
			# 8 Código del catálogo utilizado.
			self.product_id.categ_id.pe_code or '1',
			# 9 Código de la existencia correspondiente al catálogo señalado en el campo 8.
			self.product_id.pe_code_osce or '10000000',
			# 10 Fecha de emisión del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.date.strftime('%d/%m/%Y'),
			# 11 Tipo del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_document_type_code(),
			# 12 Número de serie del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_account_move_serie(),
			# 13 Número del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_account_move_number(),
			# 14 Tipo de operación efectuada
			self.get_l10n_table_12_operation_type_code(),
			# 15 Descripción de la existencia
			self.product_id.display_name[:80] if self.product_id.display_name else 'Mercancía',
			# 16 Código de la unidad de medida
			self.product_id.uom_id.sunat_code or 'NIU',
			# 17 Código del Método de valuación de existencias aplicado
			'1',
			# 18 Cantidad de unidades físicas del bien ingresado (la primera tupla corresponde al saldo inicial)
			format_positive_value(in_product_quantity, 8, True),
			# 19 Costo unitario del bien ingresado
			format_positive_value(in_product_cost, 8, True),
			# 20 Costo total del bien ingresado
			format_positive_value(self.debit, 2, True),
			# 21 Cantidad de unidades físicas del bien retirado
			format_positive_value(out_product_quantity, 8, False),
			# 22 Costo unitario del bien retirado
			format_positive_value(out_product_cost, 8, True),
			# 23 Costo total del bien retirado
			format_positive_value(self.credit, 2, False),
			# 24 Cantidad de unidades físicas del saldo final
			format_positive_value(balance_quantity, 8, False),
			# 25 Costo unitario del saldo final
			format_positive_value(balance_cost, 8, True),
			# 26 Costo total del saldo final
			format_positive_value(self.balance, 2, False),
			# 27 Indica el estado de la operación
			'1',
			# 28 Campos de libre utilización.
			''
		])
		return ple_13_1

	def ple_13_1_physical_xls(self):
		ple_13_1 = []
		in_product_quantity = self.quantity if self.debit > 0 else 0
		out_product_quantity = -1 * self.quantity if self.credit > 0 else 0
		in_product_cost = 0
		out_product_cost = 0
		balance_cost = 0
		balance_quantity = in_product_quantity if self.debit > 0 else out_product_quantity
		if self.quantity != 0 and balance_quantity != 0:
			in_product_cost = self.debit / self.quantity if self.debit > 0 else 0
			out_product_cost = self.credit / self.quantity if self.credit > 0 else 0
			balance_cost = self.balance / balance_quantity

		move = self.move_id
		invoice_date = move.date
		fecha_busqueda = str(invoice_date)
		currency_rate_id = [
			('name', '=', fecha_busqueda),
			('company_id','=', move.company_id.id),
			('currency_id','=', move.currency_id.id),
		]
		currency_rate_id = self.env['res.currency.rate'].sudo().search(currency_rate_id)
		tipo_cambio = 1.000
		if currency_rate_id:
			tipo_cambio = currency_rate_id.rate_pe

		tipo_cambio = format(tipo_cambio, '.3f')
			
		# 1-4
		ple_13_1.extend([
			# 1 Periodo
			self.date.strftime('%Y%m00'),
			# 2 Producto
			self.product_id.name,
			# 3 Fecha de emisión del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.date.strftime('%d/%m/%Y'),
			# 4 Proveedor
			self.move_id.stock_move_id.picking_id.get_partner_name(),
			# 5 Tipo del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_document_type_code(),
			# 6 Número de serie del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_account_move_serie(),
			# 7 Número del documento de traslado, comprobante de pago, documento interno o similar
			self.move_id.stock_move_id.picking_id.get_account_move_number(),
			# 8 Tipo de operación efectuada
			self.get_l10n_table_12_operation_type_code(),
			# 9 Precio
			str(self.product_id.lst_price),
			# 10 Tipo de cambio
			tipo_cambio,
			# 11 Cantidad de unidades físicas del bien ingresado (la primera tupla corresponde al saldo inicial)
			format_positive_value(in_product_quantity, 8, True),
			# 12 Costo unitario del bien ingresado
			format_positive_value(in_product_cost, 8, True),
			# 13 Costo total del bien ingresado
			format_positive_value(self.debit, 2, True),
			# 14 Cantidad de unidades físicas del bien retirado
			format_positive_value(out_product_quantity, 8, False),
			# 15 Costo unitario del bien retirado
			format_positive_value(out_product_cost, 8, True),
			# 16 Costo total del bien retirado
			format_positive_value(self.credit, 2, False),
			# 17 Cantidad de unidades físicas del saldo final
			format_positive_value(balance_quantity, 8, False),
			# 18 Costo unitario del saldo final
			format_positive_value(balance_cost, 8, True),
			# 19 Costo total del saldo final
			format_positive_value(self.balance, 2, False),
		])
		return ple_13_1
