# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, Warning, ValidationError
import tempfile
import base64
import re
from datetime import datetime, date, timedelta
from odoo.tools.misc import formatLang
from io import StringIO, BytesIO
from collections import defaultdict
from importlib import reload
import xml.etree.cElementTree as ET
from lxml import etree
import json
import sys
import time

import logging
_logging = logging.getLogger(__name__)

def encodestring(datos):
	respuesta = datos
	if not respuesta:
		return respuesta
	if sys.version_info >= (3, 9):
		respuesta = base64.b64encode(datos)
	else:
		respuesta = base64.encodestring(datos)

	return respuesta

class AccountMoveReversal(models.TransientModel):
	_inherit = 'account.move.reversal'

	l10n_pe_edi_refund_reason = fields.Selection(selection_add=[('13', 'Ajustes - montos y/o fechas de pago'), ], ondelete={'13': 'cascade'})


class AccountMove(models.Model):
	_inherit = 'account.move'

	def obtener_archivos_cpe(self):
		attachment_ids = []
		Attachment = self.env['ir.attachment']
		if self.l10n_latam_document_type_id.is_cpe and self.pe_cpe_id:
			if self.pe_cpe_id.datas_sign_fname:
				arc_n1 = Attachment.search([('res_id', '=', self.id), ('name', 'like', self.pe_cpe_id.datas_sign_fname + '%')], limit=1)
				if not arc_n1:
					attach = {}
					attach['name'] = self.pe_cpe_id.datas_sign_fname
					attach['type'] = 'binary'
					attach['datas'] = self.pe_cpe_id.datas_sign
					attach['res_model'] = 'mail.compose.message'
					attachment_id = self.env['ir.attachment'].create(attach)
					attachment_ids = []
					attachment_ids.append(attachment_id.id)
				else:
					attachment_ids.append(arc_n1.id)
			nombre = '%s.pdf' % self.pe_cpe_id.get_document_name()
			arc_n2 = Attachment.search([('res_id', '=', self.id), ('name', 'like', nombre + '%')], limit=1)
			if not arc_n2:
				attach = {}
				result_pdf, type = self.env['ir.actions.report']._get_report_from_name('solse_pe_cpe_e.report_cpe_copy_1')._render_qweb_pdf('solse_pe_cpe_e.report_cpe_copy_1', res_ids=self.ids)
				attach['name'] = '%s.pdf' % self.pe_cpe_id.get_document_name()
				attach['type'] = 'binary'
				attach['datas'] = encodestring(result_pdf)
				attach['res_model'] = 'mail.compose.message'
				attachment_id = self.env['ir.attachment'].create(attach)
				attachment_ids.append(attachment_id.id)
			else:
				attachment_ids.append(arc_n2.id)

			if self.pe_cpe_id.datas_response_fname:
				arc_n3 = Attachment.search([('res_id', '=', self.id), ('name', 'like', self.pe_cpe_id.datas_response_fname + '%')], limit=1)
				if not arc_n3:
					attach = {}
					attach['name'] = self.pe_cpe_id.datas_response_fname
					attach['type'] = 'binary'
					attach['datas'] = self.pe_cpe_id.datas_response
					attach['res_model'] = 'mail.compose.message'
					attachment_id = self.env['ir.attachment'].create(attach)
					attachment_ids.append(attachment_id.id)
				else:
					attachment_ids.append(arc_n3.id)

		return attachment_ids


	# metodo usado desde la busqueda de la web que usas los clientes para revisar las facturas que se les han emitido
	def get_public_cpe(self):
		self.ensure_one()
		res = {}
		if self.l10n_latam_document_type_id.is_cpe:
			if self.pe_cpe_id:
				temporal = self.env['ir.actions.report']._get_report_from_name('solse_pe_cpe_e.report_cpe_copy_1')
				result_pdf, type = temporal._render_qweb_pdf('solse_pe_cpe_e.report_cpe_copy_1', res_ids=self.ids)
				res['datas_sign'] = str(self.pe_cpe_id.datas_sign, 'utf-8')
				res['datas_invoice'] = str(encodestring(result_pdf), 'utf-8')
				res['name'] = self.pe_cpe_id.get_document_name()

		return res