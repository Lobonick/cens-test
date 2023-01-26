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
from dateutil.tz import gettz

_logging = logging.getLogger(__name__)
tz = pytz.timezone('America/Lima')

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

	# Obtiene los datos de cabecera con la firma
	def _getX509Template(self, content):
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

	def _getUBLVersion(self, version=None, customization=None):
		tag = etree.QName(self._cbc, 'UBLVersionID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = version or '2.1'
		tag = etree.QName(self._cbc, 'CustomizationID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = customization or '2.0'

	def _getUBLVersion21(self, version=None, customization=None):
		tag = etree.QName(self._cbc, 'UBLVersionID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = version or '2.1'
		tag = etree.QName(self._cbc, 'CustomizationID')
		etree.SubElement((self._root), (tag.text), schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = customization or '2.0'

	def _getDocumentDetail21(self, invoice_id):
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_number or ''
		tag = etree.QName(self._cbc, 'IssueDate')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_date.strftime('%Y-%m-%d')
		tag = etree.QName(self._cbc, 'IssueTime')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_date.strftime('%H:%M:%S')
		if invoice_id.pe_invoice_code in ('01', '03'):
			tag = etree.QName(self._cbc, 'InvoiceTypeCode')
			etree.SubElement((self._root), (tag.text), listID=(invoice_id.pe_sunat_transaction51), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_invoice_code
		for line in invoice_id.pe_additional_property_ids:
			tag = etree.QName(self._cbc, 'Note')
			etree.SubElement((self._root), (tag.text), languageLocaleID=(line.code), nsmap={'cbc': tag.namespace}).text = line.value
		if invoice_id.tiene_detraccion:
			tag = etree.QName(self._cbc, 'Note')
			etree.SubElement((self._root), (tag.text), languageLocaleID='2006', nsmap={'cbc': tag.namespace}).text = 'Operación sujeta al Sistema de Pago de Obligaciones Tributarias'
			#tag = etree.QName(self._cbc, 'Note')
			#etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = 'SERVICIO DE TELEFONIA VOIP - TRONCAL SIP // PERIODO: DEL 01/01/2021 AL 31/01/2021'

		tag = etree.QName(self._cbc, 'DocumentCurrencyCode')
		etree.SubElement((self._root), (tag.text), listID='ISO 4217 Alpha', listName='Currency', listAgencyName='United Nations Economic Commission for Europe', nsmap={'cbc': tag.namespace}).text = invoice_id.currency_id.name
		tag = etree.QName(self._cbc, 'LineCountNumeric')
		etree.SubElement((self._root), (tag.text), nsmap={'cbc': tag.namespace}).text = str(len(invoice_id.invoice_line_ids))
		if invoice_id.pe_invoice_code in ('01', '03'):
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


			if invoice_id.env.context.get('despatch_numbers'):
				if invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id):
					for despatch_number in invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id, []):
						tag = etree.QName(self._cac, 'DespatchDocumentReference')
						despatch = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ID')
						etree.SubElement(despatch, (tag.text), nsmap={'cbc': tag.namespace}).text = despatch_number
						tag = etree.QName(self._cbc, 'DocumentTypeCode')
						etree.SubElement(despatch, (tag.text), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = '09'

			if invoice_id.pe_additional_type:
				tag = etree.QName(self._cac, 'AdditionalDocumentReference')
				additional = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(additional, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_additional_number
				tag = etree.QName(self._cbc, 'DocumentTypeCode')
				etree.SubElement(additional, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_additional_type

	def _getSignature(self, invoice_id):
		if not invoice_id.company_id.partner_id.doc_number:
			raise UserError('No se ha establecido un numero de documento para %s' % invoice_id.company_id.partner_id.name)
		tag = etree.QName(self._cac, 'Signature')
		signature = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(signature, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id._name == 'pe.cpe' and invoice_id.name or invoice_id.name
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

	def _getCompany(self, invoice_id):
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

	def _getCompany21(self, invoice_id):
		tag = etree.QName(self._cac, 'AccountingSupplierParty')
		supplier = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'Party')
		party = etree.SubElement(supplier, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')
		party_identification = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(party_identification, (tag.text), schemeID=(invoice_id.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code), schemeName='Documento de Identidad', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06', nsmap={'cbc': tag.namespace}).text = invoice_id.company_id.partner_id.doc_number
		tag = etree.QName(self._cac, 'PartyName')
		party_name = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Name')
		comercial_name = invoice_id.company_id.partner_id.commercial_name.strip() or '-'
		etree.SubElement(party_name, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(comercial_name)
		tag = etree.QName(self._cac, 'PartyLegalEntity')
		party_legal = etree.SubElement(party, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')
		legal_name = invoice_id.company_id.partner_id.legal_name.strip() or '-'
		etree.SubElement(party_legal, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(legal_name)
		tag = etree.QName(self._cac, 'RegistrationAddress')
		address = etree.SubElement(party_legal, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		ubigeo = invoice_id.company_id.partner_id.l10n_pe_district.code
		etree.SubElement(address, (tag.text), schemeAgencyName='PE:INEI', schemeName='Ubigeos', nsmap={'cbc': tag.namespace}).text = ubigeo
		tag = etree.QName(self._cbc, 'AddressTypeCode')
		pe_branch_code = invoice_id.pe_branch_code or '0000'
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = pe_branch_code
		tag = etree.QName(self._cbc, 'CitySubdivisionName')
		urba = 'NONE'
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = urba
		tag = etree.QName(self._cbc, 'CityName')
		province_id = invoice_id.company_id.partner_id.city_id.name.strip()
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = province_id
		tag = etree.QName(self._cbc, 'CountrySubentity')
		state_id = invoice_id.company_id.partner_id.state_id.name
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = state_id
		tag = etree.QName(self._cbc, 'District')
		district_id = invoice_id.company_id.partner_id.l10n_pe_district.name
		etree.SubElement(address, (tag.text), nsmap={'cbc': tag.namespace}).text = district_id
		tag = etree.QName(self._cac, 'AddressLine')
		addresLine = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'Line')
		street_id = invoice_id.company_id.partner_id.street
		etree.SubElement(addresLine, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(street_id)
		tag = etree.QName(self._cac, 'Country')
		country_id = etree.SubElement(address, (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'IdentificationCode')
		country_code = invoice_id.company_id.partner_id.country_id.code
		etree.SubElement(country_id, (tag.text), listID='ISO 3166-1', listAgencyName='United Nations Economic Commission for Europe', listName='Country', nsmap={'cbc': tag.namespace}).text = country_code

	def _getDeliveryTerms(self, invoice_id):
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

	def _getPartner(self, invoice_id, line=None):
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

	def _getPartner21(self, invoice_id, line=None):
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

	def _getDiscrepancyResponse21(self, invoice_id):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'DiscrepancyResponse')
			discrepancy = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ReferenceID')
			etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.name or ''
			tag = etree.QName(self._cbc, 'ResponseCode')
			if invoice_id.move_type == 'out_invoice':
				etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_debit_note_code
			else:
				if invoice_id.move_type == 'out_refund':
					etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.pe_credit_note_code
			tag = etree.QName(self._cbc, 'Description')
			etree.SubElement(discrepancy, (tag.text), nsmap={'cbc': tag.namespace}).text = invoice_id.l10n_latam_document_number or invoice_id.invoice_line_ids[0].name or ''
			
	def _getBillingReference(self, invoice_id, line=None):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'BillingReference')
			reference = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'InvoiceDocumentReference')
			invoice = etree.SubElement(reference, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.l10n_latam_document_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.pe_invoice_code

	# Para agregar los comprobantes relacionados que tenemos con respecto a la factura
	def _getBillingReference21(self, invoice_id, line=None):
		for inv in invoice_id.pe_related_ids:
			tag = etree.QName(self._cac, 'BillingReference')
			reference = etree.SubElement((line or self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'InvoiceDocumentReference')
			invoice = etree.SubElement(reference, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(invoice, (tag.text), nsmap={'cbc': tag.namespace}).text = inv.l10n_latam_document_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(invoice, (tag.text), listAgencyName='PE:SUNAT', listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = inv.pe_invoice_code

	def _getDespatchDocumentReference21(self, invoice_id):
		for despatch_number in invoice_id.env.context.get('despatch_numbers', {}).get(invoice_id.id, []):
			tag = etree.QName(self._cac, 'DespatchDocumentReference')
			reference = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(reference, (tag.text), nsmap={'cbc': tag.namespace}).text = despatch_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')
			etree.SubElement(reference, (tag.text), listName='Tipo de Documento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01', nsmap={'cbc': tag.namespace}).text = '09'

	def _getPrepaidPayment21(self, invoice_id):
		try:
			for line in invoice_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('invoice_ids').filtered(lambda inv: inv.pe_sunat_transaction in ('04', ) and inv.pe_invoice_code in ('01', '03') and inv.id != invoice_id.id and inv.state not in ('draft',
																																   'cancel')):
				tag = etree.QName(self._cac, 'PrepaidPayment')
				prepaid = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				if line.pe_invoice_code == '01':
					etree.SubElement(prepaid, (tag.text), schemeID='02', schemeName='SUNAT:Identificador de Documentos Relacionados', schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = line.name
				else:
					if line.pe_invoice_code == '03':
						etree.SubElement(prepaid, (tag.text), schemeID='03', schemeName='SUNAT:Identificador de Documentos Relacionados', schemeAgencyName='PE:SUNAT', nsmap={'cbc': tag.namespace}).text = line.name
				tag = etree.QName(self._cbc, 'PaidAmount')
				etree.SubElement(prepaid, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(line.amount_total, 2))
				tag = etree.QName(self._cbc, 'InstructionID')
				etree.SubElement(prepaid, (tag.text), schemeID=(invoice_id.partner_id.doc_type or '-'), nsmap={'cbc': tag.namespace}).text = line.partner_id.doc_number or '-'
		except Exception as e:
			pass

	def _getTaxTotal21(self, invoice_id):
		tag = etree.QName(self._cac, 'TaxTotal')
		total = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		tag = etree.QName(self._cbc, 'TaxAmount')
		tax_amount_all = 0.0
		for group_tax in invoice_id.amount_by_group:
			tax = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == group_tax[(-1)])
			tax = tax and tax[0]
			if tax.l10n_pe_edi_tax_code != '7152':
				tax_amount_all += group_tax[1]
				continue

		amount_tax = invoice_id.pe_amount_tax
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(tax_amount_all, 2))
		for group_tax in invoice_id.amount_by_group:
			group_id = group_tax[(-1)]
			base_tax_line = group_tax[2]
			amount_tax_line = group_tax[1]
			tax = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == group_id)
			tax = tax and tax[0]
			if tax.pe_tax_type.code == '9996':
				continue
			else:
				if base_tax_line == 0:
					continue
				tag = etree.QName(self._cac, 'TaxSubtotal')
				tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
				if tax.l10n_pe_edi_tax_code != '7152':
					tag = etree.QName(self._cbc, 'TaxableAmount')
					if tax.l10n_pe_edi_tax_code == '9996':
						etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_free_amount, 2))
					else:
						etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(base_tax_line, 2))
				tag = etree.QName(self._cbc, 'TaxAmount')
				if tax.l10n_pe_edi_tax_code == '9996':
					etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = '0.0'
				else:
					etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_tax_line, 2))
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

		line_ids = invoice_id.invoice_line_ids.filtered(lambda ln: ln.pe_affectation_code not in ('10', '20', '30', '40'))
		tax_ids = line_ids.mapped('tax_ids')
		for tax in tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != '9996' and tax.pe_is_charge == False):
			base_amount = 0.0
			tax_amount = 0.0
			for line in line_ids:
				price_unit = line.price_unit
				if tax.id in line.tax_ids.ids:
					tax_values = tax.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
					base_amount += invoice_id.currency_id.round(tax_values['total_excluded'])
					tax_amount += invoice_id.currency_id.round(tax_values['taxes'][0]['amount'])

			tag = etree.QName(self._cac, 'TaxSubtotal')
			tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxableAmount')
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(base_amount + tax_amount, 2))
			tag = etree.QName(self._cbc, 'TaxAmount')
			amount_tax_line = tax.amount
			etree.SubElement(tax_subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = '0.00'#str(round(amount_tax_line, 2))
			tag = etree.QName(self._cac, 'TaxCategory')
			category = etree.SubElement(tax_subtotal, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cac, 'TaxScheme')
			scheme = etree.SubElement(category, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(scheme, (tag.text), schemeName='Codigo de tributos', schemeAgencyName='PE:SUNAT', schemeURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo05', nsmap={'cbc': tag.namespace}).text = '9996'
			tag = etree.QName(self._cbc, 'Name')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = 'GRA'
			tag = etree.QName(self._cbc, 'TaxTypeCode')
			etree.SubElement(scheme, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FRE'

		return amount_tax

	def _getLegalMonetaryTotal21(self, invoice_id):
		tagname = invoice_id.l10n_latam_document_type_id.code == '08' and 'RequestedMonetaryTotal' or 'LegalMonetaryTotal'
		tag = etree.QName(self._cac, tagname)
		total = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
		prepaid_amount = 0
		try:
			for line in invoice_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('invoice_ids').filtered(lambda inv: inv.pe_sunat_transaction in ('04', ) and inv.pe_invoice_code in ('01', '03') and inv.id != invoice_id.id):
				amount = line.currency_id.with_context(date=(invoice_id.date_invoice)).compute(line.amount_total, invoice_id.currency_id)
				prepaid_amount += amount

		except Exception as e:
			pass

		other = 0.0
		for tax in invoice_id.line_ids.filtered(lambda t: t.tax_line_id.pe_is_charge == True):
			other += invoice_id.currency_id.round(tax.price_total)

		amount_total = invoice_id.amount_total
		amount_untaxed = invoice_id.amount_untaxed
		tag = etree.QName(self._cbc, 'LineExtensionAmount')
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_untaxed, 2))
		tag = etree.QName(self._cbc, 'TaxInclusiveAmount')
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_total, 2))
		tag = etree.QName(self._cbc, 'ChargeTotalAmount')
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(other, 2))
		tag = etree.QName(self._cbc, 'PayableAmount')
		etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_total, 2))

	# Cuando existe descuento por operacines que son gratuitas de acuerdo a los impuestos, (Gratuitos)
	# Descuento global
	def _getAllowanceCharge(self, invoice_id):
		if invoice_id.pe_total_discount > 0.0:
			tag = etree.QName(self._cac, 'AllowanceCharge')
			allowance_charge = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ChargeIndicator')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
			tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
			etree.SubElement(allowance_charge, (tag.text), listAgencyName='PE:SUNAT', listName='Cargo/descuento', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo53', nsmap={'cbc': tag.namespace}).text = '02'
			tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
			etree.SubElement(allowance_charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round((invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax) / (invoice_id.amount_untaxed + (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)), 5))
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax, 2))
			tag = etree.QName(self._cbc, 'BaseAmount')
			amount_total = invoice_id.amount_untaxed + (invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax)
			etree.SubElement(allowance_charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_total, 2))

	# Para la parte del xml donde se agrega la informacion de la lineas con su respectiva cabecera
	def _getDocumentLines21(self, invoice_id):
		cont = 1
		decimal_precision_obj = invoice_id.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		for line in invoice_id.invoice_line_ids.filtered(lambda ln: ln.price_subtotal >= 0):
			price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
			if invoice_id.pe_invoice_code == '08':
				tag = etree.QName(self._cac, 'DebitNoteLine')
			elif invoice_id.pe_invoice_code == '07':
				tag = etree.QName(self._cac, 'CreditNoteLine')
			else:
				tag = etree.QName(self._cac, 'InvoiceLine')
			inv_line = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(inv_line, (tag.text), nsmap={'cbc': tag.namespace}).text = str(cont)
			cont += 1
			if invoice_id.pe_invoice_code == '08':
				tag = etree.QName(self._cbc, 'DebitedQuantity')
			else:
				if invoice_id.pe_invoice_code == '07':
					tag = etree.QName(self._cbc, 'CreditedQuantity')
				else:
					tag = etree.QName(self._cbc, 'InvoicedQuantity')
			etree.SubElement(inv_line, (tag.text), unitCode=(line.product_uom_id and line.product_uom_id.sunat_code or 'NIU'), unitCodeListID='UN/ECE rec 20', unitCodeListAgencyName='United Nations Economic Commission for Europe', nsmap={'cbc': tag.namespace}).text = str(line.quantity)
			tag = etree.QName(self._cbc, 'LineExtensionAmount')
			extension_amount = str(round(float_round(line.get_price_unit()['total_included'], digits), 2))
			etree.SubElement(inv_line, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(line.price_subtotal, 2))
			#etree.SubElement(inv_line, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = extension_amount
			tag = etree.QName(self._cac, 'PricingReference')
			pricing = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			price_unit_all = line.get_price_unit(True)['total_included']
			if price_unit_all > 0:
				tag = etree.QName(self._cac, 'AlternativeConditionPrice')
				alternative = etree.SubElement(pricing, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'PriceAmount')
				if price_unit_all == 0 or invoice_id.pe_invoice_code in ('07', '08'):
					etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(price_unit_all, digits), 10))
				else:
					etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.get_price_unit()['total_included'], digits), 10))
				tag = etree.QName(self._cbc, 'PriceTypeCode')
				"""if invoice_id.pe_invoice_code == '08':
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:segem:catalogos:catalogo10', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_debit_note_code
				elif invoice_id.pe_invoice_code == '07':
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:segem:catalogos:catalogo09', nsmap={'cbc': tag.namespace}).text = invoice_id.pe_credit_note_code
				else:
					etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = '01'
				"""
				etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = '01'
			if price_unit_all == 0.0:
				tag = etree.QName(self._cac, 'AlternativeConditionPrice')
				alternative = etree.SubElement(pricing, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'PriceAmount')
				etree.SubElement(alternative, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.get_price_unit()['total_included'], digits), 10))
				tag = etree.QName(self._cbc, 'PriceTypeCode')
				etree.SubElement(alternative, (tag.text), listName='Tipo de Precio', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16', nsmap={'cbc': tag.namespace}).text = '02'
			if line.discount > 0:
				if line.discount < 100:
					if invoice_id.pe_invoice_code not in ('07', '08'):
						tag = etree.QName(self._cac, 'AllowanceCharge')
						charge = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ChargeIndicator')
						etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
						tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
						etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = '00'
						tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
						etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round(line.discount / 100, 5))
						tag = etree.QName(self._cbc, 'Amount')
						etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.discount == 100 and 0.0 or line.amount_discount, digits), 2))
						tag = etree.QName(self._cbc, 'BaseAmount')
						etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.price_subtotal + line.amount_discount, digits), 2))
			if line.pe_charge_amount > 0:
				if invoice_id.pe_invoice_code not in ('07', '08'):
					tag = etree.QName(self._cac, 'AllowanceCharge')
					charge = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ChargeIndicator')
					etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = 'true'
					tag = etree.QName(self._cbc, 'AllowanceChargeReasonCode')
					etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = '47'
					tag = etree.QName(self._cbc, 'MultiplierFactorNumeric')
					etree.SubElement(charge, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round(line.pe_charge_amount / line.price_subtotal, 5))
					tag = etree.QName(self._cbc, 'Amount')
					etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.pe_charge_amount, digits), 2))
					tag = etree.QName(self._cbc, 'BaseAmount')
					etree.SubElement(charge, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(line.price_subtotal + line.amount_discount, digits), 2))
			tag = etree.QName(self._cac, 'TaxTotal')
			total = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'TaxAmount')
			taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
			tax_total_amount = 0.0
			tax_vals = {}
			for tax_val in taxes.get('taxes', []):
				tax_id = invoice_id.env['account.tax'].browse([tax_val.get('id')])
				if not tax_id.pe_is_charge:
					tax_total_amount += tax_val.get('amount', 0.0)
				tax_vals[tax_val.get('id')] = tax_val

			digits_rounding_precision = invoice_id.currency_id.rounding
			if line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9996'):
				tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.pe_tax_type.code != '9996').compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
				etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_total_values.get('total_included', 0.0) - tax_total_values.get('total_excluded', 0.0)), precision_rounding=digits_rounding_precision), 2))
				tax_total_amount = 0.0
				tax_vals = {}
				for tax_val in tax_total_values.get('taxes', []):
					tax_id = invoice_id.env['account.tax'].browse([tax_val.get('id')])
					if not tax_id.pe_is_charge:
						tax_total_amount += tax_val.get('amount', 0.0)
					tax_vals[line.tax_ids.filtered(lambda tax: tax.pe_tax_type.code == '9996')[0].id] = tax_val

			else:
				etree.SubElement(total, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(tax_total_amount, precision_rounding=digits_rounding_precision), 2))
			for tax in line.tax_ids.filtered(lambda tax: tax.pe_is_charge == False):
				if tax.l10n_pe_edi_tax_code == '9996':
					price_unit = line.price_unit
					tag = etree.QName(self._cac, 'TaxSubtotal')
					subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'TaxableAmount')
					etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('base', 0.0)), precision_rounding=digits_rounding_precision), 2))
					tag = etree.QName(self._cbc, 'TaxAmount')
					etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits_rounding_precision), 2))
					tag = etree.QName(self._cac, 'TaxCategory')
					category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						
					if line.discount == 100:
						tag = etree.QName(self._cbc, 'Percent')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != '9996')
						amount = tax.pe_tax_type.code == '9996' and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = str(amount)
					if tax.pe_tax_type.code == '2000':
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
				elif tax.l10n_pe_edi_tax_code == '7152':
					if line.discount == 100:
						pass
					else:
						tag = etree.QName(self._cac, 'TaxSubtotal')
						subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits_rounding_precision), 2))
						tag = etree.QName(self._cbc, 'BaseUnitMeasure')
						etree.SubElement(subtotal, (tag.text), unitCode='NIU', nsmap={'cbc': tag.namespace}).text = str(int(line.quantity))
						tag = etree.QName(self._cac, 'TaxCategory')
						category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'PerUnitAmount')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != '9996')
						amount = tax.l10n_pe_edi_tax_code == '9996' and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
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
						tax_total_values = line.tax_ids.with_context(round=False).filtered(lambda tax: tax.pe_tax_type.code != '9996').compute_all((line.price_unit), currency=(invoice_id.currency_id), quantity=(line.quantity), product=(line.product_id), partner=(invoice_id.partner_id))
						monto_incluido = tax_total_values.get('total_included', 0.0)
						monto_excluido = tax_total_values.get('total_excluded', 0.0)
						impuesto_aplicado = round(float_round((monto_incluido - monto_excluido), precision_rounding=digits_rounding_precision), 2)
						
						tag = etree.QName(self._cac, 'TaxSubtotal')
						subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxableAmount')
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('base', 0.0)), precision_rounding=digits_rounding_precision), 2))
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round(monto_incluido, precision_rounding=digits_rounding_precision), 2))
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(float_round((tax_vals.get(tax.id, {}).get('amount', 0.0)), precision_rounding=digits_rounding_precision), 2))
						#etree.SubElement(subtotal, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(impuesto_aplicado)
						
						
						tag = etree.QName(self._cac, 'TaxCategory')
						category = etree.SubElement(subtotal, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'Percent')
						taxes_ids = line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != '9996')
						amount = tax.l10n_pe_edi_tax_code == '9996' and (len(taxes_ids) > 1 and taxes_ids[0].amount or taxes_ids.amount) or tax.amount
						etree.SubElement(category, (tag.text), nsmap={'cbc': tag.namespace}).text = str(amount)
						if tax.pe_tax_type.code == '2000':
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

			tag = etree.QName(self._cac, 'Item')
			item = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'Description')
			product_name = line.name.replace('\n', ' ')[:250]
			etree.SubElement(item, (tag.text), nsmap={'cbc': tag.namespace}).text = etree.CDATA(product_name.strip())
			if line.product_id:
				tag = etree.QName(self._cac, 'SellersItemIdentification')
				identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'ID')
				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = line.product_id and line.product_id.default_code or '-'
				if line.product_id.categ_id.pe_unspsc_code:
					tag = etree.QName(self._cac, 'CommodityClassification')
					identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ItemClassificationCode')
					etree.SubElement(identification, (tag.text), listID='UNSPSC', listAgencyName='GS1 US', listName='Item Classification', nsmap={'cbc': tag.namespace}).text = line.product_id.categ_id.pe_unspsc_code or '-'
			if line.pe_license_plate or invoice_id.pe_license_plate and line.product_id.require_plate:
				tag = etree.QName(self._cac, 'AdditionalItemProperty')
				identification = etree.SubElement(item, (tag.text), nsmap={'cac': tag.namespace})
				tag = etree.QName(self._cbc, 'Name')
				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Gastos Art. 37 Renta: Número de Placa'
				tag = etree.QName(self._cbc, 'NameCode')
				etree.SubElement(identification, (tag.text), listName='Propiedad del item', listAgencyName='PE:SUNAT', listURI='urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo55', nsmap={'cbc': tag.namespace}).text = '7000'
				tag = etree.QName(self._cbc, 'Value')
				etree.SubElement(identification, (tag.text), nsmap={'cbc': tag.namespace}).text = line.pe_license_plate or invoice_id.pe_license_plate or ''
			tag = etree.QName(self._cac, 'Price')
			price = etree.SubElement(inv_line, (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'PriceAmount')
			_logging.info('ejecutar la parte del total')
			if price_unit_all == 0.0:
				_logging.info('ejecuta cuando la condicion es: price_unit_all == 0.0')
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(price_unit_all, 2))
			else:
				_logging.info('ejecuta cuando la condicion es else')
				etree.SubElement(price, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(line.get_price_unit()['total_excluded'], 2))

	# Para la parte donde indica si la factura es de detraccion
	def _getDetraccion(self, invoice_id):
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
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.monto_neto_pagar, 2))
			tag = etree.QName(self._cbc, 'PaymentPercent')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = str(invoice_id.porc_detraccion)
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(payment_terms, (tag.text), currencyID=(invoice_id.moneda_base.name), nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.monto_detraccion, 2))

	# Crear la parte del xml donde se asigna si es al "credito" o al "contado"
	def _get_tipo_transaccion(self, invoice_id):
		if invoice_id.invoice_payment_term_id and invoice_id.invoice_payment_term_id.tipo_transaccion == 'credito' or invoice_id.invoice_date_due > invoice_id.invoice_date:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Credito'
			tag = etree.QName(self._cbc, 'Amount')
			amount_total = invoice_id.amount_total
			etree.SubElement(payment_terms, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_total, 2))

			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms_cuota = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Cuota001'
			tag = etree.QName(self._cbc, 'Amount')
			etree.SubElement(payment_terms_cuota, (tag.text), currencyID=(invoice_id.currency_id.name), nsmap={'cbc': tag.namespace}).text = str(round(amount_total, 2))
			tag = etree.QName(self._cbc, 'PaymentDueDate')
			etree.SubElement(payment_terms_cuota, (tag.text), nsmap={'cbc': tag.namespace}).text = str(invoice_id.invoice_date_due)
		else:
			tag = etree.QName(self._cac, 'PaymentTerms')
			payment_terms = etree.SubElement((self._root), (tag.text), nsmap={'cac': tag.namespace})
			tag = etree.QName(self._cbc, 'ID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'FormaPago'
			tag = etree.QName(self._cbc, 'PaymentMeansID')
			etree.SubElement(payment_terms, (tag.text), nsmap={'cbc': tag.namespace}).text = 'Contado'

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
		self._getX509Template(content)
		self._getUBLVersion21()
		self._getDocumentDetail21(invoice_id)
		self._getSignature(invoice_id)
		self._getCompany21(invoice_id)
		self._getPartner21(invoice_id)

		self._getDetraccion(invoice_id)
		self._get_tipo_transaccion(invoice_id)

		self._getPrepaidPayment21(invoice_id)
		self._getAllowanceCharge(invoice_id)
		amount_tax = self._getTaxTotal21(invoice_id)
		self._getLegalMonetaryTotal21(invoice_id)

		self._getDocumentLines21(invoice_id)
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
		self._getX509Template(content)
		self._getUBLVersion21()
		self._getDocumentDetail21(invoice_id)
		self._getDiscrepancyResponse21(invoice_id)
		self._getBillingReference21(invoice_id)
		self._getDespatchDocumentReference21(invoice_id)
		self._getSignature(invoice_id)
		self._getCompany21(invoice_id)
		self._getPartner21(invoice_id)
		self._getAllowanceCharge(invoice_id)
		amount_tax = self._getTaxTotal21(invoice_id)
		self._getLegalMonetaryTotal21(invoice_id)
		self._getDocumentLines21(invoice_id)
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
		self._getX509Template(content)
		self._getUBLVersion21()
		self._getDocumentDetail21(invoice_id)
		self._getDiscrepancyResponse21(invoice_id)
		self._getBillingReference21(invoice_id)
		self._getDespatchDocumentReference21(invoice_id)
		self._getSignature(invoice_id)
		self._getCompany21(invoice_id)
		self._getPartner21(invoice_id)
		amount_tax = self._getTaxTotal21(invoice_id)
		self._getLegalMonetaryTotal21(invoice_id)
		self._getDocumentLines21(invoice_id)
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
		self._getX509Template(content)
		self._getUBLVersion(version='2.0', customization='1.0')
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
		self._getSignature(batch)
		self._getCompany(batch)
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
		self._getX509Template(content)
		self._getUBLVersion(version='2.0', customization='1.1')
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
		self._getSignature(batch)
		self._getCompany(batch)
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
					taxes.append({'amount_tax_line':0,  'tax_name':'1000',  'tax_description':'IGV',  'tax_type_pe':'VAT'})
					taxes.append({'amount_tax_line':0,  'tax_name':'2000',  'tax_description':'ISC',  'tax_type_pe':'EXC'})
					taxes.append({'amount_tax_line':0,  'tax_name':'9999',  'tax_description':'OTR',  'tax_type_pe':'OTH'})
					taxes.append({'amount_tax_line':0,  'tax_name':'7152',  'tax_description':'ICBPER',  'tax_type_pe':'OTH'})
					total = invoice_id.amount_total
					summary_allowcharge = invoice_id.pe_total_discount - invoice_id.pe_total_discount_tax
					for group_tax in invoice_id.amount_by_group:
						group_id = group_tax[(-1)]
						tax_id = invoice_id.line_ids.mapped('tax_ids').filtered(lambda x: x.tax_group_id.id == group_id)
						tax_id = tax_id and tax_id[0]
						if tax_id.pe_tax_type.code not in ('1000', '2000', '9999',
														   '7152'):
							continue
						amount_tax_line = group_tax[1]
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
					self._getPartner(invoice_id, line)
					if invoice_id.l10n_latam_document_type_id.code in ('07', '08'):
						self._getBillingReference(invoice_id, line)
					tag = etree.QName(self._cac, 'Status')
					status = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
					tag = etree.QName(self._cbc, 'ConditionCode')
					if invoice_id.pe_summary_id.is_voided:
						etree.SubElement(status, (tag.text), nsmap={'cbc': tag.namespace}).text = '3'
					else:
						etree.SubElement(status, (tag.text), nsmap={'cbc': tag.namespace}).text = '1'
					tag = etree.QName(self._sac, 'TotalAmount')
					etree.SubElement(line, (tag.text), currencyID=currency_code, nsmap={'sac': tag.namespace}).text = str(round(total, 2))
					if invoice_id.pe_taxable_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_taxable_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '01'
					if invoice_id.pe_exonerated_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_exonerated_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '02'
					if invoice_id.pe_unaffected_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_unaffected_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '03'
					if invoice_id.pe_free_amount > 0:
						tag = etree.QName(self._sac, 'BillingPayment')
						billing = etree.SubElement(line, (tag.text), nsmap={'sac': tag.namespace})
						tag = etree.QName(self._cbc, 'PaidAmount')
						etree.SubElement(billing, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_free_amount, 2))
						tag = etree.QName(self._cbc, 'InstructionID')
						etree.SubElement(billing, (tag.text), nsmap={'cbc': tag.namespace}).text = '05'
					if summary_allowcharge > 0:
						tag = etree.QName(self._cac, 'AllowanceCharge')
						allowance = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ChargeIndicator')
						etree.SubElement(allowance, (tag.text), nsmap={'cbc': tag.namespace}).text = 'false'
						tag = etree.QName(self._cbc, 'Amount')
						etree.SubElement(allowance, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(summary_allowcharge, 2))
					if invoice_id.pe_charge_total > 0:
						tag = etree.QName(self._cac, 'AllowanceCharge')
						allowance = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'ChargeIndicator')
						etree.SubElement(allowance, (tag.text), nsmap={'cbc': tag.namespace}).text = 'true'
						tag = etree.QName(self._cbc, 'Amount')
						etree.SubElement(allowance, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(invoice_id.pe_charge_total, 2))
				for tax in taxes:
					if tax['tax_name'] == '9999' and tax['amount_tax_line'] > 0:
						tag = etree.QName(self._cac, 'TaxTotal')
						total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TaxAmount')
						etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
						tag = etree.QName(self._cac, 'TaxSubtotal')
						tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
						tag = etree.QName(self._cbc, 'TotalAmount')
						etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
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
						if tax['amount_tax_line'] > 0 or tax['tax_name'] == '1000':
							tag = etree.QName(self._cac, 'TaxTotal')
							total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cbc, 'TaxAmount')
							etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
							tag = etree.QName(self._cac, 'TaxSubtotal')
							tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
							tag = etree.QName(self._cbc, 'TaxAmount')
							etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
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
							if tax['amount_tax_line'] > 0 or tax['tax_name'] == '7152':
								tag = etree.QName(self._cac, 'TaxTotal')
								total = etree.SubElement(line, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cbc, 'TaxAmount')
								etree.SubElement(total, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
								tag = etree.QName(self._cac, 'TaxSubtotal')
								tax_subtotal = etree.SubElement(total, (tag.text), nsmap={'cac': tag.namespace})
								tag = etree.QName(self._cbc, 'TaxAmount')
								etree.SubElement(tax_subtotal, (tag.text), currencyID=currency_code, nsmap={'cbc': tag.namespace}).text = str(round(tax['amount_tax_line'], 2))
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
