# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Company(models.Model):
	_inherit = "res.company"

	pe_is_sync = fields.Boolean("Es sincrono", default=True)
	pe_certificate_id = fields.Many2one(comodel_name="cpe.certificate", string="Certificado", domain="[('state','=','done')]")
	pe_cpe_server_id = fields.Many2one(comodel_name="cpe.server", string="Servidor", domain="[('state','=','done')]")
	enviar_email = fields.Boolean('Envio correo automatico', help="Si esta activo cada vez que se confirme un comprobante se enviara el pdf al cliente")

class Partner(models.Model):
	_inherit = "res.partner"

	@staticmethod
	def validate_ruc(vat):
		return True
		factor = '5432765432'
		sum = 0
		dig_check = False
		if len(vat) != 11:
			return False
		try:
			int(vat)
		except ValueError:
			return False
		for f in range(0, 10):
			sum += int(factor[f]) * int(vat[f])
		subtraction = 11 - (sum % 11)
		if subtraction == 10:
			dig_check = 0
		elif subtraction == 11:
			dig_check = 1
		else:
			dig_check = subtraction
		if not int(vat[10]) == dig_check:
			return False
		return True

	@api.onchange('country_id')
	def _onchange_country(self):
		pass

	@api.onchange('l10n_pe_district')
	def _onchange_district_id(self):
		if self.l10n_pe_district:
			self.zip = self.l10n_pe_district.code
			if not self.city_id:
				self.city_id = self.l10n_pe_district.city_id.id

	@api.onchange('city_id')
	def _onchange_province_id(self):
		if self.city_id:
			return {'domain': {'l10n_pe_district': [('city_id', '=', self.city_id.id)]}}
		else:
			return {'domain': {'l10n_pe_district': []}}

	@api.onchange('state_id')
	def _onchange_state_id(self):
		if self.state_id:
			return {'domain': {'city_id': [('state_id', '=', self.state_id.id)]}}
		else:
			return {'domain': {'city_id': []}}