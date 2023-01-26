# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountAdditionalTotal(models.Model):
	_name = 'account.move.additional.total'
	_description = 'Additional Monetary Total'
	_order = 'code'
	code = fields.Selection('_get_code', 'Code')
	name = fields.Char('Name')
	invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='cascade', index=True)
	reference_amount = fields.Float(string='Reference Amount')
	payable_amount = fields.Float(string='Payable Amount')
	percent = fields.Float(string='Percent', digits='Discount')
	total_amount = fields.Float(string='Total Amount')

	@api.model
	def _get_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG14')


class AccountAdditionalProperty(models.Model):
	_name = 'account.move.additional.property'
	_description = 'Additional Property'
	_order = 'code'

	code = fields.Selection('_get_code', 'Code')
	name = fields.Char('Name')
	value = fields.Char('Value')
	invoice_id = fields.Many2one(comodel_name='account.move',
	  string='Invoice',
	  ondelete='cascade',
	  index=True)

	@api.model
	def _get_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG15')