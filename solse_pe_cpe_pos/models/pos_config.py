# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PosConfig(models.Model):
	_inherit = 'pos.config'
	
	# module_account
	# auto_open_invoice = fields.Boolean("Factura automática")

	iface_journals = fields.Boolean("Mostrar documentos de venta", help="Habilita el uso de documentos electrónicos desde el Punto de Venta", default=True)
	documento_venta_ids = fields.Many2many("l10n_latam.document.type", string="Documentos de venta", domain=[("sub_type", "=", "sale")])
	cliente_varios = fields.Many2one('res.partner', string="Cliente Varios")
	doc_venta_defecto = fields.Many2one('l10n_latam.document.type', string="Documento de venta Defecto", domain='[("id", "in", documento_venta_ids)]')

