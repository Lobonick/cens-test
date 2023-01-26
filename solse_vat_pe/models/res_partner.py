# -*- encoding: utf-8 -*-
import requests
import logging

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import requests
from io import StringIO
import io
import logging
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import time
import unicodedata
from . import servicio_busqueda

_logger = logging.getLogger(__name__)

def getDatosDNI(ditrict_obj, dni, tipo_busqueda, token):
	try:
		nombre = ''
		if tipo_busqueda == 'apiperu':
			nombre = servicio_busqueda.get_dni_apiperu(token, dni)
		elif tipo_busqueda == 'apimigo':
			nombre = servicio_busqueda.get_dni_apimigo(token, dni)
		
		dist_id = ditrict_obj.search([('name_simple', '=ilike', 'LIMA'), ('city_id', '!=', False)], limit=1)
		rpt = {
			'names': nombre,
			'district_code': dist_id.code,
			'province_code': dist_id.city_id.l10n_pe_code,
			'department_code': dist_id.city_id.state_id.code,
			'district_id': dist_id.id,
			'province_id': dist_id.city_id.id,
			'department_id': dist_id.city_id.state_id.id,
			'direccion': '-',
			'distrito': dist_id.name,
			'provincia': dist_id.city_id.state_id.name,
		}
		return rpt
	except Exception as e:
		return ""

def get_data_doc_number(ditrict_obj, tipo_doc, numero_doc, tipo_busqueda, token, format='json'):
	if tipo_doc == "dni" or tipo_doc=="01" or tipo_doc=="1":
		res = {'error': False, 'message': 'OK', 'data': {'success': True, 'data': getDatosDNI(ditrict_obj, numero_doc, tipo_busqueda, token)}}
		return res
	
	d = {}
	if tipo_busqueda == 'apiperu':
		d = servicio_busqueda.get_ruc_apiperu(token, numero_doc)
		_logger.info("buscar apiperu")
		_logger.info(d)
	elif tipo_busqueda == 'apimigo':
		d = servicio_busqueda.get_ruc_apimigo(token, numero_doc)

	if d['error'] == True:
		return {'error': True, 'message': 'No se pudo completar la operacion', 'data': {}}

	dist_id = False
	if 'ubigeo' in d:
		ubigeo = d['ubigeo']
		dist_id = ditrict_obj.search([('code', '=', ubigeo)], limit=1)
	else:
		distrito = unicodedata.normalize('NFKD', d['distrito']).encode('ASCII', 'ignore').strip().upper().decode()
		provincia = unicodedata.normalize('NFKD', d['provincia']).encode('ASCII', 'ignore').strip().upper().decode()
		dist_id = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id', '!=', False)])
		if len(dist_id) < 1:
			return {'error': True, 'message': 'No se pudo ubicar el codigo de distrito', 'data': {}}
		elif len(dist_id) > 1:
			dist_id = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id.name_simple', '=ilike', provincia)])
		if len(dist_id) > 1:
			return {'error': True, 'message': 'No se pudo establecer el codigo de distrito, mas de una opcion encontrada', 'data': {}}
		elif len(dist_id) < 1:
			return {'error': True, 'message': 'No se pudo ubicar el codigo de distrito, se perdio en la validacion '+d['distrito']+' '+d['provincia']+' '+d['departamento'], 'data': {}}
	
	res = {'error': True, 'message': 'Error al construir mensaje de retorno', 'data': {}}	

	if dist_id:
		data_json = {
			'success': True,
			'data': {
				'razonSocial': d['razonSocial'],
				'district_code': dist_id.code,
				'province_code': dist_id.city_id.l10n_pe_code,
				'department_code': dist_id.city_id.state_id.code,
				'district_id': dist_id.id,
				'province_id': dist_id.city_id.id,
				'department_id': dist_id.city_id.state_id.id,
				'direccion': d['direccion'],
				'distrito': dist_id.name,
				'provincia': dist_id.city_id.name,
				'condicion': d['condicion'],
				'estado': d['estado']
			}
		}
		if 'buen_contribuyente' in d and d['buen_contribuyente']:
			data_json['data']['buen_contribuyente'] = d['buen_contribuyente']
			data_json['data']['a_partir_del'] = d['a_partir_del']
			data_json['data']['resolucion'] = d['resolucion']

		res = {'error': False, 'message': None, 'data': data_json}
	return res

class Partner(models.Model):
	_inherit = 'res.partner'

	l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', default=lambda self: self.env.ref('l10n_pe.it_RUC'))
	doc_type = fields.Char(related="l10n_latam_identification_type_id.l10n_pe_vat_code")
	doc_number = fields.Char("Numero de documento")
	commercial_name = fields.Char("Nombre commercial", default="-")
	legal_name = fields.Char("Nombre legal", default="-")
	state = fields.Selection(servicio_busqueda.STATE, 'Estado', default="ACTIVO")
	condition = fields.Selection(servicio_busqueda.CONDITION, 'Condicion', default='HABIDO')
	is_validate = fields.Boolean("Está validado")
	last_update = fields.Datetime("Última actualización")
	buen_contribuyente = fields.Boolean('Buen contribuyente')
	a_partir_del = fields.Date('A partir del')
	resolucion = fields.Char('Resolución')

	busqueda_automatica = fields.Boolean("Busqueda automatica", default=True, help="Si esta marcado cuando ingrese o cambie el numero ruc o dni se buscaran sus datos en la pagina de SUNAT")

	def consulta_datos_simple(self, tipo_documento, nro_documento):
		#res = {'error': True, 'message': None, 'data': {}}
		return self.consulta_datos(tipo_documento, nro_documento, 'json')

	# Para usar la funcion de busqueda desde llamadas javascript
	@api.model
	def consulta_datos(self, tipo_documento, nro_documento, format='json'):
		res = {'error': True, 'message': None, 'data': {}}
		res_partner = self.search([('vat', '=', nro_documento)]).exists()
		# Si el nro. de doc. ya existe
		if res_partner:
			res['message'] = 'Nro. doc. ya existe'
			return res

		token = ''
		tipo_busqueda = 'apiperu'
		if self.company_id:
			token = self.company_id.token_api
			tipo_busqueda = self.company_id.busqueda_ruc_dni
		else:
			token = self.env.company.token_api
			tipo_busqueda = self.env.company.busqueda_ruc_dni

		try:
			ditrict_obj = self.env['l10n_pe.res.city.district']
			res = get_data_doc_number(ditrict_obj, tipo_documento, str(nro_documento), tipo_busqueda, token, format='json')
		except Exception as e:
			res['message'] = 'Error en la conexion: '+str(self.company_id)
			return res
			
		return res

	# Funcion 2 Para usar la funcion de busqueda desde llamadas javascript
	@api.model
	def consulta_datos_completo(self, tipo_documento, nro_documento, format='json'):
		res = {'error': True, 'message': None, 'data': {}, 'registro': False}
		res_partner = self.search(['|', ('vat', '=', nro_documento), ('doc_number', '=', nro_documento)], limit=1)
		# Si el nro. de doc. ya existe
		if res_partner:
			res['message'] = 'Nro. doc. ya existe'
			res['error'] = False
			res['registro'] = res_partner
			return res

		token = ''
		tipo_busqueda = 'apiperu'
		if self.company_id:
			token = self.company_id.token_api
			tipo_busqueda = self.company_id.busqueda_ruc_dni
		else:
			token = self.env.company.token_api
			tipo_busqueda = self.env.company.busqueda_ruc_dni
		try:
			ditrict_obj = self.env['l10n_pe.res.city.district']
			res = get_data_doc_number(ditrict_obj, tipo_documento, str(nro_documento), tipo_busqueda, token, format='json')
		except Exception as e:
			res['message'] = 'Error en la conexion: '+str(self.company_id)
			return res
			
		return res

	@api.constrains("doc_number")
	def check_doc_number(self):
		if not self.parent_id:
			for partner in self:
				doc_type = partner.l10n_latam_identification_type_id.l10n_pe_vat_code
				if not doc_type and not partner.doc_number:
					continue
				elif doc_type == "0":
					continue
				elif doc_type and not partner.doc_number:
					raise ValidationError("Ingrese el número de documento")
				vat = partner.doc_number
				if doc_type == '6':
					check = self.validate_ruc(vat)
					if not check:
						raise ValidationError('El RUC ingresado es incorrecto')
				if self.search_count([('company_id', '=', partner.company_id.id), ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', doc_type), ('doc_number', '=', partner.doc_number)]) > 1:
					raise ValidationError('El número de documento ya existe y viola la restricción de campo único')

	@api.onchange('l10n_latam_identification_type_id')
	def onchange_company_type(self):
		doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
		if doc_type == "6":
			self.company_type = 'company'
		else:
			self.company_type = 'person'
		super(Partner, self).onchange_company_type()

	@staticmethod
	def validate_ruc(vat):
		return True
		factor = '5432765432'
		sum = 0
		dig_check = False
		if len(vat) != 11:
			return False
		try:
			int(vat)
		except ValueError:
			return False
		for f in range(0, 10):
			sum += int(factor[f]) * int(vat[f])
		subtraction = 11 - (sum % 11)
		if subtraction == 10:
			dig_check = 0
		elif subtraction == 11:
			dig_check = 1
		else:
			dig_check = subtraction
		if not int(vat[10]) == dig_check:
			return False
		return True

	@api.onchange("doc_number", "l10n_latam_identification_type_id")
	@api.depends("l10n_latam_identification_type_id", "doc_number")
	def _doc_number_change(self):
		vat = self.doc_number
		if self.busqueda_automatica == False:
			return
			
		token = ''
		tipo_busqueda_ruc_dni = 'apiperu'
		tipo_busqueda_ruc_dni = 'apiperu'
		if self.company_id:
			token = self.company_id.token_api
			tipo_busqueda_ruc_dni = self.company_id.busqueda_ruc_dni
			tipo_busqueda_ruc_dni = self.company_id.busqueda_ruc_dni
		else:
			token = self.env.company.token_api
			tipo_busqueda_ruc_dni = self.env.company.busqueda_ruc_dni
			tipo_busqueda_ruc_dni = self.env.company.busqueda_ruc_dni
		if vat and self.l10n_latam_identification_type_id:
			vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
			if vat_type == '1':
				if len(vat) != 8:
					raise UserError('El DNI ingresado es incorrecto')
				response = False
				try:
					if tipo_busqueda_ruc_dni == 'apiperu':
						response = servicio_busqueda.get_dni_apiperu(token, vat.strip())
					elif tipo_busqueda_ruc_dni == 'apimigo':
						response = servicio_busqueda.get_dni_apimigo(token, vat.strip())

				except Exception:
					reponse = False
				
				if response:
					self.name = response
					self.company_type = "person"
					self.is_validate = True

				self.vat = "%s" % (vat)
				self.company_type = "person"
				self.country_id = 173
				district = self.env['l10n_pe.res.city.district'].search([('name', 'ilike', 'Lima'), ('city_id.name', 'ilike', 'Lima')])
				if len(district) == 1:
					self.l10n_pe_district = district.id
					self.city_id = district.city_id.id
					self.state_id = district.city_id.state_id.id
				elif len(district) == 0:
					province = self.env['res.city'].search([('name', 'ilike', 'Lima')])
					if len(province) == 1:
						self.city_id = province.id
						self.state_id = district.city_id.state_id.id
				else:
					province = self.env['res.city'].search([('name', 'ilike', 'Lima')])
					if len(province) == 1:
						self.city_id = province.id
						district = self.env['l10n_pe.res.city.district'].search([('name', '=ilike', 'Lima'),
																				 ('city_id.name', 'ilike', self.city_id.name)])
						if len(district) == 1:
							self.l10n_pe_district = district.id

			elif vat_type == "6":
				if not self.validate_ruc(vat):
					raise UserError('El RUC ingresado es incorrecto')

				for x in range(0,3):
					if tipo_busqueda_ruc_dni == 'apiperu':
						vals = servicio_busqueda.get_ruc_apiperu(token, vat)
					elif tipo_busqueda_ruc_dni == 'apimigo':
						vals = servicio_busqueda.get_ruc_apimigo(token, vat)
	
					if vals.get('error') == False:
						break
					elif x == 2:
						raise UserError(vals.get('message'))
				if vals.get('error') == True:
					raise UserError(vals.get('message'))
				
				if vals:
					self.commercial_name = vals.get('razonSocial')
					self.legal_name = vals.get('razonSocial')
					self.name = vals.get('razonSocial')
					self.street = vals.get('direccion', False)
					self.company_type = "company"
					self.state = vals.get('estado', False)
					self.condition = vals.get('condicion')
					self.is_validate = True
					if vals.get('buen_contribuyente', False):
						self.buen_contribuyente = vals.get('buen_contribuyente')
						self.a_partir_del = vals.get('a_partir_del')
						self.resolucion = vals.get('resolucion')


					ditrict_obj = self.env['l10n_pe.res.city.district']
					district = False
					if vals.get('ubigeo'):
						ubigeo = vals.get('ubigeo')
						district = ditrict_obj.search([('code', '=', ubigeo)], limit=1)
					elif vals.get('distrito') and vals.get('provincia'):
						distrito = unicodedata.normalize('NFKD', vals.get('distrito')).encode('ASCII', 'ignore').strip().upper().decode()
						district = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id', '!=', False)])
						if len(district) < 1:
							raise Warning('No se pudo ubicar el codigo de distrito'+distrito)
						elif len(district) > 1:
							district = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id.name_simple', '=ilike', vals.get('provincia'))])
						if len(district) > 1:
							raise Warning('No se pudo establecer el codigo de distrito, mas de una opcion encontrada')
						elif len(district) < 1:
							raise Warning('No se pudo ubicar el codigo de distrito, se perdio en la validacion '+distrito+' '+vals.get('provincia')+' '+vals.get('departamento')) 
						
					if district:
						self.l10n_pe_district = district.id
						self.city_id = district.city_id.id
						self.state_id = district.city_id.state_id.id
						self.zip = district.code
						self.country_id = district.city_id.state_id.country_id.id


				self.vat = "%s" % vat
			elif (vat_type != '6') or (vat_type != '1'):
				self.vat = "%s" % (self.doc_number)

	@api.onchange('vat')
	def _vat_change(self):
		if self.vat:
			vat = len(self.vat) >= 1 and self.vat or ""
			doc_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code or False

			if vat:
				if doc_type == "0":
					self.doc_type = "0"
				elif doc_type == "1":
					if len(vat) != 8:
						raise UserError('El DNI ingresado es incorrecto')
					self.doc_type = "1"
				elif doc_type == "4":
					self.doc_type = "4"
				elif doc_type == "6":
					if not self.validate_ruc(vat):
						raise UserError('El RUC ingresado es incorrecto')
					self.doc_type = "6"
				elif doc_type == "A":
					self.doc_type = "A"
				if self.doc_number != vat:
					self.doc_number = vat
			else:
				self.doc_type = "7"
				if self.doc_number != vat:
					self.doc_number = vat

	@api.onchange('country_id')
	def _onchange_country(self):
		pass

	@api.onchange('l10n_pe_district')
	def _onchange_district_id(self):
		if self.l10n_pe_district:
			self.zip = self.l10n_pe_district.code
			if not self.city_id:
				self.city_id = self.l10n_pe_district.city_id.id

	@api.onchange('city_id')
	def _onchange_province_id(self):
		if self.city_id:
			return {'domain': {'l10n_pe_district': [('city_id', '=', self.city_id.id)]}}
		else:
			return {'domain': {'l10n_pe_district': []}}

	@api.onchange('state_id')
	def _onchange_state_id(self):
		if self.state_id:
			return {'domain': {'city_id': [('state_id', '=', self.state_id.id)]}}
		else:
			return {'domain': {'city_id': []}}

	@api.model
	def change_commercial_name(self):
		partner_ids = self.search(
			[('commercial_name', '!=', '-'), ('doc_type', '=', '6')])
		for partner_id in partner_ids:
			partner_id.update_document()

	def update_document(self):
		self._doc_number_change()
		self._vat_change()
