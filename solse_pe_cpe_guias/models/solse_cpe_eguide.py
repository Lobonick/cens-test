# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api
from .eguide import get_document, get_sign_document, send_sunat_eguide, get_response, get_ticket_status, get_status_cdr
from base64 import b64decode, b64encode
from lxml import etree
from datetime import datetime
from odoo.exceptions import UserError

import logging
_logging = logging.getLogger(__name__)


class CPESunatEguide(models.Model):
	_name = 'solse.cpe.eguide'
	_description = 'Guia Electronica'

	name = fields.Char("Numero", readonly=True, default="/")
	state = fields.Selection([
		('draft', 'Borrador'),
		('generate', 'Generado'),
		('send', 'Enviado'),
		('verify', 'Esperando'),
		('done', 'Hecho'),
		('cancel', 'Cancelado'),
	], string='Status', index=True, readonly=False, default='draft',
		track_visibility='always', copy=False)
	type = fields.Selection([
		('sync', 'Envio online'),
		('low', 'Comunicación de baja'),
	], string="Tipo", default='sync', states={'draft': [('readonly', False)]})
	date = fields.Date("Fecha", default=fields.Date.context_today, states={
					   'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', string='Company', change_default=True,
								 required=True, readonly=True, states={'draft': [('readonly', False)]},
								 default=lambda self: self.env['res.company']._company_default_get('pe.eguide'))
	xml_document = fields.Text("Documento XML")
	datas = fields.Binary("Datos XML", readonly=True)
	datas_fname = fields.Char("Nombre de archivo XML", readonly=True)
	datas_sign = fields.Binary("XML firmado", readonly=True)
	datas_sign_fname = fields.Char("Nombre de archivo firmado XML", readonly=True)
	datas_zip = fields.Binary("Datos Zip XML", readonly=True)
	datas_zip_fname = fields.Char("Nombre de archivo zip XML", readonly=True)
	datas_response = fields.Binary("Datos de respuesta XML", readonly=True)
	datas_response_fname = fields.Char("Nombre de archivo de respuesta XML", readonly=True)
	response = fields.Char("Respuesta", readonly=True)
	response_code = fields.Char("Código de respuesta", readonly=True)
	note = fields.Text("Nota", readonly=True)
	error_code = fields.Selection(
		"_get_error_code", string="Código de error", readonly=True)
	digest = fields.Char("Codigo", readonly=True)
	signature = fields.Text("Firma", readonly=True)
	ticket = fields.Char("Ticket")
	date_end = fields.Datetime("Fecha final")
	send_date = fields.Datetime("Fecha de envio")
	voided_ids = fields.One2many("stock.picking", "pe_voided_id", string="Guía cancelada")
	picking_ids = fields.One2many("stock.picking", "pe_guide_id", string="Guía")

	_order = 'name, date'

	@api.model
	def _get_error_code(self):
		return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

	def action_draft(self):
		self.state = 'draft'

	def action_generate(self):
		if not self.xml_document and self.type == "sync":
			self._prepare_eguide()
			self._sign_eguide()
		# else:
		#    self._sign_eguide()
		self.state = 'generate'

	def action_send(self):
		state = self.send_eguide()
		self.state = state

	def action_verify(self):
		self.state = 'verify'

	def action_done(self):
		if self.ticket:
			status = self.get_sunat_ticket_status()
			if status:
				self.state = status
		else:
			self.state = 'done'

	def action_cancel(self):
		self.state = 'cancel'

	@api.model
	def create_from_stock(self, picking_id):
		vals = {}
		vals['picking_ids'] = [(4, picking_id.id)]
		vals['type'] = 'sync'
		vals['company_id'] = picking_id.company_id.id
		res = self.create(vals)
		return res

	@api.model
	def get_eguide_async(self, type, picking_id):
		res = None
		eguide_id = self.search([('state', '=', 'draft'), ('type', '=', type), ('date', '=', picking_id.pe_date_issue),
								 ('name', '=', "/"), ('company_id', '=', picking_id.company_id.id)], limit=1, order="date DESC")
		if eguide_id:
			res = eguide_id
		else:
			vals = {}
			vals['type'] = type
			vals['company_id'] = picking_id.company_id.id
			vals['date'] = picking_id.pe_date_issue
			res = self.create(vals)
		return res

	@api.model
	def get_document_name(self):
		self.ensure_one()
		ruc = self.company_id.partner_id.doc_number
		if self.type == "sync":
			doc_code = "-%s" % "09"
			number = self.picking_ids[0].pe_guide_number
		else:
			doc_code = "-%s" % "09"
			number = self.name
		return "%s%s-%s" % (ruc, doc_code, number)

	@api.model
	def prepare_sunat_auth(self):
		self.ensure_one()
		res = {}
		res['ruc'] = self.company_id.partner_id.doc_number
		res['username'] = self.company_id.pe_cpe_eguide_server_id.user
		res['password'] = self.company_id.pe_cpe_eguide_server_id.password
		res['client_id'] = self.company_id.pe_cpe_eguide_server_id.client_id
		res['client_secret'] = self.company_id.pe_cpe_eguide_server_id.client_secret
		return res

	@api.model
	def _prepare_eguide(self):
		if not self.xml_document and self.type != "low":
			file_name = self.get_document_name()
			xml_document = get_document(self)
			self.xml_document = xml_document
			self.datas = b64encode(xml_document)
			self.datas_fname = file_name+".xml"

	def _sign_eguide(self):
		file_name = self.get_document_name()
		if not self.xml_document:
			self._prepare_eguide()
		elif self.xml_document.encode('utf-8') != b64decode(self.datas):
			self.datas = b64encode(self.xml_document.encode('utf-8'))
		key = self.company_id.pe_certificate_id.key
		crt = self.company_id.pe_certificate_id.crt
		self.datas_sign = b64encode(
			get_sign_document(self.xml_document, key, crt))
		self.datas_sign_fname = file_name+".xml"
		self.get_sign_details()

	# Enviar guía electronica
	def send_eguide(self):
		self.ensure_one()
		file_name = self.get_document_name()
		record = self.with_context(tz=self.env.user.tz)
		#self.send_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(record, datetime.now()))
		self.send_date = fields.Datetime.to_string(datetime.now())
		if self.name == "/" and self.type != "low":
			self.name = self.picking_ids[0].pe_guide_number
		else:
			if self.name == "/":
				self.name = self.env['ir.sequence'].next_by_code('pe.eguide.cancel')
			file_name = self.get_document_name()
			xml_document = get_document(self)
			self.xml_document = xml_document
			self.datas = b64encode(xml_document)
			self.datas_fname = file_name+".xml"
			self._sign_eguide()
		if self.xml_document.encode('utf-8') != b64decode(self.datas):
			self._sign_eguide()

		client = self.prepare_sunat_auth()
		document = {}
		document['document_name'] = file_name
		document['type'] = self.type
		document['xml'] = b64decode(self.datas_sign)
		self.datas_zip, response_status, response, response_data = send_sunat_eguide(
			client, document)
		self.datas_zip_fname = file_name+".zip"
		if response_status:
			self.ticket = response_data
			state = "verify"
		else:
			state = "send"
		return state


	def send_eguide_anterior(self):
		self.ensure_one()
		file_name = self.get_document_name()
		record = self.with_context(tz=self.env.user.tz)
		#self.send_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(record, datetime.now()))
		self.send_date = fields.Datetime.to_string(datetime.now())
		if self.name == "/" and self.type != "low":
			self.name = self.picking_ids[0].pe_guide_number
		else:
			if self.name == "/":
				self.name = self.env['ir.sequence'].next_by_code(
					'pe.eguide.cancel')
			file_name = self.get_document_name()
			xml_document = get_document(self)
			self.xml_document = xml_document
			self.datas = b64encode(xml_document)
			self.datas_fname = file_name+".xml"
			self._sign_eguide()
		if self.xml_document.encode('utf-8') != b64decode(self.datas):
			self._sign_eguide()

		client = self.prepare_sunat_auth()
		document = {}
		document['document_name'] = file_name
		document['type'] = self.type
		document['xml'] = b64decode(self.datas_sign)
		self.datas_zip, response_status, response, response_data = send_sunat_eguide(
			client, document)
		self.datas_zip_fname = file_name+".zip"
		res = None
		if response_status:
			res = "verify"
			if self.type == "sync":
				self.datas_response = response_data
				new_state = self.get_response_details()
				self.datas_response_fname = 'R-%s.zip' % file_name
				res = new_state or res
			else:
				self.ticket = response_data
		else:
			res = "send"
			if 'faultcode' not in response:
				raise UserError('No se pudo obtener una respuesta')
			self.response = response.get("faultcode")
			self.note = response.get("faultstring")
			if not response.get("faultcode"):
				code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
					response.get("faultcode").split(".")[-1].encode('utf-8')) or False
				self.response_code = code
			#self.error_code= code
		return res

	@api.model
	def get_sign_details(self):
		self.ensure_one()
		vals = {}
		tag = etree.QName('http://www.w3.org/2000/09/xmldsig#', 'DigestValue')
		xml_sign = b64decode(self.datas_sign)
		digest = etree.fromstring(xml_sign).find('.//'+tag.text)
		if digest != -1:
			self.digest = digest.text
		tag = etree.QName(
			'http://www.w3.org/2000/09/xmldsig#', 'SignatureValue')
		sign = etree.fromstring(xml_sign).find('.//'+tag.text)
		if sign != -1:
			self.signature = sign.text

	@api.model
	@api.depends('datas_response')
	def get_response_details(self):
		self.ensure_one()
		vals = {}
		state = None
		return state

	def generate_eguide(self):
		self._prepare_eguide()
		self._sign_eguide()
		self.state = "generate"

	@api.model
	def get_sunat_ticket_status(self):
		self.ensure_one()
		client = self.prepare_sunat_auth()
		response_status, response, response_file = get_ticket_status(self.ticket, client)
		state = None
		if response_status in ['99', '0', '00']:
			file_name = self.get_document_name()
			self.datas_response = response_file
			self.datas_response_fname = 'R-%s.zip' % file_name
			state = "done"
			if response_status == '99':
				self.response = response["error"]["desError"]
				self.note = response["error"]["desError"]
				try:
					self.error_code = response["error"]["numError"]

				except:
					self.response = response["error"]["desError"]
			else:
				self.response = 'OK'

		return state
		

	def action_document_status(self):
		pass