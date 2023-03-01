# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

DEFAULT_PLE_DATA = '%(month)s%(day)s%(ple_id)s%(report_03)s%(operacion)s%(contenido)s%(moneda)s%(ple)s'
DEFAULT_FORMAT_DICT = {
	'header_format': {
		'bold': True,
		'text_wrap': True,
		'valign': 'top',
		'fg_color': '#D7E4BC',
		'border': 1,
	},
	'text_format': {
		'num_format': '@',
	},
}

def number_to_ascii_chr(n) :
	try :
		n = int(n)
	except :
		_logging.info('error en lineaaaaaaaaaaaaaa 52')
		n = 0
	digits = []
	if n > 0 :
		while n :
			digits.append(int(n % 26))
			n //= 26
	else :
		digits.append(0)
	digits = ''.join(chr(numero+65) for numero in digits[::-1])
	return digits

def get_last_day(day) :
	first_next = day.replace(day=28) + datetime.timedelta(days=4)
	return (first_next - datetime.timedelta(days=first_next.day))

def get_selection_name(env, model, field, value):
	return dict(env[model].fields_get(field, 'selection').get(field, {}).get('selection',{})).get(value)

class SolsePeCpeReport(models.Model):
	_name = 'solse.pe.cpe.report'
	_description = 'Reporte CPE'

	name = fields.Char('Nombre')
	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	reporte_nombre = fields.Char(string='Nombre del Excel')
	reporte_binary = fields.Binary(string='Excel', readonly=True)

	reporte_sunat_nombre = fields.Char(string='Nombre del Excel (Sunat)')
	reporte_sunat_binary = fields.Binary(string='Excel (Ventas Sunat)', readonly=True)

	date_generated = fields.Datetime(string='Fecha de generación', readonly=True)
	fecha_inicio = fields.Date('Fecha de inicio', required=True)
	fecha_fin = fields.Date('Fecha Fin', required=True)
	factura_ids = fields.Many2many(comodel_name='account.move', string='Facturas', readonly=True)
	partner_id = fields.Many2many("res.partner", string="Contactos para envió")
	es_de_alerta = fields.Boolean('Es de Alerte', help="Es usado exclusivamente para informar de errores o inconsistencias en los comprobanes electronicos, los comprobantes con estado aceptado no seran tomados en cuenta")

	def update_report(self) :
		domain_company = []
		empresas = self.env['res.company'].sudo().search([])
		pais_id = self.env.ref('base.pe').id
		if len(empresas) > 1:
			domain_company = [('company_id','=',self.company_id.id), ('company_id.partner_id.country_id','=',pais_id)]
		
		lines = []
		if self.es_de_alerta:
			lines = [
				('is_cpe', '=', True),
				('state','in',['posted']),
				('estado_sunat','in',['01', '03', '07', '09']),
				('no_enviar_rnoaceptados', '=', False),
				('journal_id.type','in',['sale']),
			]
		else:
			lines = [
				('is_cpe', '=', True),
				('invoice_date','>=',str(self.fecha_inicio)),
				('invoice_date','<=',str(self.fecha_fin)),
				('state','in',['posted', 'annul', 'cancel']),
				('journal_id.type','in',['sale']),
			]
		paremtros_buscar = domain_company + lines
		lines = self.env[self.factura_ids._name].search(paremtros_buscar, order='invoice_date asc')
		self.factura_ids = lines

	def generate_report(self) :
		self.update_report()
		lines_to_write_01 = []
		lines_to_write_02 = []
		lines = self.factura_ids.sudo()
		for move in lines :
			m = move.journal_id.type
			m_01 = []
			m_02 = []

			m_01.append(str(move.l10n_latam_document_number))
			m_01.append(str(move.amount_total))
			m_01.append(str(move.amount_untaxed_signed))
			m_01.append(str(move.amount_tax_signed))
			estado_sunat = get_selection_name(self.env, 'account.move', 'estado_sunat', move.estado_sunat)
			m_01.append(estado_sunat or '')
			m_01.append(move.partner_id.display_name)
			m_01.append(move.partner_id.doc_number or '-')
			m_01.append(str(move.invoice_date))
			m_01.append('0000')
			estado = get_selection_name(self.env, 'account.move', 'state', move.state)
			m_01.append(estado)

			if m_01 :
				try :
					lines_to_write_01.append('|'.join(m_01))
				except Exception as e:
					raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_01))

			seriec = move.l10n_latam_document_number
			seria_arrary = seriec.split("-")
			serie = ""
			correlativo = ""
			serie = seria_arrary[0]
			if len(seria_arrary) == 2:
				correlativo = seria_arrary[1]
			

			m_02.append(str(move.invoice_date.strftime("%d/%m/%Y")))
			m_02.append(str(serie))
			m_02.append(str(correlativo))
			m_02.append(str(move.pe_invoice_code))
			m_02.append(str(move.partner_id.doc_number or '-'))
			m_02.append(move.partner_id.display_name)
			m_02.append(move.currency_id.name)
			#m_02.append(str(round(move.tipo_cambio_dolar_sistema, 2)))
			m_02.append(str(move.tipo_cambio_dolar_sistema))

			"""
			'Op. Gravada',
			'Op. Gravada PEN',
			'Op. Exonerada',
			'Op. Exonerada PEN',
			'Op. Inafecta',
			'Op. Inafecta PEN',
			'Impuesto',
			'Impuesto PEN',
			'Total',
			'Total PEN',
			'Fecha',
			'Tipo',
			'Num. Ref.',
			"""

			if move.state in ['annul', 'cancel']:
				m_02.append("0.00")
				m_02.append("0.00")
				
				m_02.append("0.00")
				m_02.append("0.00")

				m_02.append("0.00")
				m_02.append("0.00")

				m_02.append("0.00")
				m_02.append("0.00")
				
				m_02.append("0.00")
				m_02.append("0.00")
			
				m_02.append('')
				m_02.append('')
				m_02.append('')
			else:

				m_02.append(str(round(move.total_operaciones_gravadas_dolar, 2)))
				m_02.append(str(round(move.total_operaciones_gravadas, 2)))

				m_02.append(str(round(move.total_operaciones_exoneradas_dolar, 2)))
				m_02.append(str(round(move.total_operaciones_exoneradas, 2)))

				m_02.append(str(round(move.total_operaciones_inafectas_dolar, 2)))
				m_02.append(str(round(move.total_operaciones_inafectas, 2)))

				if move.move_type in ['in_refund', 'out_refund']:
					m_02.append(str(abs(move.amount_tax) * -1))
					m_02.append(str(abs(move.amount_tax_signed) * -1))
					
					m_02.append(str(abs(move.amount_total) * -1))
					m_02.append(str(abs(move.amount_total_signed) * -1))

					m_02.append(str(move.reversed_entry_id.invoice_date.strftime("%d/%m//%Y")))
					m_02.append(str(move.reversed_entry_id.pe_invoice_code))
					m_02.append(str(move.reversed_entry_id.l10n_latam_document_number))

				else:
					m_02.append(str(abs(move.amount_tax)))
					m_02.append(str(abs(move.amount_tax_signed)))
					
					m_02.append(str(abs(move.amount_total)))
					m_02.append(str(abs(move.amount_total_signed)))
				
					m_02.append('')
					m_02.append('')
					m_02.append('')


			if m_02 :
				try :
					lines_to_write_02.append('|'.join(m_02))
				except Exception as e:
					raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_02))

		name_01 = "Reporte electrónicos"
		lines_to_write_01.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_01)

		name_02 = "Reporte electrónicos (SUNAT)"
		lines_to_write_02.append('')
		txt_string_02 = '\r\n'.join(lines_to_write_02)


		dict_to_write = dict()

		if txt_string_01 :
			headers = [
				'Número de comprobante',
				'Monto Total',
				'Monto sin IGV',
				'IGV',
				'Estado Sunat',
				'Nombre de contacto - Cliente',
				'Número de RUC / DNI',
				'Fecha de factura / Recibo',
				'Sucursal',
				'Estado',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=headers)
			dict_to_write.update({
				'reporte_binary': xlsx_file_base_64.encode(),
				'reporte_nombre': name_01 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'reporte_binary': False,
				'reporte_nombre': False,
			})

		if txt_string_02 :
			headers = [
				'Fecha',
				'Serie',
				'Número',
				'Tipo de Doc.',
				'RUC/DNI',
				'Cliente',
				'Moneda',
				'Tasa Cambio',
				'Op. Gravada',
				'Op. Gravada PEN',
				'Op. Exonerada',
				'Op. Exonerada PEN',
				'Op. Inafecta',
				'Op. Inafecta PEN',
				'Impuesto',
				'Impuesto PEN',
				'Total',
				'Total PEN',
				'Fecha',
				'Tipo',
				'Num. Ref.',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_02, name_02[2:], headers=headers)
			dict_to_write.update({
				'reporte_sunat_binary': xlsx_file_base_64.encode(),
				'reporte_sunat_nombre': name_02 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'reporte_sunat_binary': False,
				'reporte_sunat_nombre': False,
			})

		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res

	def _generate_xlsx_base64_bytes(self, txt_string, sheet_name, headers=[], custom_format_dict=dict()) :
		xlsx_file = BytesIO()
		xlsx_writer = pandas.ExcelWriter(xlsx_file, engine='xlsxwriter')
		df = pandas.read_csv(StringIO(txt_string), sep='|', header=None, dtype=str)
		df.to_excel(xlsx_writer, sheet_name, startrow=1, index=False, header=False)
		workbook  = xlsx_writer.book
		worksheet = xlsx_writer.sheets[sheet_name]
		format_dict = {k:workbook.add_format(v) for k,v in DEFAULT_FORMAT_DICT.items()}
		if custom_format_dict and isinstance(custom_format_dict, dict()) :
			for custom_format, custom_format_value in custom_format_dict.items() :
				format_dict.update({
					custom_format: workbook.add_format(custom_format_value),
				})
		len_headers = 0
		if headers and isinstance(headers, list) :
			len_headers = len(headers)
		for col_num, value in enumerate(df.columns.values) :
			col_name = number_to_ascii_chr(col_num)
			header_text = str(value)
			col_format = 'text_format'
			if len_headers :
				if col_num < len_headers :
					csv_file = headers[col_num]
					#csv_file = 'Header' or {'header_text': 'Header', 'col_format': 'format_name'}
					if not isinstance(csv_file, dict) :
						csv_file = {'header_text': str(csv_file)}
					if 'header_text' in csv_file :
						header_text = str(csv_file.get('header_text'))
					if 'col_format' in csv_file :
						col_format = str(csv_file.get('col_format'))
			if col_format not in format_dict :
				col_format = 'text_format'
			col_format = format_dict.get(col_format)
			csv_file = worksheet.write(0, col_num, header_text, format_dict.get('header_format'))
			csv_file = worksheet.set_column(':'.join([col_name, col_name]), max(25, len(header_text) // 2), col_format)
		xlsx_writer.save()
		xlsx_file_value = base64.b64encode(xlsx_file.getvalue()).decode()
		return xlsx_file_value

	# Tarea programada para enviar reporte de comprobantes
	def tp_enviar_reporte_comprobantes(self):
		current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		fecha = datetime.datetime.now()
		start = datetime.date(fecha.year, int(fecha.month), 1)
		end = get_last_day(start)

		empresas = self.env['res.company'].sudo().search([])
		for empresa in empresas:
			contactos = False
			servidor = self.env['cpe.server'].search([('company_id', '=', empresa.id),('state', '=', 'done')])
			for reg in servidor:
				for contacto in reg.partner_ids:
					if not contactos:
						contactos = []
					contactos.append(contacto.id)

			if not contactos:
				continue
			registro = self.env['solse.pe.cpe.report'].search([('company_id', '=', empresa.id), ('fecha_inicio', '=', start), ('fecha_fin', '=', end)], limit=1)
			if not registro:
				paramtros_busqueda = {
					'name': 'Reporte de comprobantes',
					'company_id': empresa.id,
					'reporte_nombre': 'Reporte comprobantes',
					'fecha_inicio': str(start),
					'fecha_fin': str(end),
					'partner_id': [(6, 0, contactos)],
				}
				registro = self.env['solse.pe.cpe.report'].create(paramtros_busqueda)
			else:
				registro.write({
					'company_id': empresa.id,
					'fecha_inicio': str(start),
					'fecha_fin': str(end),
					'partner_id': [(6, 0, contactos)],
				})

			registro.generate_report()
			registro.enviar_mensaje()

	# Tarea programada para enviar reporte de comprobantes con error de sunat
	def tp_enviar_reporte_comprobantes_con_error(self):
		current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		fecha = datetime.datetime.now()
		start = datetime.date(fecha.year, int(fecha.month), 1)

		empresas = self.env['res.company'].sudo().search([])
		for empresa in empresas:
			contactos = False
			servidor = self.env['cpe.server'].sudo().search([('company_id', '=', empresa.id), ('state', '=', 'done')])
			for reg in servidor:
				for contacto in reg.partner_errror_ids:
					if not contactos:
						contactos = []
					contactos.append(contacto.id)

			if not contactos:
				continue

			registro = self.env['solse.pe.cpe.report'].sudo().search([('company_id', '=', empresa.id), ('es_de_alerta', '=', True)], limit=1)
			if not registro:
				paramtros_busqueda = {
					'es_de_alerta': True,
					'name': 'Reporte de comprobantes con Error',
					'company_id': empresa.id,
					'reporte_nombre': 'Reporte de comprobantes con Error',
					'fecha_inicio': str(start),
					'fecha_fin': str(start),
					'partner_id': [(6, 0, contactos)],
				}
				registro = self.env['solse.pe.cpe.report'].create(paramtros_busqueda)
			else:
				registro.write({
					'es_de_alerta': True,
					'company_id': empresa.id,
					'fecha_inicio': str(start),
					'fecha_fin': str(start),
					'partner_id': [(6, 0, contactos)],
				})

			registro.generate_report()
			registro.enviar_mensaje()

	def enviar_mensaje(self):
		if not self.factura_ids:
			return

		if not self.partner_id:
			return

		destinos = []
		for contacto in self.partner_id:
			if not contacto.email:
				continue

			destinos.append(contacto.email)

		if len(destinos) == 0:
			return
		
		account_mail = self.obtener_datos_correo()
		context = account_mail.get('context')
		if not context:
			return
		template_id = account_mail['context'].get('default_template_id')
		if not template_id:
			return
		attachment_ids = []
		if context.get('default_attachment_ids', False):
			for attach in context.get('default_attachment_ids'):
				attachment_ids += attach[2]

		mail_id = self.env['mail.template'].browse(template_id)
		motivo = "%s: Resumen cpe's emitidos" % self.company_id.partner_id.name
		if self.es_de_alerta:
			motivo = "%s: Lista cpe's con error de envió" % self.company_id.partner_id.name

		email_values = {
			'email_to': ','.join(destinos),
			'attachment_ids': attachment_ids,
			'subject': motivo,
		}
		mail_id.send_mail((self.id), force_send=True, email_values=email_values)

	def obtener_archivos_cpe(self):
		attachment_ids = []
		Attachment = self.env['ir.attachment']
		attach = {}
		attach['name'] = self.reporte_nombre
		attach['type'] = 'binary'
		attach['datas'] = self.reporte_binary
		attach['res_model'] = 'mail.compose.message'
		attachment_id = self.env['ir.attachment'].create(attach)
		attachment_ids = []
		attachment_ids.append(attachment_id.id)
			
		return attachment_ids

	def obtener_datos_correo(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			#template_id = ir_model_data.get_object_reference('solse_pe_cpe_report', 'cpe_envio_estado_email')[1]
			template_id = self.env.ref('solse_pe_cpe_report.cpe_envio_estado_email').id
		except ValueError:
			template_id = False
		try:
			#compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
			compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
		except ValueError:
			compose_form_id = False

		attachment_ids = self.obtener_archivos_cpe()

		ctx = {
			'default_model': 'solse.pe.cpe.report',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'default_attachment_ids': [(6, 0, attachment_ids)],
			#'custom_layout': "sale.mail_template_data_notification_email_sale_order",
			'force_email': True
		}
		return {
			'type': 'ir.actions.act_window',
			#'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}


