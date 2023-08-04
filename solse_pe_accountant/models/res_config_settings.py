# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models
import logging
_logging = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	cuenta_detracciones = fields.Many2one("account.account", string="Cuenta de detracciones [Venta]", related="company_id.cuenta_detracciones", store=True, readonly=False)
	cuenta_detracciones_compra = fields.Many2one("account.account", string="Cuenta de detracciones [Compra]", related="company_id.cuenta_detracciones_compra", store=True, readonly=False)
	cuenta_detrac_ganancias = fields.Many2one("account.account", string="Cuenta para ganancias", related="company_id.cuenta_detrac_ganancias", store=True, readonly=False)
	cuenta_detrac_perdidas = fields.Many2one("account.account", string="Cuenta para perdidas", related="company_id.cuenta_detrac_perdidas", store=True, readonly=False)
	
	cuenta_retenciones = fields.Many2one("account.account", string="Cuenta de retenciones", related="company_id.cuenta_retenciones", store=True, readonly=False)
