# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from base64 import b64decode, b64encode, encodebytes
import datetime
from odoo.addons.solse_pe_ple.models import ple_report

import logging
_logging = logging.getLogger(__name__)

class PLEReport13(models.Model) :
	_name = 'ple.report.13'
	_description = 'PLE 13 - Estructura del Registro de Inventario Permanente Valorizado'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	
	line_ids = fields.Many2many(comodel_name='account.move.line', string='Transferencias', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 13.1')
	ple_txt_01_binary = fields.Binary(string='TXT 13.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 13.1')
	ple_xls_01_binary = fields.Binary(string='Excel 13.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 13.1')

	ple_xls_01_physical_binary = fields.Binary(string='Ple Xls 01 Físico', readonly=True)
	ple_xls_01_physical_filename = fields.Char(string='Ple Xls 01 Físico Filename')

	product_ids = fields.Many2many('product.product', string='Productos a reportar')
	
	def get_default_filename(self, ple_id='130100', tiene_datos=False) :
		name = super().get_default_filename()
		name_dict = {
			'month': str(self.month).rjust(2,'0'),
			'ple_id': ple_id,
		}
		if not tiene_datos :
			name_dict.update({
				'contenido': '0',
			})
		ple_report.fill_name_data(name_dict)
		name = name % name_dict
		return name
	
	def _get_ple_13_01_domain(self):
		start = datetime.date(self.year, int(self.month), 1)
		end = ple_report.get_last_day(start)
		domain = [
			('company_id', '=', self.company_id.id),
			('date', '>=', str(start)),
			('date', '<=', str(end)),
			('parent_state', '=', 'posted'),
			('display_type', 'not in', ['line_section', 'line_note']),
		]
		if self.product_ids:
			domain += [('product_id', 'in', self.product_ids.ids)]

		inventory_domain = domain + [('account_id.is_inventory_account', '=', True)]
		return inventory_domain
	
	def update_report(self) :
		res = super().update_report()
		domain = self._get_ple_13_01_domain()
		line_ids = self.env['account.move.line'].search(
			domain, order='date asc')
		self.line_ids = line_ids
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write_1 = []
		for line in self.line_ids.sudo():
			m_1 = line.ple_13_1_fields()
			try :
				lines_to_write_1.append('|'.join(m_1))
			except :
				raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_1))
	
		name_01 = self.get_default_filename(ple_id='130100', tiene_datos=bool(lines_to_write_1))
		lines_to_write_1.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_1)
		dict_to_write = dict()
		if txt_string_01 :
			headers= ['Periodo', 
				'Número correlativo del mes o Código Único de la Operación (CUO)', 
				'Número correlativo del asiento contable identificado en el campo 2.', 
				'Código de establecimiento anexo', 
				'Código del catálogo utilizado.', 
				'Tipo de existencia', 
				'Código propio de la existencia correspondiente al catálogo señalado en el campo 5.', 
				'Código del catálogo utilizado.', 
				'Código de la existencia correspondiente al catálogo señalado en el campo 8.', 
				'Fecha de emisión del documento de traslado, comprobante de pago, documento interno o similar',
				'Tipo del documento de traslado, comprobante de pago, documento interno o similar',
				'Número de serie del documento de traslado, comprobante de pago, documento interno o similar',
				'Número del documento de traslado, comprobante de pago, documento interno o similar',
				'Tipo de operación efectuada',
				'Descripción de la existencia',
				'Código de la unidad de medida',
				'Código del Método de valuación de existencias aplicado',
				'Cantidad de unidades físicas del bien ingresado (la primera tupla corresponde al saldo inicial)',
				'Costo unitario del bien ingresado',
				'Costo total del bien ingresado',
				'Cantidad de unidades físicas del bien retirado',
				'Costo unitario del bien retirado',
				'Costo total del bien retirado',
				'Cantidad de unidades físicas del saldo final',
				'Costo unitario del saldo final',
				'Costo total del saldo final',
				'Indica el estado de la operación',
				'28']
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_01': txt_string_01,
				'ple_txt_01_binary': b64encode(txt_string_01.encode()),
				'ple_txt_01_filename': name_01 + '.txt',
				'ple_xls_01_binary': xlsx_file_base_64,
				'ple_xls_01_filename': name_01 + '.xls',
			})
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res

	def generate_physical_xls(self):
		lines_to_write_1 = []
		for move in self.line_ids.sudo():
			m_1 = move.ple_13_1_physical_xls()
			try:
				lines_to_write_1.append('|'.join(m_1))
			except:
				raise UserError(
					'Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_1))
		name_01 = self.get_default_filename(ple_id='130100', tiene_datos=bool(lines_to_write_1))
		txt_string_01 = '\r\n'.join(lines_to_write_1)
		dict_to_write = dict()
		if txt_string_01:
			xlsx_file_base_64 = self.generate_xlsx_physical_bytes(lines_to_write_1, '13_01')
			dict_to_write.update({
				'ple_xls_01_physical_binary': xlsx_file_base_64,
				'ple_xls_01_physical_filename': name_01 + '.xlsx',
			})
		res = self.write(dict_to_write)
		return res
	
	def get_physical_content(self, sheet, ple_format, row_values_array, style_dict):
		formats = {
		"13_01": self.get_13_01_sheet_format
		}
		try:
			sheet = formats[ple_format](sheet, row_values_array, style_dict)
		except:
			raise UserError(f'Formato {ple_format} incorrecto o no implementado aún, pruebe de nuevo mas tarde ')

		else:
			return sheet
		
	def get_13_01_sheet_format(self, sheet, row_values_array, style_dict):
		periodo = "%s%s%s" % (str(self.year), self.month, "00")
		sheet.merge_range('A1:F1', f'FORMATO 13.1: REGISTRO DE INVENTARIO PERMANENTE VALORIZADO - DETALLE DEL INVENTARIO VALORIZADO', style_dict['bold'])
		sheet.write('A4', f"PERÍODO: ", style_dict['bold'])
		sheet.write('B4', periodo, style_dict['bold'])
		sheet.write('A5', f"RUC: ", style_dict['bold'])
		sheet.write('B5', self.company_id.vat, style_dict['bold'])
		sheet.write('A6', f"RAZÓN SOCIAL: ", style_dict['bold'])
		sheet.write('B6', self.company_id.name, style_dict['bold'])
		sheet.write('A7', f"ESTABLECIMIENTO: ", style_dict['bold'])
		"""sheet.write('A8', f"CÓDIGO DE LA EXISTENCIA: ", style_dict['bold'])
		sheet.write('A9', f"TIPO (TABLA 5): ", style_dict['bold'])
		sheet.write('A10', f"DESCRIPCIÓN: ", style_dict['bold'])
		sheet.write('A11', f"CÓDIGO DE LA UNIDAD DE MEDIDA", style_dict['bold'])
		sheet.write('A12', f"METODO DE VALUACIÓN: PROMEDIO PONDERADO", style_dict['bold'])"""
		row = 10
		sheet = self._write_13_01_physical_table_headers(sheet, style_dict, row)
		quantity_entries = 0
		total_entries = 0
		quantity = 0
		total = 0
		for row_value in row_values_array:
			column = 0
			row_value_list = row_value.split('|')
			for field in row_value_list:
				field = self.convert_field_to_string(field)
				sheet.write(row, column, field,  style_dict['basic_border_cell'])
				column += 1
			quantity_entries += float(row_value_list[10])
			total_entries += float(row_value_list[12])
			quantity += float(row_value_list[13])
			total += float(row_value_list[15])
			row += 1

		current_row = row + 1
			
		#sheet.merge_range(f'G{current_row}:H{current_row}', 'COMPRAS DEL MES', style_dict['bold'])
		current_row +=1
		sheet.merge_range(f'H{current_row}:I{current_row}', 'SALDOS FINALES DEL MES', style_dict['bold'])
		sheet.write(f'K{current_row}', format(quantity_entries, '.{}f'.format(2)), style_dict['bold'])
		sheet.write(f'M{current_row}', format(total_entries, '.{}f'.format(2)), style_dict['bold'])
		sheet.write(f'N{current_row}', format(quantity, '.{}f'.format(2)), style_dict['bold'])
		sheet.write(f'P{current_row}', format(total, '.{}f'.format(2)), style_dict['bold'])
		current_row +=1
		#sheet.merge_range(f'F{current_row}:H{current_row}', 'CONSUMO DEL MES', style_dict['bold'])
		   
		return sheet
		
	def _write_13_01_physical_table_headers(self, sheet, style_dict, row):
		# II
		row_pre = row - 1
		sheet.set_column('A:A', 15)
		sheet.set_column('B:B', 35)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 15)
		sheet.set_column('F:F', 15)
		sheet.set_column('G:G', 15)
		sheet.set_column('H:H', 15)
		sheet.set_column('I:I', 15)
		sheet.set_column('J:J', 15)
		sheet.set_column('K:K', 15)
		sheet.set_column('L:L', 15)
		sheet.set_column('M:M', 15)
		sheet.set_column('N:N', 15)
		sheet.set_column('O:O', 15)
		sheet.set_column('P:P', 15)
		sheet.set_column('Q:Q', 15)
		sheet.set_column('R:R', 15)
		sheet.set_column('S:S', 15)
		
		sheet.merge_range(f'A{row_pre}:G{row_pre}', 'DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO, DOCUMENTO INTERNO O SIMILAR', style_dict['bold_center_border_cell'])
		sheet.merge_range(f'H{row_pre}:H{row}', 'TIPO DE OPERACIÓN (TABLA 12)', style_dict['bold_center_border_cell'])
		sheet.merge_range(f'I{row_pre}:J{row_pre}', 'PRECIO UNITARIO', style_dict['bold_center_border_cell'])
		sheet.merge_range(f'K{row_pre}:M{row_pre}', 'ENTRADAS', style_dict['bold_center_border_cell'])
		sheet.merge_range(f'N{row_pre}:P{row_pre}', 'SALIDAS', style_dict['bold_center_border_cell'])
		sheet.merge_range(f'Q{row_pre}:S{row_pre}', 'SALDO FINAL', style_dict['bold_center_border_cell'])
		sheet.set_row((row_pre - 1), 30)
		sheet.set_row(row_pre, 35)

		sheet.write(f'A{row}', 'PERIODO', style_dict['bold_center_border_cell'])
		sheet.write(f'B{row}', 'PRODUCTO', style_dict['bold_center_border_cell'])
		sheet.write(f'C{row}', 'FECHA', style_dict['bold_center_border_cell'])
		sheet.write(f'D{row}', 'PROVEEDOR', style_dict['bold_center_border_cell'])
		sheet.write(f'E{row}', 'TIPO (TABLA 10)', style_dict['bold_center_border_cell'])
		sheet.write(f'F{row}', 'SERIE', style_dict['bold_center_border_cell'])
		sheet.write(f'G{row}', 'NÚMERO', style_dict['bold_center_border_cell'])
		sheet.write(f'I{row}', 'PRECIO $', style_dict['bold_center_border_cell'])
		sheet.write(f'J{row}', 'TIPO DE CAMBIO', style_dict['bold_center_border_cell'])
		sheet.write(f'K{row}', 'CANTIDAD', style_dict['bold_center_border_cell'])
		sheet.write(f'L{row}', 'COSTO UNITARIO', style_dict['bold_center_border_cell'])
		sheet.write(f'M{row}', 'COSTO TOTAL', style_dict['bold_center_border_cell'])
		sheet.write(f'N{row}', 'CANTIDAD', style_dict['bold_center_border_cell'])
		sheet.write(f'O{row}', 'COSTO UNITARIO', style_dict['bold_center_border_cell'])
		sheet.write(f'P{row}', 'COSTO TOTAL', style_dict['bold_center_border_cell'])
		sheet.write(f'Q{row}', 'CANTIDAD', style_dict['bold_center_border_cell'])
		sheet.write(f'R{row}', 'COSTO UNITARIO', style_dict['bold_center_border_cell'])
		sheet.write(f'S{row}', 'COSTO TOTAL', style_dict['bold_center_border_cell'])
		return sheet
