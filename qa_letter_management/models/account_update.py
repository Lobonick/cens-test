import logging

from datetime import timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AccountUpdate(models.Model):
	_name = 'account.update'
	
	document_type_id = fields.Many2one('l10n_latam.document.type', string='Document Type', required=True)
	transaction_type = fields.Selection([('is_sale_document', 'Sale'), ('is_purchase_document', 'Purchase')], string='Transaction Type', required=True)
	currency_id = fields.Many2one('res.currency', string='Currency', required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True)
	account_id = fields.Many2one('account.account', string='Account', required=True)

	letter_state = fields.Selection([
		('portfolio', 'Letter in portfolio'),
		], string='Letter State')

	document_type_code = fields.Char(string='Code', related="document_type_id.code", store=True)