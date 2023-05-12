# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"

	es_x_cierre = fields.Boolean("Es de cierre")

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	@api.model
	def _query_get(self, domain=None):
		self.check_access_rights('read')

		context = dict(self._context or {})
		domain = domain or []
		if not isinstance(domain, (list, tuple)):
			domain = ast.literal_eval(domain)

		date_field = 'date'
		if context.get('aged_balance'):
			date_field = 'date_maturity'
		if context.get('date_to'):
			domain += [(date_field, '<=', context['date_to'])]

		if 'es_x_cierre' in context:
			domain += [('move_id.es_x_cierre', '=', context['es_x_cierre'])]

		if context.get('date_from'):
			if not context.get('strict_range'):
				domain += ['|', (date_field, '>=', context['date_from']),
						   ('account_id.include_initial_balance', '=', True)]
			elif context.get('initial_bal'):
				domain += [(date_field, '<', context['date_from'])]
			else:
				domain += [(date_field, '>=', context['date_from'])]

		if context.get('journal_ids'):
			domain += [('journal_id', 'in', context['journal_ids'])]

		state = context.get('state')
		if state and state.lower() != 'all':
			domain += [('parent_state', '=', state)]

		if context.get('company_id'):
			domain += [('company_id', '=', context['company_id'])]
		elif context.get('allowed_company_ids'):
			domain += [('company_id', 'in', self.env.companies.ids)]
		else:
			domain += [('company_id', '=', self.env.company.id)]

		if context.get('reconcile_date'):
			domain += ['|', ('reconciled', '=', False), '|',
					   ('matched_debit_ids.max_date', '>', context['reconcile_date']),
					   ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

		if context.get('account_tag_ids'):
			domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

		if context.get('account_ids'):
			domain += [('account_id', 'in', context['account_ids'].ids)]

		if context.get('analytic_tag_ids'):
			domain += [('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

		if context.get('analytic_account_ids'):
			domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

		if context.get('partner_ids'):
			domain += [('partner_id', 'in', context['partner_ids'].ids)]

		if context.get('partner_categories'):
			domain += [('partner_id.category_id', 'in', context['partner_categories'].ids)]

		where_clause = ""
		where_clause_params = []
		tables = ''
		if domain:
			domain.append(('display_type', 'not in', ('line_section', 'line_note')))
			domain.append(('parent_state', '!=', 'cancel'))

			query = self._where_calc(domain)

			# Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
			self._apply_ir_rules(query)

			tables, where_clause, where_clause_params = query.get_sql()
		return tables, where_clause, where_clause_params