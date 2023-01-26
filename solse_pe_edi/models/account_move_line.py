# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	nombre_producto = fields.Char('Prod.', related="product_id.product_tmpl_id.name", store=True)