# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _

class Company(models.Model):
	_inherit = "res.company"

	pe_cpe_eguide_server_id = fields.Many2one(comodel_name="cpe.server", string="Servidor para Guías", domain="[('state','=','done')]")
