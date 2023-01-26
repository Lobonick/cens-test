# -*- encoding: utf-8 -*-
import requests
import logging
from datetime import datetime
import requests
from io import StringIO, BytesIO
import io
import logging
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import time
import unicodedata
import json
import logging
from odoo import _
_logging = logging.getLogger(__name__)

URL_CONSULT = 'https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/consultaIndividual';
URL_CAPTCHA = 'https://ww1.sunat.gob.pe/ol-ti-itconsultaunificadalibre/consultaUnificadaLibre/doCaptcha?accion=image';
HEADERS_CPE = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}
HTML_PARSER = 'html.parser'

DOCUMENT_STATE = {
    '-': '-',
    '0': 'NO EXISTE',
    '1': 'ACEPTADO',
    '2': 'ANULADO',
    '3': 'AUTORIZADO',
    '4': 'NO AUTORIZADO',
}

COMPANY_STATE = {
	'-': '-',
	'00': 'ACTIVO',
	'01': 'BAJA PROVISIONAL',
	'02': 'BAJA PROV. POR OFICIO',
	'03': 'SUSPENSION TEMPORAL',
	'10': 'BAJA DEFINITIVA',
	'11': 'BAJA DE OFICIO',
	'12': 'BAJA MULT.INSCR. Y OTROS ',
	'20': 'NUM. INTERNO IDENTIF.',
	'21': 'OTROS OBLIGADOS',
	'22': 'INHABILITADO-VENT.UNICA',
	'30': 'ANULACION - ERROR SUNAT',
}

COMPANY_CONDITION = {
    '-': '-',
    '00': 'HABIDO',
    '01': 'NO HALLADO SE MUDO DE DOMICILIO',
    '02': 'NO HALLADO FALLECIO',
    '03': 'NO HALLADO NO EXISTE DOMICILIO',
    '04': 'NO HALLADO CERRADO',
    '05': 'NO HALLADO NRO.PUERTA NO EXISTE',
    '06': 'NO HALLADO DESTINATARIO DESCONOCIDO',
    '07': 'NO HALLADO RECHAZADO',
    '08': 'NO HALLADO OTROS MOTIVOS',
    '09': 'PENDIENTE',
    '10': 'NO APLICABLE',
    '11': 'POR VERIFICAR',
    '12': 'NO HABIDO',
    '20': 'NO HALLADO',
    '21': 'NO EXISTE LA DIRECCION DECLARADA',
    '22': 'DOMICILIO CERRADO',
    '23': 'NEGATIVA RECEPCION X PERSONA CAPAZ',
    '24': 'AUSENCIA DE PERSONA CAPAZ',
    '25': 'NO APLICABLE X TRAMITE DE REVERSION',
    '40': 'DEVUELTO',
}

def _get_captcha_validar_cpe():
	s = requests.Session() 
	try:
		r = s.get(url = URL_CAPTCHA, data={'accion': 'image'}, headers = HEADERS_CPE)
	except Exception as e:
		return (False, e)
	if not r.content:
		return (False, "")
	img = Image.open(BytesIO(r.content))
	captcha_val = pytesseract.image_to_string(img)
	captcha_val = captcha_val.strip().upper()
	return (s, captcha_val)

def get_estado_cpe(move_id):
	captcha_val = ""
	rpt = False
	consulta = False
	for i in range(10):
		consulta, captcha_val = _get_captcha_validar_cpe()
		if not consulta:
			res = {}
			res['rpta'] = 0
			res['mensaje'] = '¡El servidor no está disponible! ¡intentar otra vez!'
			return res
		if len(captcha_val) == 4:
			break
	if len(captcha_val) == 4:
		nombre = move_id.name.split('-')
		serie = nombre[0]
		numero = nombre[1]
		param = {
			'numRuc': move_id.company_id.partner_id.doc_number,
			'codComp': move_id.pe_invoice_code,
			'numeroSerie': serie,
			'numero': numero,
			'fechaEmision': move_id.invoice_date.strftime("%d/%m/%Y"),
			'monto': move_id.amount_total,
			'codigo': captcha_val,
			'codDocRecep': '',
			'numDocRecep': '',
		}
		try:
			rpt = consulta.post(url = URL_CONSULT, data = param, headers = HEADERS_CPE)
			rpt = json.loads(rpt.text)
			rpt = json.loads(rpt)
			rpt['estado'] = DOCUMENT_STATE[rpt['data']['estadoCp']] 
		except Exception as e:
			rpt = {
				'rpta': 0,
				'mensaje': 'Error al obtener respuesta'
			}
	return rpt

