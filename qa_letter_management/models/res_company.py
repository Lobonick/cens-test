import logging

from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
	_inherit = 'res.company'

	bridge_journal = fields.Many2one("account.journal", string="Diario Puente")
	letter_portfolio = fields.Many2one('product.product', string='Letter in portfolio')
	# letter_collection = fields.Many2one('product.product', string='Letter in collection')
	# letter_discount = fields.Many2one('product.product', string='Letter in discount MN')
	letter_interest = fields.Many2one('product.product', string='Letter interest')
	# letter_discount_me = fields.Many2one('product.product', string='Letter in discount ME')
	# loans_journal = fields.Many2one('account.journal', string='Loans Journal')

