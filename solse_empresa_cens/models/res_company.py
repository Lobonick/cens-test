# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php

from odoo import api, fields, models, _


class Company(models.Model):
	_inherit = "res.company"

	cuenta_detracciones = fields.Many2one("account.account", string="Cuenta de detracciones [Venta]")
	cuenta_detracciones_compra = fields.Many2one("account.account", string="Cuenta de detracciones [Compra]")
	cuenta_detrac_ganancias = fields.Many2one("account.account", string="Cuenta para ganancias")
	cuenta_detrac_perdidas = fields.Many2one("account.account", string="Cuenta para perdidas")
	
	cuenta_retenciones = fields.Many2one("account.account", string="Cuenta de retenciones")
