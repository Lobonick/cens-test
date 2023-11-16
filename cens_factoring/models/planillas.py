# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

from odoo import models, fields, api, _
from datetime import timedelta
from contextlib import ExitStack, contextmanager
import logging
from odoo.exceptions import UserError, ValidationError

_logging = logging.getLogger(__name__)

class PlanillasFactoring(models.Model):
	_inherit = 'solse.factoring.planillas'
	x_cens_company_id = fields.Many2one("res.company", string="Compañia", domain=[])
	x_cens_company_id.id = 1
	x_cens_logo_financiera = fields.Binary(string='', related='empresa_factoring.image_256', store=True, attachment=True)
	x_cens_marcador_pagina = fields.Binary(string='', related='x_cens_company_id.x_studio_factoring', store=True, attachment=True)

