# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, Warning
from pdf417gen.encoding import to_bytes, encode_high, encode_rows
from pdf417gen.util import chunks
from pdf417gen.compaction import compact_bytes
from pdf417gen import render_image
import tempfile
import re
from datetime import datetime, date, timedelta
from odoo.tools.misc import formatLang
from io import StringIO, BytesIO
from importlib import reload
import sys
import time
from .cpe_servicios_extras import get_estado_cpe
from . import constantes

import logging
_logging = logging.getLogger(__name__)


try:
	import qrcode
	qr_mod = True
except:
	qr_mod = False

from ast import literal_eval
import socket
from binascii import hexlify
from functools import partial
TYPE2JOURNAL = {'out_invoice':'sale', 
 'in_invoice':'purchase',  'out_refund':'sale', 
 'in_refund':'purchase'}


class AccountInvoiceLine(models.Model):
	_inherit = 'account.move.line'
	
	pe_affectation_code = fields.Selection(selection='_get_pe_reason_code', string='Tipo de afectación', default='10', help='Tipo de afectación al IGV')
	pe_tier_range = fields.Selection(selection='_get_pe_tier_range', string='Tipo de sistema', help='Tipo de sistema al ISC')
	pe_license_plate = fields.Char('License Plate', size=10)
	pe_charge_amount = fields.Float('Cargos por ítem', compute='get_pe_charge_amount')
	pe_icbper_amount = fields.Float('ICBPER', compute='_compute_pe_icbper_amount')
	amount_discount = fields.Float("Monto de descuento", compute="_compute_amount_discount")

	pe_invoice_ids = fields.Many2many('account.move', 'pe_account_invoice_line_invoice_rel', 'line_id', 'move_id', string="Líneas de facturas", copy=False, readonly=True)
	pe_invoice_id = fields.Many2one('account.move', string="Facturas", copy=False, readonly=True)
	move_type = fields.Selection(related="move_id.move_type", store=True)

	@api.depends('price_unit', 'discount', 'move_id.currency_id', 'tax_ids')
	def _compute_amount_discount(self):
		for line in self:
			price = line.price_unit * (line.discount or 0.0) / 100.0
			amount_discount = line.tax_ids.compute_all(price, line.move_id.currency_id, line.quantity, line.product_id, line.move_id.partner_id)
			line.amount_discount = amount_discount['total_excluded']

	@api.depends('tax_ids')
	def _compute_pe_icbper_amount(self):
		for line in self:
			pe_icbper_amount = 0.0
			if line.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['ICBPER']):
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, line.move_id.currency_id, 1, line.product_id, line.move_id.partner_id).get('taxes', [])
				for tax_val in taxes:
					tax = self.env['account.tax'].browse(tax_val.get('id'))
					if tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['ICBPER']:
						pe_icbper_amount += tax_val.get('amount', 0.0)

			line.pe_icbper_amount = pe_icbper_amount

	@api.depends('price_unit', 'tax_ids', 'discount')
	def get_pe_charge_amount(self):
		for line in self:
			pe_charge_amount = 0.0
			if line.tax_ids.filtered(lambda tax: tax.pe_is_charge == True):
				price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
				taxes = line.tax_ids.with_context(round=False).compute_all(price_unit, line.move_id.currency_id, 1, line.product_id, line.move_id.partner_id).get('taxes', [])
				for tax_val in taxes:
					tax = self.env['account.tax'].browse(tax_val.get('id'))
					if tax.pe_is_charge:
						pe_charge_amount += tax_val.get('amount', 0.0)

			line.pe_charge_amount = pe_charge_amount

	@api.model
	def _get_pe_reason_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG7')

	@api.model
	def _get_pe_tier_range(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG8')

	def _set_free_tax(self):
		if self.pe_affectation_code not in ('10', '20', '30', '40'):
			ids = self.tax_ids.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
			self.discount = 100
			if not vat:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito'])], limit=1)
				self.tax_ids = [(6, 0, ids + res.ids)]
		else:
			if self.discount == 100:
				self.discount = 0
			ids = self.tax_ids.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
		if vat:
			res = self.env['account.tax'].search([('id', 'in', ids), ('id', 'not in', vat.ids)]).ids
			self.tax_ids = [(6, 0, res)]

	@api.onchange('discount')
	def onchange_affectation_code_discount(self):
		for rec in self:
			if rec.discount != 100:
				pass
			elif rec.pe_affectation_code not in ['11', '12', '13', '14', '15', '16', '17', '21', '31', '32', '33', '34', '35', '36']:
				rec.pe_affectation_code = '11'

	@api.onchange('pe_affectation_code')
	def onchange_pe_affectation_code(self):
		if not self.move_id.move_type == 'out_invoice':
			return


		# Catalogo 7
		# (10) Gravado - Operación Onerosa; ​(11) Gravado - Retiro por premio; ​(12) Gravado - Retiro por donación; ​ ​ 
		# (13) Gravado - Retiro;​ (14)​ Gravado - Retiro por publicidad; ​ (15) Gravado - Bonificaciones; ​(16)​ Gravado - Retiro por entrega a trabajadores
		if self.pe_affectation_code in ('10'):
			ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv'])], limit=1)
			self.tax_ids = [(6, 0, ids + res.ids)]
			self._set_free_tax()

		elif self.pe_affectation_code in ('11', '12', '13', '14', '15', '16', '17'):
			self.tax_ids = [(6, 0, [])]
			self._set_free_tax()
		
		# (20) Exonerado - Operación Onerosa;
		elif self.pe_affectation_code in ('20'):
			ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado'])], limit=1)
			self.tax_ids = [(6, 0, ids + res.ids)]
			self._set_free_tax()
		# (21) Exonerado – Transferencia gratuita
		elif self.pe_affectation_code in ('21'):
			self.tax_ids = [(6, 0, [])]
			self._set_free_tax()
		# (30) Inafecto - Operación Onerosa; ​ ​ 
		elif self.pe_affectation_code in ('30'):
			ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto'])], limit=1)
			self.tax_ids = [(6, 0, ids + res.ids)]
			#self.discount = 100
		# (31) Inafecto - Retiro por bonificación; ​ ​ (32) Inafecto - Retiro; ​ ​ 
		# (33) Inafecto - Retiro por muestras médicas; ​ ​ (34) Inafecto - Retiro por convenio colectivo; ​ ​ (35) Inafecto - Retiro por premio; ​ ​ 
		# (36) Inafecto - Retiro por publicidad
		elif self.pe_affectation_code in ('31', '32', '33', '34', '35', '36'):
			self.tax_ids = [(6, 0, [])]
			self._set_free_tax()
			#self._set_free_tax()
		# (40) Exportación
		elif self.pe_affectation_code in ('40', ):
			ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion'])], limit=1)
			self.tax_ids = [(6, 0, ids + res.ids)]
			self._set_free_tax()

	def set_pe_affectation_code(self):
		igv = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv'])
		if self.tax_ids:
			if igv:
				if self.discount == 100:
					self.pe_affectation_code = '11'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '10'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado'])
		if self.tax_ids:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '21'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '20'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto'])
		if self.tax_ids:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '31'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '30'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion'])
		if self.tax_ids:
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
			tax_ids = self.tax_ids
		else:
			tax_ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
		res = tax_ids.with_context(round=False).compute_all(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res

	def get_price_unit_sunat(self, all=False):
		self.ensure_one()
		price_unit = self.price_unit
		if all:
			price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			tax_ids = self.tax_ids
		else:
			tax_ids = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
			
		res = tax_ids.with_context(round=False).compute_all_sunat(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res