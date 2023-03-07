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
from future.backports.http import client as http_client
from tornado.http1connection import HTTP1Connection, HTTP1ConnectionParameters
from tornado.iostream import StreamClosedError, IOStream

#import httplib2
from pysimplesoap.helpers import Alias, fetch, sort_dict, make_key, process_element, postprocess_element, get_message, preprocess_schema, get_local_name, get_namespace_prefix, TYPE_MAP, urlsplit

import ssl
import sys
import bisect
import hashlib
import array
import warnings

try:
	import urllib2
	from cookielib import CookieJar
except ImportError:
	from urllib import request as urllib2
	from http.cookiejar import CookieJar
	from urllib.parse import (urlparse, urlsplit, urljoin, unwrap, quote, unquote, splittype, splithost, splitport, splituser, splitpasswd, splitattr, splitquery, splitvalue, splittag, to_bytes, urlunparse)


_logging = logging.getLogger(__name__)
log = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

TIMEOUT = 60
__version__ = sys.version[:3]

_http_connectors = {}  # libname: classimpl mapping
_http_facilities = {}  # functionalitylabel: [sequence of libname] mapping

# connection states
_CS_IDLE = 'Idle'
_CS_REQ_STARTED = 'Request-started'
_CS_REQ_SENT = 'Request-sent'

import http.client

_strict_sentinel = object()

def _create_connection(self, stream: IOStream) -> HTTP1Connection:
	stream.set_nodelay(True)
	connection = HTTP1Connection(
		stream,
		True,
		HTTP1ConnectionParameters(
			no_keep_alive=True,
			max_header_size=self.max_header_size,
			max_body_size=self.max_body_size,
			decompress=bool(self.request.decompress_response),
		),
		self._sockaddr,
	)
	return connection

try:
	import httplib2
	import http.client
	# httplib2 workaround: check_hostname needs a SSL context with either 
	#                      CERT_OPTIONAL or CERT_REQUIRED
	# see https://code.google.com/p/httplib2/issues/detail?id=173
	orig__init__ = http.client.HTTPSConnection.__init__ 

	def ini_ori(self, host, port=None, strict=_strict_sentinel,
				 timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
		if strict is not _strict_sentinel:
			warnings.warn("the 'strict' argument isn't supported anymore; "
				"http.client now always assumes HTTP/1.x compliant servers.",
				DeprecationWarning, 2)
		self.timeout = timeout
		self.source_address = source_address
		self.sock = None
		self._buffer = []
		self.__response = None
		self.__state = _CS_IDLE
		self._method = None
		self._tunnel_host = None
		self._tunnel_port = None
		self._tunnel_headers = {}

		self._set_hostport(host, port)

	def fixer4(self, host, port=None, key_file=None, cert_file=None,
					 strict=_strict_sentinel, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
					 source_address=None, **_3to2kwargs):
		#ini_ori(self, host, port, strict, timeout, source_address)
		

		if 'check_hostname' in _3to2kwargs: check_hostname = _3to2kwargs['check_hostname']; del _3to2kwargs['check_hostname']
		else: check_hostname = None
		if 'context' in _3to2kwargs: context = _3to2kwargs['context']; del _3to2kwargs['context']
		else: context = None

		super(http.client.HTTPSConnection, self).__init__(host, port, None, timeout, source_address)

		self.key_file = key_file
		self.cert_file = cert_file
		if context is None:
			# Some reasonable defaults
			context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
			context.options |= ssl.OP_NO_SSLv2
		will_verify = False
		if check_hostname is None:
			check_hostname = will_verify
		elif check_hostname and not will_verify:
			raise ValueError("check_hostname needs a SSL context with either CERT_OPTIONAL or CERT_REQUIRED")
		if key_file or cert_file:
			context.load_cert_chain(cert_file, key_file)
		self._context = context
		self._check_hostname = check_hostname

	http.client.HTTPSConnection.__init__ = fixer4
	"""http.client.HTTPSConnection._HTTPConnection__response = ""
	http.client.HTTPSConnection.sock = None
	http.client.HTTPSConnection.host = None
	http.client.HTTPSConnection._HTTPConnection__state = _CS_IDLE
	http.client.HTTPSConnection._buffer = []
	http.client.HTTPSConnection._create_connection = _create_connection"""
#except ImportError:
except Exception as e:
	log.info("horror locallllllllllll")


class TransportBase:
	@classmethod
	def supports_feature(cls, feature_name):
		return cls._wrapper_name in _http_facilities[feature_name]

class OpenerDirectorLocal(object):
	def __init__(self):
		client_version = "Python-urllib/%s" % __version__
		self.addheaders = [('User-agent', client_version)]
		# self.handlers is retained only for backward compatibility
		self.handlers = []
		# manage the individual handlers
		self.handle_open = {}
		self.handle_error = {}
		self.process_response = {}
		self.process_request = {}

	def add_handler(self, handler):
		if not hasattr(handler, "add_parent"):
			raise TypeError("expected BaseHandler instance, got %r" %
							type(handler))

		added = False
		for meth in dir(handler):
			if meth in ["redirect_request", "do_open", "proxy_open"]:
				# oops, coincidental match
				continue

			i = meth.find("_")
			protocol = meth[:i]
			condition = meth[i+1:]

			if condition.startswith("error"):
				j = condition.find("_") + i + 1
				kind = meth[j+1:]
				try:
					kind = int(kind)
				except ValueError:
					pass
				lookup = self.handle_error.get(protocol, {})
				self.handle_error[protocol] = lookup
			elif condition == "open":
				kind = protocol
				lookup = self.handle_open
			elif condition == "response":
				kind = protocol
				lookup = self.process_response
			elif condition == "request":
				kind = protocol
				lookup = self.process_request
			else:
				continue

			handlers = lookup.setdefault(kind, [])
			if handlers:
				bisect.insort(handlers, handler)
			else:
				handlers.append(handler)
			added = True

		if added:
			bisect.insort(self.handlers, handler)
			handler.add_parent(self)

	def close(self):
		# Only exists for backwards compatibility.
		pass

	def _call_chain(self, chain, kind, meth_name, *args):
		# Handlers raise an exception if no one else should try to handle
		# the request, or return None if they can't but another handler
		# could.  Otherwise, they return the response.
		handlers = chain.get(kind, ())
		for handler in handlers:
			func = getattr(handler, meth_name)
			result = func(*args)
			if result is not None:
				return result

	def open(self, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
		if isinstance(fullurl, bytes):
			fullurl = fullurl.decode()

		if isinstance(fullurl, str):
			req = urllib2.Request(fullurl, data)
		else:
			req = fullurl
			if data is not None:
				req.data = data

		req.timeout = timeout
		protocol = req.type

		# pre-process request
		meth_name = protocol+"_request"
		for processor in self.process_request.get(protocol, []):
			meth = getattr(processor, meth_name)
			req = meth(req)

		response = self._open(req, data)
		# post-process response
		meth_name = protocol+"_response"
		for processor in self.process_response.get(protocol, []):
			meth = getattr(processor, meth_name)
			response = meth(req, response)

		return response

	def _open(self, req, data=None):
		result = self._call_chain(self.handle_open, 'default',
								  'default_open', req)
		if result:
			return result

		protocol = req.type
		result = self._call_chain(self.handle_open, protocol, protocol +
								  '_open', req)
		if result:
			return result

		return self._call_chain(self.handle_open, 'unknown',
								'unknown_open', req)

	def error(self, proto, *args):
		if proto in ('http', 'https'):
			# XXX http[s] protocols are special-cased
			dict = self.handle_error['http'] # https is not different than http
			proto = args[2]  # YUCK!
			meth_name = 'http_error_%s' % proto
			http_err = 1
			orig_args = args
		else:
			dict = self.handle_error
			meth_name = proto + '_error'
			http_err = 0
		args = (dict, proto, meth_name) + args
		result = self._call_chain(*args)
		if result:
			return result

		if http_err:
			args = (dict, 'default', 'http_error_default') + orig_args
			return self._call_chain(*args)

def build_opener_local(*handlers):
	def isclass(obj):
		return isinstance(obj, type) or hasattr(obj, "__bases__")

	opener = OpenerDirectorLocal()
	default_classes = [urllib2.ProxyHandler, urllib2.UnknownHandler, urllib2.HTTPHandler,
					   urllib2.HTTPDefaultErrorHandler, urllib2.HTTPRedirectHandler,
					   urllib2.FTPHandler, urllib2.FileHandler, urllib2.HTTPErrorProcessor]

	if hasattr(http_client, "HTTPSConnection"):
		default_classes.append(urllib2.HTTPSHandler)

	skip = set()
	for klass in default_classes:
		for check in handlers:
			if isclass(check):
				if issubclass(check, klass):
					skip.add(klass)
			elif isinstance(check, klass):
				skip.add(klass)
	for klass in skip:
		default_classes.remove(klass)

	for klass in default_classes:
		opener.add_handler(klass())

	for h in handlers:
		if isclass(h):
			h = h()
		opener.add_handler(h)
	return opener

#urllib2.build_opener = build_opener_local

class urllib2Transport(TransportBase):
	_wrapper_version = "urllib2 %s" % urllib2.__version__
	_wrapper_name = 'urllib2'

	def __init__(self, timeout=None, proxy=None, cacert=None, sessions=False):
		if (timeout is not None) and not self.supports_feature('timeout'):
			raise RuntimeError('timeout is not supported with urllib2 transport')
		if proxy:
			raise RuntimeError('proxy is not supported with urllib2 transport')
		if cacert:
			raise RuntimeError('cacert is not support with urllib2 transport')
		
		handlers = []

		if ((sys.version_info[0] == 2 and sys.version_info >= (2,7,9)) or
			(sys.version_info[0] == 3 and sys.version_info >= (3,2,0))):
			context = ssl.create_default_context()
			context.check_hostname = None
			context.key_file = None
			context.verify_mode = ssl.CERT_NONE
			handlers.append(urllib2.HTTPSHandler(check_hostname=False, context=context))
		
		if sessions:
			handlers.append(urllib2.HTTPCookieProcessor(CookieJar()))

		#opener = urllib2.build_opener(*handlers)
		opener = build_opener_local(*handlers)
		self.request_opener = opener.open
		self._timeout = timeout

	def request(self, url, method="GET", body=None, headers={}):
		req = urllib2.Request(url, body, headers)
		try:
			#f = self.request_opener(req, timeout=self._timeout)
			f = self.request_opener(req, timeout=self._timeout)
			return f.info(), f.read()
		except urllib2.HTTPError as f:
			if f.code != 500:
				raise
			return f.info(), f.read()

class SoapClientLocal(SoapClient):
	"""Simple SOAP Client (simil PHP)"""
	def __init__(self, location=None, action=None, namespace=None,
				 cert=None, exceptions=True, proxy=None, ns=None,
				 soap_ns=None, wsdl=None, wsdl_basedir='', cache=False, cacert=None,
				 sessions=False, soap_server=None, timeout=TIMEOUT,
				 http_headers=None, trace=False,
				 username=None, password=None,
				 key_file=None, plugins=None, strict=True,
				 ):
		"""
		:param http_headers: Additional HTTP Headers; example: {'Host': 'ipsec.example.com'}
		"""
		self.certssl = cert
		self.keyssl = key_file
		self.location = location        # server location (url)
		self.action = action            # SOAP base action
		self.namespace = namespace      # message
		self.exceptions = exceptions    # lanzar execpiones? (Soap Faults)
		self.xml_request = self.xml_response = ''
		self.http_headers = http_headers or {}
		self.plugins = plugins or []
		self.strict = strict
		# extract the base directory / url for wsdl relative imports:
		if wsdl and wsdl_basedir == '':
			# parse the wsdl url, strip the scheme and filename
			url_scheme, netloc, path, query, fragment = urlsplit(wsdl)
			wsdl_basedir = os.path.dirname(netloc + path)

		self.wsdl_basedir = wsdl_basedir

		# shortcut to print all debugging info and sent / received xml messages
		if trace:
			if trace is True:
				level = logging.DEBUG           # default logging level
			else:
				level = trace                   # use the provided level
			logging.basicConfig(level=level)
			log.setLevel(level)

		if not soap_ns and not ns:
			self.__soap_ns = 'soap'  # 1.1
		elif not soap_ns and ns:
			self.__soap_ns = 'soapenv'  # 1.2
		else:
			self.__soap_ns = soap_ns

		# SOAP Server (special cases like oracle, jbossas6 or jetty)
		self.__soap_server = soap_server

		# SOAP Header support
		self.__headers = {}         # general headers
		self.__call_headers = None  # Struct to be marshalled for RPC Call

		# check if the Certification Authority Cert is a string and store it
		if cacert and cacert.startswith('-----BEGIN CERTIFICATE-----'):
			fd, filename = tempfile.mkstemp()
			f = os.fdopen(fd, 'w+b', -1)
			log.debug("Saving CA certificate to %s" % filename)
			f.write(cacert)
			cacert = filename
			f.close()
		self.cacert = cacert

		# Create HTTP wrapper
		#self.http = Httplib2Transport(timeout=timeout, cacert=cacert, proxy=proxy, sessions=sessions)
		self.http = urllib2Transport(cacert=cacert, proxy=proxy, sessions=sessions)
		if username and password:
			if hasattr(self.http, 'add_credentials'):
				self.http.add_credentials(username, password)
		if cert and key_file:
			if hasattr(self.http, 'add_certificate'):
				self.http.add_certificate(key=key_file, cert=cert, domain='')


		# namespace prefix, None to use xmlns attribute or False to not use it:
		self.__ns = ns
		if not ns:
			self.__xml = """<?xml version="1.0" encoding="UTF-8"?>
<%(soap_ns)s:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns:xsd="http://www.w3.org/2001/XMLSchema"
	xmlns:%(soap_ns)s="%(soap_uri)s">
<%(soap_ns)s:Header/>
<%(soap_ns)s:Body>
	<%(method)s xmlns="%(namespace)s">
	</%(method)s>
</%(soap_ns)s:Body>
</%(soap_ns)s:Envelope>"""
		else:
			self.__xml = """<?xml version="1.0" encoding="UTF-8"?>
<%(soap_ns)s:Envelope xmlns:%(soap_ns)s="%(soap_uri)s" xmlns:%(ns)s="%(namespace)s">
<%(soap_ns)s:Header/>
<%(soap_ns)s:Body><%(ns)s:%(method)s></%(ns)s:%(method)s></%(soap_ns)s:Body></%(soap_ns)s:Envelope>"""

		# parse wsdl url
		self.services = wsdl and self.wsdl_parse(wsdl, cache=cache)
		self.service_port = None