# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosMakePayment(models.TransientModel):
	_inherit = 'pos.make.payment'

	def check_base(self):
		self.ensure_one()
		active_id = self.env.context.get('active_id')
		order = self.env['pos.order'].browse(active_id)
		session_id = order.session_id or self.env['pos.session'].search([
			('state', '=', 'opened'),
			('user_id', '=', self.env.uid)], limit=1)
		if not session_id:
			session_id = self.env['pos.session'].search([
				('state', '=', 'opened')], limit=1)
		if not session_id and self.env.context.get("paid_on_line"):
			raise ValidationError(
				_("No se puede realizar el pago. Necesitas crear una nueva sesión"))
		elif order and self.env.context.get("paid_on_line"):
			order.write({'session_id': session_id.id})
		res = super(PosMakePayment, self).check()
		is_auto_open_invoice = all((self.env.context.get("paid_on_line"), order.state == 'paid'))
		if is_auto_open_invoice:
			order.action_pos_order_invoice()
		return res

	def check(self):
		order = self.env['pos.order'].browse(
			self.env.context.get('active_id', False))
		if order.pe_invoice_type == 'annul':
			context = dict(self.env.context)
			context['paid_on_line'] = False
			self = self.with_context(**context)
		res = self.check_base()
		if order.pe_invoice_type == 'annul':
			order.refund_invoice_id.sudo().button_annul()
			if order.refund_order_id.state in ["invoiced", "paid"]:
				order.refund_order_id.account_move = False
				order.refund_order_id.state = 'paid'
			order.refund_order_id.pe_invoice_type = 'annul'
		return res
