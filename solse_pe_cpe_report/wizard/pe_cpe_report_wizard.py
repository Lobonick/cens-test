# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
import base64, zipfile
from io import StringIO, BytesIO
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class ValidateAccountMove(models.TransientModel):
	_name = "solse.pe.cpe.report.wizard"
	_description = "Generar archivo con los CPE's"

	diario_pago = fields.Many2one('account.journal', 'Diario de pago', domain=[('type', 'in', ['bank'])])
	name = fields.Char('Nombre de lote')
	datas_zip_fname = fields.Char("Nombre de archivo zip",  readonly=True)
	datas_zip = fields.Binary("Datos Zip", readonly=True)
	
	def generar_archivo(self):
		facturas = self.env['account.move'].browse(self._context.get('active_ids', []))
		in_memory_data = BytesIO()
		in_memory_zip = zipfile.ZipFile(in_memory_data, 'w', zipfile.ZIP_DEFLATED, False)

		Attachment = self.env['ir.attachment']
		#for reg in cpes:
		for factura in facturas:
			reg = factura.pe_cpe_id
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

		form_descarga = self.env["solse.pe.cpe.descargar"].search([], limit=1)
		datos_guardar = {
			"datas_zip_fname": "pdf_xml_cdr.zip",
			"datas_zip": self.datas_zip,
		}
		if not form_descarga:
			form_descarga = self.env["solse.pe.cpe.descargar"].create(datos_guardar)
		else:
			form_descarga.write(datos_guardar)

		action = self.env["ir.actions.actions"]._for_xml_id("solse_pe_cpe_report.action_scpe_descargar")
		form_view = [(self.env.ref('solse_pe_cpe_report.view_scpe_descargar_form').id, 'form')]
		if 'views' in action:
			action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
		else:
			action['views'] = form_view
		action['res_id'] = form_descarga.id
		action['context'] = {}
		return action
		
