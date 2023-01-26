# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import pytz

import datetime
import logging
_logger = logging.getLogger(__name__)
tz = pytz.timezone('America/Lima')

class ResCurrency(models.Model):
	_inherit = 'res.currency'

	_sql_constraints = [
		('unique_name', 'CHECK(1=1)','Error Message'),
		('unique_type_name', 'unique (name,rate_type)',
		 'The currency code already exists in this rate type!'),
		('rounding_gt_zero', 'CHECK (rounding>0)',
		 'The rounding factor must be greater than 0!')
	]
	
	rate_type = fields.Selection([
		('compra', 'Compra'),
		('venta', 'Venta'),
	], string='Tipo de cambio', default='compra')

	def name_get(self):
		res = []
		for currency in self:
			if currency.rate_type:
				rate_type = ''
				if currency.rate_type == 'compra':
					rate_type = 'Compra'
				elif currency.rate_type == 'venta':
					rate_type = 'Venta'
				complete_name = '%s / %s ' % (currency.name, rate_type)
			else:
				complete_name = currency.name
			res.append((currency.id, complete_name))
		return res

	def update_exchange_rate_migo(self, token, fecha):
		token = self.env.company.token_api
		url = "https://api.migo.pe/api/v1/exchange/date"

		record = self.with_context(tz=pytz.timezone('America/Lima'))
		if not fecha:
			fecha = fields.Datetime.to_string(fields.Datetime.context_timestamp(record, datetime.datetime.now()))
			fecha = datetime.datetime.strptime(str(fecha), "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d")
		else:
			fecha = datetime.datetime.strptime(str(fecha), "%Y-%m-%d").date().strftime("%Y-%m-%d")

		payload = {
			"token": token,
			"fecha": fecha
		}

		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json"
		}

		response = requests.post(url, json=payload, headers=headers).json()

		if not token:
			raise ValidationError('Token no encontrado')

		if not response['success']:
			return

		usd_venta = self.env['res.currency'].search([('name', '=', 'USD'), ('rate_type', '=', 'venta')], limit=1)
		
		#fecha = fields.Date.context_today(self)
		if usd_venta:
			rate_pe = response['precio_venta']
			data_sale = {
				'name': fecha,
				'rate': 1 / float(rate_pe),
				'rate_pe': response['precio_venta'],
				'currency_id': usd_venta.id
			}
			moneda = self.env['res.currency.rate'].search([('name', '=', fecha), ('currency_id', '=', usd_venta.id)])
			if moneda:
				moneda.write(data_sale)
			else:
				self.env['res.currency.rate'].create(data_sale)
		usd_compra = self.env['res.currency'].search([('name', '=', 'USD'), ('rate_type', '=', 'compra')], limit=1)

		if usd_compra:
			rate_pe = response['precio_compra']
			data_purchase = {
				'name': fecha,
				'rate': 1 / float(rate_pe),
				'rate_pe': response["precio_compra"],
				'currency_id': usd_compra.id
			}
			moneda = self.env['res.currency.rate'].search([('name', '=', fecha), ('currency_id', '=', usd_compra.id)])
			if moneda:
				moneda.write(data_purchase)
			else:
				self.env['res.currency.rate'].create(data_purchase)

	def update_exchange_rate_apidev(self, token, fecha):
		token = self.env.company.token_api

		if not fecha:
			fecha = datetime.datetime.today().strftime('%Y-%m-%d')
		else:
			fecha = datetime.datetime.strptime(str(fecha), "%Y-%m-%d").date().strftime("%Y-%m-%d")

		url = "https://apiperu.dev/api/tipo_de_cambio"
		payload = {
			"token": token,
			"fecha": fecha
		}


		headers = {
			"Authorization": "Bearer %s" % token,
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

		response = requests.post(url, json=payload, headers=headers).json()
		if not token:
			raise ValidationError('Token no encontrado')

		if not response['success']:
			return

		response = response['data']

		usd_venta = self.env['res.currency'].search(
			[('name', '=', 'USD'), ('rate_type', '=', 'venta')], limit=1)
		if usd_venta:
			rate_pe = response['venta']
			data_sale = {
				'name': fields.Date.context_today(self),
				'company_rate': 1 / float(rate_pe),
				'rate': 1 / float(rate_pe),
				'rate_pe': response['venta'],
				'currency_id': usd_venta.id
			}
			self.env['res.currency.rate'].create(data_sale)
		usd_compra = self.env['res.currency'].search(
			[('name', '=', 'USD'), ('rate_type', '=', 'compra')], limit=1)

		if usd_compra:
			rate_pe = response['compra']
			data_purchase = {
				'name': fields.Date.context_today(self),
				'company_rate': 1 / float(rate_pe),
				'rate': 1 / float(rate_pe),
				'rate_pe': response["compra"],
				'currency_id': usd_compra.id
			}
			self.env['res.currency.rate'].create(data_purchase)

	def update_exchange_rate(self, fecha):
		token = ''
		tipo_busqueda = 'apiperu'
		if self.env.company:
			token = self.env.company.token_api
			tipo_busqueda = self.env.company.busqueda_ruc_dni
		else:
			token = self.env.company.token_api
			tipo_busqueda = self.env.company.busqueda_ruc_dni

		if tipo_busqueda == 'apimigo':
			self.update_exchange_rate_migo(token, fecha)
		else:
			self.update_exchange_rate_apidev(token, fecha)
		

	@api.model
	def auto_update(self):
		self.update_exchange_rate(False)

	def auto_update_simple(self):
		self.update_exchange_rate(False)


class CurrencyRate(models.Model):
	_inherit = "res.currency.rate"

	def actualizar_tc(self):
		self.currency_id.update_exchange_rate(self.name)

	@api.depends('currency_id', 'company_id', 'name')
	def _compute_rate(self):
		for currency_rate in self:
			currency_rate.rate = currency_rate.rate or currency_rate._get_latest_rate().rate or 1.0

	@api.depends('rate', 'name', 'currency_id', 'company_id', 'currency_id.rate_ids.rate')
	@api.depends_context('company')
	def _compute_company_rate(self):
		last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.company_id | self.env.company)
		for currency_rate in self:
			company = currency_rate.company_id or self.env.company
			currency_rate.company_rate = (currency_rate.rate or currency_rate._get_latest_rate().rate or 1.0) / last_rate[company]