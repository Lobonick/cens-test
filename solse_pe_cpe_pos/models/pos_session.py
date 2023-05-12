# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models
from itertools import groupby
from odoo.osv.expression import AND
import logging
_logging = logging.getLogger(__name__)

class PosSession(models.Model):
	_inherit = 'pos.session'

	def _check_invoices_are_posted(self):
		unposted_invoices = self.order_ids.account_move.filtered(lambda x: x.state not in ['posted', 'annul', 'cancel'])
		if unposted_invoices:
			raise UserError(_('You cannot close the POS when invoices are not posted.\n'
							  'Invoices: %s') % str.join('\n',
														 ['%s - %s' % (invoice.name, invoice.state) for invoice in
														  unposted_invoices]))

	def _pos_ui_models_to_load(self):
		result = super()._pos_ui_models_to_load()
		result.append('l10n_latam.identification.type')
		result.append('account.payment.term')
		result.append('l10n_latam.document.type')
		return result

	def _loader_params_l10n_latam_identification_type(self):
		return {
			'search_params': {
				'domain': [('country_id.code', '=', 'PE')],
				'fields': ['name', 'id', 'l10n_pe_vat_code'],
				'order': 'sequence',
			},
		}

	def _get_pos_ui_l10n_latam_identification_type(self, params):
		datos = self.env['l10n_latam.identification.type'].search_read(**params['search_params'])
		return datos

	def _loader_params_account_payment_term(self):
		return {
			'search_params': {
				'domain': [],
				'fields': [],
			},
		}

	def _get_pos_ui_account_payment_term(self, params):
		datos = self.env['account.payment.term'].search_read(**params['search_params'])
		return datos

	def _loader_params_l10n_latam_document_type(self):
		return {
			'search_params': {
				'domain': [('id', 'in', self.config_id.documento_venta_ids.ids)],
				'fields': [],
			},
		}

	def _get_pos_ui_l10n_latam_document_type(self, params):
		datos = self.env['l10n_latam.document.type'].search_read(**params['search_params'])
		return datos

	def _loader_params_res_partner(self):
		res = super(PosSession, self)._loader_params_res_partner()
		res['search_params']['fields'].extend(["state_id", "city_id", "l10n_pe_district", "doc_type", "doc_number", 
		"commercial_name", "type", "cod_doc_rel", "parent_id", "nombre_temp", "legal_name", "is_validate", "state", "condition", "l10n_latam_identification_type_id", "numero_temp"])
		return res

	def _loader_params_res_currency(self):
		res = super(PosSession, self)._loader_params_res_currency()
		res['search_params']['fields'].extend(["singular_name", "plural_name", "fraction_name", "show_fraction"])
		return res

	def _loader_params_res_company(self):
		res = super(PosSession, self)._loader_params_res_company()
		res['search_params']['fields'].extend(["street", "sunat_amount"])
		return res

	"""def _loader_params_pos_config(self):
		res = super(PosSession, self)._loader_params_pos_config()
		res['search_params']['fields'].extend(["documento_venta_ids"])
		return res"""

	def _loader_params_pos_order(self):
		res = super(PosSession, self)._loader_params_pos_order()
		res['search_params']['fields'].extend(["refunded_order_ids", "number", "number_ref", "l10n_latam_document_type_id"])
		return res
	

		

	