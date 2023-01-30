# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning
import pytz
import logging

_logging = logging.getLogger(__name__)
tz = pytz.timezone('America/Lima')

class PeruSunatCpe(models.Model):
	_inherit = 'solse.cpe'

	name = fields.Char("Name", default="/")
	state = fields.Selection([
		('draft', 'Borrador'),
		('generate', 'Generado'),
		('send', 'Enviado'),
		('verify', 'Esperando'),
		('done', 'Hecho'),
		('cancel', 'Cancelado'),
	], string='Estado', index=True, readonly=False, default='draft', copy=False)
	type = fields.Selection([
		('sync', 'Envio online'),
		('rc', 'Resumen diario'),
		('ra', 'Comunicación de Baja'),
	], string="Tipo", default='sync', readonly=False)

	date = fields.Date("Fecha", default=fields.Date.context_today, readonly=False)
	date_end = fields.Datetime("Fecha final", readonly=False)
	send_date = fields.Datetime("Fecha de envio", readonly=False)

	datas = fields.Binary("Datos XML", readonly=False)
	datas_fname = fields.Char("Nombre de archivo XML",  readonly=False)
	datas_sign = fields.Binary("Datos firmado XML",  readonly=False)
	datas_sign_fname = fields.Char("Nombre de archivo firmado XML",  readonly=False)
	datas_zip = fields.Binary("Datos Zip XML", readonly=False)
	datas_zip_fname = fields.Char("Nombre de archivo zip XML",  readonly=False)
	datas_response = fields.Binary("Datos de respuesta XML",  readonly=False)
	datas_response_fname = fields.Char("Nombre de archivo de respuesta XML",  readonly=False)
	response = fields.Char("Respuesta", readonly=False)
	response_code = fields.Char("Código de respuesta", readonly=False)
	note = fields.Text("Nota", readonly=False)
	error_code = fields.Selection("_get_error_code", string="Código de error", readonly=False)
	digest = fields.Char("Codigo", readonly=False)
	signature = fields.Text("Firma", readonly=False)
	#invoice_ids = fields.One2many("account.move", 'pe_cpe_id', string="Facturas", readonly=False)
	ticket = fields.Char("Ticket", readonly=False)