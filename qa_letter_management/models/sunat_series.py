import logging

from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class Series(models.Model):
	_inherit = 'sunat.series'

	name = fields.Char(string="Serie", size=6, required=True)

	# class ResConfigSettings(models.TransientModel):
	#     _inherit = 'res.config.settings'
	#
	#     loans_journal = fields.Many2one('account.journal', string='Loans Journal',
	#                                     related="company_id.loans_journal", readonly=False)
