# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import Warning
import pytz
import logging
from . import constantes

_logging = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

class LogCPE(models.Model):
	_name = 'solse.cpe.log'
	_description = 'Log de comprobantes'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	move_id = fields.Many2one('account.move', 'Comprobante', required=True)
	pe_doc_name = fields.Char(related='move_id.pe_doc_name', store=True)
	partner_id = fields.Many2one('res.partner', related='move_id.partner_id', store=True)
	estado_sunat = fields.Selection([
		('01', 'Registrado'),
		('03', 'Enviado'),
		('05', 'Aceptado'),
		('07', 'Observado'),
		('09', 'Rechazado'),
		('11', 'Anulado'),
		('13', 'Por anular'),
	], string='Estado Sunat', default='01')

	name = fields.Char('Nombre', related="move_id.name")
	descripcion = fields.Char('Descripcion')

	cod_respuesta = fields.Char('Codigo respuesta')
	mensaje_respuesta = fields.Char('Mensaje respuesta')
	cod_accion = fields.Char('Codigo accion')

	error_ids = fields.One2many('solse.cpe.log.error', 'log_id', 'Errores')

	def ejecturarAcciones(self):
		for reg in error_ids:
			for accion in reg.error_id.accion_ids:
				if accion == 'notificar_correo':
					# enviar correo a lista
				elif accion == 'notificar_cliente':
					# enviar correo al cliente

	def action_enviar_log(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('solse_pe_cpe', 'email_template_error_cpe')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = {
			'default_model': 'solse.cpe.log',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			#'custom_layout': "sale.mail_template_data_notification_email_sale_order",
			'force_email': True
		}
		return {
			'type': 'ir.actions.act_window',
			#'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}

	def enviarLog(self):
		if not self.partner_id.email:
			pass
		account_mail = self.action_enviar_log()
		context = account_mail.get('context')
		if not context:
			pass
		else:
			template_id = account_mail['context'].get('default_template_id')
			if not template_id:
				pass

			attachment_ids = []
			if context.get('default_attachment_ids', False):
				for attach in context.get('default_attachment_ids'):
					attachment_ids += attach[2]
			mail_id = self.env['mail.template'].browse(template_id)
			mail_id.send_mail((self.id), force_send=True, email_values={'attachment_ids': attachment_ids})


class Acciones(models.Model):
	_name = 'solse.cpe.accion'
	_description = 'Acciones'

	name = fields.Char('Accion')
	tipo = fields.Selection(constantes.ACCION)
	contactos_correo =  fields.Many2many('res.partner', 'cantacto_accion_id', 'contacto_id', 'accion_id', string='Contactos')

class ErroresCPE(models.Model):
	_name = 'solse.cpe.error'
	_description = 'Error en cpe'

	name = fields.Char('Error', required=True)
	accion_ids =  fields.Many2many('solse.cpe.accion', 'accion_error_id', 'accion_id', 'error_id', string='Acciones')

class ErroresLog(models.Model):
	_name ='solse.cpe.log.error'
	_description = 'Errores en proceso'

	log_id = fields.Many2one('solse.cpe.log', 'Log')
	error_id = fields.Many2one('solse.cpe.error', 'Error')