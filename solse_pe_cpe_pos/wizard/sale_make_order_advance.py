# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleAdvancePosOrder(models.TransientModel):
	_name = "sale.advance.pos.order"
	_description = "Sales Pos Order"

	def _get_default_journal_id(self):
		active_id = self.env.context.get('active_id')
		journal_id = False
		if active_id:
			order_id = self.env['sale.order'].browse(active_id)
			if order_id.partner_id.doc_type in ["6"]:
				journal_id = self.env['account.journal'].search([('company_id', '=', order_id.company_id.id), ('type', '=', 'sale')], limit=1)
				if journal_id:
					journal_id = journal_id
			else:
				journal_id = self.env['account.journal'].search([('company_id', '=', order_id.company_id.id), ('type', '=', 'sale')], limit=1)
				journal_id = journal_id or False
		return journal_id

	
	@api.model
	def _count(self):
		return len(self._context.get('active_ids', []))

	def _default_session(self):
		session_id = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
		if not session_id:
			session_id = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
		return session_id
	
	count = fields.Integer(default=_count, string='# of Orders')
	session_id = fields.Many2one('pos.session', string='Session', required=True, domain="[('state', '=', 'opened')]", default=_default_session)
	journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain="[('type', 'in', ['sale'])]", default=_get_default_journal_id)
	journal_ids = fields.Many2many("account.journal", string="Invoice Sale Journals", domain="[('type', 'in', ['sale'])]")
	
	def create_orders(self):
		sale_orders = self.env['sale.order'].browse(
			self._context.get('active_ids', []))
		if sale_orders:
			sale_orders.sudo().write({'session_id':self.session_id.id})
		sale_orders.sudo().action_pos_order_create()
		if self.env.context.get("open_pos_order"):
			return sale_orders.action_view_pos_order()
		return {'type': 'ir.actions.act_window_close'}
