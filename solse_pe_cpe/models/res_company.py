# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Company(models.Model):
	_inherit = "res.company"

	pe_is_sync = fields.Boolean("Es sincrono", default=True)
	pe_certificate_id = fields.Many2one(comodel_name="cpe.certificate", string="Certificado", domain="[('state','=','done')]")
	pe_cpe_server_id = fields.Many2one(comodel_name="cpe.server", string="Servidor", domain="[('state','=','done')]")
	enviar_email = fields.Boolean('Envio correo automatico', help="Si esta activo cada vez que se confirme un comprobante se enviara el pdf al cliente")