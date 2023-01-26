# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_detracciones = fields.Many2one("account.account", string="Cuenta de detracciones", config_parameter='solse_pe_accountant.default_cuenta_detracciones')
	cuenta_detrac_ganancias = fields.Many2one("account.account", string="Cuenta para ganancias", config_parameter='solse_pe_accountant.default_cuenta_detrac_ganancias')
	cuenta_detrac_perdidas = fields.Many2one("account.account", string="Cuenta para perdidas", config_parameter='solse_pe_accountant.default_cuenta_detrac_perdidas')
	
	cuenta_retenciones = fields.Many2one("account.account", string="Cuenta de retenciones", config_parameter='solse_pe_accountant.default_cuenta_retenciones')
