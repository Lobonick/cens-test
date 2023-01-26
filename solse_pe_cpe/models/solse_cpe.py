# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from .cpe_core import get_sign_document, send_sunat_cpe, get_ticket_status, get_response, get_status_cdr
from base64 import b64decode, b64encode
from lxml import etree
from datetime import datetime
from odoo.exceptions import Warning, UserError
import pytz
import logging
from .cpe_xml import CPE

_logging = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

#obtiene el xml de acuerdo al tipo de documento
def get_document(self):
	xml = None
	if self.type == 'sync':
		if self.invoice_ids[0].pe_invoice_code == '08':
			xml = CPE().getDebitNote(self.invoice_ids[0])
		elif self.invoice_ids[0].pe_invoice_code == '07':
			xml = CPE().getCreditNote(self.invoice_ids[0])
		else:
			xml = CPE().getInvoice(self.invoice_ids[0])
	else:
		if self.type == 'rc':
			xml = CPE().getSummaryDocuments(self)
		elif self.type == 'ra':
			xml = CPE().getVoidedDocuments(self)
	return xml

class PeruSunatCpe(models.Model):
	_name = 'solse.cpe'
	_description = 'Sunat Perú'

	name = fields.Char("Name", default="/")
	state = fields.Selection([
		('draft', 'Borrador'),
		('generate', 'Generado'),
		('send', 'Enviado'),
		('verify', 'Esperando'),
		('done', 'Hecho'),
		('cancel', 'Cancelado'),
	], string='Estado', index=True, readonly=True, default='draft', track_visibility='onchange', copy=False)
	type = fields.Selection([
		('sync', 'Envio online'),
		('rc', 'Resumen diario'),
		('ra', 'Comunicación de Baja'),
	], string="Tipo", default='sync', states={'draft': [('readonly', False)]})
	estado_sunat = fields.Selection([
		('01', 'Registrado'),
		('03', 'Enviado'),
		('05', 'Aceptado'),
		('07', 'Observado'),
		('09', 'Rechazado'),
		('11', 'Anulado'),
		('13', 'Por anular'),
	], string='Estado Sunat', default='01')
	
	date = fields.Date("Fecha", default=fields.Date.context_today, states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', string='Empresa', change_default=True, required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('pe.sunat.cpe'))
	xml_document = fields.Text("Documento XML", states={'draft': [('readonly', False)]})
	datas = fields.Binary("Datos XML", readonly=True)
	datas_fname = fields.Char("Nombre de archivo XML",  readonly=True)
	datas_sign = fields.Binary("Datos firmado XML",  readonly=True)
	datas_sign_fname = fields.Char("Nombre de archivo firmado XML",  readonly=True)
	datas_zip = fields.Binary("Datos Zip XML", readonly=True)
	datas_zip_fname = fields.Char("Nombre de archivo zip XML",  readonly=True)
	datas_response = fields.Binary("Datos de respuesta XML",  readonly=True)
	datas_response_fname = fields.Char("Nombre de archivo de respuesta XML",  readonly=True)
	response = fields.Char("Respuesta", readonly=True)
	response_code = fields.Char("Código de respuesta", readonly=True)
	note = fields.Text("Nota", readonly=True)
	error_code = fields.Selection("_get_error_code", string="Código de error", readonly=True)
	digest = fields.Char("Codigo", readonly=True)
	signature = fields.Text("Firma", readonly=True)
	invoice_ids = fields.One2many("account.move", 'pe_cpe_id', string="Facturas", readonly=True)
	ticket = fields.Char("Ticket", readonly=True)
	date_end = fields.Datetime("Fecha final", states={'draft': [('readonly', False)]})
	send_date = fields.Datetime("Fecha de envio", states={'draft': [('readonly', False)]})
	#send_date_pe = fields.Datetime("Fecha de envio PE", states={'draft': [('readonly', False)]})
	voided_ids = fields.One2many("account.move", "pe_voided_id", string="Facturas anuladas")
	summary_ids = fields.One2many("account.move", "pe_summary_id", string="Resumen de comprobantes")
	is_voided = fields.Boolean("Está anulado")
	journal_id = fields.Many2one('account.journal', 'Diario')

	_order = 'date desc, name desc'

	def getEstadoSunatItem(self, code_sunat_p):
		rpt = '01'
		code_sunat = 0
		try:
			code_sunat = int(code_sunat_p)
		except:
			return '01'
		if code_sunat == 0:
			rpt = '11' if self.is_voided or self.type == 'ra' else '05'
		else:
			rpt = self.getEstadoSunat(code_sunat_p)
		return rpt

	def getEstadoSunat(self, code_sunat_p):
		rpt = '01'
		code_sunat = 0
		try:
			code_sunat = int(code_sunat_p)
		except:
			return '01'
		if code_sunat == 0:
			rpt = '05'
		elif code_sunat < 2000:
			rpt = '07'
		elif code_sunat < 4000:
			rpt = '09'
		else:
			rpt = '07'
		return rpt

	def unlink(self):
		for batch in self:
			if batch.name != "/" and batch.state not in ["draft", "generate"]:
				raise Warning(_('Solo puede eliminar los documentos que no han sido enviados.'))
		return super(PeruSunatCpe, self).unlink()

	@api.model
	def _get_error_code(self):
		return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

	def write(self, values) :
		res = super().write(values)
		for reg in self.summary_ids:
			reg.pe_cpe_id.estado_sunat = reg.pe_summary_id.estado_sunat
		return res

	# Opcion "Borrador"
	def action_draft(self):
		if not self.xml_document and self.type == "sync":
			self._prepare_cpe()
		self.state = 'draft'

	# Opcion "Generar"
	def action_generate(self):
		if not self.xml_document and self.type == "sync":
			self._prepare_cpe()
		elif self.type == "sync" and self.name != "/":
			if self.get_document_name() != self.name:
				self._prepare_cpe()
		if self.type == "sync":
			self._sign_cpe()
		self.state = 'generate'

	# Opcion "Enviar"
	def action_send(self):
		state = self.send_cpe()
		if state:
			self.state = state

	# Opcion "Esperar"
	def action_verify(self):
		self.state = 'verify'

	# Opcion "Hecho"
	def action_done(self):
		if self.type in ['rc', 'ra']:
			status = self.get_sunat_ticket_status()
			if status:
				self.state = status
		else:
			self.state = 'done'

	# Opcion "Cancelar"
	def action_cancel(self):
		self.state = 'cancel'

	# proceso para crear "solse.cpe", este proceso es llamado desde "account.move"
	@api.model
	def create_from_invoice(self, invoice_id):
		vals = {}
		vals['invoice_ids'] = [(4, invoice_id.id)]
		vals['type'] = 'sync'
		vals['journal_id'] = invoice_id.journal_id.id
		vals['company_id'] = invoice_id.company_id.id
		res = self.create(vals)
		return res

	@api.model
	def get_cpe_async(self, type, invoice_id, is_voided=False):
		res = None
		company_id = invoice_id.company_id.id
		date_invoice = invoice_id.invoice_date
		cpe_ids = self.search([('state', '=', 'draft'), ('type', '=', type), ('date', '=', date_invoice), ('name', '=', "/"), ('company_id', '=', company_id), ('is_voided', '=', is_voided)], order="date DESC")
		for cpe_id in cpe_ids:
			if cpe_id and len(cpe_id.summary_ids.ids) < 500:
				res = cpe_id
				break
		if not res:
			vals = {}
			vals['type'] = type
			vals['date'] = date_invoice
			vals['company_id'] = company_id
			vals['is_voided'] = is_voided
			res = self.create(vals)
		return res

	# obtener el nombre del registro, dependiendo si es comprobante individual o resumen su formato de nombre sera diferente
	def get_document_name(self):
		self.ensure_one()
		ruc = self.company_id.partner_id.doc_number
		if not self.invoice_ids and not self.voided_ids and not self.summary_ids:
			raise Warning('No se encontraron registros dentro del resumen')
		if self.type == "sync":
			doc_code = "-%s" % self.invoice_ids[0].l10n_latam_document_type_id.code
			if self.name and self.name != '/':
				number = self.name
			else:
				number = self.invoice_ids[0].l10n_latam_document_number
				self.name = number
		else:
			doc_code = ""
			number = self.name or ""
		return "%s%s-%s" % (ruc, doc_code, number)

	# obtiene datos para la peticion soap
	def prepare_sunat_auth(self):
		self.ensure_one()
		res = {}
		res['ruc'] = self.company_id.partner_id.doc_number
		res['username'] = self.company_id.pe_cpe_server_id.user
		res['password'] = self.company_id.pe_cpe_server_id.password
		res['url'] = self.company_id.pe_cpe_server_id.url
		return res

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

	# crear el xml
	def _prepare_cpe(self):
		if not self.xml_document:
			file_name = self.get_document_name()
			xml_document = get_document(self)
			self.xml_document = xml_document
			self.datas = b64encode(xml_document)
			self.datas_fname = file_name+".xml"

	# firmar el xml con el certificado digital
	def _sign_cpe(self):
		if not self.company_id.pe_certificate_id:
			raise UserError('No se ha establecido un Certificado digital. Revise la configuración de la empresa')
		file_name = self.get_document_name()
		if not self.xml_document:
			self._prepare_cpe()
		if self.xml_document.encode('utf-8') != b64decode(self.datas):
			self.datas = b64encode(self.xml_document.encode('utf-8'))
			#self.datas_fname = file_name+".xml"
		key = self.company_id.pe_certificate_id.key
		crt = self.company_id.pe_certificate_id.crt
		self.datas_sign = b64encode(get_sign_document(self.xml_document, key, crt))
		self.datas_sign_fname = file_name+".xml"
		self.get_sign_details()

	# proceso que lee el cdr de respuesta para obtener el mensaje y codigo de respuesta
	@api.depends('datas_response')
	def get_response_details(self):
		self.ensure_one()
		vals = {}
		state = self.state
		if not self.datas_response:
			return state
		try:
			file_name = self.get_document_name()
			xml_response = get_response({'file': self.datas_response, 'name': 'R-%s.%s' % (file_name, self.company_id.pe_cpe_server_id.extension_xml)})
			sunat_response = etree.fromstring(xml_response)
			cbc = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
			tag = etree.QName(cbc, 'ResponseDate')
			date = sunat_response.find('.//'+tag.text)
			tag = etree.QName(cbc, 'ResponseTime')
			time = sunat_response.find('.//'+tag.text)
			if time != -1 and date != -1:
				record = self.with_context(tz=self.env.user.tz)
				self.date_end = fields.Datetime.to_string(datetime.now())
			tag = etree.QName(cbc, 'ResponseCode')
			code = sunat_response.find('.//'+tag.text)
			res_code = ""
			if code != -1:
				res_code = "%04d" % int(code.text)
				self.response_code = res_code
				if res_code == "0000":
					self.error_code = False
					state = "done"
			tag = etree.QName(cbc, 'Description')
			description = sunat_response.find('.//'+tag.text)
			res_desc = ""
			if description != -1:
				res_desc = description.text
			self.response = "%s - %s" % (res_code, res_desc)
			self.estado_sunat = self.getEstadoSunat(res_code)
			notes = sunat_response.xpath(".//cbc:Note", namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
			res_note = ""
			for note in notes:
				res_note += note.text
			self.note = res_note

			estado_sunat_item = self.getEstadoSunatItem(res_code)
			if self.type == "ra":
				cpe_ids = self.voided_ids.mapped('pe_cpe_id').ids
				anuladas = self.search([('id', 'in', cpe_ids)])
				for reg in anuladas:
					reg.estado_sunat = estado_sunat_item
			elif self.type == "rc":
				cpe_ids = self.summary_ids.mapped('pe_cpe_id').ids
				resumen = self.search([('id', 'in', cpe_ids)])
				for reg in resumen:
					reg.estado_sunat = estado_sunat_item

		except Exception as e:
			print('******* ERROR ********')
			print(e)
			print('******* ERROR ********')
			pass
		return state

	# crear el xml y firmarlo
	def generate_cpe(self):
		self._prepare_cpe()
		self._sign_cpe()
		self.state = "generate"

	def validar_envio(self):

		return True


	# (@rpt) enviar cpe individual o resumen
	def send_cpe(self):
		res = None
		self.ensure_one()
		if not self.validar_envio():
			return False
		record = self.with_context(tz=self.env.user.tz)
		if not self.send_date:
			self.send_date = fields.Datetime.to_string(datetime.now())
		local_date = fields.Datetime.to_string(fields.Datetime.context_timestamp(record, self.send_date))
		local_date = datetime.strptime(str(local_date), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")

		if self.type == "sync" and self.name == "/":
			self.name = self.invoice_ids[0].number
		elif self.type == "ra" and self.name == "/":
			correlativo_anulacion = self.env['ir.sequence'].with_context(ir_sequence_date=local_date).next_by_code('pe.sunat.cpe.ra')
			if not correlativo_anulacion:
				raise UserError('No se encontro una secuencia para el resumen de baja')
			self.name = correlativo_anulacion
		elif self.type == "rc" and self.name == "/":
			correlativo_resumen = self.env['ir.sequence'].with_context(ir_sequence_date=local_date).next_by_code('pe.sunat.cpe.rc')
			if not correlativo_resumen:
				raise UserError('No se encontro una secuencia para el resumen')
			self.name = correlativo_resumen
		file_name = self.get_document_name()
		if self.type in ["rc", "ra"]:
			self._prepare_cpe()
			self._sign_cpe()
			self.datas_fname = file_name+".xml"
			self.datas_sign_fname = file_name+".xml"
		client = self.prepare_sunat_auth()
		document = {}
		document['document_name'] = file_name
		document['type'] = self.type
		document['xml'] = b64decode(self.datas_sign)
		self.datas_zip, response_status, response, response_data = send_sunat_cpe(client, document)
		self.datas_zip_fname = file_name+".zip"
		if response_status:
			res = "verify"
			if self.type == "sync":
				self.datas_response = response_data
				new_state = self.get_response_details()
				self.datas_response_fname = 'R-%s.zip' % file_name
				res = new_state or res
			else:
				self.ticket = response_data
				self.estado_sunat = '03'

			# Actualizamos el estado de los cpe dentro del resumen de boletas o de anulaciones
			if self.type == "ra":
				cpe_ids = self.voided_ids.mapped('pe_cpe_id').ids
				anuladas = self.search([('id', 'in', cpe_ids)])
				for reg in anuladas:
					reg.estado_sunat = self.estado_sunat
			elif self.type == "rc":
				cpe_ids = self.summary_ids.mapped('pe_cpe_id').ids
				resumen = self.search([('id', 'in', cpe_ids)])
				for reg in resumen:
					reg.estado_sunat = self.estado_sunat
		else:
			res = "send"
			self.response = response.get("faultcode")
			self.note = response.get("faultstring", "No se pudo obtener un codigo de respuesta valido")
			if response.get("faultcode"):
				code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
					response.get("faultcode").split(".")[-1].encode('utf-8')) or False
				self.response_code = code
				try:
					self.error_code = code
				except Exception as e:
					self.error_code = False
				self.estado_sunat = '07'
			else:
				self.estado_sunat = "01"
			
			if self.type == "ra":
				cpe_ids = self.voided_ids.mapped('pe_cpe_id').ids
				anuladas = self.search([('id', 'in', cpe_ids)])
				for reg in anuladas:
					reg.estado_sunat = self.estado_sunat
			elif self.type == "rc":
				cpe_ids = self.summary_ids.mapped('pe_cpe_id').ids
				resumen = self.search([('id', 'in', cpe_ids)])
				for reg in resumen:
					reg.estado_sunat = self.estado_sunat
		return res

	# (@rpt) consultar el ticket de los resumenes
	def get_sunat_ticket_status(self):
		self.ensure_one()
		client = self.prepare_sunat_auth()
		response_status, response, response_file = get_ticket_status(self.ticket, client)
		state = None			
		if not response:
			raise Warning('No se pudo obtener respuesta del ticket '+ self.ticket)
		if response_status:
			file_name = self.get_document_name()
			self.datas_response = response_file
			self.datas_response_fname = 'R-%s.zip' % file_name
			state = self.get_response_details()
		else:
			res = "send"
			self.response = response.get("faultcode", False)
			self.note = response.get("faultstring", "No se pudo obtener un codigo de respuesta valido")
			if response.get("faultcode", False):
				code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
					response.get("faultcode").split(".")[-1].encode('utf-8')) or False
				try:
					self.error_code = code
				except Exception as e:
					self.error_code = False
				self.estado_sunat = '07'
			else:
				self.estado_sunat = "03"
			
			if self.type == "ra":
				cpe_ids = self.voided_ids.mapped('pe_cpe_id').ids
				anuladas = self.search([('id', 'in', cpe_ids)])
				for reg in anuladas:
					reg.estado_sunat = self.estado_sunat
			elif self.type == "rc":
				cpe_ids = self.summary_ids.mapped('pe_cpe_id').ids
				resumen = self.search([('id', 'in', cpe_ids)])
				for reg in resumen:
					reg.estado_sunat = self.estado_sunat
		return state

	# (@rpt) consultar cdr (valido para envios individuales)
	def action_document_status(self):
		client = self.prepare_sunat_auth()
		name = self.get_document_name()
		response_status, response, response_file = get_status_cdr(name, client)
		state = None
		if response_status:
			self.note = "%s - %s" % (response['statusCdr'].get('statusCode', ""), response['statusCdr'].get('statusMessage', ""))
			self.estado_sunat = self.getEstadoSunat(response['statusCdr'].get('statusCode', ""))
			if response_file:
				self.datas_response = response_file
				self.datas_response_fname = 'R-%s.zip' % name
				state = self.get_response_details()
				if state:
					self.state = state
		else:
			self.response = response.get("faultcode", False)
			self.note = response.get("faultstring") or str(response)
			if response.get("faultcode"):
				try:
					code = len(response.get("faultcode").split(".")) >= 2 and "%04d" % int(
						response.get("faultcode").split(".")[-1].encode('utf-8')) or False
					self.error_code = code
					self.estado_sunat = "07"
				except:
					pass

	
	# Tarea programada para "Envio Automatico de Resumen"
	def send_rc(self):
		cpe_ids = self.search([('state', 'in', ['draft', 'generate', 'verify']), ('type', 'in', ['rc'])])
		for cpe_id in cpe_ids:
			try:
				if not cpe_id.ticket:
					cpe_id.action_generate()
					cpe_id.action_send()
			except Exception:
				pass

	# Tarea programada para "Envio Automatico de Baja"
	def send_ra(self):
		cpe_ids = self.search([('state', 'in', ['draft', 'generate', 'verify']), ('type', 'in', ['ra'])])
		for cpe_id in cpe_ids:
			try:
				if not cpe_id.ticket:
					check = True
					for invoice_id in cpe_id.invoice_ids:
						if invoice_id.pe_invoice_code in ["03"] and invoice_id.origin_doc_code in ["03"]:
							if invoice_id.pe_summary_id.state not in ['verify', 'done']:
								check = False
								break
					if check:
						cpe_id.action_generate()
						cpe_id.action_send()
			except Exception:
				pass

	# Tarea programada para consultar ticket
	def tp_estado_ticket(self):
		cpe_ids = self.search([('state', 'in', ['verify']), ('type', 'in', ['ra', 'rc'])])
		for cpe_id in cpe_ids:
			try:
				if cpe_id.ticket:
					cpe_id.action_done()
			except Exception:
				pass

	# Tarea programada para "Envio Automatico de Facturas y Notas debito"	
	def send_async_cpe(self):
		cpe_ids = self.search([('state', 'in', ['generate', 'send']), ('type', 'in', ['sync'])])
		for cpe_id in cpe_ids:
			if cpe_id.invoice_ids:
				if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03", "07"]:
					try:
						cpe_id.action_document_status()
					except Exception:
						pass
				if cpe_id.state != 'done':
					if cpe_id.invoice_ids[0].pe_invoice_code not in ["03", "07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03", "07"]:
						try:
							cpe_id.action_generate()
							cpe_id.action_send()
						except Exception:
							pass

	# Tarea programada para "Envio Automatico de Notas de Crédito"
	def send_async_cpe_nc(self):
		cpe_ids = self.search([('state', 'in', ['generate', 'send']), ('type', 'in', ['sync'])])
		for cpe_id in cpe_ids:
			if not cpe_id.invoice_ids:
				continue
			if cpe_id.invoice_ids[0].pe_invoice_code in ["07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03"]:
				try:
					cpe_id.action_document_status()
				except Exception:
					pass
			if cpe_id.state != 'done':
				if cpe_id.invoice_ids[0].pe_invoice_code in ["07"] and cpe_id.invoice_ids[0].origin_doc_code not in ["03"]:
					try:
						cpe_id.action_generate()
						cpe_id.action_send()
					except Exception:
						pass
