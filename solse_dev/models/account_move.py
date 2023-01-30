# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning
import pytz
import logging

_logging = logging.getLogger(__name__)

class AccountAccount(models.Model):
	_inherit = 'account.account'
	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)

class AccountMove(models.Model):
	_inherit = 'account.move'

	estado_temp = fields.Char("Estado al importar")
	reversed_entry_id = fields.Many2one('account.move', string="Reversal of", readonly=False, copy=False, check_company=True)
	debit_origin_id = fields.Many2one('account.move', 'Original Invoice Debited', readonly=False, copy=False)
	pago_id = fields.Many2one('sdev.facturas.pago', 'Pago')
	
