# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from datetime import datetime
import odoo.addons.decimal_precision as dp
from . import constantes
import logging

_logging = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = "sale.order"

	factura_ids = fields.One2many('account.move', 'venta_id', 'Facturas')
	nro_factura = fields.Char("Nro Factura", compute="_get_invoiced", store=False)
	orden_compra = fields.Char("Orden de compra")
	descuento_global = fields.Boolean("Aplicar descuento Global")
	amount_discount = fields.Monetary(string='Descuento', store=True, readonly=True, compute='_amount_all', digits=dp.get_precision('Account'), track_visibility='always')

	@api.onchange('discount_type', 'discount_rate', 'order_line', 'descuento_global')
	def supply_rate(self):
		for order in self:
			if not order.descuento_global:
				return
			elif order.discount_type == 'percent':
				for line in order.order_line:
					line.discount = order.discount_rate
			else:
				total = discount = 0.0
				for line in order.order_line:
					total += round((line.product_uom_qty * line.price_unit))
				if order.discount_rate != 0:
					discount = (order.discount_rate / total) * 100
				else:
					discount = order.discount_rate
				for line in order.order_line:
					line.discount = discount


	@api.depends('order_line.invoice_lines', 'factura_ids', 'factura_ids.state', 'factura_ids.name')
	def _get_invoiced(self):
		for order in self:
			#invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			invoices = order.factura_ids.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			if not invoices:
				invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))

			order.invoice_ids = invoices
			if invoices:
				order.nro_factura = invoices[0].l10n_latam_document_number
			else:
				order.nro_factura = ""
			order.invoice_count = len(invoices)

	def recalcular_nro_factura(self):
		lista = self.env['sale.order'].search([('nro_factura', 'in', [False, ''])])
		for order in lista:
			invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			if invoices:
				order.nro_factura = invoices[0].l10n_latam_document_number
			else:
				order.nro_factura = ""


	def _prepare_invoice(self):
		self.ensure_one()
		res = super(SaleOrder, self)._prepare_invoice()
		res['venta_id'] = self.id
		res['orden_compra'] = self.orden_compra
		tipo_documento = self.env['l10n_latam.document.type']
		l10n_latam_document_type_id = False
		partner_id = self.partner_id.parent_id or self.partner_id
		doc_type = partner_id.doc_type
		if not doc_type:
			return res
		
		tipo_doc_id = False
		if doc_type in '6':
			tipo_doc_id = tipo_documento.search([('code', '=', '01'), ('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id

		elif doc_type in '1':
			tipo_doc_id = tipo_documento.search([('code', '=', '03'), 
				('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id
		else:
			tipo_doc_id = tipo_documento.search([('code', '=', '03'), 
				('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id

		if not tipo_doc_id:
			tipo_doc_id = tipo_documento.search([('code', '=', '00'), ('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id
		
		if l10n_latam_document_type_id:
			res['l10n_latam_document_type_id'] = l10n_latam_document_type_id

		reg = self
		tipo_transaccion = 'contado'
		if reg.payment_term_id:
			tipo_transaccion = reg.payment_term_id.tipo_transaccion or 'contado'

		res['tipo_transaccion'] = tipo_transaccion
		res['descuento_global'] = self.descuento_global
		return res

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	pe_affectation_code = fields.Selection(selection='_get_pe_reason_code', string='Tipo de afectación', default='10', help='Tipo de afectación al IGV')

	nro_ov = fields.Char("Nro OV", related="order_id.name", store=True)
	nro_comprobante = fields.Char("Nro Comprobante", related="order_id.nro_factura", store=True)
	cliente = fields.Many2one('res.partner',string='Cliente', related='order_id.partner_id', store=True)
	nro_ruc_dni = fields.Char(related="order_id.partner_id.vat", store=True)
	fecha_pedido = fields.Datetime("Fecha Pedido", related="order_id.date_order", store=True)
	uom_po_id = fields.Many2one('uom.uom', related="product_id.uom_po_id")

	def _prepare_invoice_line(self, **optional_values):
		self.ensure_one()
		res = super(SaleOrderLine, self)._prepare_invoice_line()
		res['pe_affectation_code'] = self.pe_affectation_code
		return res

	@api.model
	def _get_pe_reason_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG7')

	@api.model
	def _get_pe_tier_range(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG8')

	def _set_free_tax(self):
		if self.pe_affectation_code not in ('10', '20', '30', '40'):
			ids = self.tax_id.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
			self.discount = 100
			if not vat:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito'])], limit=1)
				self.tax_id = [(6, 0, ids + res.ids)]
		else:
			if self.discount == 100:
				self.discount = 0
			ids = self.tax_id.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
		if vat:
			res = self.env['account.tax'].search([('id', 'in', ids), ('id', 'not in', vat.ids)]).ids
			self.tax_id = [(6, 0, res)]

	@api.onchange('discount')
	def onchange_affectation_code_discount(self):
		for rec in self:
			if rec.discount != 100:
				pass
			elif rec.pe_affectation_code not in ['11', '12', '13', '14', '15', '16', '17', '21', '31', '32', '33', '34', '35', '36']:
				rec.pe_affectation_code = '11'

	@api.onchange('pe_affectation_code')
	def onchange_pe_affectation_code(self):
		# Catalogo 7
		# (10) Gravado - Operación Onerosa; ​(11) Gravado - Retiro por premio; ​(12) Gravado - Retiro por donación; ​ ​ 
		# (13) Gravado - Retiro;​ (14)​ Gravado - Retiro por publicidad; ​ (15) Gravado - Bonificaciones; ​(16)​ Gravado - Retiro por entrega a trabajadores
		if self.pe_affectation_code in ('10'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()

		elif self.pe_affectation_code in ('11', '12', '13', '14', '15', '16', '17'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
		
		# (20) Exonerado - Operación Onerosa;
		elif self.pe_affectation_code in ('20'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()
		# (21) Exonerado – Transferencia gratuita
		elif self.pe_affectation_code in ('21'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
		# (30) Inafecto - Operación Onerosa; ​ ​ 
		elif self.pe_affectation_code in ('30'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			#self.discount = 100
		# (31) Inafecto - Retiro por bonificación; ​ ​ (32) Inafecto - Retiro; ​ ​ 
		# (33) Inafecto - Retiro por muestras médicas; ​ ​ (34) Inafecto - Retiro por convenio colectivo; ​ ​ (35) Inafecto - Retiro por premio; ​ ​ 
		# (36) Inafecto - Retiro por publicidad
		elif self.pe_affectation_code in ('31', '32', '33', '34', '35', '36'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
			#self._set_free_tax()
		# (40) Exportación
		elif self.pe_affectation_code in ('40', ):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()

	def set_pe_affectation_code(self):
		igv = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv'])
		if self.tax_id:
			if igv:
				if self.discount == 100:
					self.pe_affectation_code = '11'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '10'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado'])
		if self.tax_id:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '21'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '20'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto'])
		if self.tax_id:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '31'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '30'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion'])
		if self.tax_id:
			if vat:
				self.pe_affectation_code = '40'

	@api.onchange('product_id')
	def _onchange_product_id(self):
		for rec in self.filtered(lambda x: x.product_id):
			rec.set_pe_affectation_code()

		self = self.with_context(check_move_validity=False)

	def get_price_unit(self, all=False):
		self.ensure_one()
		price_unit = self.price_unit
		if all:
			price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			tax_id = self.tax_id
		else:
			tax_id = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
		res = tax_id.with_context(round=False).compute_all(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res

	def get_price_unit_sunat(self, all=False):
		self.ensure_one()
		price_unit = self.price_unit
		if all:
			price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			tax_id = self.tax_id
		else:
			tax_id = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
			
		res = tax_id.with_context(round=False).compute_all_sunat(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res
