# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	balance_as_supplier = fields.Monetary('Saldo como proveedor', default=0)
	balance_as_customer = fields.Monetary('Saldo como cliente', default=0)

	def action_view_balance_supplier_movement(self):
		self.ensure_one()
		action = self.env.ref('solse_reportes.action_report_account_balances').read()[0]
		action['domain'] = [('state', 'not in', ['cancelled', 'cancel', 'draft']), ('partner_id.id', 'in', self.ids), ('partner_type', '=', 'supplier')]
		action['limit'] = 60
		return action

	def action_view_balance_customer_movement(self):
		self.ensure_one()
		action = self.env.ref('solse_reportes.action_report_account_balances').read()[0]
		action['domain'] = [('state', 'not in', ['cancelled', 'cancel', 'draft']), ('partner_id.id', 'in', self.ids), ('partner_type', '=', 'customer')]
		action['limit'] = 60
		return action