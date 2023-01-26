# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pe_sunat_server(models.Model):
	_name = 'cpe.server'
	_description = 'Servidores SUNAT'

	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	name = fields.Char("Nombre", required=True)
	url = fields.Char("Url", required=True)
	user = fields.Char("Usuario")
	password = fields.Char("Clave")
	description = fields.Text("Descripcion")
	active = fields.Boolean("Activo", default=True)
	state = fields.Selection([
		('draft', 'Borrador'),
		('done', 'Listo'),
		('cancel', 'Anulado'),
	], string='Status', index=True, readonly=True, default='draft', copy=False)

	extension_xml = fields.Char("Extension 'xml' de Respuesta", default="xml", help="Extension con la que se recibe la respuesta, por defecto para sunat es .xml con minuscula y para la OSE bizlink es con .XML con mayuscula")

	def action_draft(self):
		self.state = "draft"

	def action_done(self):
		self.state = "done"

	def action_cancel(self):
		self.state = "cancel"
