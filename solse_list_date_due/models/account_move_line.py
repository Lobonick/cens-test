# -*- coding: utf-8 -*-
# Copyright (c) 2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMoveLine(models.Model) :
	_inherit = 'account.move.line'

	tipo_factura = fields.Selection(related="move_id.move_type", store=True)
	saldo = fields.Monetary(related="move_id.amount_residual", store=True)