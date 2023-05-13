# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api
from odoo.exceptions import Warning

class productTemplate(models.Model):
	_inherit = 'product.template'

	def action_view_stock_move_custom_lines(self):
		self.ensure_one()
		action = self.env.ref('solse_kardex.stock_move_line_custom_action').read()[0]
		action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
		return action