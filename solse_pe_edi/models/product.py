# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
_logging = logging.getLogger(__name__)

class ProductCategory(models.Model):
	_inherit = "product.category"

	def _default_metodo_costeo(self):
		return self.env['pe.datas'].search([('table_code', 'in', ['PE.TABLA14']), ('code', '=', '1')], limit=1)

	@api.model
	def _get_pe_metodo_valoracion(self):
		return self.env['pe.datas'].get_selection("PE.TABLA14")

	@api.model
	def _get_pe_code(self):
		return self.env['pe.datas'].get_selection("PE.TABLA13")
	
	@api.model
	def _get_pe_type(self):
		return self.env['pe.datas'].get_selection("PE.TABLA05")

	pe_unspsc_code = fields.Char("UNSPSC Code")
	l10n_pe_valuation_method_id = fields.Many2one(comodel_name='pe.datas', default=_default_metodo_costeo, domain=[('table_code', 'in', ['PE.TABLA14'])], string=u"Método de valoración", required=True)
	pe_code = fields.Selection("_get_pe_code", "Código del catálogo", help="Código del catálogo utilizado. Sólo se podrá incluir las opciones 3 y 9 de la tabla 13.")
	pe_type = fields.Selection("_get_pe_type", "Tipo de existencia")


class ProductUoM(models.Model):
	_inherit = "uom.uom"

	sunat_code = fields.Selection(selection="_get_sunat_code", string="Código de unidad SUNAT")
	@api.model
	def _get_sunat_code(self):
		return self.env['pe.datas'].get_selection("PE.TABLA06")


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	@api.model
	def _get_pe_type(self):
		return self.env['pe.datas'].get_selection("PE.TABLA05")

	@api.model
	def _get_pe_type_detraccion(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG54")

	@api.model
	def _get_codigo_osce(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG25")
	
	#pe_code_osce = fields.Selection('_get_codigo_osce', 'Código existencia OSCE')
	pe_code_osce = fields.Char('Código OSCE')
	pe_type = fields.Selection("_get_pe_type", "Tipo de existencia")
	require_plate = fields.Boolean('Requiere Placa', help="Este producto requiere placa de vehículo")
	aplica_detraccion = fields.Selection('_get_pe_type_detraccion', string="Aplicar detracción")
	detraccion_id = fields.Many2one('pe.datas', "Id de detracción", compute="_compute_porc_detraccion", store=True)
	porc_detraccion = fields.Float(string='% Detracción', compute="_compute_porc_detraccion", store=True)

	@api.depends('aplica_detraccion')
	def _compute_porc_detraccion(self):
		for reg in self:
			if reg.aplica_detraccion:
				reg_det = self.env['pe.datas'].search([('code', '=', reg.aplica_detraccion), ('table_code', '=', 'PE.CPE.CATALOG54')], limit=1)
				reg.porc_detraccion = reg_det.value
				reg.detraccion_id = reg_det.id
			else:
				reg.porc_detraccion = 0
				reg.detraccion_id = False

class ProductProduct(models.Model):
	_inherit = 'product.product'

	@api.depends('aplica_detraccion')
	def _compute_porc_detraccion(self):
		for reg in self:
			if reg.aplica_detraccion:
				reg_det = self.env['pe.datas'].search([('code', '=', reg.aplica_detraccion), ('table_code', '=', 'PE.CPE.CATALOG54')], limit=1)
				reg.porc_detraccion = reg_det.value
				reg.detraccion_id = reg_det.id
			else:
				reg.porc_detraccion = 0
				reg.detraccion_id = False