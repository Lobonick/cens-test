# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	partner_doc_type = fields.Char("Tipo Doc. Contacto", related="partner_id.l10n_latam_identification_type_id.name")
	partner_doc_number = fields.Char("Nro Doc. Contacto", related="partner_id.doc_number")