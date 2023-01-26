# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from odoo.tools.misc import ustr
import stdnum
import logging
_logging = logging.getLogger(__name__)

STATE = [('ACTIVO', 'ACTIVO'),
		 ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
		 ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
		 ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
		 ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
		 ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
		 ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
		 ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
		 ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
		 ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
		 ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
		 ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
		 ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
		 ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')]

CONDITION = [('HABIDO', 'HABIDO'),
			 ('NO HABIDO', 'NO HABIDO'),
			 ('NO HALLADO', 'NO HALLADO'),
			 ('PENDIENTE', 'PENDIENTE'),
			 ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
			 ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
			 ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
			 ('-', 'NO HABIDO'),
			 ('NO HALLADO OTROS MOT', 'NO HALLADO OTROS MOT'),
			 ('NO APLICABLE', 'NO APLICABLE'),
			 ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
			 ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
			 ('POR VERIFICAR', 'POR VERIFICAR'),
			 ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
			 ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')]

class Pertner(models.Model):
	_inherit = "res.partner"

	doc_type = fields.Char(related="l10n_latam_identification_type_id.l10n_pe_vat_code")
	doc_number = fields.Char("Numero de documento")
	commercial_name = fields.Char("Nombre commercial", default="-")
	legal_name = fields.Char("Nombre legal", default="-")
	state = fields.Selection(STATE, 'Estado', default="ACTIVO")
	condition = fields.Selection(CONDITION, 'Condicion', default='HABIDO')
	is_validate = fields.Boolean("Está validado")
	last_update = fields.Datetime("Última actualización")
	buen_contribuyente = fields.Boolean('Buen contribuyente')
	a_partir_del = fields.Date('A partir del')
	resolucion = fields.Char('Resolución')

	cod_doc_rel = fields.Char("Cod Doc relacionado", related="parent_id.l10n_latam_identification_type_id.l10n_pe_vat_code", store=True)
	numero_temp = fields.Char("Número doc relacionado", related="parent_id.doc_number", store=True)
	nombre_temp = fields.Char("Nombre relacionado", related="parent_id.name", store=True)

	"""@api.depends('name')
	def name_get(self):
		result = []
		for reg in self:
			#name = (reg.nro_dni if reg.nro_dni else '') + ' ' + reg.name
			name = reg.name
			_logging.info("name_getttttttttttttttttttttttttt")
			_logging.info(reg.id)
			_logging.info(name)
			result.append((reg.id, name))
		return result"""

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [("doc_number", operator, name), ("name", operator, name)]
		else:
			domain = ['|', ("doc_number", operator, name), ("name", operator, name)]
		
		lines = self.search(expression.AND([domain, args]), limit=limit)
		datos = lines.name_get()
		return datos

	@api.constrains('vat', 'country_id')
	def check_vat(self):
		# The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
		# This is for API pushes from external platforms where you have no control over VAT numbers.
		if self.env.context.get('no_vat_validation'):
			return

		for partner in self:
			country = partner.commercial_partner_id.country_id
			if country.id == self.env.ref('base.pe').id:
				return
			if partner.vat and self._run_vat_test(partner.vat, country, partner.is_company) is False:
				partner_label = _("partner [%s]", partner.name)
				msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat, partner_label)
				raise ValidationError(msg)


	@api.model
	def simple_vat_check(self, country_code, vat_number):
		'''
		Check the VAT number depending of the country.
		http://sima-pc.com/nif.php
		'''
		return True
		
		if country_code.upper() == 'PE':
			return True
		if not ustr(country_code).encode('utf-8').isalpha():
			return False
		check_func_name = 'check_vat_' + country_code
		check_func = getattr(self, check_func_name, None) or getattr(stdnum.util.get_cc_module(country_code, 'vat'), 'is_valid', None)
		if not check_func:
			# No VAT validation available, default to check that the country code exists
			if country_code.upper() == 'EU':
				# Foreign companies that trade with non-enterprises in the EU
				# may have a VATIN starting with "EU" instead of a country code.
				return True
			country_code = _eu_country_vat_inverse.get(country_code, country_code)
			return bool(self.env['res.country'].search([('code', '=ilike', country_code)]))
		return check_func(vat_number)

class PertnerBank(models.Model):
	_inherit = "res.partner.bank"

	cci = fields.Char("CCI", help="Codigo cuenta interbancario")
