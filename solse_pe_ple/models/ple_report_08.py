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

class PLEReport08(models.Model) :
	_name = 'ple.report.08'
	_description = 'PLE 08 - Estructura del Registro de Compras'
	_inherit = 'ple.report.templ'
	
	year = fields.Integer(required=True)
	month = fields.Selection(selection_add=[], required=True)
	
	bill_ids = fields.Many2many(comodel_name='account.move', string='Compras', readonly=True)
	
	# Normal
	ple_txt_01 = fields.Text(string='Contenido del TXT 8.1')
	ple_txt_01_binary = fields.Binary(string='TXT 8.1')
	ple_txt_01_filename = fields.Char(string='Nombre del TXT 8.1')
	ple_xls_01_binary = fields.Binary(string='Excel 8.1')
	ple_xls_01_filename = fields.Char(string='Nombre del Excel 8.1')

	# No domiciliado
	ple_txt_02 = fields.Text(string='Contenido del TXT 8.2')
	ple_txt_02_binary = fields.Binary(string='TXT 8.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 8.2')
	ple_xls_02_binary = fields.Binary(string='Excel 8.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 8.2')

	# Simplicado
	ple_txt_03 = fields.Text(string='Contenido del TXT 8.3')
	ple_txt_03_binary = fields.Binary(string='TXT 8.3', readonly=True)
	ple_txt_03_filename = fields.Char(string='Nombre del TXT 8.3')
	ple_xls_03_binary = fields.Binary(string='Excel 8.3', readonly=True)
	ple_xls_03_filename = fields.Char(string='Nombre del Excel 8.3')

	documento_compra_ids = fields.Many2many('l10n_latam.document.type', 'ple_report_l10n_latam_id', 'report_id', 'doc_id', string='Documentos a incluir', required=False, domain="[('sub_type', 'in', ['purchase'])]")
	
	@api.onchange('company_id')
	def _onchange_company(self):
		dominio = [('company_id', '=', self.company_id.id), ('sub_type', '=', 'purchase'), ('inc_ple_compras', '=', True)]
		documentos = self.env['l10n_latam.document.type'].search(dominio)
		self.documento_compra_ids = [(6, 0, documentos.ids)]

	def get_default_filename(self, ple_id='080100', tiene_datos=False) :
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

		bills = self.env.ref('base.pe').id
		bills = [
			('company_id','=',self.company_id.id),
			('company_id.partner_id.country_id','=',bills),
			('move_type','in',['in_invoice','in_refund']),
			('state','=','posted'),
			('date','>=',str(start)),
			('date','<=',str(end)),
		]
		if self.documento_compra_ids:
			bills.append(('l10n_latam_document_type_id', 'in', doc_type_ids))
		bills = self.env[self.bill_ids._name].search(bills, order='date asc, ref asc')
		self.bill_ids = bills
		return res
	
	def generate_report(self) :
		res = super().generate_report()
		lines_to_write_01 = []
		lines_to_write_02 = []
		lines_to_write_03 = []
		bills = self.bill_ids.sudo()
		peru = self.env.ref('base.pe')
		contador = 1
		fecha_inicio = datetime.date(self.year, int(self.month), 1)

		for move in bills :
			m_01 = move.ple_8_1_fields(contador, fecha_inicio)
			contador = contador + 1

			if m_01 :
				lines_to_write_01.append('|'.join(m_01))

			m_02 = []
			if m_01 and (move.partner_id.country_id != peru):
				_logging.info('recorre no domiciliado')

			if m_02 :
				lines_to_write_02.append('|'.join(m_02))

			m_03 = []
			if m_01:
				m_03.extend(m_01[0:4])
				m_03.append(m_01[4])
				m_03.extend([
					m_01[5],
					m_01[6],
					m_01[8],
				])
				m_03.extend(m_01[10:13])
				m_03.extend(m_01[13:15])
				m_03.append(m_01[21]) #ICBP
				m_03.extend(m_01[22:26])
				m_03.extend([
					m_01[26],
					m_01[27],
					m_01[28],
					m_01[30],
				])
				m_03.extend(m_01[31:35]+m_01[36:39]+m_01[40:])
			if m_03 :
				lines_to_write_03.append('|'.join(m_03))
		name_01 = self.get_default_filename(ple_id='080100', tiene_datos=bool(lines_to_write_01))
		lines_to_write_01.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_01)
		dict_to_write = dict()
		if txt_string_01 :
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=[
				'Periodo',
				'Número correlativo del mes o Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Fecha de emisión del comprobante de pago o documento',
				'Fecha de Vencimiento o Fecha de Pago',
				'Tipo de Comprobante de Pago o Documento',
				'Serie del comprobante de pago o documento o código de la dependencia Aduanera',
				'Año de emisión de la DUA o DSI',
				'Número del comprobante de pago o documento o número de orden del formulario físico o virtual o número final',
				'Número final',
				'Tipo de Documento de Identidad del proveedor',
				'Número de RUC del proveedor o número de documento de Identidad',
				'Apellidos y nombres, denominación o razón social del proveedor',
				'Base imponible de las adquisiciones gravadas que dan derecho a crédito fiscal y/o saldo a favor por exportación, destinadas exclusivamente a operaciones gravadas y/o de exportación',
				'Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Base imponible de las adquisiciones gravadas que dan derecho a crédito fiscal y/o saldo a favor por exportación, destinadas a operaciones gravadas y/o de exportación y a operaciones no gravadas',
				'Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Base imponible de las adquisiciones gravadas que no dan derecho a crédito fiscal y/o saldo a favor por exportación, por no estar destinadas a operaciones gravadas y/o de exportación',
				'Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Valor de las adquisiciones no gravadas',
				'Monto del Impuesto Selectivo al Consumo en los casos en que el sujeto pueda utilizarlo como deducción',
				'Impuesto al Consumo de las Bolsas de Plástico',
				'Otros conceptos, tributos y cargos que no formen parte de la base imponible',
				'Importe total de las adquisiciones registradas según comprobante de pago',
				'Código de la Moneda',
				'Tipo de cambio',
				'Fecha de emisión del comprobante de pago que se modifica',
				'Tipo de comprobante de pago que se modifica',
				'Número de serie del comprobante de pago que se modifica',
				'Código de la dependencia Aduanera de la Declaración Única de Aduanas (DUA) o de la Declaración Simplificada de Importación (DSI)',
				'Número del comprobante de pago que se modifica',
				'Fecha de emisión de la Constancia de Depósito de Detracción',
				'Número de la Constancia de Depósito de Detracción',
				'Marca del comprobante de pago sujeto a retención',
				'Clasificación de los bienes y servicios adquiridos',
				'Identificación del Contrato o del proyecto',
				'Error tipo 1: inconsistencia en el tipo de cambio',
				'Error tipo 2: inconsistencia por proveedores no habidos',
				'Error tipo 3: inconsistencia por proveedores que renunciaron a la exoneración del Apéndice I del IGV',
				'Error tipo 4: inconsistencia por DNIs que fueron utilizados en las Liquidaciones de Compra y que ya cuentan con RUC',
				'Indicador de Comprobantes de pago cancelados con medios de pago',
				'Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste',
				'43',
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


		name_03 = self.get_default_filename(ple_id='080300', tiene_datos=bool(lines_to_write_03))
		lines_to_write_03.append('')
		txt_string_03 = '\r\n'.join(lines_to_write_03)
		if txt_string_03 :
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_03, name_03[2:], headers=[
				'Periodo',
				'Número correlativo del mes o Código Único de la Operación (CUO)',
				'Número correlativo del asiento contable',
				'Fecha de emisión del comprobante de pago o documento',
				'Fecha de Vencimiento o Fecha de Pago',
				'Tipo de Comprobante de Pago o Documento',
				'Serie del comprobante de pago o documento o código de la dependencia Aduanera',
				'Número del comprobante de pago o documento o número de orden del formulario físico o virtual o número final',
				'Número final',
				'Tipo de Documento de Identidad del proveedor',
				'Número de RUC del proveedor o número de documento de Identidad',
				'Apellidos y nombres, denominación o razón social del proveedor',
				'Base imponible de las adquisiciones gravadas que dan derecho a crédito fiscal y/o saldo a favor por exportación, destinadas exclusivamente a operaciones gravadas y/o de exportación',
				'Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal',
				'Impuesto al Consumo de las Bolsas de Plástico',
				'Otros conceptos, tributos y cargos que no formen parte de la base imponible',
				'Importe total de las adquisiciones registradas según comprobante de pago',
				'Código de la Moneda',
				'Tipo de cambio',
				'Fecha de emisión del comprobante de pago que se modifica',
				'Tipo de comprobante de pago que se modifica',
				'Número de serie del comprobante de pago que se modifica',
				'Número del comprobante de pago que se modifica',
				'Fecha de emisión de la Constancia de Depósito de Detracción',
				'Número de la Constancia de Depósito de Detracción',
				'Marca del comprobante de pago sujeto a retención',
				'Clasificación de los bienes y servicios adquiridos',
				'Error tipo 1: inconsistencia en el tipo de cambio',
				'Error tipo 2: inconsistencia por proveedores no habidos',
				'Error tipo 3: inconsistencia por proveedores que renunciaron a la exoneración del Apéndice I del IGV',
				'Indicador de Comprobantes de pago cancelados con medios de pago',
				'Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste',
			])
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
		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res
