# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _

class pe_sunat_server(models.Model):
	_inherit = 'cpe.server'

	es_guia = fields.Boolean("Es para guías")
	client_id = fields.Char("Id Cliente")
	client_secret = fields.Char("Clave Cliente")