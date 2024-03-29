# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_factoring = fields.Many2one("account.account", string="Cuenta para Factoring", config_parameter='solse_pe_factoring.default_cuenta_factoring')
	cuenta_factoring_gastos = fields.Many2one("account.account", string="Cuenta para Factoring (Gastos)", config_parameter='solse_pe_factoring.default_cuenta_factoring_gastos')
	cuenta_factoring_comision = fields.Many2one("account.account", string="Cuenta para Factoring (Comisión)", config_parameter='solse_pe_factoring.default_cuenta_factoring_comision')
	cuenta_factoring_garantia = fields.Many2one("account.account", string="Cuenta para Factoring (Garantia)", config_parameter='solse_pe_factoring.default_cuenta_factoring_garantia')