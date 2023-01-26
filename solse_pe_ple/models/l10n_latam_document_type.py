# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'

	inc_ple_compras = fields.Boolean("Incluir en PLE de Compras")
	inc_ple_ventas = fields.Boolean("Incluir en PLE de Ventas")

	