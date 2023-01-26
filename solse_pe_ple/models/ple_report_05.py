# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from .ple_report import get_last_day
from .ple_report import fill_name_data
from .ple_report import number_to_ascii_chr

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

class PLEReport05(models.Model) :
	_name = 'ple.report.05'
	_description = 'PLE 05 - Estructura del Libro Diario'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	eximido_presentar_caja_bancos = fields.Boolean("Eximido de presenta Libro Caja y Bancos")
	
	line_ids = fields.Many2many(comodel_name='account.move.line', string='Movimientos', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 5.1')
	ple_txt_01_binary = fields.Binary(string='TXT 5.1', readonly=True)
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 5.1')
	ple_xls_01_binary = fields.Binary(string='Excel 5.1', readonly=True)
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 5.1')
	ple_txt_02 = fields.Text(string='Contenido del TXT 5.2')
	ple_txt_02_binary = fields.Binary(string='TXT 5.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 5.2')
	ple_xls_02_binary = fields.Binary(string='Excel 5.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 5.2')
	ple_txt_03 = fields.Text(string='Contenido del TXT 5.3')
	ple_txt_03_binary = fields.Binary(string='TXT 5.3', readonly=True)
	ple_txt_03_filename = fields.Char(string='Nombre del TXT 5.3')
	ple_xls_03_binary = fields.Binary(string='Excel 5.3', readonly=True)
	ple_xls_03_filename = fields.Char(string='Nombre del Excel 5.3')
	ple_txt_04 = fields.Text(string='Contenido del TXT 5.4')
	ple_txt_04_binary = fields.Binary(string='TXT 5.4', readonly=True)
	ple_txt_04_filename = fields.Char(string='Nombre del TXT 5.4')
	ple_xls_04_binary = fields.Binary(string='Excel 5.4', readonly=True)
	ple_xls_04_filename = fields.Char(string='Nombre del Excel 5.4')
	
	def get_default_filename(self, ple_id='050100', tiene_datos=False) :
		name = super().get_default_filename()
		name_dict = {
			'month': str(self.month).rjust(2,'0'),
			'ple_id': ple_id,
		}
		if not tiene_datos :
			name_dict.update({
				'contenido': '0',
			})
		fill_name_data(name_dict)
		name = name % name_dict
		return name
	
	def update_report(self) :
		res = super().update_report()
		start = datetime.date(self.year, int(self.month), 1)
		end = get_last_day(start)
		#current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		#start = start - current_offset
		#end = end - current_offset
		lines = self.env.ref('base.pe').id
		lines = [
			('company_id','=',self.company_id.id),
			('company_id.partner_id.country_id','=',lines),
			('move_id.state','=','posted'),
			('display_type', 'in', ['product', 'cogs', 'tax', 'rounding', '']),
			('date','>=',str(start)),
			('date','<=',str(end)),
		]
		lines = self.env[self.line_ids._name].search(lines, order='date asc')
		self.line_ids = lines
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write_01 = []
		lines_to_write_02 = []
		lines_to_write_03 = []
		lines_to_write_04 = []
		lines = self.line_ids.sudo()
		move_dates = lines.mapped('date')
		#move_dates = lines.mapped('move_id')
		#move_dates = move_dates.mapped('date')
		fecha_inicio = datetime.date(self.year, int(self.month), 1)

		date_accounts = self.env['account.account'].search([])
		fecha = datetime.date(self.year, int(self.month), 1)
		for date_account in date_accounts :
			m_03 = []
			m_04 = []
			try :
				#1-3
				nro_cuenta_contable = date_account.code
				m_03.extend([
					fecha.strftime('%Y%m00'),
					nro_cuenta_contable,
					date_account.name,
				])
				#4-9
				m_03.extend(['01', 'PLAN CONTABLE GENERAL EMPRESARIAL', '', '', '1', ''])
			except :
				_logging.info('error en lineaaaaaaaaaaaaaa 1219')
				m_03 = []
			if m_03 :
				lines_to_write_03.append('|'.join(m_03))
			if m_03 :
				#1-3
				m_04.extend(m_03[0:3])
				#4-9
				m_04.extend(m_03[3:])
			if m_04 :
				lines_to_write_04.append('|'.join(m_04))
		contador = 0
		numero_factura = ""
		lines = sorted(lines, key=lambda student: student.move_id.id)
		for move in lines :
			m_01 = []
			m_02 = []
			try :
				factura = move.move_id
				if numero_factura != factura.l10n_latam_document_number:
					contador = 0
					numero_factura = factura.l10n_latam_document_number
				
				contador = contador + 1
				
				sunat_number = factura.l10n_latam_document_number
				sunat_number = sunat_number and ('-' in sunat_number) and sunat_number.split('-') or ['','']
				sunat_partner_code = factura.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
				sunat_partner_vat = factura.partner_id.vat
				move_id = factura.l10n_latam_document_number
				move_name = move.name
				if move_name :
					move_name = move_name.replace('\r', ' ').replace('\n', ' ').split()
					move_name = ' '.join(move_name)
				if not move_name :
					move_name = 'Movimiento'
				move_name = move_name[:200].strip()
				date = move.date
				cuenta_contable = move.account_id
				nro_cuenta_contable = cuenta_contable.code
				#nro_cuenta_contable = nro_cuenta_contable.rstrip('0')
				#1-4
				m_01.extend([
					date.strftime('%Y%m00'),
					str(move_id),
					('M'+str(contador).rjust(9,'0')),
					nro_cuenta_contable,
				])
				#5-6
				m_01.extend(['', ''])
				#7
				#m_01.append(move.always_set_currency_id.name)
				m_01.append(move.currency_id.name)
				#8-9
				if sunat_partner_code and sunat_partner_vat :
					m_01.extend([
						sunat_partner_code,
						sunat_partner_vat,
					])
				else :
					m_01.extend(['', ''])
				#10
				if factura.move_type in ['entry', 'out_receipt', 'in_receipt']:
					m_01.append('00')
				else:
					m_01.append((factura.pe_invoice_code or ''))

				#11-12
				if factura.move_type in ['out_invoice', 'out_refund']:
					m_01.extend(sunat_number)
				elif factura.move_type in ['in_invoice', 'in_refund']:
					purchase_number = factura.ref
					if not purchase_number:
						raise UserError("La factura %s no tiene registrado la serie y nummeracion de la factura del proveedor" % factura.name)
					purchase_number = purchase_number and ('-' in purchase_number) and purchase_number.split('-') or ['','']
					m_01.extend(purchase_number)
				else:
					m_01.extend(['', str(move_id)])
				#13-14
				m_01.extend([date.strftime('%d/%m/%Y'), ''])
				#15
				if factura.move_type in ['entry', 'out_receipt', 'in_receipt']:
					m_01.append(date.strftime('%d/%m/%Y'))
				else:
					m_01.append(factura.invoice_date.strftime('%d/%m/%Y'))
				#16-17
				glosa = move_name
				if factura.glosa:
					glosa = factura.glosa[:200].strip()
				m_01.extend([
					glosa,
					'',
				])
				#18-20
				m_01.extend([format(move.debit, '.2f'), format(move.credit, '.2f'), ''])
				#21
				estado = '1'
				if factura.move_type in ['entry', 'out_receipt', 'in_receipt']:
					estado = '1'
				elif factura.invoice_date < fecha_inicio:
					estado = '8'
				m_01.extend([estado])

				if self.eximido_presentar_caja_bancos == True:
					campos_faltantes = ['', '', '', '', '','','']
				else:
					campos_faltantes = ['']

				if self.eximido_presentar_caja_bancos == False:
					m_01.extend(campos_faltantes)
				elif factura.move_type not in ['entry']:
					m_01.extend(campos_faltantes)
				elif factura.journal_id.type not in ['bank', 'cash']:
					m_01.extend(campos_faltantes)
				else:
					pago = self.env['account.payment'].search([('name', '=', factura.name)], limit=1)
					if not pago:
						raise UserError('No se pudo encontrar el pago relacionado para %s ' % factura.name)

					#22 Entidad Financiera
					if pago.journal_id.type in ['cash']:
						m_01.append('99')
					elif pago.journal_id.type in ['bank']:
						cuenta_bancaria = pago.partner_bank_id
						if not cuenta_bancaria:
							raise UserError('No se ha establecido una cuenta bancaria para %s' % factura.name)
						banco = cuenta_bancaria.bank_id
						if not banco:
							raise UserError('No se ha configurado un banco para %s' % cuenta_bancaria.name)
						entidad_financiera = banco.l10n_pe_bank_code
						if not entidad_financiera:
							raise UserError('No se ha establecido una entidad financiera para %s ' % banco.name)
						m_01.append(entidad_financiera)
					#23 Cuenta Bancaria emisor
					if pago.journal_id.type in ['cash']:
						m_01.append('')
					elif pago.journal_id.type in ['bank']:
						if not pago.journal_id.bank_account_id:
							raise UserError("No se ha establecido una cuenta para %s " % pago.journal_id.name)
						cuenta_bancaria_emisor = pago.journal_id.bank_account_id.acc_number
						m_01.append(cuenta_bancaria_emisor)

					#24 Medio de Pago
					if not pago.l10n_pe_payment_method_code:
						raise UserError('No se ha establecido el medio de pago para %s ' % factura.name)
					m_01.append(pago.l10n_pe_payment_method_code)

					#25 Descripcion de la operacion bancaria
					descripcion = "%s %s" % (str(pago.payment_type), pago.ref)
					m_01.append(descripcion)

					#26 Nombre o Razon social del emisor o beneficiario
					if not pago.partner_id:
						raise UserError("No se ha establecido un emisor o beneficiario para el pago %s " % pago.name)
					m_01.append(pago.partner_id.display_name)

					# 27 Número de transaccion bancaria
					m_01.append(pago.transaction_number or '')
					m_01.append('')


			except Exception as e:
				raise UserError(e)
				m_01 = []
			if m_01 :
				#1-4
				m_02.extend(m_01[0:4])
				#5-6
				m_02.extend(m_01[4:6])
				#7
				m_02.append(m_01[6])
				#8-9
				m_02.extend(m_01[7:9])
				#10
				m_02.append(m_01[9])
				#11-12
				m_02.extend(m_01[10:12])
				#13-14
				m_02.extend(m_01[12:14])
				#15
				m_02.append(m_01[14])
				#16-17
				m_02.extend(m_01[15:17])
				#18-20
				m_02.extend(m_01[17:20])
				#21-22
				m_02.extend(m_01[20:])
			if m_01 :
				_logging.info("como queda n1")
				_logging.info(m_01)
				lines_to_write_01.append('|'.join(m_01))
			if m_02 :
				lines_to_write_02.append('|'.join(m_02))
		
		_logging.info("lines_to_write_01")
		_logging.info(lines_to_write_01)
		name_01 = self.get_default_filename(ple_id='050100', tiene_datos=bool(lines_to_write_01))
		lines_to_write_01.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_01)
		dict_to_write = dict()
		if txt_string_01 :
			headers = [
				'Periodo',
				'Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Código de la cuenta contable desagregado en subcuentas al nivel máximo de dígitos utilizado',
				'Código de la Unidad de Operación, de la Unidad Económica Administrativa, de la Unidad de Negocio, de la Unidad de Producción, de la Línea, de la Concesión, del Local o del Lote',
				'Código del Centro de Costos, Centro de Utilidades o Centro de Inversión',
				'Tipo de Moneda de origen',
				'Tipo de documento de identidad del emisor',
				'Número de documento de identidad del emisor',
				'Tipo de Comprobante de Pago o Documento asociada a la operación',
				'Número de serie del comprobante de pago o documento asociada a la operación',
				'Número del comprobante de pago o documento asociada a la operación',
				'Fecha contable',
				'Fecha de vencimiento',
				'Fecha de la operación o emisión',
				'Glosa o descripción de la naturaleza de la operación registrada',
				'Glosa referencial',
				'Movimientos del Debe',
				'Movimientos del Haber',
				'Código del libro, campo 1, campo 2 y campo 3 del Registro de Ventas e Ingresos o del Registro de Compras',
				'Indica el estado de la operación',
			]
			if self.eximido_presentar_caja_bancos == True:
				headers.append('#22')
				headers.append('#23')
				headers.append('#24')
				headers.append('#25')
				headers.append('#26')
				headers.append('#27')

			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_01': txt_string_01,
				'ple_txt_01_binary': base64.b64encode(txt_string_01.encode()),
				'ple_txt_01_filename': name_01 + '.txt',
				'ple_xls_01_binary': xlsx_file_base_64.encode(),
				'ple_xls_01_filename': name_01 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_01': False,
				'ple_txt_01_binary': False,
				'ple_txt_01_filename': False,
				'ple_xls_01_binary': False,
				'ple_xls_01_filename': False,
			})
		name_03 = self.get_default_filename(ple_id='050300', tiene_datos=bool(lines_to_write_03))
		lines_to_write_03.append('')
		txt_string_03 = '\r\n'.join(lines_to_write_03)
		if txt_string_03 :
			headers = [
				'Periodo',
				'Código de la Cuenta Contable desagregada hasta el nivel máximo de dígitos utilizado',
				'Descripción de la Cuenta Contable desagregada al nivel máximo de dígitos utilizado',
				'Código del Plan de Cuentas utilizado por el deudor tributario',
				'Descripción del Plan de Cuentas utilizado por el deudor tributario',
				'Código de la Cuenta Contable Corporativa desagregada hasta el nivel máximo de dígitos utilizado',
				'Descripción de la Cuenta Contable Corporativa desagregada al nivel máximo de dígitos utilizado',
				'Indica el estado de la operación',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_03, name_03[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_03': txt_string_03,
				'ple_txt_03_binary': base64.b64encode(txt_string_03.encode()),
				'ple_txt_03_filename': name_03 + '.txt',
				'ple_xls_03_binary': xlsx_file_base_64.encode(),
				'ple_xls_03_filename': name_03 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_03': False,
				'ple_txt_03_binary': False,
				'ple_txt_03_filename': False,
				'ple_xls_03_binary': False,
				'ple_xls_03_filename': False,
			})
		name_02 = self.get_default_filename(ple_id='050200', tiene_datos=bool(lines_to_write_02))
		lines_to_write_02.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_02)
		if txt_string_02 :
			headers = [
				'Periodo',
				'Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Código de la cuenta contable desagregado en subcuentas al nivel máximo de dígitos utilizado',
				'Código de la Unidad de Operación, de la Unidad Económica Administrativa, de la Unidad de Negocio, de la Unidad de Producción, de la Línea, de la Concesión, del Local o del Lote',
				'Código del Centro de Costos, Centro de Utilidades o Centro de Inversión',
				'Tipo de Moneda de origen',
				'Tipo de documento de identidad del emisor',
				'Número de documento de identidad del emisor',
				'Tipo de Comprobante de Pago o Documento asociada a la operación',
				'Número de serie del comprobante de pago o documento asociada a la operación',
				'Número del comprobante de pago o documento asociada a la operación',
				'Fecha contable',
				'Fecha de vencimiento',
				'Fecha de la operación o emisión',
				'Glosa o descripción de la naturaleza de la operación registrada',
				'Glosa referencial',
				'Movimientos del Debe',
				'Movimientos del Haber',
				'Código del libro, campo 1, campo 2 y campo 3 del Registro de Ventas e Ingresos o del Registro de Compras',
				'Indica el estado de la operación',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_02, name_02[2:], headers=headers)
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': base64.b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': xlsx_file_base_64.encode(),
				'ple_xls_02_filename': name_02 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_02': False,
				'ple_txt_02_binary': False,
				'ple_txt_02_filename': False,
				'ple_xls_02_binary': False,
				'ple_xls_02_filename': False,
			})
		name_04 = self.get_default_filename(ple_id='050400', tiene_datos=bool(lines_to_write_04))
		lines_to_write_04.append('')
		txt_string_04 = '\r\n'.join(lines_to_write_04)
		if txt_string_04 :
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_04, name_04[2:], headers=[
				'Periodo',
				'Código de la Cuenta Contable desagregada hasta el nivel máximo de dígitos utilizado',
				'Descripción de la Cuenta Contable desagregada al nivel máximo de dígitos utilizado',
				'Código del Plan de Cuentas utilizado por el deudor tributario',
				'Descripción del Plan de Cuentas utilizado por el deudor tributario',
				'Código de la Cuenta Contable Corporativa desagregada hasta el nivel máximo de dígitos utilizado',
				'Descripción de la Cuenta Contable Corporativa desagregada al nivel máximo de dígitos utilizado',
				'Indica el estado de la operación',
			])
			dict_to_write.update({
				'ple_txt_04': txt_string_04,
				'ple_txt_04_binary': base64.b64encode(txt_string_04.encode()),
				'ple_txt_04_filename': name_04 + '.txt',
				'ple_xls_04_binary': xlsx_file_base_64.encode(),
				'ple_xls_04_filename': name_04 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'ple_txt_04': False,
				'ple_txt_04_binary': False,
				'ple_txt_04_filename': False,
				'ple_xls_04_binary': False,
				'ple_xls_04_filename': False,
			})
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res
