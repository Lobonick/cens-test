# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
	_inherit = 'res.company'

	busqueda_ruc_dni = fields.Selection([('apiperu', 'APIPERU'), ('apimigo', 'Migo.pe')], default="apiperu", string="API a usar", required=True)
	token_api = fields.Char('Token', default='')