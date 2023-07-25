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

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	transaction_number = fields.Char(string='Número de operación')
	glosa = fields.Char('Glosa', compute="_compute_glosa", store=True)

	@api.depends('reconciled_invoice_ids')
	def _compute_glosa(self):
		for reg in self:
			if not reg.reconciled_invoice_ids and not reg.reconciled_bill_ids:
				reg.glosa = ''
				continue

			factura = False
			if reg.reconciled_invoice_ids:
				factura = reg.reconciled_invoice_ids[0]
			elif reg.reconciled_bill_ids:
				factura = reg.reconciled_bill_ids[0]
				
			if not factura:
				reg.glosa = ''
				continue

			reg.glosa = factura.glosa
			reg.move_id.write({'glosa': factura.glosa})

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	transaction_number = fields.Char(related='payment_id.transaction_number', store=True)
	glosa = fields.Char("Glosa", related="move_id.glosa", store=True)

	@api.depends('display_type', 'company_id')
	def _compute_account_id(self):
		term_lines = self.filtered(lambda line: line.display_type == 'payment_term')
		cuenta_det_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones')
		cuenta_det_id = int(cuenta_det_id or 0)

		cuenta_det_compra_id = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant.default_cuenta_detracciones_compra')
		cuenta_det_compra_id = int(cuenta_det_compra_id or 0)

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
				if account_id in [cuenta_det_compra_id, cuenta_det_id]:
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

class StatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	transaction_number = fields.Char(string='Número de transacción')


class AccountMove(models.Model):
	_inherit = 'account.move'

	transaction_number = fields.Char(related='payment_id.transaction_number', store=True)
	asiento_det_ret = fields.Many2one('account.move', string='Asiento retención/detracción')
	pago_detraccion = fields.Many2one('account.payment', 'Pago de Detracción/Retención', copy=False)

	es_x_apertura = fields.Boolean("Movimiento por Apertura")
	fecha_apertura = fields.Date("Fecha Apertura", default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]},)
	glosa = fields.Char('Glosa')
	tipo_cambio_dolar_sistema = fields.Float("Tipo Cambio ($)", compute="_compute_tipo_cambio_sistema", store=False, digits=(16, 3))

	def obtener_cuotas_pago(self):
		invoice = self
		invoice_date_due_vals_list = []
		first_time = True
		for rec_line in invoice.line_ids.filtered(lambda l: l.account_id.account_type in ['asset_receivable', 'liability_payable'] ):
			amount = rec_line.amount_currency
			"""if first_time and (invoice.monto_detraccion or invoice.monto_retencion):
				if invoice.currency_id.id == invoice.company_id.currency_id.id:
					amount -= (invoice.monto_detraccion + invoice.monto_retencion)
				else:
					amount -= (invoice.monto_detraccion_base + invoice.monto_retencion_base)"""
			first_time = False
			datos_json = {
				'amount': rec_line.move_id.currency_id.round(amount),
				'currency_name': rec_line.move_id.currency_id.name,
				'date_maturity': rec_line.date_maturity
			}
			invoice_date_due_vals_list.append(datos_json)

		if invoice.monto_detraccion or invoice.monto_retencion:
			invoice_date_due_vals_list.pop()

		return invoice_date_due_vals_list

	@api.onchange('es_x_apertura', 'fecha_apertura')
	def _onchange_fecha_apertura(self):
		if self.es_x_apertura and self.fecha_apertura:
			self.date = self.fecha_apertura or fields.Date.context_today(self)
		else:
			self.date = self.invoice_date or fields.Date.context_today(self)

	def _post(self, soft=True):
		res = super(AccountMove, self)._post(soft=soft)

		return res

	@api.depends('invoice_date', 'currency_id')
	def _compute_tipo_cambio_sistema(self):
		for reg in self:
			if reg.currency_id and reg.currency_id.name == 'USD':
				moneda_dolar = reg.currency_id
			else:
				tipo = 'venta'
				if reg.move_type in ['out_invoice', 'out_refund']:
					tipo = 'venta'
				if reg.move_type in ['in_invoice', 'in_refund']:
					tipo = 'compra'
				moneda_dolar = self.env["res.currency"].search([("name", "=", "USD"), ("rate_type", "=", tipo)], limit=1)

			if not moneda_dolar:
				moneda_dolar = self.env["res.currency"].search([("name", "=", "USD")], limit=1)

			tipo_cambio = 1.0
			if reg.invoice_date:
				tipo_cambio = moneda_dolar._convert(1, reg.company_id.currency_id, reg.company_id, reg.invoice_date, round=False)
			reg.tipo_cambio_dolar_sistema = tipo_cambio

	def obtener_totales_linea_detraccion(self, total_balance, total_amount_currency, total):
		if total_balance > 0:
			monto_detraccion = total - self.monto_neto_pagar
			#monto_detraccion = self.monto_detraccion
			total_balance_neto = total_balance - monto_detraccion
			#total_balance_detra = self.monto_detraccion
			total_balance_detra = monto_detraccion

			total_amount_currency_neto = total_amount_currency - self.monto_detraccion_base
			total_amount_currency_detra = self.monto_detraccion_base
		else:
			monto_detraccion = total - self.monto_neto_pagar
			#monto_detraccion = self.monto_neto_pagar
			total_balance_neto = total_balance + monto_detraccion
			#total_balance_detra = self.monto_detraccion * -1
			total_balance_detra = monto_detraccion * -1

			total_amount_currency_neto = total_amount_currency + self.monto_detraccion_base
			total_amount_currency_detra = self.monto_detraccion_base * -1

		respuesta = {
			'total_balance_neto': total_balance_neto,
			'total_balance_detra': total_balance_detra,
			'total_amount_currency_neto': total_amount_currency_neto,
			'total_amount_currency_detra': total_amount_currency_detra,
		}
		return respuesta

	@api.depends('invoice_payment_term_id', 'journal_id', 'invoice_date', 'currency_id', 'amount_total_in_currency_signed', 'amount_total_signed', 'invoice_date_due', 'monto_detraccion')
	def _compute_needed_terms(self):
		_logging.info("============================ _compute_needed_terms")
		for invoice in self:
			is_draft = invoice.id != invoice._origin.id
			invoice.needed_terms = {}
			invoice.needed_terms_dirty = True
			account_id = False
			sign = 1 if invoice.is_inbound(include_receipts=True) else -1
			if invoice.is_invoice(True) and invoice.invoice_line_ids:
				_logging.info("paso el primer if")
				if invoice.invoice_payment_term_id:
					_logging.info("tiene plazo de pago")
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
						"""else:
							invoice.needed_terms[key]['balance'] += values['balance']
							invoice.needed_terms[key]['amount_currency'] += values['amount_currency']"""

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
					_logging.info("es directoooooooooooooo")
					_logging.info(invoice.monto_detraccion)
					_logging.info(invoice.monto_detraccion_base)
					untaxed_amount_currency = invoice.amount_total_in_currency_signed
					untaxed_amount = invoice.amount_total_signed
					_logging.info(untaxed_amount_currency)
					_logging.info(untaxed_amount)
					if invoice.tiene_detraccion:
						untaxed_amount_currency = untaxed_amount_currency - invoice.monto_detraccion_base
						untaxed_amount = untaxed_amount - invoice.monto_detraccion

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
							'balance': invoice.monto_detraccion,
							'amount_currency': invoice.monto_detraccion_base,
						}
						_logging.info("primera parte")
						_logging.info(values)
						invoice.needed_terms[key_detraccion] = values

						values_n2 = {
							'balance': untaxed_amount,
							'amount_currency': untaxed_amount_currency,
						}
						_logging.info("parte 2")
						_logging.info(values_n2)
						invoice.needed_terms[frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
							'discount_date': False,
							'discount_percentage': 0
						})] = values_n2

					else:
						_logging.info("pasa por el segudooooooooooooooooooo")
						_logging.info(invoice.amount_total_signed)
						invoice.needed_terms[frozendict({
							'move_id': invoice.id,
							'date_maturity': fields.Date.to_date(invoice.invoice_date_due),
							'discount_date': False,
							'discount_percentage': 0
						})] = {
							'balance': invoice.amount_total_signed,
							'amount_currency': invoice.amount_total_in_currency_signed,
						}


