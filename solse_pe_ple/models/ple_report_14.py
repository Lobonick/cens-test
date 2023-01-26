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

class PLEReport14(models.Model) :
	_name = 'ple.report.14'
	_description = 'PLE 14 - Estructura del Registro de Ventas'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	
	invoice_ids = fields.Many2many(comodel_name='account.move', string='Ventas', readonly=True)
	
	ple_txt_01 = fields.Text(string='Contenido del TXT 14.1')
	ple_txt_01_binary = fields.Binary(string='TXT 14.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 14.1')
	ple_xls_01_binary = fields.Binary(string='Excel 14.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 14.1')
	ple_txt_02 = fields.Text(string='Contenido del TXT 14.2')
	ple_txt_02_binary = fields.Binary(string='TXT 14.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 14.2')
	ple_xls_02_binary = fields.Binary(string='Excel 14.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 14.2')

	documento_compra_ids = fields.Many2many('l10n_latam.document.type', 'ple_14_report_l10n_latam_id', 'report_14_id', 'doc_14_id', string='Documentos a incluir', required=False, domain="[('sub_type', 'in', ['sale'])]")

	@api.onchange('company_id')
	def _onchange_company(self):
		dominio = [('company_id', '=', self.company_id.id), ('sub_type', '=', 'sale'), ('inc_ple_ventas', '=', True)]
		documentos = self.env['l10n_latam.document.type'].search(dominio)
		self.documento_compra_ids = [(6, 0, documentos.ids)]
	
	def get_default_filename(self, ple_id='140100', tiene_datos=False) :
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
		doc_type_ids = []
		for reg in self.documento_compra_ids:
			doc_type_ids.append(reg.id)

		invoices = self.env.ref('base.pe').id
		invoices = [
			('company_id','=',self.company_id.id),
			('company_id.partner_id.country_id','=',invoices),
			('move_type','in',['out_invoice','out_refund']),
			('state','in',['posted', 'annul', 'cancel']),
			#('estado_sunat','not in',['07', '09']),
			('invoice_date','>=',str(start)),
			('invoice_date','<=',str(end)),
		]
		if self.documento_compra_ids:
			invoices.append(('l10n_latam_document_type_id', 'in', doc_type_ids))


		invoices = self.env[self.invoice_ids._name].search(invoices, order='invoice_date asc, name asc')
		self.invoice_ids = invoices
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write = []
		lines_to_write_2 = []
		invoices = self.invoice_ids.sudo()
		contador = 1
		for move in invoices :
			if move.is_cpe and move.estado_sunat in ['07', '09']:
				continue
			m_1 = []
			try :
				sunat_number = move.l10n_latam_document_number
				sunat_number = sunat_number and ('-' in sunat_number) and sunat_number.split('-') or ['','']
				sunat_code = move.pe_invoice_code
				sunat_partner_code = move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
				sunat_partner_vat = move.partner_id.vat
				#sunat_partner_name = move.partner_id.legal_name or move.partner_id.name
				sunat_partner_name = move.partner_id.name
				move_id = move.id
				invoice_date = move.invoice_date
				date_due = move.invoice_date_due
				#1-4
				#m_1.extend([periodo.strftime('%Y%m00'), str(number), ('A'+str(number).rjust(9,'0')), invoice.invoice_date.strftime('%d/%m/%Y')])
				m_1.extend([
					invoice_date.strftime('%Y%m00'),
					str(move.l10n_latam_document_number),
					('M'+str(1).rjust(9,'0')),
					invoice_date.strftime('%d/%m/%Y'),
				])
				contador = contador + 1
				#5: 1. Obligatorio, excepto cuando el campo 35 = '2'
				if date_due :
					m_1.append(date_due.strftime('%d/%m/%Y'))
				else :
					m_1.append('')

				#6-9
				m_1.extend([
					sunat_code,
					sunat_number[0],
					sunat_number[1],
					'',
				])
				#10-13
				if sunat_partner_code and sunat_partner_vat and sunat_partner_name :
					m_1.extend([
						sunat_partner_code,
						sunat_partner_vat,
						sunat_partner_name,
						'',
					])
				else :
					m_1.extend(['', '', '', ''])
				#14-18
				total_sin_impuestos = abs(move.amount_untaxed_signed)
				total_impuestos = abs(move.amount_tax_signed)
				m_1.extend([format(total_sin_impuestos, '.2f'), '', format(total_impuestos, '.2f'), '', ''])
				#19-24
				m_1.extend(['', '', '', '', '0.00', '']) #ICBP
				#25-27
				monto_total = abs(move.amount_total_signed)
				#m_1.extend([format(move.amount_total, '.2f'), '', ''])
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
				
				m_1.extend([format(monto_total, '.2f'), move.currency_id.name, tipo_cambio])
				#28-31
				# notas credito
				if sunat_code in ['07'] :
					origin = move.reversed_entry_id
					origin_number = origin.l10n_latam_document_number
					origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
					m_1.extend([origin.invoice_date.strftime('%d/%m/%Y'), origin.pe_invoice_code])
					m_1.extend(origin_number)
				# notas debito
				elif sunat_code in ['08'] :
					origin = move.debit_origin_id
					origin_number = origin.l10n_latam_document_number
					origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
					m_1.extend([origin.invoice_date.strftime('%d/%m/%Y'), origin.pe_invoice_code])
					m_1.extend(origin_number)
				else :
					m_1.extend(['', '', '', ''])
				#32-36
				estado_comprobante = '1'
				if move.state in ["annul", "cancel"]:
					estado_comprobante = '2'
				m_1.extend(['', '', '', estado_comprobante, ''])
			except Exception as e:
				raise UserError(e)
				m_1 = []
			if m_1 :
				lines_to_write.append('|'.join(m_1))
			m_2 = []
			if m_1 :
				#1-4
				#m_1.extend([
				#    invoice_date.strftime('%Y%m00'),
				#    str(move_id),
				#    ('A'+str(move_id).rjust(9,'0')),
				#    invoice_date.strftime('%d/%m/%Y'),
				#])
				m_2.extend(m_1[0:4])
				#5
				#if date_due :
				#    m_1.append(date_due.strftime('%d/%m/%Y'))
				#else :
				#    m_1.append('')
				m_2.append(m_1[4])
				#6-9
				#m_1.extend([
				#    sunat_code,
				#    sunat_number[0],
				#    sunat_number[1],
				#    '',
				#])
				m_2.extend(m_1[5:9])
				#10-12
				#if sunat_partner_code and sunat_partner_vat and sunat_partner_name :
				#    m_1.extend([
				#        sunat_partner_code,
				#        sunat_partner_vat,
				#        sunat_partner_name,
				#    ])
				#else :
				#    m_1.extend(['', '', ''])
				m_2.extend(m_1[9:12])
				#13-14
				#m_1.extend([format(move.amount_untaxed, '.2f'), '', format(move.amount_tax, '.2f'), '', ''])
				m_2.extend([
					m_1[13],
					m_1[15],
				])
				#15-16
				#m_1.extend(['', '', '', '', '0.00', '']) #ICBP
				m_2.extend(m_1[22:24])
				#17-19
				#m_1.extend([format(move.amount_total, '.2f'), '', ''])
				m_2.extend(m_1[24:27])
				#20-23
				#if sunat_code in ['07', '08'] :
				#    origin = (sunat_code == '07') and move.credit_origin_id or move.debit_origin_id
				#    origin_number = origin.name
				#    origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
				#    m_1.extend([origin.invoice_date.strftime('%d/%m/%Y'), origin.pe_invoice_code])
				#    m_1.extend(origin_number)
				#else :
				#    m_1.extend(['', '', '', ''])
				m_2.extend(m_1[27:31])
				#32-36
				#m_1.extend(['', '', '', '1', ''])
				m_2.extend(m_1[32:])
			if m_2 :
				lines_to_write_2.append('|'.join(m_2))
		name_01 = self.get_default_filename(ple_id='140100', tiene_datos=bool(lines_to_write))
		lines_to_write.append('')
		txt_string_01 = '\r\n'.join(lines_to_write)
		dict_to_write = dict()
		if txt_string_01 :
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=[
				'Periodo',
				'Número correlativo del mes o Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Fecha de emisión del Comprobante de Pago',
				'Fecha de Vencimiento o Fecha de Pago',
				'Tipo de Comprobante de Pago o Documento',
				'Número serie del comprobante de pago o documento o número de serie de la maquina registradora',
				'Número del comprobante de pago o documento o número inicial o constancia de depósito',
				'Número final',
				'Tipo de Documento de Identidad del cliente',
				'Número de Documento de Identidad del cliente',
				'Apellidos y nombres, denominación o razón social del cliente',
				'Valor facturado de la exportación',
				'Base imponible de la operación gravada',
				'Descuento de la Base Imponible',
				'Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Descuento del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Importe total de la operación exonerada',
				'Importe total de la operación inafecta',
				'Impuesto Selectivo al Consumo',
				'Base imponible de la operación gravada con el Impuesto a las Ventas del Arroz Pilado',
				'Impuesto a las Ventas del Arroz Pilado',
				'Impuesto al Consumo de las Bolsas de Plástico',
				'Otros conceptos, tributos y cargos que no forman parte de la base imponible',
				'Importe total del comprobante de pago',
				'Código de la Moneda',
				'Tipo de cambio',
				'Fecha de emisión del comprobante de pago o documento original que se modifica o documento referencial al documento que sustenta el crédito fiscal',
				'Tipo del comprobante de pago que se modifica',
				'Número de serie del comprobante de pago que se modifica o Código de la Dependencia Aduanera',
				'Número del comprobante de pago que se modifica o Número de la DUA',
				'Identificación del Contrato o del proyecto',
				'Error tipo 1: inconsistencia en el tipo de cambio',
				'Indicador de Comprobantes de pago cancelados con medios de pago',
				'Estado que identifica la oportunidad de la anotación o indicación',
				'36',
			])
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
		name_02 = self.get_default_filename(ple_id='140200', tiene_datos=bool(lines_to_write_2))
		lines_to_write_2.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_2)
		if txt_string_02 :
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_02, name_02[2:], headers=[
				'Periodo',
				'Número correlativo del mes o Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Fecha de emisión del Comprobante de Pago',
				'Fecha de Vencimiento o Fecha de Pago',
				'Tipo de Comprobante de Pago o Documento',
				'Número serie del comprobante de pago o documento o número de serie de la maquina registradora',
				'Número del comprobante de pago o documento o número inicial o constancia de depósito',
				'Número final',
				'Tipo de Documento de Identidad del cliente',
				'Número de Documento de Identidad del cliente',
				'Apellidos y nombres, denominación o razón social del cliente',
				'Valor facturado de la exportación',
				'Base imponible de la operación gravada',
				'Descuento de la Base Imponible',
				'Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Descuento del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Importe total de la operación exonerada',
				'Importe total de la operación inafecta',
				'Impuesto Selectivo al Consumo',
				'Base imponible de la operación gravada con el Impuesto a las Ventas del Arroz Pilado',
				'Impuesto a las Ventas del Arroz Pilado',
				'Impuesto al Consumo de las Bolsas de Plástico',
				'Otros conceptos, tributos y cargos que no forman parte de la base imponible',
				'Importe total del comprobante de pago',
				'Código de la Moneda',
				'Tipo de cambio',
				'Fecha de emisión del comprobante de pago o documento original que se modifica o documento referencial al documento que sustenta el crédito fiscal',
				'Tipo del comprobante de pago que se modifica',
				'Número de serie del comprobante de pago que se modifica o Código de la Dependencia Aduanera',
				'Número del comprobante de pago que se modifica o Número de la DUA',
				'Identificación del Contrato o del proyecto',
				'Error tipo 1: inconsistencia en el tipo de cambio',
				'Indicador de Comprobantes de pago cancelados con medios de pago',
				'Estado que identifica la oportunidad de la anotación o indicación',
				'36',
			])
			xlsx_file = StringIO(txt_string_02)
			df = pandas.read_csv(xlsx_file, sep='|', header=None)
			xlsx_file = BytesIO()
			df.to_excel(xlsx_file, name_02, index=False, header=False)
			xlsx_file = base64.b64encode(xlsx_file.getvalue())
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': base64.b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': xlsx_file,
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
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res
