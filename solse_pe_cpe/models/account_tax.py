# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from odoo.tools import (
	date_utils,
	email_re,
	email_split,
	float_compare,
	float_is_zero,
	format_amount,
	format_date,
	formatLang,
	frozendict,
	get_lang,
	is_html_empty,
	sql
)

import math
import logging
_logging = logging.getLogger(__name__)

TYPE_TAX_USE = [
	('sale', 'Sales'),
	('purchase', 'Purchases'),
	('none', 'None'),
]	

def round_up(n, decimals=0):
	return float(("%."+str(decimals)+"f") % n)
	#multiplier = 10 ** decimals
	#return math.ceil(n * multiplier) / multiplier


class AccountTaxGroup(models.Model):
	_inherit = 'account.tax.group'

	mostrar_base = fields.Boolean('Mostrar base')
	
class AccountTax(models.Model):
	_inherit = 'account.tax'

	incluir_monto_completo = fields.Boolean("Incluir monto completo")

	@api.model
	def _prepare_tax_totals_pe(self, base_lines, currency, tax_lines=None):
		to_process = []
		total_impuestos_completos = 0
		for base_line in base_lines:
			to_update_vals, tax_values_list = self._compute_taxes_for_single_line(base_line)
			to_process.append((base_line, to_update_vals, tax_values_list))

		def grouping_key_generator(base_line, tax_values):
			source_tax = tax_values['tax_repartition_line'].tax_id
			return {'tax_group': source_tax.tax_group_id}

		global_tax_details = self._aggregate_taxes(to_process, grouping_key_generator=grouping_key_generator)

		tax_group_vals_list = []
		for tax_detail in global_tax_details['tax_details'].values():
			tax_group_vals = {
				'tax_group': tax_detail['tax_group'],
				'base_amount': tax_detail['base_amount_currency'],
				'tax_amount': tax_detail['tax_amount_currency'],
			}

			# Handle a manual edition of tax lines.
			if tax_lines is not None:
				matched_tax_lines = [
					x
					for x in tax_lines
					if (x['group_tax'] or x['tax_repartition_line'].tax_id).tax_group_id == tax_detail['tax_group']
				]
				if matched_tax_lines:
					tax_group_vals['tax_amount'] = sum(x['tax_amount'] for x in matched_tax_lines)

			tax_group_vals_list.append(tax_group_vals)

		tax_group_vals_list = sorted(tax_group_vals_list, key=lambda x: (x['tax_group'].sequence, x['tax_group'].id))

		# ==== Partition the tax group values by subtotals ====

		amount_untaxed = global_tax_details['base_amount_currency']
		amount_tax = 0.0

		subtotal_order = {}
		groups_by_subtotal = defaultdict(list)
		for tax_group_vals in tax_group_vals_list:
			tax_group = tax_group_vals['tax_group']

			subtotal_title = tax_group.preceding_subtotal or "Op. Gravadas"
			sequence = tax_group.sequence

			monto_asignar = tax_group_vals['tax_amount']
			monto_base = tax_group_vals['base_amount']
			if not monto_asignar:
				monto_asignar = tax_group_vals['base_amount']
				total_impuestos_completos = total_impuestos_completos + monto_asignar
				monto_base = 0

			subtotal_order[subtotal_title] = min(subtotal_order.get(subtotal_title, float('inf')), sequence)
			groups_by_subtotal[subtotal_title].append({
				'group_key': tax_group.id,
				'tax_group_id': tax_group.id,
				'tax_group_name': tax_group.name,
				'tax_group_amount': monto_asignar,
				'tax_group_base_amount': monto_base,
				'formatted_tax_group_amount': formatLang(self.env, monto_asignar, currency_obj=currency),
				'formatted_tax_group_base_amount': formatLang(self.env, monto_base, currency_obj=currency),
			})

		amount_untaxed = amount_untaxed - total_impuestos_completos

		# ==== Build the final result ====

		subtotals = []
		for subtotal_title in sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]):
			amount_total = (amount_untaxed + amount_tax)
			subtotals.append({
				'name': subtotal_title,
				'amount': amount_total,
				'formatted_amount': formatLang(self.env, amount_total, currency_obj=currency),
			})
			amount_tax += sum(x['tax_group_amount'] for x in groups_by_subtotal[subtotal_title])

		amount_total = (amount_untaxed + amount_tax)

		display_tax_base = (len(global_tax_details['tax_details']) == 1 and currency.compare_amounts(tax_group_vals_list[0]['base_amount'], amount_untaxed) != 0)\
						   or len(global_tax_details['tax_details']) > 1

		return {
			'amount_untaxed': currency.round(amount_untaxed) if currency else amount_untaxed,
			'amount_total': currency.round(amount_total) if currency else amount_total,
			'formatted_amount_total': formatLang(self.env, amount_total, currency_obj=currency),
			'formatted_amount_untaxed': formatLang(self.env, amount_untaxed, currency_obj=currency),
			'groups_by_subtotal': groups_by_subtotal,
			'subtotals': subtotals,
			'subtotals_order': sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]),
			'display_tax_base': display_tax_base
		}


	def compute_all_sunat(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, include_caba_tags=False):
		""" Returns all information required to apply taxes (in self + their children in case of a tax group).
			We consider the sequence of the parent for group of taxes.
				Eg. considering letters as taxes and alphabetic order as sequence :
				[G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

			'handle_price_include' is used when we need to ignore all tax included in price. If False, it means the
			amount passed to this method will be considered as the base of all computations.

		RETURN: {
			'total_excluded': 0.0,    # Total without taxes
			'total_included': 0.0,    # Total with taxes
			'total_void'    : 0.0,    # Total with those taxes, that don't have an account set
			'taxes': [{               # One dict for each tax in self and their children
				'id': int,
				'name': str,
				'amount': float,
				'sequence': int,
				'account_id': int,
				'refund_account_id': int,
				'analytic': boolean,
			}],
		} """
		if not self:
			company = self.env.company
		else:
			company = self[0].company_id

		# 1) Flatten the taxes.
		taxes, groups_map = self.flatten_taxes_hierarchy(create_map=True)

		# 2) Deal with the rounding methods
		if not currency:
			currency = company.currency_id

		# By default, for each tax, tax amount will first be computed
		# and rounded at the 'Account' decimal precision for each
		# PO/SO/invoice line and then these rounded amounts will be
		# summed, leading to the total amount for that tax. But, if the
		# company has tax_calculation_rounding_method = round_globally,
		# we still follow the same method, but we use a much larger
		# precision when we round the tax amount for each line (we use
		# the 'Account' decimal precision + 5), and that way it's like
		# rounding after the sum of the tax amounts of each line
		prec = currency.rounding

		# In some cases, it is necessary to force/prevent the rounding of the tax and the total
		# amounts. For example, in SO/PO line, we don't want to round the price unit at the
		# precision of the currency.
		# The context key 'round' allows to force the standard behavior.
		round_tax = False if company.tax_calculation_rounding_method == 'round_globally' else True
		if 'round' in self.env.context:
			round_tax = bool(self.env.context['round'])

		if not round_tax:
			prec *= 1e-5

		# 3) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
		#     tax  |  base  |  amount  |
		# /\ ----------------------------
		# || tax_1 |  XXXX  |          | <- we are looking for that, it's the total_excluded
		# || tax_2 |   ..   |          |
		# || tax_3 |   ..   |          |
		# ||  ...  |   ..   |    ..    |
		#    ----------------------------
		def recompute_base(base_amount, fixed_amount, percent_amount, division_amount):
			# Recompute the new base amount based on included fixed/percent amounts and the current base amount.
			# Example:
			#  tax  |  amount  |   type   |  price_include  |
			# -----------------------------------------------
			# tax_1 |   10%    | percent  |  t
			# tax_2 |   15     |   fix    |  t
			# tax_3 |   20%    | percent  |  t
			# tax_4 |   10%    | division |  t
			# -----------------------------------------------

			# if base_amount = 145, the new base is computed as:
			# (145 - 15) / (1.0 + 30%) * 90% = 130 / 1.3 * 90% = 90
			return (base_amount - fixed_amount) / (1.0 + percent_amount / 100.0) * (100 - division_amount) / 100

		# The first/last base must absolutely be rounded to work in round globally.
		# Indeed, the sum of all taxes ('taxes' key in the result dictionary) must be strictly equals to
		# 'price_included' - 'price_excluded' whatever the rounding method.
		#
		# Example using the global rounding without any decimals:
		# Suppose two invoice lines: 27000 and 10920, both having a 19% price included tax.
		#
		#                   Line 1                      Line 2
		# -----------------------------------------------------------------------
		# total_included:   27000                       10920
		# tax:              27000 / 1.19 = 4310.924     10920 / 1.19 = 1743.529
		# total_excluded:   22689.076                   9176.471
		#
		# If the rounding of the total_excluded isn't made at the end, it could lead to some rounding issues
		# when summing the tax amounts, e.g. on invoices.
		# In that case:
		#  - amount_untaxed will be 22689 + 9176 = 31865
		#  - amount_tax will be 4310.924 + 1743.529 = 6054.453 ~ 6054
		#  - amount_total will be 31865 + 6054 = 37919 != 37920 = 27000 + 10920
		#
		# By performing a rounding at the end to compute the price_excluded amount, the amount_tax will be strictly
		# equals to 'price_included' - 'price_excluded' after rounding and then:
		#   Line 1: sum(taxes) = 27000 - 22689 = 4311
		#   Line 2: sum(taxes) = 10920 - 2176 = 8744
		#   amount_tax = 4311 + 8744 = 13055
		#   amount_total = 31865 + 13055 = 37920
		decimal_precision_obj = self.env['decimal.precision']
		digits = decimal_precision_obj.precision_get('Product Price') or 2
		base = round_up(price_unit * quantity, digits)

		# For the computation of move lines, we could have a negative base value.
		# In this case, compute all with positive values and negate them at the end.
		sign = 1
		if currency.is_zero(base):
			sign = self._context.get('force_sign', 1)
		elif base < 0:
			sign = -1
		if base < 0:
			base = -base

		# Store the totals to reach when using price_include taxes (only the last price included in row)
		total_included_checkpoints = {}
		i = len(taxes) - 1
		store_included_tax_total = True
		# Keep track of the accumulated included fixed/percent amount.
		incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
		# Store the tax amounts we compute while searching for the total_excluded
		cached_tax_amounts = {}
		if handle_price_include:
			for tax in reversed(taxes):
				tax_repartition_lines = (
					is_refund
					and tax.refund_repartition_line_ids
					or tax.invoice_repartition_line_ids
				).filtered(lambda x: x.repartition_type == "tax")
				sum_repartition_factor = sum(tax_repartition_lines.mapped("factor"))

				if tax.include_base_amount:
					base = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
					incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
					store_included_tax_total = True
				if tax.price_include or self._context.get('force_price_include'):
					if tax.amount_type == 'percent':
						incl_percent_amount += tax.amount * sum_repartition_factor
					elif tax.amount_type == 'division':
						incl_division_amount += tax.amount * sum_repartition_factor
					elif tax.amount_type == 'fixed':
						incl_fixed_amount += abs(quantity) * tax.amount * sum_repartition_factor
					else:
						# tax.amount_type == other (python)
						tax_amount = tax._compute_amount(base, sign * price_unit, quantity, product, partner) * sum_repartition_factor
						incl_fixed_amount += tax_amount
						# Avoid unecessary re-computation
						cached_tax_amounts[i] = tax_amount
					# In case of a zero tax, do not store the base amount since the tax amount will
					# be zero anyway. Group and Python taxes have an amount of zero, so do not take
					# them into account.
					if store_included_tax_total and (
						tax.amount or tax.amount_type not in ("percent", "division", "fixed")
					):
						total_included_checkpoints[i] = base
						store_included_tax_total = False
				i -= 1

		#total_excluded = currency.round(recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount))
		base_temporal = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
		total_excluded = tools.float_round(base_temporal, 6)

		# 4) Iterate the taxes in the sequence order to compute missing tax amounts.
		# Start the computation of accumulated amounts at the total_excluded value.
		base = total_included = total_void = total_excluded

		# Flag indicating the checkpoint used in price_include to avoid rounding issue must be skipped since the base
		# amount has changed because we are currently mixing price-included and price-excluded include_base_amount
		# taxes.
		skip_checkpoint = False

		# Get product tags, account.account.tag objects that need to be injected in all
		# the tax_tag_ids of all the move lines created by the compute all for this product.
		product_tag_ids = product.account_tag_ids.ids if product else []

		taxes_vals = []
		i = 0
		cumulated_tax_included_amount = 0
		for tax in taxes:
			price_include = self._context.get('force_price_include', tax.price_include)

			if price_include or tax.is_base_affected:
				tax_base_amount = base
			else:
				tax_base_amount = total_excluded

			tax_repartition_lines = (is_refund and tax.refund_repartition_line_ids or tax.invoice_repartition_line_ids).filtered(lambda x: x.repartition_type == 'tax')
			sum_repartition_factor = sum(tax_repartition_lines.mapped('factor'))

			#compute the tax_amount
			if not skip_checkpoint and price_include and total_included_checkpoints.get(i) and sum_repartition_factor != 0:
				# We know the total to reach for that tax, so we make a substraction to avoid any rounding issues
				tax_amount = total_included_checkpoints[i] - (base + cumulated_tax_included_amount)
				cumulated_tax_included_amount = 0
			else:
				tax_amount = tax.with_context(force_price_include=False)._compute_amount(
					tax_base_amount, sign * price_unit, quantity, product, partner)

			# Round the tax_amount multiplied by the computed repartition lines factor.
			tax_amount = round(tax_amount, precision_rounding=prec)
			factorized_tax_amount = round(tax_amount * sum_repartition_factor, precision_rounding=prec)

			if price_include and not total_included_checkpoints.get(i):
				cumulated_tax_included_amount += factorized_tax_amount

			# If the tax affects the base of subsequent taxes, its tax move lines must
			# receive the base tags and tag_ids of these taxes, so that the tax report computes
			# the right total
			subsequent_taxes = self.env['account.tax']
			subsequent_tags = self.env['account.account.tag']
			if tax.include_base_amount:
				subsequent_taxes = taxes[i+1:].filtered('is_base_affected')

				taxes_for_subsequent_tags = subsequent_taxes

				if not include_caba_tags:
					taxes_for_subsequent_tags = subsequent_taxes.filtered(lambda x: x.tax_exigibility != 'on_payment')

				subsequent_tags = taxes_for_subsequent_tags.get_tax_tags(is_refund, 'base')

			# Compute the tax line amounts by multiplying each factor with the tax amount.
			# Then, spread the tax rounding to ensure the consistency of each line independently with the factorized
			# amount. E.g:
			#
			# Suppose a tax having 4 x 50% repartition line applied on a tax amount of 0.03 with 2 decimal places.
			# The factorized_tax_amount will be 0.06 (200% x 0.03). However, each line taken independently will compute
			# 50% * 0.03 = 0.01 with rounding. It means there is 0.06 - 0.04 = 0.02 as total_rounding_error to dispatch
			# in lines as 2 x 0.01.
			repartition_line_amounts = [round(tax_amount * line.factor, precision_rounding=prec) for line in tax_repartition_lines]
			total_rounding_error = round(factorized_tax_amount - sum(repartition_line_amounts), precision_rounding=prec)
			nber_rounding_steps = int(abs(total_rounding_error / currency.rounding))
			rounding_error = round(nber_rounding_steps and total_rounding_error / nber_rounding_steps or 0.0, precision_rounding=prec)

			for repartition_line, line_amount in zip(tax_repartition_lines, repartition_line_amounts):

				if nber_rounding_steps:
					line_amount += rounding_error
					nber_rounding_steps -= 1

				if not include_caba_tags and tax.tax_exigibility == 'on_payment':
					repartition_line_tags = self.env['account.account.tag']
				else:
					repartition_line_tags = repartition_line.tag_ids

				taxes_vals.append({
					'id': tax.id,
					'name': partner and tax.with_context(lang=partner.lang).name or tax.name,
					'amount': sign * line_amount,
					'base': round(sign * tax_base_amount, precision_rounding=prec),
					'sequence': tax.sequence,
					'account_id': tax.cash_basis_transition_account_id.id if tax.tax_exigibility == 'on_payment' else repartition_line.account_id.id,
					'analytic': tax.analytic,
					'price_include': price_include,
					'tax_exigibility': tax.tax_exigibility,
					'tax_repartition_line_id': repartition_line.id,
					'group': groups_map.get(tax),
					'tag_ids': (repartition_line_tags + subsequent_tags).ids + product_tag_ids,
					'tax_ids': subsequent_taxes.ids,
				})

				if not repartition_line.account_id:
					total_void += line_amount

			# Affect subsequent taxes
			if tax.include_base_amount:
				base += factorized_tax_amount
				if not price_include:
					skip_checkpoint = True

			total_included += factorized_tax_amount
			i += 1

		base_taxes_for_tags = taxes
		if not include_caba_tags:
			base_taxes_for_tags = base_taxes_for_tags.filtered(lambda x: x.tax_exigibility != 'on_payment')

		base_rep_lines = base_taxes_for_tags.mapped(is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(lambda x: x.repartition_type == 'base')

		return {
			'base_tags': base_rep_lines.tag_ids.ids + product_tag_ids,
			'taxes': taxes_vals,
			'total_excluded': sign * total_excluded,
			'total_included': sign * currency.round(total_included),
			'total_void': sign * currency.round(total_void),
		}