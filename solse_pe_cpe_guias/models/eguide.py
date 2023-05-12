# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from lxml import etree
from io import StringIO, BytesIO
import xmlsec
from collections import OrderedDict
from pysimplesoap.client import SoapClient, SoapFault
import base64
import zipfile
from odoo import _, fields
from odoo.exceptions import UserError
from datetime import datetime
import logging
from tempfile import gettempdir
import hashlib
import requests
import base64
import json
log = logging.getLogger(__name__)

class EGuide():
	def __init__(self):
		self._cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
		self._cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
		self._ccts="urn:un:unece:uncefact:documentation:2"
		self._ds="http://www.w3.org/2000/09/xmldsig#"
		self._ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
		self._qdt="urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2"
		self._sac="urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1"
		self._udt="urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2"
		self._xsi="http://www.w3.org/2001/XMLSchema-instance"
		self._root=None
	   
	def _getX509Template(self, content):
		tag = etree.QName(self._ds, 'Signature')   
		signature=etree.SubElement(content, tag.text, Id="signatureOdoo", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'SignedInfo')   
		signed_info=etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'CanonicalizationMethod')   
		etree.SubElement(signed_info, tag.text, Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'SignatureMethod')   
		etree.SubElement(signed_info, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'Reference')   
		reference=etree.SubElement(signed_info, tag.text, URI="", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'Transforms')   
		transforms=etree.SubElement(reference, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'Transform')   
		etree.SubElement(transforms, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'DigestMethod')   
		etree.SubElement(reference, tag.text, Algorithm="http://www.w3.org/2000/09/xmldsig#sha1", nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'DigestValue')   
		etree.SubElement(reference, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'SignatureValue')   
		etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'KeyInfo')   
		key_info=etree.SubElement(signature, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'X509Data')   
		data=etree.SubElement(key_info, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'X509SubjectName')   
		etree.SubElement(data, tag.text, nsmap={'ds':tag.namespace})
		tag = etree.QName(self._ds, 'X509Certificate')   
		etree.SubElement(data, tag.text, nsmap={'ds':tag.namespace})
	
	def _getSignature(self, stock_id):
		#es parte de la firma
		tag = etree.QName(self._cac, 'Signature')   
		signature=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')   
		etree.SubElement(signature, tag.text, nsmap={'cbc':tag.namespace}).text='IDSignOdoo'
		tag = etree.QName(self._cac, 'SignatoryParty')   
		party=etree.SubElement(signature, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')   
		identification=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')   
		etree.SubElement(identification, tag.text, schemeID= stock_id.company_id.partner_id.doc_type or '-', nsmap={'cbc':tag.namespace}).text=stock_id.company_id.partner_id.doc_number
		tag = etree.QName(self._cac, 'PartyName')   
		name=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'Name')   
		etree.SubElement(name, tag.text, nsmap={'cbc':tag.namespace}).text= etree.CDATA(stock_id.company_id.name)
		tag = etree.QName(self._cac, 'DigitalSignatureAttachment')   
		attachment=etree.SubElement(signature, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'ExternalReference')   
		reference=etree.SubElement(attachment, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'URI')   
		etree.SubElement(reference, tag.text, nsmap={'cbc':tag.namespace}).text="#signatureOdoo" 
		
	def _getCompany(self, stock_id):     
		tag = etree.QName(self._cac, 'DespatchSupplierParty')
		supplier=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')   
		etree.SubElement(supplier, tag.text, schemeID=stock_id.company_id.partner_id.doc_type,
						 nsmap={'cbc':tag.namespace}).text=stock_id.company_id.partner_id.doc_number
		
		tag = etree.QName(self._cac, 'Party')
		party=etree.SubElement(supplier, tag.text, nsmap={'cac':tag.namespace})

		tag = etree.QName(self._cac, 'PartyIdentification')   
		party_identification = etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(party_identification, tag.text, schemeID=stock_id.company_id.partner_id.doc_type, schemeName="Documento de Identidad", schemeAgencyName="PE:SUNAT", schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06", nsmap={'cbc':tag.namespace}).text= stock_id.company_id.partner_id.doc_number

		"""<cac:PartyIdentification>
		<cbc:ID schemeID="6" schemeName="Documento de Identidad" schemeAgencyName="PE:SUNAT" schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">20000000001</cbc:ID>
	  </cac:PartyIdentification>"""

		tag = etree.QName(self._cac, 'PartyLegalEntity')   
		party_name=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')   
		comercial_name = stock_id.company_id.partner_id.commercial_name or "-"
		etree.SubElement(party_name, tag.text, nsmap={'cbc':tag.namespace}).text= etree.CDATA(comercial_name.strip()!="-" and comercial_name.strip() or stock_id.company_id.partner_id.name) 
		
	
	def _getUBLVersion(self):
		tag = etree.QName(self._cbc, 'UBLVersionID')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='2.1'
		tag = etree.QName(self._cbc, 'CustomizationID')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='2.0'

	def _getPartner(self, stock_id):
		parent_id = stock_id.partner_id.parent_id
		partner_id = stock_id.partner_id
		contacto = parent_id or partner_id
		tag = etree.QName(self._cac, 'DeliveryCustomerParty')   
		customer=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')   
		etree.SubElement(customer, tag.text, schemeID= parent_id and parent_id.doc_type or partner_id.doc_type or '-',
						 nsmap={'cbc':tag.namespace}).text= parent_id and parent_id.doc_number or partner_id.doc_number or '-'
		tag = etree.QName(self._cac, 'Party')  
		party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')   
		party_identification = etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(party_identification, tag.text, schemeID=contacto.doc_type, schemeName="Documento de Identidad", schemeAgencyName="PE:SUNAT", schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06", nsmap={'cbc':tag.namespace}).text= contacto.doc_number

		tag = etree.QName(self._cac, 'PartyLegalEntity')   
		entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		name= parent_id and (parent_id.commercial_name!='-' and parent_id.commercial_name or parent_id.name) or (partner_id.commercial_name!='-' and partner_id.commercial_name or partner_id.name) or '-'
		tag = etree.QName(self._cbc, 'RegistrationName')   
		etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text= etree.CDATA(name)
	
	def _getSupplier(self, stock_id):
		tag = etree.QName(self._cac, 'SellerSupplierParty')   
		customer=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'CustomerAssignedAccountID')   
		etree.SubElement(customer, tag.text, schemeID= stock_id.supplier_id.doc_type or '-',
						 nsmap={'cbc':tag.namespace}).text=stock_id.supplier_id.doc_number or '-'
		
		tag = etree.QName(self._cac, 'Party')  
		party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'PartyLegalEntity')   
		entity=etree.SubElement(party, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')   
		etree.SubElement(entity, tag.text, nsmap={'cbc':tag.namespace}).text= etree.CDATA(stock_id.supplier_id.commercial_name!='-' and stock_id.supplier_id.commercial_name or stock_id.supplier_id.name or '-')
	
	def _getCarrier(self, stock_id, stage):
		tag = etree.QName(self._cac, 'CarrierParty')   
		customer=etree.SubElement(stage, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'PartyIdentification')   
		ident=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(ident, tag.text, schemeID= stock_id.pe_carrier_id.doc_type or '-',
						 nsmap={'cbc':tag.namespace}).text=stock_id.pe_carrier_id.doc_number or '-'

		tag = etree.QName(self._cac, 'PartyLegalEntity')  
		party=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'RegistrationName')   
		etree.SubElement(party, tag.text, nsmap={'cbc':tag.namespace}).text= etree.CDATA(stock_id.pe_carrier_id.commercial_name!= '-' and stock_id.pe_carrier_id.commercial_name or stock_id.pe_carrier_id.name or '-')
	
	
	def getGuide(self, stock_id, data):
		xmlns=etree.QName("urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2", 'DespatchAdvice')
		nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
							('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), 
							('xsi', self._xsi)] )
		self._root=etree.Element(xmlns.text, nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
		
		tag = etree.QName(self._ext, 'UBLExtension')
		extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
		
		tag = etree.QName(self._ext, 'ExtensionContent')
		content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})
		# X509 Template
		self._getX509Template(content)
		
		self._getUBLVersion()
		tag = etree.QName(self._cbc, 'ID')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.pe_guide_number or ''
		tag = etree.QName(self._cbc, 'IssueDate')  
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=str(stock_id.pe_date_issue) # datetime.strptime(stock_id.min_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
		
		tag = etree.QName(self._cbc, 'IssueTime')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.date_done.strftime("%H:%M:%S")
		
		tag = etree.QName(self._cbc, 'DespatchAdviceTypeCode')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='09'
		if stock_id.note:
			tag = etree.QName(self._cbc, 'Note')   
			etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.note or '-'
			
		# Trabajar baja ./cac:OrderReference
		if stock_id.pe_is_realeted:
			tag = etree.QName(self._cac, 'AdditionalDocumentReference')
			reference= etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(reference, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.pe_related_number
			tag = etree.QName(self._cbc, 'DocumentTypeCode')   
			etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.pe_related_code
		
		self._getSignature(stock_id)
		
		self._getCompany(stock_id)
		
		self._getPartner(stock_id)
		
		if stock_id.supplier_id:
			self._getSupplier(stock_id)
		
		tag = etree.QName(self._cac, 'Shipment')
		shipment = etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
		
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(shipment, tag.text, nsmap={'cbc':tag.namespace}).text = '1'
		
		tag = etree.QName(self._cbc, 'HandlingCode')
		etree.SubElement(shipment, tag.text, nsmap={'cbc':tag.namespace}).text = stock_id.pe_transfer_code

		# Sustento de la diferencia del Peso bruto total de la carga respecto al peso de los ítems seleccionados
		if stock_id.pe_transfer_code in ['08', '09']:
			tag = etree.QName(self._cbc, 'Information')
			etree.SubElement(shipment, tag.text, nsmap={'cbc':tag.namespace}).text = etree.CDATA(stock_id.origin)
		tag = etree.QName(self._cbc, 'GrossWeightMeasure')
		etree.SubElement(shipment, tag.text, unitCode="KGM", 
						 nsmap={'cbc':tag.namespace}).text = str(stock_id.pe_gross_weight)
		if stock_id.pe_transfer_code=='08':
			tag = etree.QName(self._cbc, 'TotalTransportHandlingUnitQuantity')
			etree.SubElement(shipment, tag.text, nsmap={'cbc':tag.namespace}).text = str(stock_id.pe_unit_quantity)
		
		tag = etree.QName(self._cbc, 'SplitConsignmentIndicator')
		etree.SubElement(shipment, tag.text, nsmap={'cbc':tag.namespace}).text = stock_id.pe_is_programmed and 'true' or 'false'
		
		
		# ShipmentStage
		tag = etree.QName(self._cac, 'ShipmentStage')
		stage= etree.SubElement(shipment, tag.text, nsmap={'cac':tag.namespace})
		
		tag = etree.QName(self._cbc, 'ID')
		etree.SubElement(stage, tag.text, nsmap={'cbc':tag.namespace}).text = '1'
		
		tag = etree.QName(self._cbc, 'TransportModeCode')
		etree.SubElement(stage, tag.text, nsmap={'cbc':tag.namespace}).text = stock_id.pe_transport_mode
		
		tag = etree.QName(self._cac, 'TransitPeriod')
		period = etree.SubElement(stage, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'StartDate')
		etree.SubElement(period, tag.text, nsmap={'cbc':tag.namespace}).text = stock_id.date_done.strftime('%Y-%m-%d')
																				
		
		
		if stock_id.pe_transport_mode=='01':
			self._getCarrier(stock_id, stage)
		else:
			is_main = False
			for line in stock_id.pe_fleet_ids:
				if line.is_main:
					tag = etree.QName(self._cac, 'TransportMeans')
					transport= etree.SubElement(stage, tag.text, nsmap={'cac':tag.namespace})
					tag = etree.QName(self._cac, 'RoadTransport')
					road= etree.SubElement(transport, tag.text, nsmap={'cac':tag.namespace})
					tag = etree.QName(self._cbc, 'LicensePlateID')
					etree.SubElement(road, tag.text, nsmap={'cbc':tag.namespace}).text = line.name
					is_main=True
					break
			if not is_main:
				for line in stock_id.pe_fleet_ids:
					tag = etree.QName(self._cac, 'TransportMeans')
					transport= etree.SubElement(stage, tag.text, nsmap={'cac':tag.namespace})
					tag = etree.QName(self._cac, 'RoadTransport')
					road= etree.SubElement(transport, tag.text, nsmap={'cac':tag.namespace})
					tag = etree.QName(self._cbc, 'LicensePlateID')
					etree.SubElement(road, tag.text, nsmap={'cbc':tag.namespace}).text = line.name
					is_main=True
					break
			for line in stock_id.pe_fleet_ids:
				tag = etree.QName(self._cac, 'DriverPerson')   
				customer=etree.SubElement(stage, tag.text, nsmap={'cac':tag.namespace})
				tag = etree.QName(self._cbc, 'ID')   
				etree.SubElement(customer, tag.text, schemeID= line.driver_id.doc_type or '-',
								 nsmap={'cbc':tag.namespace}).text=line.driver_id.doc_number or '-'

				nombres = line.driver_id.name.split(" ")
				nombres = nombres[0]
				apellidos = line.driver_id.name.replace(nombres, "")

				tag = etree.QName(self._cbc, 'FirstName')   
				etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text= nombres

				tag = etree.QName(self._cbc, 'FamilyName')   
				etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text= apellidos

				tag = etree.QName(self._cbc, 'JobTitle')   
				etree.SubElement(customer, tag.text, nsmap={'cbc':tag.namespace}).text="Principal"

				tag = etree.QName(self._cac, 'IdentityDocumentReference')   
				iden_doc_ref=etree.SubElement(customer, tag.text, nsmap={'cac':tag.namespace})
				tag = etree.QName(self._cbc, 'ID')   
				etree.SubElement(iden_doc_ref, tag.text, nsmap={'cbc':tag.namespace}).text = line.driver_id.pe_driver_license or '-'
		
		
		tag = etree.QName(self._cac, 'Delivery')
		delivery = etree.SubElement(shipment, tag.text, nsmap={'cac':tag.namespace})
		# Direccion recojo
		contacto_envio = stock_id.partner_id
		tag = etree.QName(self._cac, 'DeliveryAddress')   
		address=etree.SubElement(delivery, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')    
		etree.SubElement(address, tag.text, nsmap={'cbc':tag.namespace}).text=contacto_envio.l10n_pe_district.code
		tag = etree.QName(self._cac, 'AddressLine')   
		line_address=etree.SubElement(address, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'Line')    
		etree.SubElement(line_address, tag.text, nsmap={'cbc':tag.namespace}).text=len(contacto_envio.street)>100 and contacto_envio.street[0:100] or contacto_envio.street

		# Direccion partida
		contacto_origen = stock_id.company_id.partner_id
		tag = etree.QName(self._cac, 'Despatch')   
		address=etree.SubElement(delivery, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cac, 'DespatchAddress')   
		despatch_address=etree.SubElement(address, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')    
		etree.SubElement(despatch_address, tag.text, nsmap={'cbc':tag.namespace}).text=contacto_origen.l10n_pe_district.code
		tag = etree.QName(self._cac, 'AddressLine')   
		line_address=etree.SubElement(despatch_address, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'Line')    
		etree.SubElement(line_address, tag.text, nsmap={'cbc':tag.namespace}).text=len(contacto_origen.street)>100 and contacto_origen.street[0:100] or contacto_origen.street

		
		if stock_id.pe_transport_mode=='02':
			license_plate=""
			for line in stock_id.pe_fleet_ids:
				if line.is_main:
					license_plate = line.name
					is_main=True
					break
			if not license_plate:
				for line in stock_id.pe_fleet_ids:
					license_plate = line.name
					break
			tag = etree.QName(self._cac, 'TransportHandlingUnit')   
			transport=etree.SubElement(shipment, tag.text, nsmap={'cac':tag.namespace})
			"""tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(transport, tag.text, nsmap={'cbc':tag.namespace}).text=license_plate
			for line in stock_id.pe_fleet_ids:
				if line.name != license_plate:"""
			tag = etree.QName(self._cac, 'TransportEquipment')   
			equipment=etree.SubElement(transport, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(equipment, tag.text, nsmap={'cbc':tag.namespace}).text=line.name
			
		tag = etree.QName(self._cac, 'OriginAddress')   
		oaddress=etree.SubElement(shipment, tag.text, nsmap={'cac':tag.namespace})
		tag = etree.QName(self._cbc, 'ID')
		   
		etree.SubElement(oaddress, tag.text, nsmap={'cbc':tag.namespace}).text=stock_id.picking_type_id.warehouse_id.partner_id.l10n_pe_district.code
		tag = etree.QName(self._cbc, 'StreetName')   
		etree.SubElement(oaddress, tag.text, nsmap={'cbc':tag.namespace}).text=len(stock_id.picking_type_id.warehouse_id.partner_id.street or "-")>100 and stock_id.picking_type_id.warehouse_id.partner_id.street[0:100] or stock_id.picking_type_id.warehouse_id.partner_id.street or "-" 
		
		cont=1
		for line in stock_id.move_ids:
			tag = etree.QName(self._cac, 'DespatchLine')   
			despatch=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(despatch, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
			tag = etree.QName(self._cbc, 'DeliveredQuantity')   
			etree.SubElement(despatch, tag.text, unitCode=line.product_id.uom_id.sunat_code or "NIU",
							 nsmap={'cbc':tag.namespace}).text=str(line.quantity_done)
			tag = etree.QName(self._cac, 'OrderLineReference')   
			ref=etree.SubElement(despatch, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'LineID')   
			etree.SubElement(ref, tag.text, nsmap={'cbc':tag.namespace}).text=str(cont)
			cont+=1
			
			tag = etree.QName(self._cac, 'Item')   
			item=etree.SubElement(despatch, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'Description')   
			etree.SubElement(item, tag.text, nsmap={'cbc':tag.namespace}).text=etree.CDATA(line.product_id.name)
			
			tag = etree.QName(self._cac, 'SellersItemIdentification')   
			ident=etree.SubElement(item, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(ident, tag.text, nsmap={'cbc':tag.namespace}).text=line.product_id.default_code or "-"
				
		xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
		return xml_str

	def getGuideVoided(self, data):
		xmlns=etree.QName("urn:oasis:names:specification:ubl:schema:xsd:DespatchAdvice-2", 'DespatchAdvice')
		nsmap1=OrderedDict([(None, xmlns.namespace), ('cac', self._cac), ('cbc', self._cbc), ('ccts', self._ccts), 
							('ds', self._ds), ('ext', self._ext), ('qdt', self._qdt), ('sac', self._sac), ('udt', self._udt), 
							('xsi', self._xsi)] )
		self._root=etree.Element(xmlns.text, nsmap=nsmap1)
		tag = etree.QName(self._ext, 'UBLExtensions')
		extensions=etree.SubElement(self._root, tag.text, nsmap={'ext':tag.namespace})
		
		tag = etree.QName(self._ext, 'UBLExtension')
		extension=etree.SubElement(extensions, tag.text, nsmap={'ext':tag.namespace})
		
		tag = etree.QName(self._ext, 'ExtensionContent')
		content=etree.SubElement(extension, tag.text, nsmap={'ext':tag.namespace})
		# X509 Template
		self._getX509Template(content)
		
		self._getUBLVersion()
		tag = etree.QName(self._cbc, 'ID')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text= data.name
		tag = etree.QName(self._cbc, 'IssueDate')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text= data.date # datetime.strptime(stock_id.min_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
		
		tag = etree.QName(self._cbc, 'DespatchAdviceTypeCode')   
		etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text='09'
		#if data.note:
		#    tag = etree.QName(self._cbc, 'Note')   
		#    etree.SubElement(self._root, tag.text, nsmap={'cbc':tag.namespace}).text= data.note or '-'
		
		for line in data.voided_ids:
			tag = etree.QName(self._cac, 'OrderReference')   
			reference=etree.SubElement(self._root, tag.text, nsmap={'cac':tag.namespace})
			tag = etree.QName(self._cbc, 'ID')   
			etree.SubElement(reference, tag.text, nsmap={'cbc':tag.namespace}).text=line.pe_guide_number
			tag = etree.QName(self._cbc, 'OrderTypeCode')   
			etree.SubElement(reference, tag.text, name=u"GUIA DE REMISIÓN", 
							 nsmap={'cbc':tag.namespace}).text='09'
			
		self._getSignature(data)
		
		self._getCompany(data)
		
				
		xml_str = etree.tostring(self._root, pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)
		return xml_str

	
class Document(object):

	def __init__(self):
		self._xml = None
		self._type = None
		self._document_name = None
		self._client = None
		self._response = None
		self._zip_file = None
		self._response_status = None
		self._response_data = None
		self._ticket = None
		self.in_memory_data = BytesIO()
		self.in_memory_zip = zipfile.ZipFile(self.in_memory_data, "w", zipfile.ZIP_DEFLATED, False)

	def writetofile(self, filename, filecontent):
		self.in_memory_zip.writestr(filename, filecontent)

	def prepare_zip(self):
		self._zip_filename = '{}.zip'.format(self._document_name)
		xml_filename = '{}.xml'.format(self._document_name)
		self.writetofile(xml_filename, self._xml)
		for zfile in self.in_memory_zip.filelist:
			zfile.create_system = 0
		self.in_memory_zip.close()

	def send(self):
		if self._type=="sync":
			self._zip_file = base64.b64encode(self.in_memory_data.getvalue())
			self._response_status, self._response = self._client.send_bill(self._zip_filename, self._zip_file)
		elif self._type=="ticket":
			self._response_status, self._response = self._client.get_status(self._ticket)
		elif self._type=="status":
			self._response_status, self._response = self._client.get_status_cdr(self._document_name)
		else:
			self._zip_file = base64.b64encode(self.in_memory_data.getvalue())
			self._response_status, self._response = self._client.send_bill(self._zip_filename, self._zip_file)
	
	def process_response(self):
		if self._response is None or not self._response_status:
			return
		if self._type == 'sync':
			self._response_data = self._response['numTicket']
		elif self._type == 'ticket':
			if 'arcCdr' not in self._response:
				texto = "No se pudo parsear: %s" % str(self._response)
				raise UserError(texto)
			self._response_data = self._response['arcCdr']
		elif self._type == 'status':
			self._response_data = self._response['arcCdr']
		else:
			self._response_data = self._response['numTicket']
	
	def process(self, document_name, type, xml, client):
		self._xml = xml
		self._type = type
		self._document_name = document_name
		self._client = client
		
		self.prepare_zip()
		self.send()
		self.process_response()
		return self._zip_file, self._response_status, self._response, self._response_data
	
	@staticmethod
	def get_response(file, name):
		zf=zipfile.ZipFile(BytesIO(base64.b64decode(file)))
		return zf.open(name).read()

	def get_status(self, ticket, client):
		self._type="ticket"
		self._ticket = ticket
		self._client=client
		self.send()
		self.process_response()
		return self._response_status, self._response, self._response_data
	
	def get_status_cdr(self, document_name, client):
		self._type="status"
		self._client = client
		self._document_name = document_name
		self.send()
		return self._response_status, self._response, self._response_data


class Client(object):

	def __init__(self, ruc, username, password, client_id, client_secret):
		self._type=type
		self._ruc = ruc
		self._username = "%s%s" %(ruc,username)
		self._password = password
		self._client_id = client_id
		self._client_secret = client_secret
		self._token = False
		level = logging.DEBUG
		logging.basicConfig(level=level)
		log.setLevel(level)
		self._connect()

	def _connect(self):
		endpoint = "https://api-seguridad.sunat.gob.pe/v1/clientessol/%s/oauth2/token/" % self._client_id
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
		}
		datos_json = {
			'grant_type': 'password',
			'scope': 'https://api-cpe.sunat.gob.pe',
			'client_id': self._client_id,
			'client_secret': self._client_secret,
			'username': self._username,
			'password': self._password,
		}
		datos_peticion = requests.post(endpoint, data=datos_json, headers=headers)
		if datos_peticion.status_code == 200:
			datos = datos_peticion.json()
			token = datos['access_token']
			self._token = token
		else:
			self._token = False

	def send_bill(self, filename, content_file):
		nombre = filename.split(".")[0]
		res=nombre.split("-")
		#endpoint = "https://api-cpe.sunat.gob.pe/v1/contribuyente/gem/comprobantes/{numRucEmisor}-{codCpe}-{numSerie}-{numCpe}"
		endpoint = "https://api-cpe.sunat.gob.pe/v1/contribuyente/gem/comprobantes/%s-%s-%s-%s" % (res[0], res[1], res[2], res[3])
		headers = {
			"Content-Type": "application/json",
			"Accept": "application/json",
			"Authorization": "Bearer %s" % self._token,
		}
		m = hashlib.sha256()
		m.update(base64.b64decode(content_file))
		hashZip = m.hexdigest()

		#{"numTicket":"6913f876-123a-4c01-8aba-73b2a311a6af","fecRecepcion":"2022-12-29T10:27:59"}

		datos_archivo = {
			"nomArchivo": filename,
			"arcGreZip": str(content_file, "utf-8"),
			"hashZip": hashZip
		}
		datos_json = {
			"archivo": datos_archivo,
		}
		datos_json = json.dumps(datos_json)
		datos_peticion = requests.post(endpoint, data=datos_json, headers=headers)
		if datos_peticion.status_code == 200:
			datos = json.loads(datos_peticion.text)
			rpt = [datos_peticion.status_code, datos]
			return rpt
		else:
			return [False, False]

	def send_summary(self, filename, content_file):
		params = {
			'fileName': filename,
			'contentFile': str(content_file, "utf-8")
		}
		return self._call_service('sendSummary', params)

	def get_status(self, ticket_code):
		#endpoint = "https://api-cpe.sunat.gob.pe/v1/contribuyente/gem/comprobantes/{numRucEmisor}-{codCpe}-{numSerie}-{numCpe}"
		endpoint = "https://api-cpe.sunat.gob.pe/v1/contribuyente/gem/comprobantes/envios/%s" % ticket_code
		headers = {
			"Content-Type": "application/json",
			"Accept": "application/json",
			"Authorization": "Bearer %s" % self._token,
		}
		datos_json = {}
		datos_json = json.dumps(datos_json)
		datos_peticion = requests.get(endpoint, data=datos_json, headers=headers)
		if datos_peticion.status_code == 200:
			datos = json.loads(datos_peticion.text)
			return [datos['codRespuesta'], datos]
		else:
			return [False, False]

	def get_status_cdr(self, document_name):
		res=document_name.split("-")
		params = {
			'rucComprobante': res[0],
			'tipoComprobante': res[1],
			'serieComprobante': res[2],
			'numeroComprobante': res[3]
		}
		return self._call_service('getStatusCdr', params)

def get_document(self):
	if self.type=="sync":
		xml = EGuide().getGuide(self.picking_ids[0], self)
	else:
		xml = EGuide().getGuideVoided(self)
	return xml

def get_sign_document(xml, key_file, crt_file):
	xml_iofile=BytesIO(xml.encode('utf-8'))
	root=etree.parse(xml_iofile).getroot()
	signature_node = xmlsec.tree.find_node(root, xmlsec.Node.SIGNATURE)
	assert signature_node is not None
	assert signature_node.tag.endswith(xmlsec.Node.SIGNATURE)
	ctx = xmlsec.SignatureContext()
	key = xmlsec.Key.from_memory(key_file, xmlsec.KeyFormat.PEM)
	assert key is not None
	key.load_cert_from_memory(crt_file, xmlsec.KeyFormat.PEM)
	ctx.key = key
	assert ctx.key is not None
	# Sign the template.
	ctx.sign(signature_node)
	return etree.tostring(root,  pretty_print=True, xml_declaration = True, encoding='utf-8', standalone=False)

def get_ticket_status(ticket, client):
	client = Client(**client)
	return Document().get_status(ticket, client)

def get_response(data):
	return Document().get_response(**data)

def get_status_cdr(send_number, client):
	client = Client(**client)
	return Document().get_status_cdr(send_number, client)

def send_sunat_eguide(client, document):
	client = Client(**client)    
	document['client']=client    
	return Document().process(**document)

