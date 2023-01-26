# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import api, fields, models,_
from odoo.exceptions import UserError
import logging
_logging = logging.getLogger(__name__)

class InheritedSaleOrder(models.Model):
	_inherit = 'account.move'

	nro_factura_prov = fields.Char(related="purchase_id.nro_factura")