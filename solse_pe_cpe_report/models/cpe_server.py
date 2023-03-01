# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api

class pe_sunat_server(models.Model):
	_inherit = 'cpe.server'

	partner_ids = fields.Many2many("res.partner", string="Contactos para envió", help="Contactos a los que se enviara un correo con el estado de los comprobantes. (Mensualmente)")
	partner_errror_ids = fields.Many2many("res.partner", 'server_partner_error', 'server_id', 'contacto_id', string="Contactos para envió (Error)", help="Contactos a los que se enviara un correo con los comprobantes electronicos que esten rechazados por sunat")

