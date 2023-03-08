# -*- coding: utf-8 -*-

from lxml import etree
import xmlsec
from collections import OrderedDict
from odoo import _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from pysimplesoap.simplexml import SimpleXMLElement
import logging
from odoo.tools import float_is_zero, float_round, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import fields
import dateutil.parser
import pytz
import json
from dateutil.tz import gettz
import math
from . import constantes

_logging = logging.getLogger(__name__)
tz = pytz.timezone('America/Lima')

def round_up(n, decimals=0):
	multiplier = 10 ** decimals
	return math.ceil(n * multiplier) / multiplier

def round_down(n, decimals=0):
	multiplier = 10 ** decimals
	return math.floor(n * multiplier) / multiplier

# clase generadora del xml
class CPE:

	def __init__(self):
		self._cac = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
		self._cbc = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
		self._ccts = 'urn:un:unece:uncefact:documentation:2'
		self._ds = 'http://www.w3.org/2000/09/xmldsig#'
		self._ext = 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'
		self._qdt = 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2'
		self._sac = 'urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1'
		self._udt = 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2'
		self._xsi = 'http://www.w3.org/2001/XMLSchema-instance'
		self._root = None

	def convert_TZ_UTC(self, reg, TZ_datetime):
		fmt = "%Y-%m-%d %H:%M:%S"
		# Current time in UTC
		now_utc = datetime.now(pytz.timezone('UTC'))
		# Convert to current user time zone
		now_timezone = now_utc.astimezone(pytz.timezone(reg.env.user.tz or 'America/Lima'))
		UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(fmt), fmt) - datetime.strptime(now_timezone.strftime(fmt), fmt)
		result_utc_datetime = TZ_datetime - UTC_OFFSET_TIMEDELTA
		return result_utc_datetime

	# Obtner lista de anticipos
	def _obtener_comprobantes_anticipos(self, invoice_id):
		try:
			lista = invoice_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('invoice_ids').filtered(lambda inv: inv.pe_sunat_transaction51 in ('0102', ) and inv.pe_invoice_code in ('01', '03') and inv.id != invoice_id.id and inv.state not in ('draft', 'cancel'))
			return lista
		except Exception as e:
			return []

	# Datos del certificado
	def _agregar_informacion_certificado(self, invoice_id):
		if not invoice_id.company_id.partner_id.doc_number:
			raise UserError('No se ha establecido un numero de documento para %s' % invoice_id.company_id.partner_id.name)
		tag = etree.QName(self._cac, 'Signature')
		signature = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(signature, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id._name == 'solse.cpe' and invoice_id.name or invoice_id.l10n_latam_document_number
		tag = etree.QName(self._cac, 'SignatoryParty')
		party = etree.SubElement(signature, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')
		identification = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_number
		tag = etree.QName(self._cac, 'PartyName')
		name = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Name')
		etree.SubElement(name, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.legal_name
		tag = etree.QName(self._cac, 'DigitalSignatureAttachment')
		attachment = etree.SubElement(signature, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'ExternalReference')
		reference = etree.SubElement(attachment, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'URI')
		etree.SubElement(reference, (tag.text), nsmap={'cbc': tag.namespace}).text = '#signatureOdoo'

	# Datos de los anticipos
	def _agregar_informacion_anticipos(self, invoice_id):
		try:
			for line in self._obtener_comprobantes_anticipos(invoice_id):
				tag = etree.QName(self._cac, 'PrepaidPayment')
				prepaid = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				if line.pe_invoice_code == '01':
					etree.SubElement(prepaid, (tag.text), schemeID='02', schemeName='SUNAT:Identificador de Documentos Relacionados', schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = line.name
				else:
					if line.pe_invoice_code == '03':
						etree.SubElement(prepaid, (tag.text), schemeID='03', schemeName='SUNAT:Identificador de Documentos Relacionados', schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = line.name
				tag = etree.QName(self._cbc, 'PaidAmount')
				etree.SubElement(prepaid, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(line.amount_total, 2))
				tag = etree.QName(self._cbc, 'InstructionID')
				etree.SubElement(prepaid, (tag.text), schemeID=(invoice_id.partner_id.doc_type or '-'), nsmap={'cbc': tag.namespace}).text = line.partner_id.doc_number or '-'
		except Exception as e:
			pass

	# Datos de la orden de compra relacionada a la factura o boleta
	def _agregar_informacion_orden_compra(self, invoice_id):
		try:
			sale_ids = invoice_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
			for sale in sale_ids:
				tag = etree.QName(self._cac, 'OrderReference')
				order = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(order, (tag.text), nsmap={'cbc': tag.namespace}).text = sale.client_order_ref or sale.name
				break
		except Exception as e:
			pass
 
	# Datos del comprobante cuando se trata de una nota de credito o nota de debito, aca van los datos del
	# comprobante afectado por la nota
	def _agregar_informacion_DiscrepancyResponse(self, invoice_id):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'DiscrepancyResponse')
			discrepancy = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ReferenceID')
			etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.l10n_latam_document_number or ''
			tag = etree.QName(self._cbc, 'ResponseCode')
			if invoice_id.move_type == 'out_invoice':
				etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_debit_note_code
			elif invoice_id.move_type == 'out_refund':
				etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_credit_note_code
			tag = etree.QName(self._cbc, 'Description')
			etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_number or invoice_id.invoice_line_ids[0].name or ''
			
	
	# Para agregar los comprobantes relacionados que tenemos con respecto a la factura - Usado para resumenes
	def _agregar_informacion_BillingReference_2_0(self, invoice_id, line=None):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'BillingReference')
			reference = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'InvoiceDocumentReference')
			invoice = etree.SubElement(reference, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.l10n_latam_document_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.pe_invoice_code

	# Para agregar los comprobantes relacionados que tenemos con respecto. Valido solo para notas de credito y debito
	def _agregar_informacion_BillingReference(self, invoice_id, line=None):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'BillingReference')
			reference = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'InvoiceDocumentReference')
			invoice = etree.SubElement(reference, (tag.text), nsmap={'cac': tag.namespace})
			# Serie y número del comprobante que modifica
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.l10n_latam_document_number
			# Código de tipo de comprobante que modifica
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(invoice, (tag.text), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = inv.pe_invoice_code

	# (1) Obtiene los datos de cabecera y la firma en si
	def _agregar_informacion_firma(self, content):
		tag = etree.QName(self._ds, 'Signature')
		signature = etree.SubElement(content, (tag.text), Id='signatureSistemERP', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'SignedInfo')
		signed_info = etree.SubElement(signature, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'CanonicalizationMethod')
		etree.SubElement(signed_info, (tag.text), Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'SignatureMethod')
		etree.SubElement(signed_info, (tag.text), Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'Reference')
		reference = etree.SubElement(signed_info, (tag.text), URI='', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'Transforms')
		transforms = etree.SubElement(reference, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'Transform')
		etree.SubElement(transforms, (tag.text), Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'DigestMethod')
		etree.SubElement(reference, (tag.text), Algorithm='http://www.w3.org/2000/09/xmldsig#sha1', nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'DigestValue')
		etree.SubElement(reference, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'SignatureValue')
		etree.SubElement(signature, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'KeyInfo')
		key_info = etree.SubElement(signature, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'X509Data')
		data = etree.SubElement(key_info, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'X509SubjectName')
		etree.SubElement(data, (tag.text), nsmap={'ds': tag.namespace})
		tag = etree.QName(self._ds, 'X509Certificate')
		etree.SubElement(data, (tag.text), nsmap={'ds': tag.namespace})

	# (2, 3) Obtiene los datos de la version UBL
	def _agregar_informacion_ubl(self, version=None, customization=None):
		tag = etree.QName(self._cbc, 'UBLVersionID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = version or '2.1'
		tag = etree.QName(self._cbc, 'CustomizationID')
		etree.SubElement((self._root), (tag.text), schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = customization or '2.0'

	# (4, 5, 6, 7, 9 , @10, 11) (8 es opcional y no se esta enviando) Datos de los comprobantes. Factura, nota de credito, nota de debito
	def _agregar_informacion_general_comprobante(self, invoice_id):
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_number or ''
		tag = etree.QName(self._cbc, 'IssueDate')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_date.strftime('%Y-%m-%d')
		tag = etree.QName(self._cbc, 'IssueTime')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_date.strftime('%H:%M:%S')
		if invoice_id.pe_invoice_code in ('01', '03'):
			tag = etree.QName(self._cbc, 'InvoiceTypeCode')
			etree.SubElement((self._root), (tag.text), listID=(invoice_id.pe_sunat_transaction51), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_code
		
		self._agregar_informacion_leyendas(invoice_id)

		# 11 Tipo de moneda
		tag = etree.QName(self._cbc, 'DocumentCurrencyCode')
		etree.SubElement((self._root), (tag.text), listID='ISO 4217 Alpha', listName='Currency', listAgencyName='United Nations Economic Commission for Europe', nsmap={'cbc': tag.namespace}).text = invoice_id.currency_id.name
		
		tag = etree.QName(self._cbc, 'LineCountNumeric')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = str(len(invoice_id.invoice_line_ids))
		# Si es factura o boleta
		if invoice_id.pe_invoice_code in ('01', '03'):
			self._agregar_informacion_guias_remision(invoice_id)
			self._agregar_informacion_orden_compra(invoice_id)
			self._agregar_informacion_otros_documentos_del_comprobante(invoice_id)

	# (10) Leyendas
	def _agregar_informacion_leyendas(self, invoice_id):
		for line in invoice_id.pe_additional_property_ids:
			tag = etree.QName(self._cbc, 'Note')
			etree.SubElement((self._root), (tag.text), languageLocaleID=(line.code), nsmap={'cbc': tag.namespace}).text = line.value
		if invoice_id.tiene_detraccion:
			tag = etree.QName(self._cbc, 'Note')
			etree.SubElement((self._root), (tag.text), languageLocaleID='2006', nsmap={'cbc': tag.namespace}).text = 'Operación sujeta al Sistema de Pago de Obligaciones Tributarias'
	
	# (12) Tipo y número de la guía de remisión relacionada con la operación que se factura
	# Datos de guía de remisión relacionada con la operación que se factura
	def _agregar_informacion_guias_remision(self, invoice_id):
		if not invoice_id.env.context.get('despatch_numbers'):
			return
		if invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id):
			for despatch_number in invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id, []):
				tag = etree.QName(self._cac, 'DespatchDocumentReference')
				despatch = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(despatch, (tag.text), nsmap={'cbc': tag.namespace}).text = despatch_number
				tag = etree.QName(self._cbc, 'DocumentTypeCode')
				etree.SubElement(despatch, (tag.text), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = '09'
	
	def _agregar_informacion_guias_en_notas(self, invoice_id):
		for despatch_number in invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id, []):
			tag = etree.QName(self._cac, 'DespatchDocumentReference')
			reference = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(reference, (tag.text), nsmap={'cbc': tag.namespace}).text = despatch_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(reference, (tag.text), listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = '09'

	# (13) Tipo y número de otro documento y/ código documento relacionado con la operación que se factura.
	def _agregar_informacion_otros_documentos_del_comprobante(self, invoice_id):
		lista_anticipos = self._obtener_comprobantes_anticipos(invoice_id)
		if not lista_anticipos or invoice_id.pe_invoice_code not in ['01', '03']:
			return
		for anticipo in lista_anticipos:
			tipo_rel = '02' if invoice_id.pe_invoice_code == '01' else '03'
			tag = etree.QName(self._cac, 'AdditionalDocumentReference')
			additional = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(additional, (tag.text), nsmap={'cbc': tag.namespace}).text = anticipo.l10n_latam_document_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(additional, (tag.text), listAgencyName='PE:SUNAT', listName='Documento Relacionado', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo12', nsmap={'cbc': tag.namespace}).text = tipo_rel

			tag = etree.QName(self._cbc, 'DocumentStatusCode')
			etree.SubElement(additional, (tag.text), listAgencyName='PE:SUNAT', listName='Anticipo' , nsmap={'cbc': tag.namespace}).text = '1'
			tag = etree.QName(self._cac, 'IssuerParty')
			tax_issue_party = etree.SubElement(additional, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'PartyIdentification')
			tax_issue_party = etree.SubElement(tax_issue_party, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(tax_issue_party, (tag.text), schemeID=(invoice_id.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code), schemeName='Documento de Identidad', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06', nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_number

	def _agregar_informacion_otros_documentos_del_comprobante_anterior(self, invoice_id):
		if invoice_id.pe_additional_type:
			tag = etree.QName(self._cac, 'AdditionalDocumentReference')
			additional = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(additional, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_additional_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(additional, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_additional_type

	# Obtiene datos de la empresa, usado cuando es para resumenes, tanto de boletas como de anulacion
	def _agregar_informacion_empresa_2_0(self, invoice_id):
		tag = etree.QName(self._cac, 'AccountingSupplierParty')
		supplier = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
		etree.SubElement(supplier, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_number
		tag = etree.QName(self._cbc, 'AdditionalAccountID')
		etree.SubElement(supplier, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_type
		tag = etree.QName(self._cac, 'Party')
		party = etree.SubElement(supplier, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'PartyName')
		party_name = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Name')
		comercial_name = invoice_id.company_id.partner_id.commercial_name or '-'
		etree.SubElement(party_name, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(comercial_name.strip())
		tag = etree.QName(self._cac, 'PostalAddress')
		address = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'AddressTypeCode')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.l10n_pe_district.code
		tag = etree.QName(self._cac, 'PartyLegalEntity')
		entity = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')
		name = invoice_id.company_id.partner_id.legal_name != '-' and invoice_id.company_id.partner_id.legal_name or invoice_id.company_id.partner_id.name
		etree.SubElement(entity, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(name)

	# (14, 15, 16, 17) Obtiene los datos de la empresa, usado para facturas y notas
	def _agregar_informacion_empresa(self, invoice_id):
		datos_entidad = invoice_id.obtener_datos_entidad_emisora()
		
		tag = etree.QName(self._cac, 'AccountingSupplierParty')
		supplier = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'Party')
		party = etree.SubElement(supplier, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')
		party_identification = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(party_identification, (tag.text), schemeID=(invoice_id.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code), schemeName='Documento de Identidad', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06', nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_number or invoice_id.company_id.partner_id.vat
		tag = etree.QName(self._cac, 'PartyName')
		party_name = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Name')
		comercial_name = datos_entidad['comercial_name']
		etree.SubElement(party_name, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(comercial_name)
		tag = etree.QName(self._cac, 'PartyLegalEntity')
		party_legal = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')
		legal_name = datos_entidad['legal_name']
		etree.SubElement(party_legal, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(legal_name)
		tag = etree.QName(self._cac, 'RegistrationAddress')
		address = etree.SubElement(party_legal, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		ubigeo = datos_entidad['ubigeo']
		etree.SubElement(address, (tag.text), schemeAgencyName='PE:INEI', schemeName='Ubigeos', nsmap={'cbc': tag.namespace}).text = ubigeo
		tag = etree.QName(self._cbc, 'AddressTypeCode')
		pe_branch_code = datos_entidad['pe_branch_code']
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = pe_branch_code
		tag = etree.QName(self._cbc, 'CitySubdivisionName')
		urba = 'NONE'
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = urba
		tag = etree.QName(self._cbc, 'CityName')
		province_id = datos_entidad['province_id']
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = province_id
		tag = etree.QName(self._cbc, 'CountrySubentity')
		state_id = datos_entidad['state_id']
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = state_id
		tag = etree.QName(self._cbc, 'District')
		district_id = datos_entidad['district_id']
		if not district_id:
			raise UserError('No se ha establecido un distrito para la empresa emisora')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = district_id
		tag = etree.QName(self._cac, 'AddressLine')
		addresLine = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Line')
		street_id = datos_entidad['street_id']
		etree.SubElement(addresLine, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(street_id)
		tag = etree.QName(self._cac, 'Country')
		country_id = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'IdentificationCode')
		country_code = datos_entidad['country_code']
		etree.SubElement(country_id, (tag.text), listID='ISO 3166-1', listAgencyName='United Nations Economic Commission for Europe', listName='Country', nsmap={'cbc': tag.namespace}).text = country_code


	def _agregar_informacion_cliente_2_0(self, invoice_id, line=None):
		tag = etree.QName(self._cac, 'AccountingCustomerParty')
		customer = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')
		partner_id = invoice_id.partner_id.parent_id or invoice_id.partner_id
		etree.SubElement(customer, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.doc_number or partner_id.parent_id.doc_number or '0'
		tag = etree.QName(self._cbc, 'AdditionalAccountID')
		etree.SubElement(customer, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.doc_type or partner_id.parent_id.doc_type or '-'
		if not line:
			tag = etree.QName(self._cac, 'Party')
			party = etree.SubElement(customer, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'PartyLegalEntity')
			entity = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'RegistrationName')
			etree.SubElement(entity, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(partner_id.name or '-')

	# (18, 19)
	def _agregar_informacion_cliente(self, invoice_id, line=None):
		partner_id = invoice_id.partner_id.parent_id or invoice_id.partner_id
		tag = etree.QName(self._cac, 'AccountingCustomerParty')
		customer = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'Party')
		party = etree.SubElement(customer, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')
		party_identification = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(party_identification, (tag.text), schemeID=(partner_id.doc_type or '-'), schemeName='Documento de Identidad', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06', nsmap={'cbc': tag.namespace}).text = partner_id.doc_number or '-'
		tag = etree.QName(self._cac, 'PartyLegalEntity')
		party_legal = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')
		legal_name = partner_id.legal_name and partner_id.legal_name.strip() != '-' and partner_id.legal_name.strip() or partner_id.name or '-'
		etree.SubElement(party_legal, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(legal_name)

	# (20) Dirección del lugar en el que se entrega el bien
	def _agregar_informacion_lugar_entrega(self, invoice_id):
		"""
		En el caso de venta de bienes, se deberá indicar la dirección de la entrega de dichos
		bienes siempre que: Se trate de ventas itinerantes y no figure el punto de llegada en la
		guía de remisión – remitente que realice el traslado de los bienes.
		"""
		if invoice_id.partner_id.id != invoice_id.partner_shipping_id.id:
			partner_id = invoice_id.partner_shipping_id
		else:
			partner_id = invoice_id.company_id.partner_id
		tag = etree.QName(self._cac, 'Delivery')
		delivery = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'DeliveryLocation')
		location = etree.SubElement(delivery, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'Address')
		address = etree.SubElement(location, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'AddressLine')
		address_line = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Line')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.street[:200]
		tag = etree.QName(self._cbc, 'CitySubdivisionName')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.street2 and partner_id.street2[:25] or ''
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(address, (tag.text), schemeAgencyName='PE:INEI', schemeName='Ubigeos', nsmap={'cbc': tag.namespace}).text = partner_id.l10n_pe_district.code
		tag = etree.QName(self._cbc, 'CountrySubentity')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.state_id.name or '-'
		tag = etree.QName(self._cbc, 'District')
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = partner_id.l10n_pe_district.name or '-'
		tag = etree.QName(self._cac, 'Country')
		country = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'IdentificationCode')
		etree.SubElement(country, (tag.text), listID='ISO 3166-1', listAgencyName='United Nations Economic Commission for Europe', listName='Country', nsmap={'cbc': tag.namespace}).text = partner_id.country_id.code or '-'
	
	# (21) Información de descuentos Globales
	def _agregar_informacion_descuentos_globales(self, invoice_id):
		if invoice_id.tiene_retencion:
			tag = etree.QName(self._cac, 'AllowanceCharge')
			allowance_charge = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ChargeIndicator')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
			tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
			etree.SubElement(allowance_charge, (tag.text), listAgencyName='PE:SUNAT', listName='Cargo/descuento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo53', nsmap={'cbc': tag.namespace}).text = '62'
			tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(invoice_id.porc_retencion / 100)
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.monto_retencion_base, 5))
			tag = etree.QName(self._cbc, 'BaseAmount')
			amount_total = invoice_id.amount_total
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))
		elif invoice_id.pe_total_discount > 0.0:
			tag = etree.QName(self._cac, 'AllowanceCharge')
			allowance_charge = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ChargeIndicator')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
			tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
			etree.SubElement(allowance_charge, (tag.text), listAgencyName='PE:SUNAT', listName='Cargo/descuento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo53', nsmap={'cbc': tag.namespace}).text = '02'
			tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round_up((invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax) / (invoice_id.amount_untaxed + (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)), 5))
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax, 2))
			tag = etree.QName(self._cbc, 'BaseAmount')
			amount_total = invoice_id.amount_untaxed + (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))
		elif self._obtener_comprobantes_anticipos(invoice_id):
			tag = etree.QName(self._cac, 'AllowanceCharge')
			allowance_charge = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ChargeIndicator')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
			tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
			etree.SubElement(allowance_charge, (tag.text), listAgencyName='PE:SUNAT', listName='Cargo/descuento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo53', nsmap={'cbc': tag.namespace}).text = '04'
			tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = '1.00000'
			
			monto_total = 0
			monto_sub_total = 0
			for line in self._obtener_comprobantes_anticipos(invoice_id):
				#amount_total = line.amount_untaxed + (line.pe_total_discount - line.pe_total_discount_tax)
				amount_total = line.currency_id.with_context(date=(invoice_id.invoice_date)).compute(line.amount_total, invoice_id.currency_id)
				amount_sub_total = line.currency_id.with_context(date=(invoice_id.invoice_date)).compute(line.amount_untaxed, invoice_id.currency_id)
				monto_total = monto_total + amount_total
				monto_sub_total = monto_sub_total + amount_sub_total

			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(monto_sub_total, 2))
			tag = etree.QName(self._cbc, 'BaseAmount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(monto_sub_total, 2))

	def _agregar_informacion_descuentos_globales_anterior(self, invoice_id):
		if invoice_id.pe_total_discount > 0.0:
			tag = etree.QName(self._cac, 'AllowanceCharge')
			allowance_charge = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ChargeIndicator')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
			tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
			etree.SubElement(allowance_charge, (tag.text), listAgencyName='PE:SUNAT', listName='Cargo/descuento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo53', nsmap={'cbc': tag.namespace}).text = '02'
			tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
			total_descuentos = (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)
			factor = total_descuentos / (invoice_id.amount_untaxed + total_descuentos) 

			factor = round_up(factor, 5)
			"""
			total descuentosss 
			2022-06-01 03:47:29,921 15076 INFO ropa15 odoo.addons.solse_pe_cpe.models.cpe_xml: 0.03 
			2022-06-01 03:47:29,921 15076 INFO ropa15 odoo.addons.solse_pe_cpe.models.cpe_xml: factor 1 
			2022-06-01 03:47:29,921 15076 INFO ropa15 odoo.addons.solse_pe_cpe.models.cpe_xml: 7.119464616260856e-05 
			2022-06-01 03:47:29,921 15076 INFO ropa15 odoo.addons.solse_pe_cpe.models.cpe_xml: factor 2 
			2022-06-01 03:47:29,921 15076 INFO ropa15 odoo.addons.solse_pe_cpe.models.cpe_xml: 7e-05 
			"""
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(factor)
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax, 2))
			tag = etree.QName(self._cbc, 'BaseAmount')
			if len(factor_str) > 10 and "." in factor_str:
				amount_total = invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax
			else:
				amount_total = invoice_id.amount_untaxed + (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))

	# (22, 23) Monto Total de Impuestos.
	def _agregar_informacion_de_impuestos(self, invoice_id):
		# 22
		tag = etree.QName(self._cac, 'TaxTotal')
		total = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'TaxAmount')
		tax_amount_all = 0.0
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		"""_logging.info('calcular total de impuestosss')
		invoice_id._compute_invoice_taxes_by_group()
		_logging.info('recalculando impuestos')"""

		#for group_tax in invoice_id.amount_by_group:
		datos = invoice_id.tax_totals #.replace("false", "False")
		#datos = json.loads(datos)

		"""
			{'Untaxed Amount': [{
			'tax_group_name': 'IGV', 
			'tax_group_amount': 36.0, 
			'tax_group_base_amount': 200.0, 
			'formatted_tax_group_amount': 'S/ 36.00', 
			'formatted_tax_group_base_amount': 'S/ 200.00', 
			'tax_group_id': 2, 'group_key': 'Untaxed Amount-2'}]}
		"""

		datos_sub = datos["groups_by_subtotal"]
		importe_libre = datos_sub["Importe libre de impuestos"] if "Importe libre de impuestos" in datos_sub  else False
		if not importe_libre:
			for reg in datos_sub:
				importe_libre = datos_sub[reg]
				break


		amount_by_group = importe_libre
		total_base_negativo = 0
		for group_tax in amount_by_group:
			tax_amount = group_tax['tax_group_amount']
			tax_base_amount = group_tax['tax_group_base_amount']
			tax_group = group_tax['tax_group_id']

			if tax_base_amount < 0:
				total_base_negativo += tax_base_amount

			tax = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == tax_group)
			tax = tax and tax[0]
			if tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['ICBPER']:
				tax_amount_all += tax_amount
				continue

		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(tax_amount_all, 2))
		
		# 23
		for group_tax in amount_by_group:
			group_id = group_tax['tax_group_id']
			base_tax_line = group_tax['tax_group_base_amount']
			amount_tax_line = group_tax['tax_group_amount']
			tax = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == group_id)
			tax = tax and tax[0]
			if tax.pe_tax_type.code == constantes.IMPUESTO['gratuito']:
				continue
			elif tax.pe_tax_type.code == constantes.IMPUESTO['inafecto']:
				continue
			else:
				if base_tax_line == 0:
					continue

				base_tax_line = base_tax_line - abs(total_base_negativo)
				tag = etree.QName(self._cac, 'TaxSubtotal')
				tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
				if tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['ICBPER']:
					tag = etree.QName(self._cbc, 'TaxableAmount')
					etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(base_tax_line, 2))
				tag = etree.QName(self._cbc, 'TaxAmount')
				etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_tax_line, 2))
				tag = etree.QName(self._cac, 'TaxCategory')
				category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cac, 'TaxScheme')
				scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.l10n_pe_edi_tax_code
				tag = etree.QName(self._cbc, 'Name')
				etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
				tag = etree.QName(self._cbc, 'TaxTypeCode')
				etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code

		self._agregar_informacion_de_impuestos_especiales(invoice_id, total)
		self._agregar_informacion_de_impuestos_inafectos(invoice_id, total)
		return total

	# (24) Total valor de venta - operaciones exoneradas.
	
	# (25) Total valor de venta - operaciones inafectas
	def _agregar_informacion_de_impuestos_especiales(self, invoice_id, total):
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		line_ids = invoice_id.invoice_line_ids.filtered(lambda ln: ln.pe_affectation_code not in ('10', '20', '30', '40'))
		tax_ids = line_ids.mapped('tax_ids')
		for tax in tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito'] and tax.pe_is_charge == False):
			base_amount = 0.0
			tax_amount = 0.0
			for line in line_ids:
				#price_unit = line.price_unit
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				if line.discount >= 100:
					price_unit = line.price_unit
				if tax.id in line.tax_ids.ids:
					tax_values = tax.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
					base_amount += invoice_id.currency_id.round_up(tax_values['total_excluded'])
					if line.pe_affectation_code in ['11', '12', '13', '14', '15', '16', '17']:
						tax_amount += invoice_id.currency_id.round_up(tax_values['taxes'][0]['amount'])

			tag = etree.QName(self._cac, 'TaxSubtotal')
			tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxableAmount')
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(base_amount, 2))
			tag = etree.QName(self._cbc, 'TaxAmount')

			#amount_tax_line = tax.amount
			amount_tax_line = tax_amount
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_tax_line, 2))
			tag = etree.QName(self._cac, 'TaxCategory')
			category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'TaxScheme')
			scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.l10n_pe_edi_tax_code
			tag = etree.QName(self._cbc, 'Name')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
			tag = etree.QName(self._cbc, 'TaxTypeCode')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code

		"""for tax in tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['inafecto'] and tax.pe_is_charge == False):
			_logging.info("tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['inafecto']")
			base_amount = 0.0
			tax_amount = 0.0
			for line in line_ids:
				price_unit = line.price_unit
				if tax.id in line.tax_ids.ids:
					tax_values = tax.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
					base_amount += invoice_id.currency_id.round_up(tax_values['total_excluded'])
					tax_amount += invoice_id.currency_id.round_up(tax_values['taxes'][0]['amount'])

			tag = etree.QName(self._cac, 'TaxSubtotal')
			tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxableAmount')
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(base_amount + tax_amount, 2))
			tag = etree.QName(self._cbc, 'TaxAmount')
			amount_tax_line = tax.amount
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = '0.00'#str(round_up(amount_tax_line, 2))
			tag = etree.QName(self._cac, 'TaxCategory')
			category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'TaxScheme')
			scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.l10n_pe_edi_tax_code
			tag = etree.QName(self._cbc, 'Name')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
			tag = etree.QName(self._cbc, 'TaxTypeCode')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code"""

	def _agregar_informacion_de_impuestos_inafectos(self, invoice_id, total):
		line_ids = invoice_id.invoice_line_ids.filtered(lambda ln: ln.pe_affectation_code in ('30'))
		tax_ids = line_ids.mapped('tax_ids')
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		for tax in tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto'] and tax.pe_is_charge == False):
			base_amount = 0.0
			tax_amount = 0.0
			for line in line_ids:
				#price_unit = line.price_unit
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				if line.discount >= 100:
					price_unit = line.price_unit
				if tax.id in line.tax_ids.ids:
					tax_values = tax.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
					base_amount += invoice_id.currency_id.round_up(tax_values['total_excluded'])
					tax_amount += invoice_id.currency_id.round_up(tax_values['taxes'][0]['amount'])

			tag = etree.QName(self._cac, 'TaxSubtotal')
			tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxableAmount')
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(base_amount + tax_amount, 2))
			tag = etree.QName(self._cbc, 'TaxAmount')
			amount_tax_line = tax.amount
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = '0.00'#str(round_up(amount_tax_line, 2))
			tag = etree.QName(self._cac, 'TaxCategory')
			category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'TaxScheme')
			scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.l10n_pe_edi_tax_code
			tag = etree.QName(self._cbc, 'Name')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
			tag = etree.QName(self._cbc, 'TaxTypeCode')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code

	# (26) Total Valor de Venta de Operaciones gratuitas. (trabaja con el puto 39)

	# (27) Sumatoria IGV

	# (28) Sumatoria ISC.

	# (29) Sumatoria otros tributos

	# (30 a 34) Obtener los totales del comprobante, incluye precion con impuestos
	def _agregar_informacion_montos_totales(self, invoice_id):
		tagname = invoice_id.l10n_latam_document_type_id.code == '08' and 'RequestedMonetaryTotal' or 'LegalMonetaryTotal'
		tag = etree.QName(self._cac, tagname)
		total = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		prepaid_amount = 0
		prepaid_amount_untaxed = 0
		tiene_anticipos = False
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		try:
			for line in self._obtener_comprobantes_anticipos(invoice_id):
				tiene_anticipos = True
				amount = line.currency_id.with_context(date=(invoice_id.invoice_date)).compute(line.amount_total, invoice_id.currency_id)
				amount_untaxed = line.currency_id.with_context(date=(invoice_id.invoice_date)).compute(line.amount_untaxed, invoice_id.currency_id)
				prepaid_amount += amount
				prepaid_amount_untaxed += amount_untaxed

		except Exception as e:
			pass

		other = 0.0
		for tax in invoice_id.line_ids.filtered(lambda t: t.tax_line_id.pe_is_charge == True):
			other += invoice_id.currency_id.round_up(tax.price_total)

		amount_total = invoice_id.amount_total
		amount_untaxed = invoice_id.amount_untaxed
		
		# 30 Valor de venta del ítem
		"""
		A través de este elemento se debe indicar el valor de venta total de la operación. Es decir
		el importe total de la venta sin considerar los descuentos, impuestos u otros tributos a que
		se refiere el numeral anterior, pero que incluye cualquier monto de redondeo aplicable.
		"""
		tag = etree.QName(self._cbc, 'LineExtensionAmount')
		if tiene_anticipos:
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(prepaid_amount_untaxed, 2))
		else:
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_untaxed, 2))
		# 31 Total Precio de Venta
		"""
		A través de este elemento se debe indicar el valor de venta total de la operación incluido
		los impuestos
		"""
		tag = etree.QName(self._cbc, 'TaxInclusiveAmount')
		if tiene_anticipos:
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(prepaid_amount, 2))
		else:
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))
		
		if tiene_anticipos:
			tag = etree.QName(self._cbc, 'PrepaidAmount')
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(prepaid_amount, 2))

		# 32 Total de Descuentos.
		"""
		A través de este elemento se debe indicar el valor total de los descuentos globales
		realizados de ser el caso.
		Este elemento es distinto al elemento Descuentos Globales definido en el punto 35. Su
		propósito es permitir consignar en el comprobante de pago:
		 la sumatoria de los descuentos de cada línea (descuentos por ítem), o
		 la sumatoria de los descuentos de línea (ítem) + descuentos globales
		"""
		#tag = etree.QName(self._cbc, 'AllowanceTotalAmount')
		#etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_amount_discount, 2))

		# 33 Monto total de otros cargos del comprobante
		"""
		Corresponde al total de otros cargos cobrados al adquirente o usuario y que no forman
		parte de la operación que se factura, es decir no forman parte del(os) valor(es) de ventas
		señaladas anteriormente, pero sí forman parte del importe total de la Venta (Ejemplo:
		propinas, garantías para devolución de envases, etc.)
		"""
		if not tiene_anticipos:
			tag = etree.QName(self._cbc, 'ChargeTotalAmount')
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(other, digits))
		
		# 56 Monto de redondeo del importe total
		total_redondeo = 0
		for line in invoice_id.invoice_line_ids.filtered(lambda ln: ln.display_type in ['rounding']):
			total_redondeo = total_redondeo + line.price_unit

		if total_redondeo != 0:
			tag = etree.QName(self._cbc, 'PayableRoundingAmount')
			etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(total_redondeo, digits))
		
		# 34 Importe total de la venta, cesión en uso o del servicio prestado
		"""
		Corresponde al importe total de la venta, de la cesión en uso o del servicio prestado. Es el
		resultado de la suma y/o resta (Según corresponda) de los siguientes puntos: 31-32+33
		menos los anticipos que hubieran sido recibidos. 
		"""
		# Este debe ser el ultimo campo si o si
		tag = etree.QName(self._cbc, 'PayableAmount')
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))



	# (35, 36, 37, 38, 39, 40) Para la parte del xml donde se agrega la informacion de la lineas con su respectiva cabecera
	def _agregar_informacion_lineas_comprobante(self, invoice_id):
		cont = 1
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		bases_json = {}
		for line in invoice_id.invoice_line_ids.filtered(lambda ln: ln.price_subtotal >= 0 and ln.display_type in ['product']):
			#price_unit = round_up(float_round(line.get_price_unit()['total_included'], digits), digits)
			#price_unit = price_unit * (1 - (line.discount or 0.0) / 100.0)
			price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			# 35
			if invoice_id.pe_invoice_code == '08':
				tag = etree.QName(self._cac, 'DebitNoteLine')
			elif invoice_id.pe_invoice_code == '07':
				tag = etree.QName(self._cac, 'CreditNoteLine')
			else:
				tag = etree.QName(self._cac, 'InvoiceLine')
			inv_line = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(inv_line, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cont)
			# fin 35
			cont += 1
		
			# 36
			if invoice_id.pe_invoice_code == '08':
				tag = etree.QName(self._cbc, 'DebitedQuantity')
			else:
				if invoice_id.pe_invoice_code == '07':
					tag = etree.QName(self._cbc, 'CreditedQuantity')
				else:
					tag = etree.QName(self._cbc, 'InvoicedQuantity')
			etree.SubElement(inv_line, (tag.text), unitCode=(line.product_uom_id and line.product_uom_id.sunat_code or 'NIU'), unitCodeListID='UN/ECE rec 20', unitCodeListAgencyName='United Nations Economic Commission for Europe', nsmap={'cbc': tag.namespace}).text = str(line.quantity)
			# fin 36

			# 37
			tag = etree.QName(self._cbc, 'LineExtensionAmount')
			datos_precio = line.tax_ids.compute_all(line.price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
			precio_incluido = datos_precio['total_excluded']
			if line.pe_affectation_code in ['11', '12', '13', '14', '15', '16', '17', '21']:
				precio_incluido = datos_precio['total_excluded']
			elif line.discount > 0 and line.discount < 100:
				precio_incluido = line.price_subtotal
			#extension_amount = str(round_up(float_round(line.get_price_unit()['total_included'], digits), 2))
			primer_monto = float_round(precio_incluido, 2)
			extension_amount = round_down(precio_incluido, 2)
			bases_json[line.id] = extension_amount
			extension_amount = str(extension_amount)

			#etree.SubElement(inv_line, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(line.price_subtotal, 2))
			etree.SubElement(inv_line, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = extension_amount
			
			# inicio 38
			tag = etree.QName(self._cac, 'PricingReference')
			pricing = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			price_unit_all = line.get_price_unit(True)['total_included']
			# (38) Precio unitario (incluye el IGV)
			if price_unit_all > 0 and line.pe_affectation_code not in ['30', '31', '32', '33', '34', '35', '36']:
				tag = etree.QName(self._cac, 'AlternativeConditionPrice')
				alternative = etree.SubElement(pricing, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'PriceAmount')
				if price_unit_all == 0 or invoice_id.pe_invoice_code in ('07', '08'):
					etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(price_unit_all, digits), digits))
				elif line.discount > 0:
					precio_descuento = round_up(float_round(line.get_price_unit()['total_included'], digits), digits)
					precio_descuento = precio_descuento * (1 - (line.discount or 0.0) / 100.0)
					#etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(price_unit, digits), digits))
					etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(precio_descuento, digits), digits))
				else:
					etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.get_price_unit()['total_included'], digits), digits))
					
				tag = etree.QName(self._cbc, 'PriceTypeCode')
				"""if invoice_id.pe_invoice_code == '08':
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:segem:catalogos:catalogo10', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_debit_note_code
				elif invoice_id.pe_invoice_code == '07':
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:segem:catalogos:catalogo09', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_credit_note_code
				else:
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = '01'
				"""
				etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = '01'
			# (39) Valor referencial unitario en operaciones no onerosas
			if price_unit_all == 0.0 or line.pe_affectation_code in ['30', '31', '32', '33', '34', '35', '36']:
				tag = etree.QName(self._cac, 'AlternativeConditionPrice')
				alternative = etree.SubElement(pricing, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'PriceAmount')
				etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.get_price_unit()['total_included'], digits), digits))
				tag = etree.QName(self._cbc, 'PriceTypeCode')
				codigo_precio = '02'
				if line.pe_affectation_code in ['30']:
					codigo_precio = '01'
				etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = codigo_precio
			
			# 40
			if line.discount > 0 and line.discount < 100 and invoice_id.pe_invoice_code not in ('07', '08'):
				tag = etree.QName(self._cac, 'AllowanceCharge')
				charge = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
				# Como es descuento asignamos "false"
				tag = etree.QName(self._cbc, 'ChargeIndicator')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
				# Deberia tomar del catalogo 53 (futura mejora)
				tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = '00'
				# Es el porcentaje que le corresponde por el descuento aplicado. Para el caso de retención por ejemplo es 0.03.
				tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round_up(line.discount / 100, 5))
				# Monto del descuento del ítem
				tag = etree.QName(self._cbc, 'Amount')
				etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.discount == 100 and 0.0 or line.amount_discount, digits), 2))
				# Monto sobre el cual se le debe aplicar el descuento del ítem
				tag = etree.QName(self._cbc, 'BaseAmount')
				etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.price_subtotal + line.amount_discount, digits), 2))
			
			# 41
			if line.pe_charge_amount > 0 and invoice_id.pe_invoice_code not in ('07', '08'):
				tag = etree.QName(self._cac, 'AllowanceCharge')
				charge = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ChargeIndicator')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'true'
				# Deberia tomar del catalogo 53 (futura mejora)
				tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = '50'
				tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
				etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round_up(line.pe_charge_amount / line.price_subtotal, 5))
				tag = etree.QName(self._cbc, 'Amount')
				etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.pe_charge_amount, digits), 2))
				tag = etree.QName(self._cbc, 'BaseAmount')
				etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.price_subtotal + line.amount_discount, digits), 2))

			# 42
			tag = etree.QName(self._cac, 'TaxTotal')
			total = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxAmount')
			
			# se calculan los impuestos sobre el precion ya con el descuento si es que lo hubiera
			taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
			tax_total_amount = 0.0
			tax_vals = {}
			for tax_val in taxes.get('taxes', []):
				tax_id = invoice_id.env['account.tax'].browse([tax_val.get('id')])
				if not tax_id.pe_is_charge:
					tax_total_amount += tax_val.get('amount', 0.0)
				tax_vals[tax_val.get('id')] = tax_val

			#digits = invoice_id.currency_id.rounding
			if line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito']):
				#tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.pe_tax_type.code != constantes.IMPUESTO['gratuito']).compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
				tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito']).compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
				#etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_total_values.get('total_included', 0.0) - tax_total_values.get('total_excluded', 0.0)), precision_rounding=digits), 2))
				etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = "0.00"
				tax_total_amount = 0.0
				tax_vals = {}
				for tax_val in tax_total_values.get('taxes', []):
					tax_id = invoice_id.env['account.tax'].browse([tax_val.get('id')])
					if not tax_id.pe_is_charge:
						tax_total_amount += tax_val.get('amount', 0.0)
					tax_vals[line.tax_ids.filtered(lambda tax: tax.pe_tax_type.code == constantes.IMPUESTO['gratuito'])[0].id] = tax_val

			elif line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto']):
				tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.pe_tax_type.code != constantes.IMPUESTO['inafecto']).compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
				etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_total_values.get('total_included', 0.0) - tax_total_values.get('total_excluded', 0.0)), precision_rounding=digits), 2))
				tax_total_amount = 0.0
				tax_vals = {}
				for tax_val in tax_total_values.get('taxes', []):
					tax_id = invoice_id.env['account.tax'].browse([tax_val.get('id')])
					if not tax_id.pe_is_charge:
						tax_total_amount += tax_val.get('amount', 0.0)
					tax_vals[line.tax_ids.filtered(lambda tax: tax.pe_tax_type.code == constantes.IMPUESTO['inafecto'])[0].id] = tax_val
			else:
				tax_total_values = False
				etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(tax_total_amount, 2))
			
			digits_rounding_precision = invoice_id.currency_id.rounding
			for tax in line.tax_ids.filtered(lambda tax: tax.pe_is_charge == False):
				if tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito']:
					tag = etree.QName(self._cac, 'TaxSubtotal')
					subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'TaxableAmount')
					
					if line.pe_affectation_code in ['21', '31', '32', '33', '34', '35', '36']:
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_total_values.get('total_excluded', 0.0)), precision_rounding=digits), 2))
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = "0.00"
					elif line.pe_affectation_code in ['11', '12', '13', '14', '15', '16', '17']:
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_vals.get(tax.id, {}).get('base', 0.0)), precision_rounding=digits), 2))
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits), 2))

					tag = etree.QName(self._cac, 'TaxCategory')
					category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						
					if line.discount == 100:
						tag = etree.QName(self._cbc, 'Percent')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
						amount = tax.pe_tax_type.code == constantes.IMPUESTO['gratuito'] and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = str(amount)
					if tax.pe_tax_type.code == constantes.IMPUESTO['isc']:
						tag = etree.QName(self._cbc, 'TierRange')
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = line.pe_tier_range or tax.pe_tier_range
					else:
						tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
						etree.SubElement(category, (tag.text), listAgencyName='PE:SUNAT', listName='Afectacion del IGV', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07', nsmap={'cbc': tag.namespace}).text = line.pe_affectation_code
					tag = etree.QName(self._cac, 'TaxScheme')
					scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ID')
					etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.code
					tag = etree.QName(self._cbc, 'Name')
					etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
					tag = etree.QName(self._cbc, 'TaxTypeCode')
					etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code
				elif tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto']:
					tag = etree.QName(self._cac, 'TaxSubtotal')
					subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'TaxableAmount')
					etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(line.price_subtotal, 2))
					#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.get_price_unit()['total_included'], digits), digits))
					tag = etree.QName(self._cbc, 'TaxAmount')
					etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits), 2))
					tag = etree.QName(self._cac, 'TaxCategory')
					category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						
					tag = etree.QName(self._cbc, 'Percent')
					taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['inafecto'])
					amount = tax.pe_tax_type.code == constantes.IMPUESTO['inafecto'] and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
					etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = str(amount)

					if tax.pe_tax_type.code == constantes.IMPUESTO['isc']:
						tag = etree.QName(self._cbc, 'TierRange')
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = line.pe_tier_range or tax.pe_tier_range
					else:
						tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
						etree.SubElement(category, (tag.text), listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07', nsmap={'cbc': tag.namespace}).text = line.pe_affectation_code
					tag = etree.QName(self._cac, 'TaxScheme')
					scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ID')
					etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.code
					tag = etree.QName(self._cbc, 'Name')
					etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
					tag = etree.QName(self._cbc, 'TaxTypeCode')
					etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code
				elif tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['ICBPER']:
					if line.discount == 100:
						pass
					else:
						tag = etree.QName(self._cac, 'TaxSubtotal')
						subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxAmount')
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits), 2))
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits_rounding_precision), 2))
						tag = etree.QName(self._cbc, 'BaseUnitMeasure')
						etree.SubElement(subtotal, (tag.text), unitCode='NIU', nsmap={'cbc': tag.namespace}).text = str(int(line.quantity))
						tag = etree.QName(self._cac, 'TaxCategory')
						category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'PerUnitAmount')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
						amount = tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito'] and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
						etree.SubElement(category, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(amount)
						tag = etree.QName(self._cac, 'TaxScheme')
						scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ID')
						etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.code
						tag = etree.QName(self._cbc, 'Name')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
						tag = etree.QName(self._cbc, 'TaxTypeCode')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code
				else:
					if line.discount == 100:
						pass
					else:
						"""
							format_float(line_vals['tax_details']['total_included'] - line_vals['tax_details']['total_excluded'])
						"""
						# Monto final
						tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.pe_tax_type.code != constantes.IMPUESTO['gratuito']).compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
						monto_incluido = tax_total_values.get('total_included', 0.0)
						monto_excluido = tax_total_values.get('total_excluded', 0.0)
						impuesto_aplicado = round_up(float_round((monto_incluido - monto_excluido), precision_rounding=digits), 2)
						
						tag = etree.QName(self._cac, 'TaxSubtotal')
						subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxableAmount')
						currencies = invoice_id._get_lines_onchange_currency().currency_id
						if invoice_id.move_type == 'entry' or invoice_id.is_outbound():
							sign = 1
						else:
							sign = -1
						monto_base_o = sign * (line.amount_currency if len(currencies) == 1 else line.balance)
						monto_base = round_down(monto_base_o, 2)
						if len(line.tax_ids) == 1 and monto_base != bases_json[line.id]:
							monto_base = round_up(monto_base_o, 2)

						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(monto_base)
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round((tax_vals.get(tax.id, {}).get('base', 0.0)), precision_rounding=digits), 2))
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(monto_incluido, precision_rounding=digits), 2))
						tag = etree.QName(self._cbc, 'TaxAmount')
						monto_impuestos = tax_vals.get(tax.id, {}).get('amount', 0.0)
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(monto_impuestos, 2))
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(impuesto_aplicado)
						
						
						tag = etree.QName(self._cac, 'TaxCategory')
						category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'Percent')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
						amount = tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['gratuito'] and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = str(amount)
						if tax.pe_tax_type.code == constantes.IMPUESTO['isc']:
							tag = etree.QName(self._cbc, 'TierRange')
							etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = line.pe_tier_range or tax.pe_tier_range
						else:
							if tax.pe_tax_type.code == '1016':
								tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
								etree.SubElement(category, (tag.text), listAgencyName='PE:SUNAT', listName='Afectacion del IGV', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07', nsmap={'cbc': tag.namespace}).text = '17'
							else:
								tag = etree.QName(self._cbc, 'TaxExemptionReasonCode')
								etree.SubElement(category, (tag.text), listAgencyName='PE:SUNAT', listName='Afectacion del IGV', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07', nsmap={'cbc': tag.namespace}).text = line.pe_affectation_code
						tag = etree.QName(self._cac, 'TaxScheme')
						scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ID')
						etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.code
						tag = etree.QName(self._cbc, 'Name')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.name
						tag = etree.QName(self._cbc, 'TaxTypeCode')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = tax.pe_tax_type.un_ece_code

			# fin del 42
			# 43 Sistema de ISC por ítem

			# fin de 43 (revisar codigo de implementacion)
			
			# inicio 44
			tag = etree.QName(self._cac, 'Item')
			item = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})

			# 44
			tag = etree.QName(self._cbc, 'Description')
			product_name = line.name
			if not product_name and line.product_id:
				product_name = line.product_id.name

			if not product_name:
				product_name = 'Servicio brindado'
			product_name = product_name.replace('\n', ' ')[:250]
			etree.SubElement(item, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(product_name.strip())
			
			if line.product_id:
				# 45
				tag = etree.QName(self._cac, 'SellersItemIdentification')
				identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				cod_producto = line.product_id and line.product_id.default_code or '-'
				if cod_producto == '-':
					cod_producto = 'CPROD%s' % str(line.product_id.id)
					
				cod_producto = cod_producto.replace(" ", "")

				if len(cod_producto) > 30:
					cod_producto = cod_producto[0:30]

				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = cod_producto
				if line.product_id.categ_id.pe_unspsc_code:
					# 46
					tag = etree.QName(self._cac, 'CommodityClassification')
					identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ItemClassificationCode')
					etree.SubElement(identification, (tag.text), listID='UNSPSC', listAgencyName='GS1 US', listName='Item Classification', nsmap={'cbc': tag.namespace}).text = line.product_id.categ_id.pe_unspsc_code or '-'
			# 47 (por el momento se ha dejado de usar, mejorar implementación)
			if line.pe_license_plate or invoice_id.pe_license_plate and line.product_id.require_plate:
				tag = etree.QName(self._cac, 'AdditionalItemProperty')
				identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'Name')
				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Gastos Art. 37 Renta: Número de Placa'
				tag = etree.QName(self._cbc, 'NameCode')
				etree.SubElement(identification, (tag.text), listName='Propiedad del item', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo55', nsmap={'cbc': tag.namespace}).text = '7000'
				tag = etree.QName(self._cbc, 'Value')
				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = line.pe_license_plate or invoice_id.pe_license_plate or ''
			
			# 48
			tag = etree.QName(self._cac, 'Price')
			price = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'PriceAmount')
			if line.pe_affectation_code in ['30']:
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(line.get_price_unit_sunat()['total_excluded'], 6), 6))
			elif line.pe_affectation_code in ['31', '32', '33', '34', '35', '36']:
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = "0.00"
			elif price_unit_all == 0.0:
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(price_unit_all, 6))
			elif invoice_id.move_type in ['out_refund']:
				extension_amount_refund = str(round_up(float_round(line.get_price_unit_sunat()['total_excluded'], 6), 6))
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = extension_amount_refund
			else:
				precio_sunat = line.get_price_unit_sunat()['total_excluded']
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(float_round(precio_sunat, 6), 6))
			

	# Para la parte donde indica si la factura es de detraccion
	def _agregar_informacion_detraccion(self, invoice_id):
		if invoice_id.tiene_detraccion:
			tag = etree.QName(self._cac, 'PaymentMeans')
			payment_means = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_means, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Detraccion'
			tag = etree.QName(self._cbc, 'PaymentMeansCode')
			etree.SubElement(payment_means, (tag.text), listAgencyName='PE:SUNAT', listName='Medio de pago', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo59', nsmap={'cbc': tag.namespace}).text = '001'
			tag = etree.QName(self._cac, 'PayeeFinancialAccount')
			financial = etree.SubElement(payment_means, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(financial, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.nro_cuenta_detraccion

			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Detraccion'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), schemeAgencyName='PE:SUNAT', schemeName='Codigo de detraccion', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo54', nsmap={'cbc': tag.namespace}).text = invoice_id.detraccion_id
			tag = etree.QName(self._cbc, 'Note')
			amount_total = invoice_id.amount_total
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.monto_neto_pagar, 2))
			tag = etree.QName(self._cbc, 'PaymentPercent')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = str(invoice_id.porc_detraccion)
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(payment_terms, (tag.text), currencyID=(invoice_id.moneda_base.name), nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.monto_detraccion, 2))

	# Crear la parte del xml donde se asigna si es al "credito" o al "contado"
	def _agregar_informacion_tipo_transaccion(self, invoice_id):
		if invoice_id.invoice_payment_term_id and invoice_id.invoice_payment_term_id.tipo_transaccion == 'credito' or invoice_id.invoice_date_due > invoice_id.invoice_date:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Credito'
			tag = etree.QName(self._cbc, 'Amount')
			#amount_total = invoice_id.amount_total
			amount_total = 0
			if invoice_id.company_id.currency_id.id == invoice_id.currency_id.id:
				amount_total = invoice_id.monto_neto_pagar
			else:
				amount_total = invoice_id.monto_neto_pagar_base

			etree.SubElement(payment_terms, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))

			cuotas_pago = invoice_id.obtener_cuotas_pago()
			contador = 0
			for cuota in cuotas_pago:
				contador += 1
				tag = etree.QName(self._cac, 'PaymentTerms')
				payment_terms_cuota = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
				tag = etree.QName(self._cbc, 'PaymentMeansID')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Cuota'+ ("{0:03d}".format(contador))
				tag = etree.QName(self._cbc, 'Amount')
				etree.SubElement(payment_terms_cuota, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = "%.2f" % cuota['amount'] #str(round_up(cuota['amount'], 2)) #%.2f'%(cuota['amount'])
				tag = etree.QName(self._cbc, 'PaymentDueDate')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cuota['date_maturity'])
		else:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Contado'

	# Crear la parte del xml donde se asigna si es al "credito" o al "contado"
	def _agregar_informacion_tipo_transaccion_notas_credito(self, invoice_id):
		if not invoice_id.pe_credit_note_code == '13':
			return
		factura_origen = invoice_id.reversed_entry_id
		if factura_origen.invoice_payment_term_id.tipo_transaccion == 'credito' or factura_origen.invoice_date_due > factura_origen.invoice_date:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Credito'
			tag = etree.QName(self._cbc, 'Amount')
			#amount_total = invoice_id.amount_total
			amount_total = 0
			factura_origen.write({
				"invoice_payment_term_id": invoice_id.invoice_payment_term_id,
				"invoice_date_due": invoice_id.invoice_date_due,
			})
			factura_origen._compute_needed_terms()
			if factura_origen.company_id.currency_id.id == factura_origen.currency_id.id:
				amount_total = factura_origen.monto_neto_pagar
			else:
				amount_total = factura_origen.monto_neto_pagar_base

			etree.SubElement(payment_terms, (tag.text), currencyID=(factura_origen.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(amount_total, 2))

			cuotas_pago = factura_origen.obtener_cuotas_pago()
			contador = 0
			for cuota in cuotas_pago:
				contador += 1
				tag = etree.QName(self._cac, 'PaymentTerms')
				payment_terms_cuota = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
				tag = etree.QName(self._cbc, 'PaymentMeansID')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Cuota'+ ("{0:03d}".format(contador))
				tag = etree.QName(self._cbc, 'Amount')
				etree.SubElement(payment_terms_cuota, (tag.text), currencyID=(factura_origen.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round_up(cuota['amount'], 2))
				tag = etree.QName(self._cbc, 'PaymentDueDate')
				etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cuota['date_maturity'])
		else:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Contado'


	"""
		####### Procesos para generar los distintos documentos electronicos
		####### soportados por el sistema
	"""

	# proceso primario para generar el xml para una factura usando la tabla account.move y relaciones
	def getInvoice(self, invoice_id):
		xmlns = etree.QName('urn:oasis:names:specification:ubl:schema:xsd:Invoice-2', 'Invoice')
		nsmap1 = OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
			('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), ('xsi', self._xsi)])
		self._root = etree.Element((xmlns.text), nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions = etree.SubElement((self._root), (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'UBLExtension')
		extension = etree.SubElement(extensions, (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'ExtensionContent')
		content = etree.SubElement(extension, (tag.text), nsmap={'ext': tag.namespace})
		self._agregar_informacion_firma(content)
		self._agregar_informacion_ubl()
		self._agregar_informacion_general_comprobante(invoice_id)
		self._agregar_informacion_certificado(invoice_id)
		self._agregar_informacion_empresa(invoice_id)
		self._agregar_informacion_cliente(invoice_id)
		self._agregar_informacion_detraccion(invoice_id)
		self._agregar_informacion_tipo_transaccion(invoice_id)
		self._agregar_informacion_anticipos(invoice_id)
		self._agregar_informacion_descuentos_globales(invoice_id)
		self._agregar_informacion_de_impuestos(invoice_id)
		self._agregar_informacion_montos_totales(invoice_id)
		self._agregar_informacion_lineas_comprobante(invoice_id)
		xml_str = etree.tostring((self._root), pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)
		return xml_str

	# proceso primario para generar el xml para una nota de credito
	def getCreditNote(self, invoice_id):
		xmlns = etree.QName('urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2', 'CreditNote')
		nsmap1 = OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
			('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), ('xsi', self._xsi)])
		self._root = etree.Element((xmlns.text), nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions = etree.SubElement((self._root), (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'UBLExtension')
		extension = etree.SubElement(extensions, (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'ExtensionContent')
		content = etree.SubElement(extension, (tag.text), nsmap={'ext': tag.namespace})
		self._agregar_informacion_firma(content)
		self._agregar_informacion_ubl()
		self._agregar_informacion_general_comprobante(invoice_id)
		self._agregar_informacion_DiscrepancyResponse(invoice_id)
		self._agregar_informacion_BillingReference(invoice_id)
		self._agregar_informacion_guias_en_notas(invoice_id)
		self._agregar_informacion_certificado(invoice_id)
		self._agregar_informacion_empresa(invoice_id)
		self._agregar_informacion_cliente(invoice_id)
		self._agregar_informacion_tipo_transaccion_notas_credito(invoice_id)
		self._agregar_informacion_descuentos_globales(invoice_id)
		self._agregar_informacion_de_impuestos(invoice_id)
		self._agregar_informacion_montos_totales(invoice_id)
		self._agregar_informacion_lineas_comprobante(invoice_id)
		xml_str = etree.tostring((self._root), pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)
		return xml_str

	# proceso primario para generar el xml para una nota de debito
	def getDebitNote(self, invoice_id):
		xmlns = etree.QName('urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2', 'DebitNote')
		nsmap1 = OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
			('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), ('xsi', self._xsi)])
		self._root = etree.Element((xmlns.text), nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions = etree.SubElement((self._root), (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'UBLExtension')
		extension = etree.SubElement(extensions, (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'ExtensionContent')
		content = etree.SubElement(extension, (tag.text), nsmap={'ext': tag.namespace})
		self._agregar_informacion_firma(content)
		self._agregar_informacion_ubl()
		self._agregar_informacion_general_comprobante(invoice_id)
		self._agregar_informacion_DiscrepancyResponse(invoice_id)
		self._agregar_informacion_BillingReference(invoice_id)
		self._agregar_informacion_guias_en_notas(invoice_id)
		self._agregar_informacion_certificado(invoice_id)
		self._agregar_informacion_empresa(invoice_id)
		self._agregar_informacion_cliente(invoice_id)
		self._agregar_informacion_de_impuestos(invoice_id)
		self._agregar_informacion_montos_totales(invoice_id)
		self._agregar_informacion_lineas_comprobante(invoice_id)
		xml_str = etree.tostring((self._root), pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)
		return xml_str

	# proceso primario para generar el xml para una anulacion
	def getVoidedDocuments(self, batch):
		xmlns = etree.QName('urn:sunat:names:specification:ubl:peru:schema:xsd:VoidedDocuments-1', 'VoidedDocuments')
		nsmap1 = OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
			('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), ('xsi', self._xsi)])
		self._root = etree.Element((xmlns.text), nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions = etree.SubElement((self._root), (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'UBLExtension')
		extension = etree.SubElement(extensions, (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'ExtensionContent')
		content = etree.SubElement(extension, (tag.text), nsmap={'ext': tag.namespace})
		self._agregar_informacion_firma(content)
		self._agregar_informacion_ubl(version='2.0', customization='1.0')
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = batch.name
		tag = etree.QName(self._cbc, 'ReferenceDate')
		fecha_emitio_cpe = self.convert_TZ_UTC(batch, batch.date)
		# fecha que se emitio el cpe
		#etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = fecha_emitio_cpe.strftime('%Y-%m-%d')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = batch.date.strftime('%Y-%m-%d')
		tag = etree.QName(self._cbc, 'IssueDate')
		fecha_envio = self.convert_TZ_UTC(batch, batch.send_date)
		# fecha del envio
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = fecha_envio.strftime('%Y-%m-%d')
		self._agregar_informacion_certificado(batch)
		self._agregar_informacion_empresa_2_0(batch)
		cont = 1
		for invoice_id in batch.voided_ids:
			if invoice_id.pe_cpe_id.state in ('draft', 'generate', 'cancel'):
				raise UserError(_('The invoice N° %s must be sent to the sunat to generate this document.') % invoice_id.l10n_latam_document_number)
			tag = etree.QName(self._sac, 'VoidedDocumentsLine')
			line = etree.SubElement((self._root), (tag.text), nsmap={'sac': tag.namespace})
			tag = etree.QName(self._cbc, 'LineID')
			etree.SubElement(line, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cont)
			cont += 1
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(line, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_type_id.code
			tag = etree.QName(self._sac, 'DocumentSerialID')
			etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace}).text = invoice_id.l10n_latam_document_number and invoice_id.l10n_latam_document_number.split('-')[0]
			tag = etree.QName(self._sac, 'DocumentNumberID')
			etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace}).text = invoice_id.l10n_latam_document_number and invoice_id.l10n_latam_document_number.split('-')[1]
			tag = etree.QName(self._sac, 'VoidReasonDescription')
			etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace}).text = invoice_id.state in ('cancel',
																										 'annul') and 'Anulado'

		xml_str = etree.tostring((self._root), pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)
		return xml_str

	# proceso primario para generar el xml para los resumnes de boletas
	def getSummaryDocuments(self, batch):
		journal_ids = batch.summary_ids.mapped('journal_id')
		xmlns = etree.QName('urn:sunat:names:specification:ubl:peru:schema:xsd:SummaryDocuments-1', 'SummaryDocuments')
		nsmap1 = OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ds', self._ds), 
			('ext', self._ext), ('sac', self._sac), ('xsi', self._xsi)])
		self._root = etree.Element((xmlns.text), nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions = etree.SubElement((self._root), (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'UBLExtension')
		extension = etree.SubElement(extensions, (tag.text), nsmap={'ext': tag.namespace})
		tag = etree.QName(self._ext, 'ExtensionContent')
		content = etree.SubElement(extension, (tag.text), nsmap={'ext': tag.namespace})
		self._agregar_informacion_firma(content)
		self._agregar_informacion_ubl(version='2.0', customization='1.1')
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = batch.name
		tag = etree.QName(self._cbc, 'ReferenceDate')
		fecha_emitio_cpe = self.convert_TZ_UTC(batch, batch.date)
		# fecha que se emitio el cpe
		#etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = fecha_emitio_cpe.strftime('%Y-%m-%d')
		#etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = batch.pe_invoice_date.strftime('%Y-%m-%d')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = batch.date.strftime('%Y-%m-%d')
		tag = etree.QName(self._cbc, 'IssueDate')
		fecha_envio= self.convert_TZ_UTC(batch, batch.send_date)
		# fecha del envio
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = fecha_envio.strftime('%Y-%m-%d')
		self._agregar_informacion_certificado(batch)
		self._agregar_informacion_empresa_2_0(batch)
		cont = 1
		for journal_id in journal_ids:
			summary_total = 0
			summary_untaxed = 0
			summary_inaffected = 0
			summary_exonerated = 0
			summary_gift = 0
			summary_export = 0
			for invoice_id in batch.summary_ids.filtered(lambda inv: inv.journal_id.id == journal_id.id).sorted(key=(lambda r: r.name)):
				if invoice_id.pe_cpe_id.state in ('draft', 'cancel'):
					raise UserError(_('The invoice N° %s must be sent to the sunat to generate this document.') % invoice_id.l10n_latam_document_number)
				else:
					taxes = []
					taxes.append({'amount_tax_line':0,  'tax_name': constantes.IMPUESTO['igv'],  'tax_description':'IGV',  'tax_type_pe':'VAT'})
					taxes.append({'amount_tax_line':0,  'tax_name':constantes.IMPUESTO['isc'],  'tax_description':'ISC',  'tax_type_pe':'EXC'})
					taxes.append({'amount_tax_line':0,  'tax_name':'9999',  'tax_description':'OTR',  'tax_type_pe':'OTH'})
					taxes.append({'amount_tax_line':0,  'tax_name': constantes.IMPUESTO['ICBPER'],  'tax_description':'ICBPER',  'tax_type_pe':'OTH'})
					total = invoice_id.amount_total
					summary_allowcharge = invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax

					datos = invoice_id.tax_totals #.replace("false", "False")
					#datos = json.loads(datos)

					datos_sub = datos["groups_by_subtotal"]
					importe_libre = datos_sub["Importe libre de impuestos"] if "Importe libre de impuestos" in datos_sub  else False
					if not importe_libre:
						for reg in datos_sub:
							importe_libre = reg
							break

					amount_by_group = importe_libre

					for group_tax in amount_by_group:
						group_id = group_tax['tax_group_id']
						tax_id = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == group_id)
						tax_id = tax_id and tax_id[0]
						if tax_id.pe_tax_type.code not in (constantes.IMPUESTO['igv'], constantes.IMPUESTO['isc'], '9999', constantes.IMPUESTO['ICBPER']):
							continue
						amount_tax_line = group_tax['tax_group_amount']
						for i in range(len(taxes)):
							if taxes[i]['tax_name'] == tax_id.pe_tax_type.code:
								taxes[i]['amount_tax_line'] += amount_tax_line

					currency_code = invoice_id.currency_id.name
					tag = etree.QName(self._sac, 'SummaryDocumentsLine')
					line = etree.SubElement((self._root), (tag.text), nsmap={'sac': tag.namespace})
					tag = etree.QName(self._cbc, 'LineID')
					etree.SubElement(line, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cont)
					cont += 1
					tag = etree.QName(self._cbc, 'DocumentTypeCode')
					etree.SubElement(line, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_type_id.code
					tag = etree.QName(self._cbc, 'ID')
					etree.SubElement(line, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_number
					self._agregar_informacion_cliente_2_0(invoice_id, line)
					if invoice_id.l10n_latam_document_type_id.code in ('07', '08'):
						self._agregar_informacion_BillingReference_2_0(invoice_id, line)
					tag = etree.QName(self._cac, 'Status')
					status = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ConditionCode')
					if invoice_id.pe_summary_id.is_voided:
						etree.SubElement(status, (tag.text), nsmap={'cbc': tag.namespace}).text = '3'
					else:
						etree.SubElement(status, (tag.text), nsmap={'cbc': tag.namespace}).text = '1'
					tag = etree.QName(self._sac, 'TotalAmount')
					etree.SubElement(line, (tag.text), currencyID=currency_code, nsmap={'sac': tag.namespace}).text = str(round_up(total, 2))
					if invoice_id.pe_taxable_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_taxable_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '01'
					if invoice_id.pe_exonerated_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_exonerated_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '02'
					if invoice_id.pe_unaffected_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_unaffected_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '03'
					if invoice_id.pe_free_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_free_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '05'
					if summary_allowcharge > 0:
						tag = etree.QName(self._cac, 'AllowanceCharge')
						allowance = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ChargeIndicator')
						etree.SubElement(allowance, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
						tag = etree.QName(self._cbc, 'Amount')
						etree.SubElement(allowance, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(summary_allowcharge, 2))
					if invoice_id.pe_charge_total > 0:
						tag = etree.QName(self._cac, 'AllowanceCharge')
						allowance = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ChargeIndicator')
						etree.SubElement(allowance, (tag.text), nsmap={'cbc': tag.namespace}).text = 'true'
						tag = etree.QName(self._cbc, 'Amount')
						etree.SubElement(allowance, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(invoice_id.pe_charge_total, 2))
				for tax in taxes:
					if tax['tax_name'] == '9999' and tax['amount_tax_line'] > 0:
						tag = etree.QName(self._cac, 'TaxTotal')
						total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
						tag = etree.QName(self._cac, 'TaxSubtotal')
						tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TotalAmount')
						etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
						tag = etree.QName(self._cac, 'TaxCategory')
						category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cac, 'TaxScheme')
						scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ID')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_name'])
						tag = etree.QName(self._cbc, 'Name')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_description'])
						tag = etree.QName(self._cbc, 'TaxTypeCode')
						etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_type_pe'])
					else:
						if tax['amount_tax_line'] > 0 or tax['tax_name'] == constantes.IMPUESTO['igv']:
							tag = etree.QName(self._cac, 'TaxTotal')
							total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cbc, 'TaxAmount')
							etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
							tag = etree.QName(self._cac, 'TaxSubtotal')
							tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cbc, 'TaxAmount')
							etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
							tag = etree.QName(self._cac, 'TaxCategory')
							category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cac, 'TaxScheme')
							scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cbc, 'ID')
							etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_name'])
							tag = etree.QName(self._cbc, 'Name')
							etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_description'])
							tag = etree.QName(self._cbc, 'TaxTypeCode')
							etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_type_pe'])
						else:
							if tax['amount_tax_line'] > 0 or tax['tax_name'] == constantes.IMPUESTO['ICBPER']:
								tag = etree.QName(self._cac, 'TaxTotal')
								total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cbc, 'TaxAmount')
								etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
								tag = etree.QName(self._cac, 'TaxSubtotal')
								tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cbc, 'TaxAmount')
								etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round_up(tax['amount_tax_line'], 2))
								tag = etree.QName(self._cac, 'TaxCategory')
								category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cac, 'TaxScheme')
								scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cbc, 'ID')
								etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_name'])
								tag = etree.QName(self._cbc, 'Name')
								etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_description'])
								tag = etree.QName(self._cbc, 'TaxTypeCode')
								etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = str(tax['tax_type_pe'])

		xml_str = etree.tostring((self._root), pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)
		return xml_str
