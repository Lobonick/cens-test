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

class ReportePronosticoCobranza(models.TransientModel):
	_name = "solse.reporte.pronostico.cobranza"
	_description = "Pronostico Cobranza"

	# En la fecha se debe imprimir la fecha actual del momento en que se imprime

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	fecha_ini = fields.Date("Fecha Inicial")
	fecha_fin = fields.Date("Fecha Final")
	tipo_reporte = fields.Selection([("compra", "Compra"), ("venta", "Venta")], default="venta", required=True, string="Reporte de ")
	contacto_ids = fields.Many2many('res.partner', 'cobranza_partner_id', 'rcobranza_id', 'partner_id', string="Contacto's")
	empresa_ids = fields.Many2many('res.company', 'cobranza_empresa_id', 'rcobranza_id', 'empresa_id', string="Empresa's")
	# codigo = standard_name

	def obtener_datos_venta(self, contacto):
		"""
		vendedor, v.venta, igv, v.total clientes[cantidad]
		"""
		move_type = {
			"venta": "out_invoice",
			"compra": "in_invoice",
		}
		dominio_venta = [('partner_id', '=', contacto.id), ('move_type', '=', move_type[self.tipo_reporte]), ('amount_residual_signed', '>', 0), ('state', '=', 'posted')]
		if self.empresa_ids:
			dominio_venta.append(('company_id', 'in', self.empresa_ids.ids))

		facturas_n1 = self.env['account.move'].search(dominio_venta)
		facturas = facturas_n1
		if not facturas:
			return False
		saldo_total = sum(facturas.mapped('amount_residual_signed'))
		#today = fields.Date.context_today(self)
		today = self.fecha_fin
		fecha_mas_7_dias = today + timedelta(days=7)
		fecha_8_14_dias = fecha_mas_7_dias + timedelta(days=7)
		fecha_15_21_dias = fecha_8_14_dias + timedelta(days=7)
		cuota_vencida = facturas.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= today)
		cuota_1_7 = facturas.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity > today and l.date_maturity <= fecha_mas_7_dias)
		cuota_8_14 = facturas.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity > fecha_mas_7_dias and l.date_maturity <= fecha_8_14_dias)
		cuota_15_21 = facturas.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity > fecha_8_14_dias and l.date_maturity <= fecha_15_21_dias)
		cuota_21_mas = facturas.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity > fecha_15_21_dias)
		importe_vencido = sum(cuota_vencida.mapped('amount_residual')) if cuota_vencida else 0.00
		pagar_1_7 = sum(cuota_1_7.mapped('amount_residual')) if cuota_1_7 else 0.00
		pagar_8_14 = sum(cuota_8_14.mapped('amount_residual')) if cuota_8_14 else 0.00
		pagar_15_21 = sum(cuota_15_21.mapped('amount_residual')) if cuota_15_21 else 0.00
		pagar_21_mas = sum(cuota_21_mas.mapped('amount_residual')) if cuota_21_mas else 0.00

		return {
			'tipo': 'detalle',
			'contacto': contacto.display_name,
			'saldo_total': saldo_total,
			'importe_vencido': importe_vencido,
			'pagar_n1': pagar_1_7,
			'pagar_n2': pagar_8_14,
			'pagar_n3': pagar_15_21,
			'pagar_n4': pagar_21_mas,
		}

	
	def get_report_values(self):
		esquema = []
		dominio_grupos = []
		nombre_empresas = []
		contacto_array = []
		total_saldo_total = 0.00
		total_importe_vencido = 0.00
		total_pagar_1_7 = 0.00
		total_pagar_8_14 = 0.00
		total_pagar_15_21 = 0.00
		total_pagar_21_mas = 0.00

		empresa_base = False
		if self.empresa_ids:
			if not empresa_base:
				empresa_base = self.empresa_ids[0]
			dominio_grupos.append(('company_id', 'in', self.empresa_ids.ids))
			for empresa in self.empresa_ids:
				nombre_empresas.append(empresa.name)
		else:
			empresas = self.env['res.company'].search([])
			if not empresa_base:
				empresa_base = empresas[0]
			dominio_grupos.append(('company_id', 'in', empresas.ids))
			for empresa in empresas:
				nombre_empresas.append(empresa.name)

		dominio_contactos = []
		if self.contacto_ids:
			dominio_contactos = [('id', 'in', self.contacto_ids.ids)]
			for con in self.contacto_ids:
				contacto_array.append(con.name)
		else:
			contacto_array.append("Varios")
		contactos = self.env['res.partner'].search(dominio_contactos)
		for contacto in contactos:
			datos_factura = self.obtener_datos_venta(contacto)
			if not datos_factura:
				continue
			total_saldo_total += datos_factura['saldo_total']
			total_importe_vencido += datos_factura['importe_vencido']
			total_pagar_1_7 += datos_factura['pagar_n1']
			total_pagar_8_14 += datos_factura['pagar_n2']
			total_pagar_15_21 += datos_factura['pagar_n3']
			total_pagar_21_mas += datos_factura['pagar_n4']
			esquema.append(datos_factura)


		esquema.append({
			'tipo': 'total',
			'texto': 'Total',
			'total_saldo_total': '{0:.2f}'.format(total_saldo_total),
			'total_importe_vencido': '{0:.2f}'.format(total_importe_vencido),
			'total_pagar_1_7': '{0:.2f}'.format(total_pagar_1_7),
			'total_pagar_8_14': '{0:.2f}'.format(total_pagar_8_14),
			'total_pagar_15_21': '{0:.2f}'.format(total_pagar_15_21),
			'total_pagar_21_mas': '{0:.2f}'.format(total_pagar_21_mas),
		})

		moneda_dolar = self.env["res.currency"].search([("name", "=", "USD")], limit=1)
		if moneda_dolar:
			total_saldo_total_dolar = empresa_base.currency_id._convert(total_saldo_total, moneda_dolar, empresa_base, self.fecha_fin, round=False)
			total_importe_vencido_dolar = empresa_base.currency_id._convert(total_importe_vencido, moneda_dolar, empresa_base, self.fecha_fin, round=False)
			total_pagar_1_7_dolar = empresa_base.currency_id._convert(total_pagar_1_7, moneda_dolar, empresa_base, self.fecha_fin, round=False)
			total_pagar_8_14_dolar = empresa_base.currency_id._convert(total_pagar_8_14, moneda_dolar, empresa_base, self.fecha_fin, round=False)
			total_pagar_15_21_dolar = empresa_base.currency_id._convert(total_pagar_15_21, moneda_dolar, empresa_base, self.fecha_fin, round=False)
			total_pagar_21_mas_dolar = empresa_base.currency_id._convert(total_pagar_21_mas, moneda_dolar, empresa_base, self.fecha_fin, round=False)

			esquema.append({
				'tipo': 'total',
				'texto': '',
				'total_saldo_total': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_saldo_total_dolar)),
				'total_importe_vencido': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_importe_vencido_dolar)),
				'total_pagar_1_7': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_pagar_1_7_dolar)),
				'total_pagar_8_14': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_pagar_8_14_dolar)),
				'total_pagar_15_21': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_pagar_15_21_dolar)),
				'total_pagar_21_mas': "%s %s" % (moneda_dolar.symbol,'{0:.2f}'.format(total_pagar_21_mas_dolar)),
			})


		datos_rpt = {
			"docs": esquema,
			"datos": esquema, 
			"lineas": esquema,
			"empresa": "\n".join(nombre_empresas),
			"contacto": ",".join(contacto_array)
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def action_pdf(self):
		data = self.get_report_values()
		docs = self.env['product.product'].search([], limit=10)
		return self.env.ref('solse_estados_cuenta.reporte_pronostico_cobranzas_report_pdf').report_action(docs, data)

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
		worksheet.write('A1', '')
		worksheet.write('B1', 'Saldo Total Cliente')
		worksheet.write('C1', 'Importe Vencido')
		worksheet.write('D1', 'A pagar en 1 a 7 días')
		worksheet.write('E1', 'A pagar en 8 a 14 días')
		worksheet.write('F1', 'A pagar en 15 a 21 días')
		worksheet.write('G1', 'A pagar en mas de 21 días')

		# Escribimos los datos en la hoja de trabajo
		row = 1
		for linea in data["lineas"]:
			if linea['tipo'] == 'detalle':
				format = workbook.add_format({'bold': False, 'border': 0})
				worksheet.write(row, 0, linea['contacto'])
				worksheet.write(row, 1, linea['saldo_total'], format)
				worksheet.write(row, 2, linea['importe_vencido'], format)
				worksheet.write(row, 3, linea['pagar_n1'], format)
				worksheet.write(row, 4, linea['pagar_n2'], format)
				worksheet.write(row, 5, linea['pagar_n3'], format)
				worksheet.write(row, 6, linea['pagar_n4'], format)
				row += 1
			elif linea['tipo'] == 'total':
				# Para los totales, escribimos las celdas con un formato diferente
				format = workbook.add_format({'bold': True, 'border': 1})
				worksheet.write(row, 0, linea['texto'], format)
				worksheet.write(row, 1, linea['total_saldo_total'], format)
				worksheet.write(row, 2, linea['total_importe_vencido'], format)
				worksheet.write(row, 3, linea['total_pagar_1_7'], format)
				worksheet.write(row, 4, linea['total_pagar_8_14'], format)
				worksheet.write(row, 5, linea['total_pagar_15_21'], format)
				worksheet.write(row, 6, linea['total_pagar_21_mas'], format)
				row += 2  # Agregamos una línea vacía después de los totales

		# Cerramos el libro de trabajo
		workbook.close()

		# Obtenemos el contenido del archivo en memoria
		workbook_stream.seek(0)
		file_data = workbook_stream.read()
		workbook_stream.close()

		# Devolvemos el archivo como un archivo adjunto para descargar
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


