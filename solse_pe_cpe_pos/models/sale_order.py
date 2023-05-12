# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _

class SaleOrder(models.Model):
	_inherit = "sale.order"
	
	session_id = fields.Many2one('pos.session', string='Sesión', readonly=True, copy=False)
	pos_order_id = fields.Many2one('pos.order', string='Orden POS', readonly=True, copy=False)
	pos_order_count = fields.Integer("Recuento de pedidos", compute="_compute_pos_order_count", default=0)
	
	@api.depends('pos_order_id')
	def _compute_pos_order_count(self):
		for sale in self:
			sale.pos_order_count = len(sale.pos_order_id)
	
	def action_view_pos_order(self):
		pos_order_id = self.pos_order_id
		action = self.env.ref('point_of_sale.action_pos_pos_form').read()[0]
		if len(pos_order_id) > 1:
			action['domain'] = [('id', 'in', pos_order_id.ids)]
		elif len(pos_order_id) == 1:
			action['views'] = [(self.env.ref(
				'point_of_sale.view_pos_pos_form').id, 'form')]
			action['res_id'] = pos_order_id.ids[0]
		else:
			action = {'type': 'ir.actions.act_window_close'}
		return action