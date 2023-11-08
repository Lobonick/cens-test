# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import models, fields, api
from contextlib import ExitStack, contextmanager
import logging
from odoo.exceptions import UserError, ValidationError
_logging = logging.getLogger(__name__)


class ResPartner(models.Model):
	_inherit = 'res.partner'

	es_emp_factoring = fields.Boolean("Brinda servicio de Factoring")
	porc_garantia_factoring = fields.Float("% Garantia", default=5)
	porc_cobro_factoring = fields.Float("% Gastos Factoring", default=3)