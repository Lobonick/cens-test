# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)

class AccountPaymentTerm(models.Model):
	_inherit = "account.payment.term"

	def obtener_datos_linea(self, line, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency):
		term_vals = {
			'date': line._get_due_date(date_ref),
			'has_discount': line.discount_percentage,
			'discount_date': None,
			'discount_amount_currency': 0.0,
			'discount_balance': 0.0,
			'discount_percentage': line.discount_percentage,
		}

		if line.value == 'fixed':
			term_vals['company_amount'] = sign * company_currency.round(line.value_amount)
			term_vals['foreign_amount'] = sign * currency.round(line.value_amount)
			company_proportion = tax_amount/untaxed_amount if untaxed_amount else 1
			foreign_proportion = tax_amount_currency/untaxed_amount_currency if untaxed_amount_currency else 1
			line_tax_amount = company_currency.round(line.value_amount * company_proportion) * sign
			line_tax_amount_currency = currency.round(line.value_amount * foreign_proportion) * sign
			line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
			line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
		elif line.value == 'percent':
			term_vals['company_amount'] = company_currency.round(total_amount * (line.value_amount / 100.0))
			term_vals['foreign_amount'] = currency.round(total_amount_currency * (line.value_amount / 100.0))
			line_tax_amount = company_currency.round(tax_amount * (line.value_amount / 100.0))
			line_tax_amount_currency = currency.round(tax_amount_currency * (line.value_amount / 100.0))
			line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
			line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
		else:
			line_tax_amount = line_tax_amount_currency = line_untaxed_amount = line_untaxed_amount_currency = 0.0

		tax_amount_left -= line_tax_amount
		tax_amount_currency_left -= line_tax_amount_currency
		untaxed_amount_left -= line_untaxed_amount
		untaxed_amount_currency_left -= line_untaxed_amount_currency

		if line.value == 'balance':
			term_vals['company_amount'] = tax_amount_left + untaxed_amount_left
			term_vals['foreign_amount'] = tax_amount_currency_left + untaxed_amount_currency_left
			line_tax_amount = tax_amount_left
			line_tax_amount_currency = tax_amount_currency_left
			line_untaxed_amount = untaxed_amount_left
			line_untaxed_amount_currency = untaxed_amount_currency_left

		if line.discount_percentage:
			if company.early_pay_discount_computation in ('excluded', 'mixed'):
				term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] - line_untaxed_amount * line.discount_percentage / 100.0)
				term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] - line_untaxed_amount_currency * line.discount_percentage / 100.0)
			else:
				term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] * (1 - (line.discount_percentage / 100.0)))
				term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] * (1 - (line.discount_percentage / 100.0)))
			term_vals['discount_date'] = date_ref + relativedelta(days=line.discount_days)

		return term_vals

	def obtener_linea_detraccion(self, line, date_ref, currency, company, sign):
		term_vals = {
			'date': line._get_due_date(date_ref),
			'has_discount': line.discount_percentage,
			'discount_date': None,
			'discount_amount_currency': 0.0,
			'discount_balance': 0.0,
			'discount_percentage': line.discount_percentage,
		}

		company_proportion = tax_amount/untaxed_amount if untaxed_amount else 1
		foreign_proportion = tax_amount_currency/untaxed_amount_currency if untaxed_amount_currency else 1
		line_tax_amount = company_currency.round(line.value_amount * company_proportion) * sign
		line_tax_amount_currency = currency.round(line.value_amount * foreign_proportion) * sign
		line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
		line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency

		tax_amount_left -= line_tax_amount
		tax_amount_currency_left -= line_tax_amount_currency
		untaxed_amount_left -= line_untaxed_amount
		untaxed_amount_currency_left -= line_untaxed_amount_currency

		term_vals['company_amount'] = sign * company_currency.round(line.value_amount)
		term_vals['foreign_amount'] = sign * currency.round(line.value_amount)

		return term_vals

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

	def _compute_terms_pe(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, invoice):
		self.ensure_one()
		company_currency = company.currency_id
		tax_amount_left = tax_amount
		tax_amount_currency_left = tax_amount_currency
		untaxed_amount_left = untaxed_amount
		untaxed_amount_currency_left = untaxed_amount_currency
		total_amount = tax_amount + untaxed_amount
		total_amount_currency = tax_amount_currency + untaxed_amount_currency
		result = []
		contador = 1
		"""
		solo para la primera linea descontar el monto de la detraccion, tanto en soles como en dolares
		con monto descontado agregar una nueva linea para la detraccion
		"""
		for line in self.line_ids.sorted(lambda line: line.value == 'balance'):
			if contador == 1 and invoice.tiene_detraccion:
				datos = self.obtener_totales_linea_detraccion(total_balance, total_amount_currency, total)

			contador = contador + 1
			term_vals = self.obtener_datos_linea(line, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency)

			result.append(term_vals)
		return result