# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_ganancias = fields.Many2one("account.account", string="Cuenta ganancias (Cierre Transitorio)", 
		config_parameter='solse_pe_accountant_report.default_cuenta_ganancias')
	cuenta_perdidas = fields.Many2one("account.account", string="Cuenta perdidas (Cierre Transitorio)", 
		config_parameter='solse_pe_accountant_report.default_cuenta_perdidas')

	cuenta_ganancias_cierre = fields.Many2one("account.account", string="Cuenta ganancias (Cierre)", 
		config_parameter='solse_pe_accountant_report.default_cuenta_ganancias_cierre')
	cuenta_perdidas_cierre = fields.Many2one("account.account", string="Cuenta perdidas (Cierre)", 
		config_parameter='solse_pe_accountant_report.default_cuenta_perdidas_cierre')
