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

class ReporteCalidadDeuda(models.TransientModel):
	_name = "solse.reporte.calidad.deuda"
	_description = "Calidad de Deuda"

	# En la fecha se debe imprimir la fecha actual del momento en que se imprime

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	fecha_ini = fields.Date("Fecha Inicial")
	fecha_fin = fields.Date("Fecha Final")
	tipo_reporte = fields.Selection([("compra", "Compra"), ("venta", "Venta")], default="venta", required=True, string="Reporte de ")
	contacto_ids = fields.Many2many('res.partner', 'calidad_partner_id', 'rcalidad_id', 'partner_id', string="Contacto's")
	empresa_ids = fields.Many2many('res.company', 'calidad_empresa_id', 'rcalidad_id', 'empresa_id', string="Empresa's")
	moneda = fields.Many2one("res.currency", string="Moneda")
	# codigo = standard_name

	def obtener_datos(self, factura):
		saldo_total = factura.amount_residual
		today = fields.Date.context_today(self)
		fecha_30 = today - timedelta(days=30)
		fecha_60 = fecha_30 - timedelta(days=30)
		fecha_90 = fecha_60 - timedelta(days=30)
		fecha_120 = fecha_90 - timedelta(days=30)

		cuota_por_vencer = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity > today)
		cuota_30 = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= today and l.date_maturity > fecha_30)
		cuota_60 = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= fecha_30 and l.date_maturity > fecha_60)
		cuota_90 = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= fecha_60 and l.date_maturity > fecha_90)
		cuota_120 = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= fecha_90 and l.date_maturity > fecha_120)
		cuota_mas_120 = factura.line_ids.filtered(lambda l: l.account_type=='asset_receivable' and l.date_maturity <= fecha_120)
		
		por_vencer = sum(cuota_por_vencer.mapped('amount_residual_currency')) if cuota_por_vencer else 0.00
		pagar_n1 = sum(cuota_30.mapped('amount_residual_currency')) if cuota_30 else 0.00
		pagar_n2 = sum(cuota_60.mapped('amount_residual_currency')) if cuota_60 else 0.00
		pagar_n3 = sum(cuota_90.mapped('amount_residual_currency')) if cuota_90 else 0.00
		pagar_n4 = sum(cuota_120.mapped('amount_residual_currency')) if cuota_120 else 0.00
		pagar_n5 = sum(cuota_mas_120.mapped('amount_residual_currency')) if cuota_mas_120 else 0.00
		

		return {
			'tipo': 'detalle',
			'fecha_emision': factura.invoice_date,
			'referencia': factura.name,
			'contacto': factura.partner_id.display_name,
			'fecha_vencimiento': factura.invoice_date_due,
			'saldo_total': saldo_total,
			'por_vencer': por_vencer,
			'pagar_n1': pagar_n1,
			'pagar_n2': pagar_n2,
			'pagar_n3': pagar_n3,
			'pagar_n4': pagar_n4,
			'pagar_n5': pagar_n5,
		}

	
	def get_report_values(self):
		esquema = []
		dominio_consulta = []
		nombre_empresas = []
		global_saldo_total = 0.00
		global_por_vencer = 0.00
		global_pagar_n1 = 0.00
		global_pagar_n2 = 0.00
		global_pagar_n3 = 0.00
		global_pagar_n4 = 0.00
		global_pagar_n5 = 0.00

		move_type = {
			"venta": "out_invoice",
			"compra": "in_invoice",
		}
		dominio_consulta.append(('move_type', '=', move_type[self.tipo_reporte]))
		dominio_consulta.append(('state', '=', 'posted'))
		
		if self.empresa_ids:
			dominio_consulta.append(('company_id', 'in', self.empresa_ids.ids))
			for empresa in self.empresa_ids:
				nombre_empresas.append(empresa.name)
		else:
			empresas = self.env['res.company'].search([])
			dominio_consulta.append(('company_id', 'in', empresas.ids))
			for empresa in empresas:
				nombre_empresas.append(empresa.name)

		if self.fecha_ini:
			dominio_consulta.append(('invoice_date', '>=', self.fecha_ini))

		if self.fecha_fin:
			dominio_consulta.append(('invoice_date', '<=', self.fecha_fin))

		dominio_consulta.append(('currency_id', '=', self.moneda.id))

		dominio_consulta.append(('partner_id', '=', False))

		dominio_contactos = []
		if self.contacto_ids:
			dominio_contactos = [('id', 'in', self.contacto_ids.ids)]
		contactos = self.env['res.partner'].search(dominio_contactos)
		for contacto in contactos:
			dominio_consulta.pop()
			dominio_consulta.append(('partner_id', '=', contacto.id))
			facturas = self.env['account.move'].search(dominio_consulta)
			total_saldo_total = 0.00
			total_por_vencer = 0.00
			total_pagar_n1 = 0.00
			total_pagar_n2 = 0.00
			total_pagar_n3 = 0.00
			total_pagar_n4 = 0.00
			total_pagar_n5 = 0.00

			esquema.append({
				'tipo': 'cabecera',
				'texto': contacto.display_name,
			})

			for factura in facturas:
				if factura.orden_compra and factura.orden_compra.split(" ")[0] == "LL":
					continue
				datos_factura = self.obtener_datos(factura)
				if datos_factura['saldo_total'] <= 0:
					continue
				total_saldo_total += datos_factura['saldo_total']
				total_por_vencer += datos_factura['por_vencer']
				total_pagar_n1 += datos_factura['pagar_n1']
				total_pagar_n2 += datos_factura['pagar_n2']
				total_pagar_n3 += datos_factura['pagar_n3']
				total_pagar_n4 += datos_factura['pagar_n4']
				total_pagar_n5 += datos_factura['pagar_n5']
				esquema.append(datos_factura)

			if not total_saldo_total:
				esquema.pop()
				continue

			esquema.append({
				'tipo': 'total',
				'texto': 'Saldo Acumulado de Empresa',
				'total_saldo_total': '{0:.2f}'.format(total_saldo_total),
				'total_por_vencer': '{0:.2f}'.format(total_por_vencer),
				'total_pagar_n1': '{0:.2f}'.format(total_pagar_n1),
				'total_pagar_n2': '{0:.2f}'.format(total_pagar_n2),
				'total_pagar_n3': '{0:.2f}'.format(total_pagar_n3),
				'total_pagar_n4': '{0:.2f}'.format(total_pagar_n4),
				'total_pagar_n5': '{0:.2f}'.format(total_pagar_n5),
			})

			global_saldo_total += total_saldo_total
			global_por_vencer += total_por_vencer
			global_pagar_n1 += total_pagar_n1
			global_pagar_n2 += total_pagar_n2
			global_pagar_n3 += total_pagar_n3
			global_pagar_n4 += total_pagar_n4
			global_pagar_n5 += total_pagar_n5


		esquema.append({
			'tipo': 'total',
			'texto': 'Total',
			'total_saldo_total': '{0:.2f}'.format(global_saldo_total),
			'total_por_vencer': '{0:.2f}'.format(global_por_vencer),
			'total_pagar_n1': '{0:.2f}'.format(global_pagar_n1),
			'total_pagar_n2': '{0:.2f}'.format(global_pagar_n2),
			'total_pagar_n3': '{0:.2f}'.format(global_pagar_n3),
			'total_pagar_n4': '{0:.2f}'.format(global_pagar_n4),
			'total_pagar_n5': '{0:.2f}'.format(global_pagar_n5),
		})

		total_por_vencer = '{0:.2f}%'.format(0.00)
		total_pagar_n1 = '{0:.2f}%'.format(0.00)
		total_pagar_n2 = '{0:.2f}%'.format(0.00)
		total_pagar_n3 = '{0:.2f}%'.format(0.00)
		total_pagar_n4 = '{0:.2f}%'.format(0.00)
		total_pagar_n5 = '{0:.2f}%'.format(0.00)
		if global_por_vencer:
			total_por_vencer = '{0:.2f}%'.format((global_por_vencer * 100) / global_saldo_total)
		if global_pagar_n1:
			total_pagar_n1 = '{0:.2f}%'.format((global_pagar_n1 * 100) / global_saldo_total)
		if global_pagar_n2:
			total_pagar_n2 = '{0:.2f}%'.format((global_pagar_n2 * 100) / global_saldo_total)
		if global_pagar_n3:
			total_pagar_n3 = '{0:.2f}%'.format((global_pagar_n3 * 100) / global_saldo_total)
		if global_pagar_n4:
			total_pagar_n4 = '{0:.2f}%'.format((global_pagar_n4 * 100) / global_saldo_total)
		if global_pagar_n5:
			total_pagar_n5 = '{0:.2f}%'.format((global_pagar_n5 * 100) / global_saldo_total)
		esquema.append({
			'tipo': 'total',
			'texto': 'Porcentajes',
			'total_saldo_total': '',
			'total_por_vencer': total_por_vencer,
			'total_pagar_n1': total_pagar_n1,
			'total_pagar_n2': total_pagar_n2,
			'total_pagar_n3': total_pagar_n3,
			'total_pagar_n4': total_pagar_n4,
			'total_pagar_n5': total_pagar_n5,
		})


		datos_rpt = {
			"docs": esquema,
			"datos": esquema, 
			"lineas": esquema,
			"empresa": "\n".join(nombre_empresas),
			"moneda": self.moneda.name,
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def action_pdf(self):
		data = self.get_report_values()
		docs = self.env['product.product'].search([], limit=10)
		return self.env.ref('solse_estados_cuenta.reporte_calidad_deuda_report_pdf').report_action(docs, data)

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

			if linea['tipo'] == 'cabecera':
				row += 1
				worksheet.write('A' + str(row), linea['texto'])
				row += 1
				worksheet.write('A' + str(row), 'Fecha Emisión')
				worksheet.write('B' + str(row), 'Referencia')
				worksheet.write('C' + str(row), 'Empresa')
				worksheet.write('D' + str(row), 'Fecha Vencimiento')
				worksheet.write('E' + str(row), 'Importe Adeudado')
				worksheet.write('F' + str(row), 'Por vencer')
				worksheet.write('G' + str(row), 'Tiempo 30 d.')
				worksheet.write('H' + str(row), 'Tiempo 60 d.')
				worksheet.write('I' + str(row), 'Tiempo 90 d.')
				worksheet.write('J' + str(row), 'Tiempo 120 d.')
				worksheet.write('K' + str(row), 'Mayor')
				row += 1

			if linea['tipo'] == 'detalle':
				worksheet.write('A' + str(row), linea['fecha_emision'], fmt)
				worksheet.write('B' + str(row), linea['referencia'])
				worksheet.write('C' + str(row), linea['contacto'])
				worksheet.write('D' + str(row), linea['fecha_vencimiento'], fmt)
				worksheet.write('E' + str(row), linea['saldo_total'])
				worksheet.write('F' + str(row), linea['por_vencer'])
				worksheet.write('G' + str(row), linea['pagar_n1'])
				worksheet.write('H' + str(row), linea['pagar_n2'])
				worksheet.write('I' + str(row), linea['pagar_n3'])
				worksheet.write('J' + str(row), linea['pagar_n4'])
				worksheet.write('K' + str(row), linea['pagar_n5'])
				row += 1

			if linea['tipo'] == 'total':
				worksheet.write('A' + str(row), "")
				worksheet.write('B' + str(row), "")
				worksheet.write('C' + str(row), "")
				worksheet.write('D' + str(row), linea['texto'])
				worksheet.write('E' + str(row), linea['total_saldo_total'])
				worksheet.write('F' + str(row), linea['total_por_vencer'])
				worksheet.write('G' + str(row), linea['total_pagar_n1'])
				worksheet.write('H' + str(row), linea['total_pagar_n2'])
				worksheet.write('I' + str(row), linea['total_pagar_n3'])
				worksheet.write('J' + str(row), linea['total_pagar_n4'])
				worksheet.write('K' + str(row), linea['total_pagar_n5'])
				row += 1

		# Cerrar el libro de trabajo
		workbook.close()

		# Obtener el contenido del archivo en memoria
		workbook_stream.seek(0)
		file_data = workbook_stream.read()
		workbook_stream.close()

		# Devolver el archivo como un archivo adjunto para descargar
		file_name = 'reporte_calidad_deuda.xlsx'
		attachment = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': base64.b64encode(file_data),
			'res_model': 'solse.reporte.calidad.deuda',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}


