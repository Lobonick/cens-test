# -*- coding: utf-8 -*-

from lxml import etree
from io import StringIO, BytesIO
import xmlsec
from collections import OrderedDict
from pysimplesoap.client import SoapClient, SoapFault, fetch
import base64, zipfile
from datetime import date, datetime, timedelta
from pysimplesoap.simplexml import SimpleXMLElement
import logging
from tempfile import gettempdir
import socket
from binascii import hexlify
import dateutil.parser
import pytz
from dateutil.tz import gettz

_logging = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

# Clase que encapsula el manejo del zip con el xml para su posterior envio
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
		self.in_memory_zip = zipfile.ZipFile(self.in_memory_data, 'w', zipfile.ZIP_DEFLATED, False)

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
		if self._type == 'sync':
			self._zip_file = base64.b64encode(self.in_memory_data.getvalue())
			self._response_status, self._response = self._client.send_bill(self._zip_filename, self._zip_file)
		elif self._type == 'ticket':
			self._response_status, self._response = self._client.get_status(self._ticket)
		elif self._type == 'status':
			self._response_status, self._response = self._client.get_status_cdr(self._document_name)
		else:
			self._zip_file = base64.b64encode(self.in_memory_data.getvalue())
			self._response_status, self._response = self._client.send_summary(self._zip_filename, self._zip_file)

	def process_response(self):
		if self._response is None or not self._response_status:
			return
		if self._type == 'sync':
			self._response_data = self._response['applicationResponse']
		elif self._type == 'ticket':
			if self._response.get('status', {}).get('content'):
				self._response_data = self._response['status']['content']
			else:
				res = self._response
				self._response_status = False
				self._response = {'faultcode':res['status'].get('statusCode', False),  'faultstring':''}
		elif self._type == 'status':
			self._response_data = self._response.get('statusCdr', {}).get('content', None)
			if not self._response_data:
				self._response_status = False
				self._response = {'faultcode':self._response.get('statusCdr', {}).get('statusCode', False),  'faultstring':self._response.get('statusCdr', {}).get('statusMessage', False)}
		else:
			self._response_data = self._response['ticket']

	def process(self, document_name, type, xml, client):
		self._xml = xml
		self._type = type
		self._document_name = document_name
		self._client = client
		self.prepare_zip()
		self.send()
		self.process_response()
		return (self._zip_file, self._response_status, self._response, self._response_data)

	#devuelve el xml con nombre "name" que viende dentro del zip "file"
	@staticmethod
	def get_response(file, name):
		zf = zipfile.ZipFile(BytesIO(base64.b64decode(file)))
		return zf.open(name).read()

	def get_status(self, ticket, client):
		self._type = 'ticket'
		self._ticket = ticket
		self._client = client
		self.send()
		self.process_response()
		return (self._response_status, self._response, self._response_data)

	def get_status_cdr(self, document_name, client):
		self._type = 'status'
		self._client = client
		self._document_name = document_name
		self.send()
		self.process_response()
		return (self._response_status, self._response, self._response_data)

# Clase para implementar las llamdas soap
class Client(object):

	def __init__(self, ruc, username, password, url, debug=False, type=None, server=None):
		self._type = type
		self._username = '%s%s' % (ruc, username)
		self._password = password
		self._debug = debug
		self._url = '%s?WSDL' % url
		self._location = url
		self._namespace = url
		self._soapaction = 'urn:getStatus'
		self._method = 'getStatusCdr'
		self._soapenv = '<?xml version="1.0" encoding="UTF-8"?>\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tzmed="http://service.sunat.gob.pe">\n    <soapenv:Header>\n        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">\n            <wsse:UsernameToken>\n                <wsse:Username>%s</wsse:Username>\n                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">%s</wsse:Password>\n            </wsse:UsernameToken>\n        </wsse:Security>\n    </soapenv:Header>\n    <soapenv:Body>\n        %s\n    </soapenv:Body>\n</soapenv:Envelope>'
		self._xml_method = None
		self._soap_namespaces = dict(soap11='http://schemas.xmlsoap.org/soap/envelope/', soap='http://schemas.xmlsoap.org/soap/envelope/', soapenv='http://schemas.xmlsoap.org/soap/envelope/', soap12='http://www.w3.org/2003/05/soap-env', soap12env='http://www.w3.org/2003/05/soap-envelope')
		self._exceptions = True
		level = logging.DEBUG
		logging.basicConfig(level=level)
		_logging.setLevel(level)
		self._connect()

	def _connect(self):
		if not self._type:
			cache = '%s/sunat' % gettempdir()
			self._client = SoapClient(wsdl=(self._url), cache=None, ns='tzmed', soap_ns='soapenv', soap_server='jbossas6', trace=True)
			self._client['wsse:Security'] = {'wsse:UsernameToken': {'wsse:Username':self._username,  'wsse:Password':self._password}}
		else:
			#self._client = SoapClient(location=(self._location), action=(self._soapaction), namespace=(self._namespace))
			self._client = SoapClient(location=(self._location), namespace=(self._namespace))

	def _call_ws(self, xml):
		xml_response = self._client.send(self._method, xml.encode('utf-8'))
		vals = {}
		root = etree.fromstring(xml_response)
		state = True
		if root.find('.//applicationResponse') is not None:
			vals['applicationResponse'] = root.find('.//applicationResponse').text
		if root.find('.//ticket') is not None:
			vals['ticket'] = root.find('.//ticket').text
		if root.find('.//content') is not None:
			if self._type == 'status':
				vals['status'] = {'content': root.find('.//content').text}
		if root.find('.//content') is not None:
			if self._type == 'statusCdr':
				vals['statusCdr'] = {'content': root.find('.//content').text}
		if root.find('.//faultcode') is not None:
			vals['faultcode'] = root.find('.//faultcode').text
			state = False
		if root.find('.//faultstring') is not None:
			vals['faultstring'] = root.find('.//faultstring').text
			state = False
		if root.find('.//faultcode') is not None:
			if self._type == 'statusCdr':
				vals['faultcode'] = {'statusCdr': root.find('.//faultcode').text}
				state = False
		if root.find('.//faultstring') is not None:
			if self._type == 'statusCdr':
				vals['faultstring'] = {'statusCdr': root.find('.//faultstring').text}
				state = False
		return (state, vals)

	def _call_service(self, name, params):
		if not self._type:
			try:
				service = getattr(self._client, name)
				return (
				 True, service(**params))
			except SoapFault as ex:
				return (False, {'faultcode':ex.faultcode,  'faultstring':ex.faultstring})
		try:
			xml = self._soapenv % (self._username, self._password, self._xml_method)
			return self._call_ws(xml)
		except Exception as e:
			return (False, {})

	def send_bill(self, filename, content_file):
		params = {'fileName':filename, 'contentFile': str(content_file, 'utf-8')}
		self._xml_method = '<tzmed:sendBill>\n            <fileName>%s</fileName>\n            <contentFile>%s</contentFile>\n        </tzmed:sendBill>' % (params['fileName'], params['contentFile'])
		return self._call_service('sendBill', params)

	def send_summary(self, filename, content_file):
		params = {'fileName':filename, 'contentFile':str(content_file, 'utf-8')}
		self._xml_method = '<tzmed:sendSummary>\n            <fileName>%s</fileName>\n            <contentFile>%s</contentFile>\n        </tzmed:sendSummary>' % (params['fileName'], params['contentFile'])
		return self._call_service('sendSummary', params)

	def get_status(self, ticket_code):
		params = {'ticket': ticket_code}
		self._xml_method = '<tzmed:getStatus>\n            <ticket>%s</ticket>\n        </tzmed:getStatus>' % params['ticket']
		return self._call_service('getStatus', params)

	def get_status_cdr(self, document_name):
		res = document_name.split('-')
		params = {'rucComprobante':res[0],  'tipoComprobante':res[1], 'serieComprobante':res[2], 'numeroComprobante':res[3]}
		self._xml_method = '<tzmed:getStatusCdr>\n            <rucComprobante>%s</rucComprobante>\n            <tipoComprobante>%s</tipoComprobante>\n            <serieComprobante>%s</serieComprobante>\n            <numeroComprobante>%s</numeroComprobante>\n        </tzmed:getStatusCdr>' % (params['rucComprobante'], params['tipoComprobante'], params['serieComprobante'], params['numeroComprobante'])
		return self._call_service('getStatusCdr', params)

def get_sign_document(xml, key_file, crt_file):
	parser = etree.XMLParser(strip_cdata=False)
	xml_iofile = BytesIO(xml.encode('utf-8'))
	root = etree.parse(xml_iofile, parser).getroot()
	signature_node = xmlsec.tree.find_node(root, xmlsec.Node.SIGNATURE)
	if signature_node is None:
		raise AssertionError
	elif not signature_node.tag.endswith(xmlsec.Node.SIGNATURE):
		raise AssertionError
	ctx = xmlsec.SignatureContext()
	key = xmlsec.Key.from_memory(key_file, xmlsec.KeyFormat.PEM)
	assert not key is None
	key.load_cert_from_memory(crt_file, xmlsec.KeyFormat.PEM)
	ctx.key = key
	assert not ctx.key is None
	ctx.sign(signature_node)
	return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='utf-8', standalone=False)

def get_ticket_status(ticket, client):
	client['type'] = 'status'
	client = Client(**client)
	return Document().get_status(ticket, client)

def get_status_cdr(send_number, client):
	client['url'] = 'https://e-factura.sunat.gob.pe/ol-it-wsconscpegem/billConsultService'
	client['type'] = 'statusCdr'
	client = Client(**client)
	return Document().get_status_cdr(send_number, client)

#lee el xml que viene dentro del zip devuelto como cdr por parte de sunat
def get_response(data):
	return (Document().get_response)(**data)

def send_sunat_cpe(client, document):
	client['type'] = 'send'
	client = Client(**client)
	document['client'] = client
	return (Document().process)(**document)

