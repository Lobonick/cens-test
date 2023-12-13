# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

from odoo import api, fields, models
from datetime import timedelta
import logging

_logging = logging.getLogger(__name__)

class PlanillasFactoringCens(models.Model):
	_inherit = 'solse.factoring.planillas'
	x_cens_company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        domain=[],
        store=True,
        default=lambda self: self._default_company_id()
    )    
	x_cens_logo_financiera = fields.Binary(string='', related='empresa_factoring.image_256', store=True, attachment=True)
	x_cens_marcador_pagina = fields.Binary(string='', related='x_cens_company_id.x_studio_factoring', store=True, attachment=True)
	x_cens_linea_separadora = fields.Binary(string='', related='x_cens_company_id.x_studio_separador_06', store=False)


	# ------------------------------
    # ASIGNA LA CIA x DEFAULT
    # ------------------------------
	def _default_company_id(self):
		return self.env.company.id

	# ------------------------------
    # IMPRIME PLANILLA FACTORING
    # ------------------------------
	def imprime_planilla_factoring(self):
		w_correlativo = ""
		pass