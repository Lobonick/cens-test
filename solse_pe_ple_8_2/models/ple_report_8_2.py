# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from base64 import b64decode, b64encode, encodebytes
import datetime

import logging
_logging = logging.getLogger(__name__)

PLE_8_2_HEADERS = [
	'Periodo',
	'1. Contribuyentes del Régimen General: Número correlativo del mes o Código Único de la Operación (CUO), que es la llave única o clave única o clave primaria del software contable que identifica de manera unívoca el asiento contable en el Libro Diario o del Libro Diario de Formato Simplificado en que se registró la operación. 2. Contribuyentes del Régimen Especial de Renta - RER:  Número correlativo del mes. ',
	'Número correlativo del asiento contable identificado en el campo 2, cuando se utilice el Código Único de la Operación (CUO). El primer dígito debe ser: "A" para el asiento de apertura del ejercicio, "M" para los asientos de movimientos o ajustes del mes o "C" para el asiento de cierre del ejercicio. ',
	'Fecha de emisión del comprobante de pago o documento ',
	'Tipo de Comprobante de Pago o Documento del sujeto no domiciliado ',
	'Serie del comprobante de pago o documento. ',
	'Número del comprobante de pago o documento. ',
	'Valor de las adquisiciones ',
	'Otros conceptos adicionales ',
	'Importe total de las adquisiciones registradas según comprobante de pago o documento ',
	'Tipo de Comprobante de Pago o Documento que sustenta el crédito fiscal ',
	'Serie del comprobante de pago o documento que sustenta el crédito fiscal. En los casos de la Declaración Única de Aduanas (DUA) o de la Declaración Simplificada de Importación (DSI) se consignará el código de la dependencia Aduanera. ',
	'Año de emisión de la DUA o DSI que sustenta el crédito fiscal ',
	'Número del comprobante de pago o documento o número de orden del formulario físico o virtual donde conste el pago del impuesto, tratándose de la utilización de servicios prestados por no domiciliados u otros, número de la DUA o de la DSI, que sustente el crédito fiscal. ',
	'Monto de retención del IGV ',
	'Código  de la Moneda (Tabla 4) ',
	'Tipo de cambio ',
	'Pais de la residencia del sujeto no domiciliado ',
	'Apellidos y nombres, denominación o razón social  del sujeto no domiciliado. En caso de personas naturales se debe consignar los datos en el siguiente orden: apellido paterno, apellido materno y nombre completo. ',
	'Domicilio en el extranjero del sujeto no domiciliado ',
	'Número de identificación del sujeto no domiciliado ',
	'Número de identificación fiscal del beneficiario efectivo de los pagos ',
	'Apellidos y nombres, denominación o razón social  del beneficiario efectivo de los pagos. En caso de personas naturales se debe consignar los datos en el siguiente orden: apellido paterno, apellido materno y nombre completo. ',
	'Pais de la residencia del beneficiario efectivo de los pagos ',
	'Vínculo entre el contribuyente y el residente en el extranjero ',
	'Renta Bruta ',
	'Deducción / Costo de Enajenación de bienes de capital ',
	'Renta Neta ',
	'Tasa de retención ',
	'Impuesto retenido ',
	'Convenios para evitar la doble imposición ',
	'Exoneración aplicada ',
	'Tipo de Renta ',
	'Modalidad del servicio prestado por el no domiciliado ',
	'Aplicación del penultimo parrafo del Art. 76° de la Ley del Impuesto a la Renta ',
	'Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste. ',
	'37',
]

class PLEReport0802(models.Model) :
	_inherit = 'ple.report.08'

	# No domiciliado
	ple_txt_02 = fields.Text(string='Contenido del TXT 8.2')
	ple_txt_02_binary = fields.Binary(string='TXT 8.2', readonly=True)
	ple_txt_02_filename = fields.Char(string='Nombre del TXT 8.2')
	ple_xls_02_binary = fields.Binary(string='Excel 8.2', readonly=True)
	ple_xls_02_filename = fields.Char(string='Nombre del Excel 8.2')

	def generate_report(self) :
		res = super().generate_report()
		self.generate_report_02()
		return res
	
	def generate_report_02(self) :
		res = True
		lines_to_write_02 = []
		bills = self.bill_ids.sudo()
		peru = self.env.ref('base.pe')
		fecha_inicio = datetime.date(self.year, int(self.month), 1)
		contador = 1
		for move in bills:
			m_02 = move.ple_8_2_fields(contador, fecha_inicio)
			contador = contador + 1
			try:
				if move.partner_id.country_id != peru:
					lines_to_write_02.append('|'.join(m_02))
			except:
				raise UserError(
					'Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_02))

		name_02 = self.get_default_filename(ple_id='080200', tiene_datos=bool(lines_to_write_02))
		lines_to_write_02.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_02)
		dict_to_write = dict()
		if txt_string_02:
			xlsx_file_02 = self._generate_xlsx_base64_bytes(txt_string_02, name_02[2:], headers=PLE_8_2_HEADERS)
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': xlsx_file_02.encode(),
				'ple_xls_02_filename': name_02 + '.xlsx',
			})
		else:
			txt_string_02 = " "
			dict_to_write.update({
				'ple_txt_02': txt_string_02,
				'ple_txt_02_binary': b64encode(txt_string_02.encode()),
				'ple_txt_02_filename': name_02 + '.txt',
				'ple_xls_02_binary': False,
				'ple_xls_02_filename': False,
			})

		res = self.write(dict_to_write)
		return res