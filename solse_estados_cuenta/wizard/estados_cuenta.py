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
import logging
_logger = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

class EstadosCuenta(models.TransientModel):
	_name = "solse.estados.cuenta"
	_description = "Reporte Estados de Cuenta"

	# En la fecha se debe imprimir la fecha actual del momento en que se imprime

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	fecha_ini = fields.Date("Fecha Inicial")
	fecha_fin = fields.Date("Fecha Final")
	tipo_reporte = fields.Selection([("compra", "Compra"), ("venta", "Venta")], default="venta", required=True, string="Reporte de ")
	contacto_ids = fields.Many2many('res.partner', 'cuenta_partner_id', 'cuenta_id', 'partner_id', string="Contacto's")
	# codigo = standard_name

	def obtener_pagos(self, factura):
		pagos = factura.payment_move_line_ids
		datos = []
		array_ref = []
		for reg in pagos:
			datos.append("%s %s (%s)" % (reg.currency_id.symbol, abs(reg.amount_currency), reg.date))
			array_ref.append(reg.ref)

		if not datos:
			datos.append("%s 0.00" % factura.currency_id.symbol)

		datos = "\n".join(datos)
		array_ref = "\n".join(array_ref)
		return [datos, array_ref]

	def obtener_lista_contacto(self, id_contacto, moneda_id):
		dominio_contacto = [('amount_residual', '!=', 0)]
		move_type = {
			"venta": "out_invoice",
			"compra": "in_invoice",
		}
		dominio_contacto.append(('move_type', '=', move_type[self.tipo_reporte]))
		dominio_contacto.append(('state', '=', 'posted'))

		if id_contacto:
			dominio_contacto.append(('partner_id', '=', id_contacto))

		if moneda_id:
			dominio_contacto.append(('currency_id', '=', moneda_id.id))

		if self.fecha_ini:
			dominio_contacto.append(('invoice_date', '>=', self.fecha_ini))

		if self.fecha_fin:
			dominio_contacto.append(('invoice_date', '<=', self.fecha_fin))

		facturas_contacto = self.env['account.move'].search(dominio_contacto, order="partner_id desc")
		facturas_procesar = facturas_contacto
		id_contacto = False
		esquema_contacto = []
		inicio = False
		total_importe = 0
		total_pago = 0
		total_saldo = 0
		cant_total = len(facturas_procesar)
		contador = 0
		json_total = {}
		for reg in facturas_procesar:
			contador = contador + 1
			if id_contacto != reg.partner_id.id:
				id_contacto = reg.partner_id.id

				texto_fecha = "Informes hasta %s" % str(self.fecha_fin)
				if self.fecha_ini:
					texto_fecha = "Informe desde %s hasta %s" % (str(self.fecha_ini),str(self.fecha_fin))

				monedas = {
					'S/': 'SOLES',
					'$': 'DOLARES',
				}
				titulo = "%s: %s en %s" % (reg.partner_id.display_name, texto_fecha, monedas[reg.currency_id.symbol])
				if len(self.contacto_ids) == 1:
					titulo = "%s en %s" % (texto_fecha, monedas[reg.currency_id.symbol])

				esquema_contacto.append({
					'tipo': 'titulo',
					'texto': titulo,
					'currency_id': reg.currency_id.symbol,
				})
				esquema_contacto.append({
					'tipo': 'cabecera',
					'documento': 'Documento',
					'fecha_emision': 'Fecha de Emisión',
					'importe': 'Importe',
					'referencia': 'Referencia',
					'pagos': 'Pagos',
					'saldo_actual': 'Saldo Actual',
					'fecha_vencimieno': 'Fecha de Vencimiento',
					'vendedor': 'Vendedor',
					'currency_id': reg.currency_id.symbol,
				})

			monto_pagado = round(reg.amount_total - reg.amount_residual,2)
			datos_pago = self.obtener_pagos(reg)
			esquema_contacto.append({
				'tipo': 'detalle',
				'documento': reg.name,
				'fecha_emision': reg.invoice_date,
				'importe': '{0:.2f}'.format(reg.amount_total),
				'referencia': datos_pago[1],
				'pagos': datos_pago[0],#'{0:.2f}'.format(monto_pagado),
				'saldo_actual': '{0:.2f}'.format(reg.amount_residual),
				'fecha_vencimieno': reg.invoice_date_due,
				'vendedor': reg.user_id.name,
				'currency_id': reg.currency_id.symbol,
			})

			total_importe = total_importe + reg.amount_total
			total_pago = total_pago + monto_pagado
			total_saldo = total_saldo + reg.amount_residual

			if contador == cant_total:
				json_total = {
					'tipo': 'total',
					'total_importe': '{0:.2f}'.format(total_importe),
					'total_pago': '{0:.2f}'.format(total_pago),
					'total_saldo': '{0:.2f}'.format(total_saldo),
					'currency_id': reg.currency_id.symbol,
				}

		esquema_contacto.append({
			'tipo': 'total',
			'total_importe': '{0:.2f}'.format(total_importe),
			'total_pago': '{0:.2f}'.format(total_pago),
			'total_saldo': '{0:.2f}'.format(total_saldo),
			'currency_id': moneda_id.symbol,
		})

		datos_rpt = {
			"docs": esquema_contacto,
			"datos": esquema_contacto, 
			"lineas": esquema_contacto,
			"json_total": json_total,
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def get_report_values(self):
		moneda_dolar = self.env['res.currency'].search([('name', '=', 'USD#')], limit=1)
		moneda_sol = self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
		dominio = [('amount_residual', '!=', 0)]
		dominio_sol = [('amount_residual', '!=', 0)]
		#dominio = []
		#dominio_sol = []
		move_type = {
			"venta": "out_invoice",
			"compra": "in_invoice",
		}
		dominio.append(('state', '=', 'posted'))
		dominio_sol.append(('state', '=', 'posted'))
		contactos = []
		dominio.append(('move_type', '=', move_type[self.tipo_reporte]))
		dominio_sol.append(('move_type', '=', move_type[self.tipo_reporte]))
		dominio.append(('currency_id', '=', moneda_dolar.id))
		dominio_sol.append(('currency_id', '=', moneda_sol.id))

		if self.contacto_ids:
			dominio.append(('partner_id', 'in', self.contacto_ids.ids))
			

		if self.fecha_ini:
			dominio.append(('invoice_date', '>=', self.fecha_ini))
			dominio_sol.append(('invoice_date', '>=', self.fecha_ini))

		if self.fecha_fin:
			dominio.append(('invoice_date', '<=', self.fecha_fin))
			dominio_sol.append(('invoice_date', '<=', self.fecha_fin))

		facturas_n1 = self.env['account.move'].search(dominio, order="partner_id desc")
		facturas = facturas_n1
		contacto_dolar_ids = facturas.mapped('partner_id')
		if not self.contacto_ids:
			dominio_sol.append(('partner_id', 'not in', contacto_dolar_ids.ids))
			contactos.append("Varios")
		else:
			dominio_sol.append(('partner_id', 'not in', contacto_dolar_ids.ids))
			dominio_sol.append(('partner_id', 'in', self.contacto_ids.ids))
			for con in self.contacto_ids:
				contactos.append(con.name)
			
		facturas_n2 = self.env['account.move'].search(dominio_sol, order="partner_id desc")
		facturas_sol = facturas_n2
		

		id_contacto = False
		esquema = []
		inicio = False
		total_importe = 0
		total_pago = 0
		total_saldo = 0
		cant_total = len(facturas)
		contador = 0
		for reg in facturas:
			contador = contador + 1
			if id_contacto != reg.partner_id.id:
				id_contacto = reg.partner_id.id
				datos_sol = self.obtener_lista_contacto(id_contacto, moneda_sol)
				esquema.extend(datos_sol['datos'])
				if inicio != False:
					esquema.append({
						'tipo': 'total',
						'total_importe': '{0:.2f}'.format(total_importe),
						'total_pago': '{0:.2f}'.format(total_pago),
						'total_saldo': '{0:.2f}'.format(total_saldo),
						'currency_id': reg.currency_id.symbol,
					})
					total_importe = 0
					total_pago = 0
					total_saldo = 0

				inicio = True
				texto_fecha = "Informes hasta %s" % str(self.fecha_fin)
				if self.fecha_ini:
					texto_fecha = "Informe desde %s hasta %s" % (str(self.fecha_ini),str(self.fecha_fin))

				monedas = {
					'S/': 'SOLES',
					'$': 'DOLARES',
				}
				titulo = "%s: %s en %s" % (reg.partner_id.display_name, texto_fecha, monedas[reg.currency_id.symbol])
				if len(self.contacto_ids) == 1:
					titulo = "%s en %s" % (texto_fecha, monedas[reg.currency_id.symbol])

				esquema.append({
					'tipo': 'titulo',
					'texto': titulo,
					'currency_id': reg.currency_id.symbol,
				})
				esquema.append({
					'tipo': 'cabecera',
					'documento': 'Documento',
					'fecha_emision': 'Fecha de Emisión',
					'importe': 'Importe',
					'referencia': 'Referencia',
					'pagos': 'Abonos',
					'saldo_actual': 'Saldo',
					'fecha_vencimieno': 'Fecha de Vencimiento',
					'vendedor': 'Vendedor',
					'currency_id': reg.currency_id.symbol,
				})

			monto_pagado = round(reg.amount_total - reg.amount_residual,2)
			datos_pago = self.obtener_pagos(reg)
			esquema.append({
				'tipo': 'detalle',
				'documento': reg.name,
				'fecha_emision': reg.invoice_date,
				'importe': '{0:.2f}'.format(reg.amount_total),
				'referencia': datos_pago[1],
				'pagos': datos_pago[0],#'{0:.2f}'.format(monto_pagado),
				'saldo_actual': '{0:.2f}'.format(reg.amount_residual),
				'fecha_vencimieno': reg.invoice_date_due,
				'vendedor': reg.user_id.name,
				'currency_id': reg.currency_id.symbol,
			})

			total_importe = total_importe + reg.amount_total
			total_pago = total_pago + monto_pagado
			total_saldo = total_saldo + reg.amount_residual

			if contador == cant_total:
				esquema.append({
					'tipo': 'total',
					'total_importe': '{0:.2f}'.format(total_importe),
					'total_pago': '{0:.2f}'.format(total_pago),
					'total_saldo': '{0:.2f}'.format(total_saldo),
					'currency_id': reg.currency_id.symbol,
				})

		id_contacto = False
		inicio = False
		total_importe = 0
		total_pago = 0
		total_saldo = 0
		cant_total = len(facturas_sol)
		contador = 0
		for reg in facturas_sol:
			contador = contador + 1
			if id_contacto != reg.partner_id.id:
				id_contacto = reg.partner_id.id
				if inicio != False:
					esquema.append({
						'tipo': 'total',
						'total_importe': '{0:.2f}'.format(total_importe),
						'total_pago': '{0:.2f}'.format(total_pago),
						'total_saldo': '{0:.2f}'.format(total_saldo),
						'currency_id': reg.currency_id.symbol,
					})
					total_importe = 0
					total_pago = 0
					total_saldo = 0

				inicio = True
				texto_fecha = "Informes hasta %s" % str(self.fecha_fin)
				if self.fecha_ini:
					texto_fecha = "Informe desde %s hasta %s" % (str(self.fecha_ini),str(self.fecha_fin))

				monedas = {
					'S/': 'SOLES',
					'$': 'DOLARES',
				}
				titulo = "%s: %s en %s" % (reg.partner_id.display_name, texto_fecha, monedas[reg.currency_id.symbol])
				if len(self.contacto_ids) == 1:
					titulo = "%s en %s" % (texto_fecha, monedas[reg.currency_id.symbol])
					
				esquema.append({
					'tipo': 'titulo',
					'texto': titulo,
					'currency_id': reg.currency_id.symbol,
				})
				esquema.append({
					'tipo': 'cabecera',
					'documento': 'Documento',
					'fecha_emision': 'Fecha de Emisión',
					'importe': 'Importe',
					'referencia': 'Referencia',
					'pagos': 'Pagos',
					'saldo_actual': 'Saldo Actual',
					'fecha_vencimieno': 'Fecha de Vencimiento',
					'vendedor': 'Vendedor',
					'currency_id': reg.currency_id.symbol,
				})

			monto_pagado = round(reg.amount_total - reg.amount_residual,2)
			esquema.append({
				'tipo': 'detalle',
				'documento': reg.name,
				'fecha_emision': reg.invoice_date,
				'importe': '{0:.2f}'.format(reg.amount_total),
				'referencia': '',
				'pagos': '{0:.2f}'.format(monto_pagado),
				'saldo_actual': '{0:.2f}'.format(reg.amount_residual),
				'fecha_vencimieno': reg.invoice_date_due,
				'vendedor': reg.user_id.name,
				'currency_id': reg.currency_id.symbol,
			})

			total_importe = total_importe + reg.amount_total
			total_pago = total_pago + monto_pagado
			total_saldo = total_saldo + reg.amount_residual

			if contador == cant_total:
				esquema.append({
					'tipo': 'total',
					'total_importe': '{0:.2f}'.format(total_importe),
					'total_pago': '{0:.2f}'.format(total_pago),
					'total_saldo': '{0:.2f}'.format(total_saldo),
					'currency_id': reg.currency_id.symbol,
				})

		datos_rpt = {
			"docs": esquema,
			"datos": esquema, 
			"lineas": esquema,
			"contacto": ",".join(contactos)
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def action_pdf(self):
		data = self.get_report_values()
		docs = self.env['product.product'].search([], limit=10)
		return self.env.ref('solse_estados_cuenta.estados_cuenta_report_pdf').report_action(docs, data)

	def generate_excel_report(self):
		# Obtén los datos para el informe
		data = self.get_report_values()

		# Crear un archivo en memoria usando io.BytesIO()
		workbook_stream = io.BytesIO()

		# Crear un libro de trabajo y una hoja en el archivo Excel
		workbook = xlsxwriter.Workbook(workbook_stream)
		worksheet = workbook.add_worksheet()
		formatdict = {'num_format':'dd/mm/yy'}
		fmt = workbook.add_format(formatdict)

		# Escribir cabecera en la hoja de trabajo

		# Escribir los datos en el archivo Excel
		row = 2
		for linea in data["lineas"]:
			if linea['tipo'] == 'titulo':
				row += 1
				worksheet.write('A' + str(row), linea['texto'])
				row += 1

			if linea['tipo'] == 'cabecera':
				worksheet.write('A' + str(row), linea['documento'])
				worksheet.write('B' + str(row), linea['fecha_emision'])
				worksheet.write('C' + str(row), linea['fecha_vencimieno'])
				worksheet.write('D' + str(row), linea['importe'])
				worksheet.write('E' + str(row), linea['referencia'])
				worksheet.write('F' + str(row), linea['pagos'])
				worksheet.write('G' + str(row), linea['saldo_actual'])
				row += 1

			if linea['tipo'] == 'detalle':
				worksheet.write('A' + str(row), linea['documento'])
				worksheet.write('B' + str(row), linea['fecha_emision'], fmt)
				worksheet.write('C' + str(row), linea['fecha_vencimieno'], fmt)
				worksheet.write('D' + str(row), linea['importe'])
				worksheet.write('E' + str(row), linea['referencia'])
				worksheet.write('F' + str(row), linea['pagos'])
				worksheet.write('G' + str(row), linea['saldo_actual'])
				row += 1

			if linea['tipo'] == 'total':
				worksheet.write('A' + str(row), "Total")
				worksheet.write('B' + str(row), "")
				worksheet.write('C' + str(row), "")
				worksheet.write('D' + str(row), "%s %s" % (linea['currency_id'], linea['total_importe']))
				worksheet.write('E' + str(row), "")
				worksheet.write('F' + str(row), "%s %s" % (linea['currency_id'], linea['total_pago']))
				worksheet.write('G' + str(row), "%s %s" % (linea['currency_id'], linea['total_saldo']))
				row += 1



		# Cerrar el libro de trabajo
		workbook.close()

		# Obtener el contenido del archivo en memoria
		workbook_stream.seek(0)
		file_data = workbook_stream.read()
		workbook_stream.close()

		# Devolver el archivo como un archivo adjunto para descargar
		file_name = 'reporte_estados_cuenta.xlsx'
		attachment = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': base64.b64encode(file_data),
			'res_model': 'solse.estados.cuenta',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}


	def generate_excel_report_n2(self):
		# Obtén los datos para el informe
		data = self.get_report_values()

		# Crear un archivo en memoria usando io.BytesIO()
		workbook_stream = io.BytesIO()

		# Crear un libro de trabajo y una hoja en el archivo Excel
		workbook = xlsxwriter.Workbook(workbook_stream)
		worksheet = workbook.add_worksheet()

		# Escribir la fecha del informe y la moneda en la cabecera
		worksheet.write('A1', f'Informes desde {data["fecha_ini"]} hasta {data["fecha_fin"]} para el cliente {data["contacto"]}')

		# Escribir cabecera en la hoja de trabajo
		worksheet.write('A2', 'Documento')
		worksheet.write('B2', 'Fecha de Emisión')
		worksheet.write('C2', 'Importe')
		worksheet.write('D2', 'Pagos')
		worksheet.write('E2', 'Saldo Actual')
		worksheet.write('F2', 'Fecha de Vencimiento')
		worksheet.write('G2', 'Vendedor')

		formatdict = {'num_format':'mm-dd-yy'}
		fmt = workbook.add_format(formatdict)

		# Escribir los datos en el archivo Excel
		row = 3
		for linea in data["lineas"]:
			if linea['tipo'] == 'detalle':
				worksheet.write('A' + str(row), linea['documento'])
				worksheet.write('B' + str(row), linea['fecha_emision'], fmt)
				worksheet.write('C' + str(row), linea['importe'])
				worksheet.write('D' + str(row), linea['pagos'])
				worksheet.write('E' + str(row), linea['saldo_actual'])
				worksheet.write('F' + str(row), linea['fecha_vencimieno'], fmt)
				worksheet.write('G' + str(row), linea['vendedor'])
				row += 1

		# Cerrar el libro de trabajo
		workbook.close()

		# Obtener el contenido del archivo en memoria
		workbook_stream.seek(0)
		file_data = workbook_stream.read()
		workbook_stream.close()

		# Devolver el archivo como un archivo adjunto para descargar
		file_name = 'reporte_ventas.xlsx'
		attachment = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': base64.b64encode(file_data),
			'res_model': 'solse.reporte.ventas',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}




