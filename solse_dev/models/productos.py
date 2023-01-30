# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning
from odoo.osv import expression
import pytz
import logging

_logging = logging.getLogger(__name__)

class ProductAttributeValue(models.Model):
	_inherit = "product.attribute.value"

	def name_get(self):
		return [(value.id, "%s: %s" % (value.attribute_id.name, value.name)) for value in self]

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		domain = []
		nombre = name.split(": ")
		if name:
			domain = [('name', operator, nombre[1]), ('attribute_id.name', operator, nombre[0])]
		return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)