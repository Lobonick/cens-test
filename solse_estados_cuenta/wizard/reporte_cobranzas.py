# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import io
import xlsxwriter
import time
import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import pytz
import base64
from odoo.exceptions import UserError, ValidationError
from odoo.tools.image import image_data_uri, base64_to_image
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

class ReporteCobranzas(models.TransientModel):
	_name = "solse.reporte.cobranza"
	_description = "Cobranza"

	# En la fecha se debe imprimir la fecha actual del momento en que se imprime

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	fecha_ini = fields.Date("Fecha Inicial")
	fecha_fin = fields.Date("Fecha Final")
	tipo_reporte = fields.Selection([("compra", "Compra"), ("venta", "Venta")], default="venta", required=True, string="Reporte de ")
	contacto_ids = fields.Many2many('res.partner', 'cobranza2_partner_id', 'rcobranza2_id', 'partner_id', string="Contacto's")
	empresa_ids = fields.Many2many('res.company', 'cobranza2_empresa_id', 'rcobranza2_id', 'empresa_id', string="Empresa's")
	moneda = fields.Many2one("res.currency", string="Moneda")

	def obtener_datos(self, pago):
		"""
		vendedor, v.venta, igv, v.total clientes[cantidad]
		"""
		
		factura = pago.factura_pagada
		return {
			'tipo': 'detalle',
			'contacto': pago.partner_id.display_name,
			'vendedor': factura.invoice_user_id.name,
			'cantidad': '',
			'nro_operacion': pago.ref,
			'tipo_doc': factura.l10n_latam_document_type_id.code,
			'nro_doc': factura.l10n_latam_document_number,
			'fecha_pago': pago.date,
			'monto': abs(pago.amount_currency),
			'localidad': pago.journal_id.name,
		}

	
	def get_report_values(self):
		esquema = []
		dominio_grupos = []
		nombre_empresas = []
		total_saldo_total = 0.00
		total_importe_vencido = 0.00
		total_pagar_1_7 = 0.00
		total_pagar_8_14 = 0.00
		total_pagar_15_21 = 0.00
		total_pagar_21_mas = 0.00

		move_type = {
			"venta": "out_invoice",
			"compra": "in_invoice",
		}
		dominio_venta = [('move_type', '=', move_type[self.tipo_reporte]), ('payment_move_line_ids', '!=', False), ('fecha_ini_pago', '>=', self.fecha_ini), ('fecha_fin_pago', '<=', self.fecha_fin)]
		if self.empresa_ids:
			dominio_venta.append(('company_id', 'in', self.empresa_ids.ids))

		dominio_venta.append(('currency_id', '=', self.moneda.id))
		dominio_venta.append(('state', '=', 'posted'))

		facturas_n1 = self.env['account.move'].search(dominio_venta)
		facturas = facturas_n1
		for reg in facturas:
			reg.payment_move_line_ids.write({'factura_pagada': reg.id})
		pagos = facturas.mapped('payment_move_line_ids').filtered(lambda r: r.date >= self.fecha_ini and r.date <= self.fecha_fin)
		monto_total = 0
		for pago in pagos:
			datos_pago = self.obtener_datos(pago)
			esquema.append(datos_pago)
			monto_total += datos_pago['monto']


		if self.empresa_ids:
			for empresa in self.empresa_ids:
				nombre_empresas.append(empresa.name)
		else:
			empresas = self.env['res.company'].search([])
			for empresa in empresas:
				nombre_empresas.append(empresa.name)


		datos_rpt = {
			"docs": esquema,
			"datos": esquema, 
			"lineas": esquema,
			"monto_total": monto_total,
			"empresa": "\n".join(nombre_empresas),
			"moneda": self.moneda.name,
			"moneda_simbolo": self.moneda.symbol,
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def action_pdf(self):
		data = self.get_report_values()
		docs = self.env['product.product'].search([], limit=10)
		return self.env.ref('solse_estados_cuenta.reporte_cobranzas_report_pdf').report_action(docs, data)

	def action_excel(self):
		data = self.get_report_values()

		# Creamos un archivo en memoria
		workbook_stream = io.BytesIO()

		# Creamos un libro de trabajo y una hoja
		workbook = xlsxwriter.Workbook(workbook_stream)
		worksheet = workbook.add_worksheet()
		formatdict = {'num_format':'dd/mm/yy'}
		fmt = workbook.add_format(formatdict)

		# Definimos los títulos de las columnas
		worksheet.write('A1', 'Cliente')
		worksheet.write('B1', 'Vendedor')
		worksheet.write('C1', 'Nº Operación')
		worksheet.write('D1', 'Tipo Doc.')
		worksheet.write('E1', 'Nº Documento')
		worksheet.write('F1', 'Fecha Pago')
		worksheet.write('G1', 'Monto')
		worksheet.write('H1', 'Tipo de Pago')

		# Escribimos los datos en la hoja de trabajo
		row = 1
		for linea in data["lineas"]:
			if linea['tipo'] == 'detalle':
				format = workbook.add_format({'bold': False, 'border': 0})
				worksheet.write(row, 0, linea['contacto'])
				worksheet.write(row, 1, linea['vendedor'], format)
				worksheet.write(row, 2, linea['nro_operacion'], format)
				worksheet.write(row, 3, linea['tipo_doc'], format)
				worksheet.write(row, 4, linea['nro_doc'], format)
				worksheet.write(row, 5, linea['fecha_pago'], fmt)
				worksheet.write(row, 6, linea['monto'], format)
				worksheet.write(row, 7, linea['localidad'], format)
				row += 1

		row += 1
		format = workbook.add_format({'bold': True, 'border': 1})
		worksheet.write(row, 0, "",format)
		worksheet.write(row, 1, "",format)
		worksheet.write(row, 2, "",format)
		worksheet.write(row, 3, "",format)
		worksheet.write(row, 4, "",format)
		worksheet.write(row, 5, "",format)
		worksheet.write(row, 6, data["monto_total"],format)
		worksheet.write(row, 7, "",format)


		# Cerramos el libro de trabajo
		workbook.close()

		# Obtenemos el contenido del archivo en memoria
		workbook_stream.seek(0)
		file_data = workbook_stream.read()
		workbook_stream.close()

		# Devolvemos el archivo como un archivo adjunto para descargar
		file_name = 'reporte_cobranzas.xlsx'
		attachment = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': base64.b64encode(file_data),
			'res_model': 'solse.reporte.cobranza',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}


