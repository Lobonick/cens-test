# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning, ValidationError
import xml.etree.cElementTree as ET
from lxml import etree
import json
import logging
_logging = logging.getLogger(__name__)


class LineaAfectacionCompra(models.Model):
	_name = "solse.pe.afectacion.compra"
	_description = "Linea Afectación compra"

	name = fields.Char("Nombre")
	active = fields.Boolean(default=True)
	sequence = fields.Integer(default=10)
	impuesto_afect_ids = fields.One2many(comodel_name="solse.pe.impuesto.afectacion.compra", inverse_name="linea_afectacion_id", string="Impuesto")
	impuesto_defecto = fields.Many2one("solse.pe.impuesto.afectacion.compra", domain="[('id', 'in', impuesto_afect_ids)]", string="Impuesto por defecto")
	nro_col_importe_afectacion = fields.Integer("Columna Importe Afectación")

class ImpuestoAfectacionCompra(models.Model):
	_name = "solse.pe.impuesto.afectacion.compra"
	_description = "Impuesto Afectación compra"

	active = fields.Boolean(default=True)
	linea_afectacion_id = fields.Many2one("solse.pe.afectacion.compra", string="Afectación compra")
	impuesto_id = fields.Many2one("account.tax", string="Impuesto")
	name = fields.Char("Nombre", related="impuesto_id.name")
	nro_col_importe_impuesto = fields.Integer("Columna Importe Impuesto")
	

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def get_view(self, view_id=None, view_type='form', **options):
		res = super(AccountMove, self).get_view(view_id, view_type, **options)
		if view_type in ['form']:
			paso_validacion = False
			if self._context.get('params') and 'action' in self._context['params']:
				parametros = self._context['params']
				accion = self.env['ir.actions.act_window'].search([('id', '=', parametros['action'])])
				if accion and accion.domain and ('in_invoice' in accion.domain or 'in_refund' in accion.domain):
					paso_validacion = True

			elif self._context.get('default_move_type'):
				move_type = self._context.get('default_move_type')
				if move_type in ['in_invoice', 'in_refund']:
					paso_validacion = True

			if paso_validacion:
				root = etree.fromstring(res['arch'])
				for el in root.iter('field'):
					if el.attrib.get('name') in ['tipo_afectacion_compra']:
						json_mod = {
							'column_invisible': False,
						}
						el.attrib.update({'invisible': '0', 'modifiers': json.dumps(json_mod)})
						break

				res.update({'arch': etree.tostring(root, encoding='utf8')})

		return res


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def _default_afectacion_compra(self):
		afectacion = self.env['solse.pe.afectacion.compra'].search([], limit=1)

		return afectacion

	tipo_afectacion_compra = fields.Many2one("solse.pe.afectacion.compra", string='Tipo de afectación', help='Tipo de afectación Compra', store=True)

	@api.onchange('tipo_afectacion_compra')
	def onchange_tipo_afectacion_compra(self):
		if not self.move_id.move_type in ['in_invoice', 'in_refund']:
			return

		if self.tipo_afectacion_compra:
			por_defecto = False
			impuesto = self.tax_ids[0]
			impuesto_afect_ids = []

			for item in self.tipo_afectacion_compra.impuesto_afect_ids:
				impuesto_afect_ids.append(item.impuesto_id.id)

			if impuesto._origin.id in impuesto_afect_ids:
				return

			if self.tipo_afectacion_compra.impuesto_defecto and self.tipo_afectacion_compra.impuesto_defecto.impuesto_id:
				por_defecto = self.tipo_afectacion_compra.impuesto_defecto.impuesto_id.id

			if not por_defecto and self.tipo_afectacion_compra.impuesto_afect_ids:
				por_defecto = self.tipo_afectacion_compra.impuesto_afect_ids[0].impuesto_id.id

			if por_defecto:
				self.tax_ids = [(6, 0, [por_defecto])]

			self._set_free_tax_purchase()

	def set_pe_affectation_purchase_code(self):
		if self.tax_ids:
			impuesto = self.tax_ids[0]
			impuesto_afect_ids = []
			for item in self.tipo_afectacion_compra.impuesto_afect_ids:
				impuesto_afect_ids.append(item.impuesto_id.id)

			if impuesto._origin.id in impuesto_afect_ids:
				return

			afectacion_compra_ids = self.env['solse.pe.afectacion.compra'].search([])
			for afectacion in afectacion_compra_ids:
				impuesto_afect_ids = []
				for item in afectacion.impuesto_afect_ids:
					impuesto_afect_ids.append(item.impuesto_id.id)

				if impuesto._origin.id in impuesto_afect_ids:
					self.tipo_afectacion_compra = afectacion.id

	@api.onchange('tax_ids')
	def _onchange_impuesto_compra(self):
		if self.tax_ids:
			impuesto = self.tax_ids[0]
			impuesto_afect_ids = []
			for item in self.tipo_afectacion_compra.impuesto_afect_ids:
				impuesto_afect_ids.append(item.impuesto_id.id)

			if impuesto._origin.id in impuesto_afect_ids:
				return

			afectacion_compra_ids = self.env['solse.pe.afectacion.compra'].search([])
			for afectacion in afectacion_compra_ids:
				impuesto_afect_ids = []
				for item in afectacion.impuesto_afect_ids:
					impuesto_afect_ids.append(item.impuesto_id.id)

				if impuesto._origin.id in impuesto_afect_ids:
					self.tipo_afectacion_compra = afectacion.id
					return

	@api.onchange('product_id')
	def _onchange_purchase_product_id(self):
		for rec in self.filtered(lambda x: x.product_id):
			rec.set_pe_affectation_purchase_code()

		self = self.with_context(check_move_validity=False)


	def _set_free_tax_purchase(self):
		return
		if self.tipo_afectacion_compra in ('9996'):
			self.discount = 100
		else:
			if self.discount == 100:
				self.discount = 0

		
 
		


