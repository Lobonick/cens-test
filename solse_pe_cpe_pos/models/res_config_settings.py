# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	documento_venta_ids = fields.Many2many("l10n_latam.document.type", string="Documentos de venta", domain=[("sub_type", "=", "sale")], related="pos_config_id.documento_venta_ids", readonly=False)
	cliente_varios = fields.Many2one('res.partner', string="Cliente Varios", related="pos_config_id.cliente_varios", readonly=False)
	doc_venta_defecto = fields.Many2one('l10n_latam.document.type', string="Documento de venta Defecto", domain='[("id", "in", documento_venta_ids)]', related="pos_config_id.doc_venta_defecto", readonly=False)
