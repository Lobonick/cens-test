# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import requests
import logging
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class Country(models.Model):
	_inherit = 'res.country'

	@api.model
	def get_pos_sale_departamentos(self, partner):
		country_id = partner.get('id', False)
		if country_id:  # Modifying existing partner
			return [(st.id, st.name, st.code) for st in self.env['res.country'].search([('id', '=', country_id)], limit=1).state_ids] 
		return []

class State(models.Model):
	_inherit = 'res.country.state'

	provincias_ids = fields.One2many('res.city', 'state_id', 'Princias')

	@api.model
	def get_pos_sale_privincias(self, partner):
		departamento_id = partner.get('id', False)
		if departamento_id:  # Modifying existing partner
			return [(st.id, st.name, st.l10n_pe_code) for st in self.env['res.country.state'].search([('id', '=', departamento_id)], limit=1)[0].provincias_ids] 
		return []

class City(models.Model):
	_inherit = 'res.city'

	distritos_ids = fields.One2many('l10n_pe.res.city.district', 'city_id', 'Distritos')

	@api.model
	def get_pos_sale_distritos(self, partner):
		provincia_id = partner.get('id', False)
		if provincia_id:  # Modifying existing partner
			return [(st.id, st.name, st.code) for st in self.env['res.city'].search([('id', '=', provincia_id)], limit=1)[0].distritos_ids] 
		return []