# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _

class Partner(models.Model):
	_inherit = 'res.partner'

	pe_driver_license = fields.Char("Licencia de conducir")
	doc_name = fields.Char(string="Tipo doc.",related="l10n_latam_identification_type_id.name")
