# -*- encoding: utf-8 -*-
import requests
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class Partner(models.Model):
	_inherit = 'res.partner'

	@api.constrains("doc_number")
	def check_doc_number(self):
		pass