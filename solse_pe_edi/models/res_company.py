# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

class Company(models.Model) :
	_inherit = 'res.company'

	sunat_amount = fields.Float(string="Monto", help="Usado para el control de boletas", digits=(16, 2), default=700)
	cuenta_detraccion = fields.Many2one('account.journal', string='Cuenta de Detracción', domain="[('type','=', 'bank')]")
	monto_detraccion = fields.Float(string='Monto detracción', help="Monto usado para determinar cuando aplicar detracción", default=700)
	agente_retencion = fields.Boolean('Es agente de retención')
	por_retencion = fields.Float('% Retención', default=3.0)
	configuracion_id = fields.Many2one('res.company.conf', string='Configuración')
	
	def _localization_use_documents(self):
		self.ensure_one()
		return self.country_id == self.env.ref('base.pe') or super()._localization_use_documents()
