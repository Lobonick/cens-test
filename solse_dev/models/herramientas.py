# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64, zipfile
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
import logging

_logging = logging.getLogger(__name__)

class SolseDevHerramientas(models.Model):
	_name = "sdev.herramientas"
	_description = "Herramientas (solse)"

	name = fields.Char('Nombre')

	datas_zip_fname = fields.Char("Nombre de archivo zip",  readonly=True)
	datas_zip = fields.Binary("Datos Zip", readonly=True)
	utl_fecha_ejecucion = fields.Datetime("Ultima Fecha ejecución")

	nombre_modelo_procesar = fields.Char("Nombre modelo")

	def borrar_datos_modelo(self):
		lista = self.env[self.nombre_modelo_procesar].sudo().search([('active', 'in', [False, True])]).ids
		for reg in lista:
			self.borrar_registro_modelo(reg)
			
	def borrar_registro_modelo(self, registro):
		#self.env[self.nombre_modelo_procesar].sudo().search([('id', '=', registro)]).with_context(force_delete=True).unlink()
		obj_name = self.nombre_modelo_procesar
		obj = self.pool.get(self.nombre_modelo_procesar)
		if not obj:
			t_name = obj_name.replace('.', '_')
		else:
			t_name = obj._table

		sql = "delete from %s where id = %s" % (t_name, registro)
		try:
			self._cr.execute(sql)
			self._cr.commit()
		except Exception as e:
			_logging.warning('remove data error: %s,%s', obj_name, e)


	def llenar_direccion_usando_ubigeo(self):
		pacientes = self.env['res.partner'].search([])
		for reg in pacientes:
			if reg.zip:
				district = self.env['l10n_pe.res.city.district'].search([('code', '=', reg.zip)], limit=1)
				reg.l10n_pe_district = district.id
				reg.city_id = district.city_id.id
				reg.state_id = district.city_id.state_id.id
				reg.country_id = district.city_id.state_id.country_id.id

	def llenar_vat_con_doc_number(self):
		pacientes = self.env['res.partner'].search([])
		for reg in pacientes:
			if not reg.doc_number:
				continue
			reg.vat = reg.doc_number

	def llenar_doc_number_con_doc_vat(self):
		pacientes = self.env['res.partner'].search([])
		for reg in pacientes:
			if not reg.vat:
				continue
			reg.doc_number = reg.vat

	def buscar_con_doc_number(self):
		pacientes = self.env['res.partner'].search([])
		for reg in pacientes:
			if not reg.l10n_pe_district and reg.doc_number:
				reg.update_document()

	def borrar_pagos(self):
		self.env['account.payment'].search([]).action_draft()
		self.env['account.payment'].search([]).unlink()

	def borrar_supplierinfo(self):
		self.env['product.supplierinfo'].search([]).unlink()

	def borrar_pagos_pos(self):
		self.env['pos.payment'].search([]).unlink()

	def borrar_notas_credito(self):
		notas_credito = self.env['account.move'].search([('move_type', '=', 'out_refund')])
		notas_credito.write({'state': 'draft', 'name': '/'})
		lineas = notas_credito.line_ids

		self.env['account.partial.reconcile'].search([('credit_move_id', 'in', lineas.ids)]).unlink()
		self.env['account.analytic.line'].search([('move_id', 'in', lineas.ids)]).unlink()

		self.env['account.move'].search([('move_type', '=', 'out_refund')]).with_context(force_delete=True).unlink()

	def borrar_facturas(self):
		self.env['account.move'].search([('move_type', '!=', 'entry')]).write({'state': 'draft', 'name': '/'})
		self.env['account.partial.reconcile'].search([]).unlink()
		self.env['account.analytic.line'].search([]).unlink()
		self.env['account.move'].search([]).with_context(force_delete=True).unlink()
		#self.env['account.journal'].search([]).write({'sequence_number_next': 1})

	def borrar_cpe(self):
		self.env['solse.cpe'].search([]).write({'state': 'draft'})
		self.env['solse.cpe'].search([]).unlink()

	def borrar_inventarios(self):
		self.env['stock.move'].search([]).write({'state': 'draft'})
		self.env['stock.move'].search([]).unlink()
		self.env['stock.picking'].search([]).write({'state': 'draft'})
		self.env['stock.picking'].search([]).unlink()
		self.env['stock.quant'].search([]).unlink()
		self.env['stock.valuation.layer'].search([]).unlink()
		self.env['stock.inventory'].search([]).action_cancel_draft()
		self.env['stock.inventory'].search([]).unlink()

	def borrar_ventas(self):
		self.env['sale.order'].search([]).write({'state': 'draft'})
		self.env['sale.order'].search([]).unlink()

	def borrar_ventas_pos(self):
		self.env['pos.order'].search([]).write({'state': 'draft'})
		self.env['pos.order'].search([]).unlink()

	def borrar_compras(self):
		self.env['purchase.order'].search([]).write({'state': 'cancel'})
		self.env['purchase.order'].search([]).unlink()

	def borrar_datos_crm(self):
		self.env['crm.lead'].search([]).unlink()

	def borrar_producciones(self):
		self.env['mrp.workorder'].search([]).unlink()
		lista = self.env['mrp.production'].search([('state', '=', 'draft')]).unlink()
		lista = self.env['mrp.production'].search([('state', '=', 'cancel')]).unlink()
		#for reg in lista:
		#	reg.unlink()
		#self.env['mrp.production'].search([('state', '!=', 'done')]).action_cancel()
		#self.env['mrp.production'].search([('state', '!=', 'done')]).unlink()

	def aplicar_estados_importacion(self):
		facturas = self.env["account.move"].search([("estado_temp", "!=", False)])
		for reg in facturas:
			reg.state = reg.estado_temp
			reg.estado_temp = False

	def aplicar_estados_guias_importacion(self):
		facturas = self.env["stock.picking"].search([("estado_temp", "!=", False)], limit=250)
		for reg in facturas:
			estado_temporal = reg.estado_temp
			if reg.state not in ['draft']:
				reg.estado_temp = False
			elif reg.estado_temp == 'done':
				try:
					reg.button_validate()
					reg.estado_temp = False
				except Exception as msg_error:
					reg.estado_temp = estado_temporal
					_logging.info(msg_error)
			else:
				reg.state = reg.estado_temp
				reg.estado_temp = False

	def aplicar_pagos_factura(self):
		pagos = self.env['sdev.facturas.pago'].search([('factura_ids', '!=', False)], limit=10)
		for reg in pagos:
			try:
				pmt_wizard = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=reg.factura_ids.ids).create({
					'payment_date': reg.payment_date,
					'journal_id': reg.journal_id.id,
					'payment_method_id': reg.payment_method_id.id,
					'amount': reg.amount,
					'currency_id': reg.currency_id.id,
					'partner_id': reg.partner_id.id,
					'communication': reg.communication
				})
				pmt_wizard._create_payments()
				reg.factura_ids.write({
					'pago_id': False
				})
			except Exception as msg_error:
				_logging.info(msg_error)
			

	def aplicar_notas_credito(self):
		notas_credito = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted')])
		for nota in notas_credito:
			pay_term_lines = nota.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
			domain = [
				('move_id', '=', nota.reversed_entry_id.id),
				('account_id', 'in', pay_term_lines.account_id.ids),
				('move_id.state', '=', 'posted'),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]
			if nota.is_inbound():
				domain.append(('balance', '<', 0.0))
			else:
				domain.append(('balance', '>', 0.0))
			linea_factura = self.env['account.move.line'].search(domain)
			if pay_term_lines and linea_factura:
				lines = pay_term_lines + linea_factura
				lines.reconcile()

	def aplicar_tipo_operacion_facturas(self):
		facturas = self.env['account.move'].search([('invoice_picking_id', '!=', False), ('picking_type_id', '=', False)])
		for reg in facturas:
			reg.picking_type_id = reg.invoice_picking_id.picking_type_id.id

	def aplicar_notas_credito_2(self):
		notas_credito = self.env['account.move'].search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('payment_state', '!=', 'paid')])
		for nota in notas_credito:
			pay_term_lines = nota.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
			domain = [
				('account_id', 'in', pay_term_lines.account_id.ids),
				('move_id.state', '=', 'posted'),
				('partner_id', '=', nota.commercial_partner_id.id),
				('reconciled', '=', False),
				'|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
			]
			if nota.is_inbound():
				domain.append(('balance', '<', 0.0))
			else:
				domain.append(('balance', '>', 0.0))
			linea_factura = self.env['account.move.line'].search(domain)
			if pay_term_lines and linea_factura:
				lines = pay_term_lines + linea_factura
				lines.reconcile()

	# retorna el json con los datos necesarios para la accion "descargar_datos_cpe"
	def obtener_datos_cpe(self):
		in_memory_data = BytesIO()
		in_memory_zip = zipfile.ZipFile(in_memory_data, 'w', zipfile.ZIP_DEFLATED, False)

		cpes = self.env['solse.cpe'].search([])
		Attachment = self.env['ir.attachment']
		for reg in cpes:
			if reg.datas_sign_fname:
				_document_name = reg.datas_sign_fname
				filecontent = base64.b64decode(reg.datas_sign)
				in_memory_zip.writestr(_document_name, filecontent)
			if reg.datas_response_fname:
				_document_name = reg.datas_response_fname
				filecontent = base64.b64decode(reg.datas_response)
				in_memory_zip.writestr(_document_name, filecontent)

			if reg.type == 'sync':
				nombre = '%s.pdf' % reg.get_document_name()
				factura = self.env['account.move'].search([('pe_cpe_id', '=', reg.id)], limit=1)
				pdf = Attachment.search([('res_id', '=', factura.id), ('name', 'like', nombre + '%')], limit=1)
				if pdf:
					filecontent = base64.b64decode(pdf.datas)
					in_memory_zip.writestr(nombre, filecontent)
				"""else:
					result_pdf, type = self.env['ir.actions.report']._get_report_from_name('account.report_invoice')._render_qweb_pdf(factura.ids)
					result_pdf = base64.encodestring(result_pdf)
					filecontent = base64.b64decode(result_pdf)
					in_memory_zip.writestr(nombre, filecontent)"""

		for zfile in in_memory_zip.filelist:
			zfile.create_system = 0
		in_memory_zip.close()

		self.datas_zip = base64.b64encode(in_memory_data.getvalue())
		self.datas_zip_fname = "pdf_xml_cdr.zip"

	def completar_pdf_faltantes(self):
		Attachment = self.env['ir.attachment']
		facturas = self.env['account.move'].search([('is_cpe', '=', True)])
		for reg in facturas:
			if not reg.pe_cpe_id:
				continue
			nombre = '%s.pdf' % reg.pe_cpe_id.get_document_name()
			pdf = Attachment.search([('res_id', '=', reg.id), ('name', 'like', nombre + '%')], limit=1)
			if not pdf:
				attach = {}
				result_pdf, type = self.env['ir.actions.report']._get_report_from_name('account.report_invoice')._render_qweb_pdf(reg.ids)
				attach['name'] = nombre
				attach['type'] = 'binary'
				attach['datas'] = base64.encodestring(result_pdf)
				attach['res_model'] = 'mail.compose.message'
				attachment_id = self.env['ir.attachment'].create(attach)
		self.utl_fecha_ejecucion = fields.Datetime.to_string(datetime.now())