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

class ReporteVentas(models.TransientModel):
	_name = "solse.reporte.ventas"
	_description = "Reporte Ventas"

	# En la fecha se debe imprimir la fecha actual del momento en que se imprime

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	fecha_ini = fields.Date("Fecha Inicial")
	fecha_fin = fields.Date("Fecha Final")
	tipo_reporte = fields.Selection([("compra", "Compra"), ("venta", "Venta")], default="venta", required=True, string="Reporte de ")
	contacto_ids = fields.Many2many('res.partner', 'rventa_partner_id', 'venta_id', 'partner_id', string="Contacto's")
	empresa_ids = fields.Many2many('res.company', 'rventa_empresa_id', 'ventaemp_id', 'empresa_id', string="Empresa's")
	# codigo = standard_name

	def generate_excel_report(self):
		# Crear un archivo en memoria usando io.BytesIO()
		workbook_stream = io.BytesIO()

		# Crear un libro de trabajo y una hoja en el archivo Excel
		workbook = xlsxwriter.Workbook(workbook_stream)
		worksheet = workbook.add_worksheet()

		# Escribir datos en la hoja de trabajo
		worksheet.write('A1', 'Nombre del cliente')
		worksheet.write('B1', 'Total de venta')

		# Ejemplo de datos de ventas (reemplazar con tus propios datos)
		ventas_data = [
			{'cliente': 'Cliente 1', 'total_venta': 1000},
			{'cliente': 'Cliente 2', 'total_venta': 1500},
			{'cliente': 'Cliente 3', 'total_venta': 800},
		]

		# Escribir los datos de ventas en el archivo Excel
		row = 1
		col = 0
		for venta in ventas_data:
			worksheet.write(row, col, venta['cliente'])
			worksheet.write(row, col + 1, venta['total_venta'])
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
			#'datas_fname': file_name,
			'res_model': 'solse.reporte.ventas',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}

	def obtener_datos_venta(self, grupo_venta, vendedor):
		"""
		vendedor, v.venta, igv, v.total clientes[cantidad]
		"""
		dominio_venta = [('team_id', '=', grupo_venta.id), ('user_id', '=', vendedor.id), ('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]
		if self.fecha_ini:
			dominio_venta.append(('invoice_date', '>=', self.fecha_ini))
		if self.fecha_fin:
			dominio_venta.append(('invoice_date', '<=', self.fecha_fin))

		if self.empresa_ids:
			dominio_venta.append(('company_id', 'in', self.empresa_ids.ids))

		facturas_n1 = self.env['account.move'].search(dominio_venta)
		ventas = facturas_n1
		
		v_venta = sum(ventas.mapped('amount_untaxed_signed'))
		igv = sum(ventas.mapped('amount_tax_signed'))
		v_total = sum(ventas.mapped('amount_total_signed'))
		cant_clientes = len(ventas.mapped('partner_id'))
		return {
			'tipo': 'detalle',
			'vendedor': vendedor.display_name,
			'v_venta': v_venta,
			'igv': igv,
			'v_total': v_total,
			'cant_clientes': cant_clientes,
		}

	
	def get_report_values(self):
		esquema = []
		global_base = 0
		global_igv = 0
		global_grupo = 0
		global_cant = 0
		dominio_grupos = []
		nombre_empresas = []
		if self.empresa_ids:
			dominio_grupos.append(('company_id', 'in', self.empresa_ids.ids))
			for empresa in self.empresa_ids:
				nombre_empresas.append(empresa.name)
		else:
			empresas = self.env['res.company'].search([])
			dominio_grupos.append(('company_id', 'in', empresas.ids))
			for empresa in empresas:
				nombre_empresas.append(empresa.name)
		
		equipo_ventas = self.env['crm.team'].search(dominio_grupos)
		if not equipo_ventas:
			equipo_ventas = self.env['crm.team'].search([])

		for equipo in equipo_ventas:
			vendedores = equipo.member_ids
			total_base = 0
			total_igv = 0
			total_grupo = 0
			total_cant = 0
			for vendedor in vendedores:
				datos_venta = self.obtener_datos_venta(equipo, vendedor)
				if datos_venta['v_venta'] == 0:
					continue
				total_base += datos_venta['v_venta']
				total_igv += datos_venta['igv']
				total_grupo += datos_venta['v_total']
				total_cant += datos_venta['cant_clientes']
				esquema.append(datos_venta)

			if total_base == 0:
				continue
			esquema.append({
				'tipo': 'total',
				'texto': 'Total %s' % equipo.name,
				'total_base': '{0:.2f}'.format(total_base),
				'total_igv': '{0:.2f}'.format(total_igv),
				'total_grupo': '{0:.2f}'.format(total_grupo),
				'total_cant': total_cant,
			})
			global_base += total_base
			global_igv += total_igv
			global_grupo += total_grupo
			global_cant += total_cant

		esquema.append({
			'tipo': 'total',
			'texto': 'Total',
			'total_base': '{0:.2f}'.format(global_base),
			'total_igv': '{0:.2f}'.format(global_igv),
			'total_grupo': '{0:.2f}'.format(global_grupo),
			'total_cant': global_cant,
		})


		datos_rpt = {
			"docs": esquema,
			"datos": esquema, 
			"lineas": esquema,
			"empresa": "\n".join(nombre_empresas),
		}
		if self.fecha_ini:
			datos_rpt['fecha_ini'] = self.fecha_ini

		if self.fecha_fin:
			datos_rpt['fecha_fin'] = self.fecha_fin

		return datos_rpt

	def action_pdf(self):
		data = self.get_report_values()
		docs = self.env['product.product'].search([], limit=10)
		return self.env.ref('solse_estados_cuenta.reporte_ventas_report_pdf').report_action(docs, data)


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
		worksheet.write('A1', 'VENDEDORES')
		worksheet.write('B1', 'V.VENTA')
		worksheet.write('C1', 'I.G.V')
		worksheet.write('D1', 'V.TOTAL')
		worksheet.write('E1', 'CLIENTES')

		# Escribimos los datos en la hoja de trabajo
		row = 1
		for linea in data["lineas"]:
			if linea['tipo'] == 'detalle':
				worksheet.write(row, 0, linea['vendedor'])
				worksheet.write(row, 1, linea['v_venta'])
				worksheet.write(row, 2, linea['igv'])
				worksheet.write(row, 3, linea['v_total'])
				worksheet.write(row, 4, linea['cant_clientes'])
				row += 1
			elif linea['tipo'] == 'total':
				# Para los totales, escribimos las celdas con un formato diferente
				format = workbook.add_format({'bold': True, 'border': 1})
				worksheet.write(row, 0, linea['texto'], format)
				worksheet.write(row, 1, linea['total_base'], format)
				worksheet.write(row, 2, linea['total_igv'], format)
				worksheet.write(row, 3, linea['total_grupo'], format)
				worksheet.write(row, 4, linea['total_cant'], format)
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


		"""file_name = 'reporte_ventas.xlsx'
		attachment = self.env['ir.attachment'].create({
			'name': file_name,
			'type': 'binary',
			'datas': base64.b64encode(file_data),
			#'datas_fname': file_name,
			'res_model': 'solse.reporte.ventas',
			'res_id': self.id,
			'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		})

		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/%s?download=true' % attachment.id,
			'target': 'self',
		}"""



