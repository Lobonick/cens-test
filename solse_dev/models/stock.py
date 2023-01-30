# -*- coding: utf-8 -*-
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError
import logging

_logging = logging.getLogger(__name__)

class Picking(models.Model):
	_inherit = "stock.picking"

	name = fields.Char('Operation Type', readonly=False, required=True, translate=True)
	estado_temp = fields.Char("Estado al importar")