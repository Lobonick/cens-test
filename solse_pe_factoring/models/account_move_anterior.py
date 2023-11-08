# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api
from contextlib import ExitStack, contextmanager
import logging
import copy
import datetime
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools import frozendict
_logging = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.depends('display_type', 'company_id')
	def _compute_account_id(self):
		term_lines = self.filtered(lambda line: line.display_type == 'payment_term')
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
		cuenta_det_id = int(cuenta_det_id or 0)

		cuenta_det_compra_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
		cuenta_det_compra_id = int(cuenta_det_compra_id or 0)

		cuenta_factoring = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
		cuenta_factoring = int(cuenta_factoring or 0)

		term_lines_filtro = self.filtered(lambda line: line.display_type == 'payment_term' and line.account_id.id not in [cuenta_det_id, cuenta_det_compra_id])
		if term_lines:
			moves = term_lines.move_id
			self.env.cr.execute("""
				WITH previous AS (
					SELECT DISTINCT ON (line.move_id)
						   'account.move' AS model,
						   line.move_id AS id,
						   NULL AS account_type,
						   line.account_id AS account_id
					  FROM account_move_line line
					 WHERE line.move_id = ANY(%(move_ids)s)
					   AND line.display_type = 'payment_term'
					   AND line.id != ANY(%(current_ids)s)
				),
				properties AS(
					SELECT DISTINCT ON (property.company_id, property.name)
						   'res.partner' AS model,
						   SPLIT_PART(property.res_id, ',', 2)::integer AS id,
						   CASE
							   WHEN property.name = 'property_account_receivable_id' THEN 'asset_receivable'
							   ELSE 'liability_payable'
						   END AS account_type,
						   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
					  FROM ir_property property
					  JOIN res_company company ON property.company_id = company.id
					 WHERE property.name IN ('property_account_receivable_id', 'property_account_payable_id')
					   AND property.company_id = ANY(%(company_ids)s)
					   AND property.res_id = ANY(%(partners)s)
				  ORDER BY property.company_id, property.name, account_id
				),
				default_properties AS(
					SELECT DISTINCT ON (property.company_id, property.name)
						   'res.partner' AS model,
						   company.partner_id AS id,
						   CASE
							   WHEN property.name = 'property_account_receivable_id' THEN 'asset_receivable'
							   ELSE 'liability_payable'
						   END AS account_type,
						   SPLIT_PART(property.value_reference, ',', 2)::integer AS account_id
					  FROM ir_property property
					  JOIN res_company company ON property.company_id = company.id
					 WHERE property.name IN ('property_account_receivable_id', 'property_account_payable_id')
					   AND property.company_id = ANY(%(company_ids)s)
					   AND property.res_id IS NULL
				  ORDER BY property.company_id, property.name, account_id
				),
				fallback AS (
					SELECT DISTINCT ON (account.company_id, account.account_type)
						   'res.company' AS model,
						   account.company_id AS id,
						   account.account_type AS account_type,
						   account.id AS account_id
					  FROM account_account account
					 WHERE account.company_id = ANY(%(company_ids)s)
					   AND account.account_type IN ('asset_receivable', 'liability_payable')
					   AND account.deprecated = 'f'
				)
				SELECT * FROM previous
				UNION ALL
				SELECT * FROM properties
				UNION ALL
				SELECT * FROM default_properties
				UNION ALL
				SELECT * FROM fallback
			""", {
				'company_ids': moves.company_id.ids,
				'move_ids': moves.ids,
				'partners': [f'res.partner,{pid}' for pid in moves.commercial_partner_id.ids],
				'current_ids': term_lines_filtro.ids
			})
			accounts = {
				(model, id, account_type): account_id
				for model, id, account_type, account_id in self.env.cr.fetchall()
			}
			for line in term_lines:
				account_type = 'asset_receivable' if line.move_id.is_sale_document(include_receipts=True) else 'liability_payable'
				move = line.move_id
				account_id = (
					accounts.get(('account.move', move.id, None))
					or accounts.get(('res.partner', move.commercial_partner_id.id, account_type))
					or accounts.get(('res.partner', move.company_id.partner_id.id, account_type))
					or accounts.get(('res.company', move.company_id.id, account_type))
				)
				if account_id in [cuenta_det_compra_id, cuenta_det_id, cuenta_factoring]:
					account_id = (
						accounts.get(('res.partner', move.commercial_partner_id.id, account_type))
						or accounts.get(('res.partner', move.company_id.partner_id.id, account_type))
						or accounts.get(('res.company', move.company_id.id, account_type))
					)
				if line.move_id.fiscal_position_id:
					account_id = self.move_id.fiscal_position_id.map_account(self.env['account.account'].browse(account_id))
				line.account_id = account_id

		product_lines = self.filtered(lambda line: line.display_type == 'product' and line.move_id.is_invoice(True))
		for line in product_lines:
			if line.product_id:
				fiscal_position = line.move_id.fiscal_position_id
				accounts = line.with_company(line.company_id).product_id\
					.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)

				if line.move_id.is_sale_document(include_receipts=True):
					line.account_id = accounts['income'] or line.account_id
				elif line.move_id.is_purchase_document(include_receipts=True):
					line.account_id = accounts['expense'] or line.account_id
			elif line.partner_id:
				line.account_id = self.env['account.account']._get_most_frequent_account_for_partner(
					company_id=line.company_id.id,
					partner_id=line.partner_id.id,
					move_type=line.move_id.move_type,
				)
		for line in self:
			if not line.account_id and line.display_type not in ('line_section', 'line_note'):
				previous_two_accounts = line.move_id.line_ids.filtered(
					lambda l: l.account_id and l.display_type == line.display_type
				)[-2:].account_id
				if len(previous_two_accounts) == 1 and len(line.move_id.line_ids) > 2:
					line.account_id = previous_two_accounts
				else:
					line.account_id = line.move_id.journal_id.default_account_id


class AccountMove(models.Model):
	_inherit = 'account.move'

	con_factoring = fields.Boolean("Pagado con Factoring")

	@api.depends('invoice_payment_term_id', 'journal_id', 'invoice_date', 'currency_id', 'amount_total_in_currency_signed', 'invoice_date_due', 'con_factoring')
	def _compute_needed_terms(self):
		for invoice in self:
			is_draft = invoice.id != invoice._origin.id
			invoice.needed_terms = {}
			invoice.needed_terms_dirty = True
			account_id = False
			sign = 1 if invoice.is_inbound(include_receipts=True) else -1
			if invoice.is_invoice(True) and invoice.invoice_line_ids:
				if invoice.invoice_payment_term_id:
					if is_draft:
						tax_amount_currency = 0.0
						untaxed_amount_currency = 0.0
						for line in invoice.invoice_line_ids:
							untaxed_amount_currency += line.price_subtotal
							for tax_result in (line.compute_all_tax or {}).values():
								tax_amount_currency += -sign * tax_result.get('amount_currency', 0.0)
						untaxed_amount = untaxed_amount_currency
						tax_amount = tax_amount_currency
					else:
						# Impuesto en moneda extranjera
						tax_amount_currency = invoice.amount_tax * sign
						# Impuesto en soles
						tax_amount = invoice.amount_tax_signed
						# base en dolares
						untaxed_amount_currency = invoice.amount_untaxed * sign
						# base imponible en soles
						untaxed_amount = invoice.amount_untaxed_signed

					if invoice.tiene_detraccion:
						untaxed_amount_currency = untaxed_amount_currency - invoice.monto_detraccion
						untaxed_amount = untaxed_amount_currency - invoice.monto_detraccion_base

					invoice_payment_terms = invoice.invoice_payment_term_id._compute_terms(
						date_ref=invoice.invoice_date or invoice.date or fields.Date.today(),
						currency=invoice.currency_id,
						tax_amount_currency=tax_amount_currency,
						tax_amount=tax_amount,
						untaxed_amount_currency=untaxed_amount_currency,
						untaxed_amount=untaxed_amount,
						company=invoice.company_id,
						sign=sign
					)
					fecha_ini = False
					discount_date = False
					discount_percentage = False
					for term in invoice_payment_terms:
						if fecha_ini == False:
							fecha_ini = fields.Date.to_date(term.get('date'))
							discount_date = term.get('discount_date')
							discount_percentage = term.get('discount_percentage')
						key = frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(term.get('date')),
							'discount_date': term.get('discount_date'),
							'discount_percentage': term.get('discount_percentage'),
						})
						values = {
							'balance': term['company_amount'],
							'amount_currency': term['foreign_amount'],
							'discount_amount_currency': term['discount_amount_currency'] or 0.0,
							'discount_balance': term['discount_balance'] or 0.0,
							'discount_date': term['discount_date'],
							'discount_percentage': term['discount_percentage'],
						}
						if key not in invoice.needed_terms:
							invoice.needed_terms[key] = values
						else:
							invoice.needed_terms[key]['balance'] += values['balance']
							invoice.needed_terms[key]['amount_currency'] += values['amount_currency']

					if fecha_ini and invoice.tiene_detraccion:
						cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
						cuenta_det_id = int(cuenta_det_id)

						cuenta_det_compra_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
						cuenta_det_compra_id = int(cuenta_det_compra_id or 0)

						if invoice.move_type == 'out_invoice' and not cuenta_det_id:
							raise UserError("No se ha configurado una cuenta de detracción para ventas")

						if invoice.move_type == 'in_invoice' and not cuenta_det_compra_id:
							raise UserError("No se ha configurado una cuenta de detracción para compras")

						if invoice.move_type == 'in_invoice':
							cuenta_det_id = cuenta_det_compra_id

						fecha_ini = invoice.invoice_date or invoice.date or fields.Date.today()
						key_detraccion = frozendict({
							'move_id': invoice.id,
							'date_maturity': fecha_ini,
							'account_id': cuenta_det_id,
							'discount_date': False,
							'discount_percentage': 0
						})
						values = {
							'balance': invoice.monto_detraccion_base,
							'amount_currency': invoice.monto_detraccion,
						}
						if key_detraccion not in invoice.needed_terms:
							invoice.needed_terms[key_detraccion] = values
						else:
							invoice.needed_terms[key_detraccion]['balance'] = invoice.monto_detraccion_base
							invoice.needed_terms[key_detraccion]['amount_currency'] = invoice.monto_detraccion

				else:
					untaxed_amount_currency = invoice.amount_total_in_currency_signed
					untaxed_amount = invoice.amount_total_signed
					if invoice.tiene_detraccion:
						untaxed_amount_currency = untaxed_amount_currency - invoice.monto_detraccion
						untaxed_amount = untaxed_amount_currency - invoice.monto_detraccion_base

						cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
						cuenta_det_id = int(cuenta_det_id)

						cuenta_det_compra_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
						cuenta_det_compra_id = int(cuenta_det_compra_id or 0)

						if invoice.move_type == 'out_invoice' and not cuenta_det_id:
							raise UserError("No se ha configurado una cuenta de detracción para ventas")

						if invoice.move_type == 'in_invoice' and not cuenta_det_compra_id:
							raise UserError("No se ha configurado una cuenta de detracción para compras")

						if invoice.move_type == 'in_invoice':
							cuenta_det_id = cuenta_det_compra_id

						fecha_ini = invoice.invoice_date or invoice.date or fields.Date.today()
						key_detraccion = frozendict({
							'move_id': invoice.id,
							'date_maturity': fecha_ini,
							'account_id': cuenta_det_id,
							'discount_date': False,
							'discount_percentage': 0
						})
						values = {
							'balance': invoice.monto_detraccion_base,
							'amount_currency': invoice.monto_detraccion,
						}
						invoice.needed_terms[key_detraccion] = values


						invoice.needed_terms[frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
							'discount_date': False,
							'discount_percentage': 0
						})] = {
							'balance': untaxed_amount,
							'amount_currency': untaxed_amount_currency,
						}
					elif invoice.con_factoring:
						cuenta_factoring = self.env['ir.config_parameter'].sudo().get_param('solse_pe_factoring.default_cuenta_factoring')
						cuenta_factoring = int(cuenta_factoring or 0)
						invoice.needed_terms[frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
							'discount_date': False,
							'discount_percentage': 0,
							'account_id': cuenta_factoring
						})] = {
							'balance': invoice.amount_total_signed,
							'amount_currency': invoice.amount_total_in_currency_signed,
						}
					else:
						invoice.needed_terms[frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
							'discount_date': False,
							'discount_percentage': 0
						})] = {
							'balance': invoice.amount_total_signed,
							'amount_currency': invoice.amount_total_in_currency_signed,
						}

