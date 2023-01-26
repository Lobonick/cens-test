# -*- coding: utf-8 -*-

from odoo import models, fields, api
import unicodedata

class District(models.Model):
	_description = "Distrito"
	_inherit = 'l10n_pe.res.city.district'
	
	name_simple = fields.Char('Nombre simple', compute='_compute_nombre_simple', store=True)

	@api.depends('name')
	def _compute_nombre_simple(self):
		for reg in self:
			reg.name_simple = unicodedata.normalize('NFKD', reg.name).encode('ASCII', 'ignore').strip().upper().decode()