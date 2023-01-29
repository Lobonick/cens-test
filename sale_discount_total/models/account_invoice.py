# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Faslu Rahman(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class AccountInvoice(models.Model):
	_inherit = "account.move"

	discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
									 readonly=True,
									 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
									 default='percent')
	discount_rate = fields.Float('Discount Rate', digits=(16, 2),
								 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
	amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, track_visibility='always')

	@api.onchange('discount_type', 'discount_rate', 'invoice_line_ids')
	def supply_rate(self):
		for inv in self:
			if inv.discount_type == 'percent':
				discount_totals = 0
				for line in inv.invoice_line_ids:
					line.discount = inv.discount_rate
					total_price = line.price_unit * line.quantity
					discount_total = total_price - line.price_subtotal
					discount_totals = discount_totals + discount_total
					inv.amount_discount = discount_totals
					line._compute_totals()
			else:
				total = discount = 0.0
				for line in inv.invoice_line_ids:
					total += (line.quantity * line.price_unit)
				if inv.discount_rate != 0:
					discount = (inv.discount_rate / total) * 100
				else:
					discount = inv.discount_rate
				for line in inv.invoice_line_ids:
					line.discount = discount
					inv.amount_discount = inv.discount_rate
					line._compute_totals()

			inv._compute_tax_totals()

	def button_dummy(self):
		self.supply_rate()
		return True


class AccountInvoiceLine(models.Model):
	_inherit = "account.move.line"

	discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)

