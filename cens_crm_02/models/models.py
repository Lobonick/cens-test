from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mail import email_split
from datetime import datetime
import requests
import base64
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    cens_preventa_1 = fields.Many2one('res.users', string='PreVenta Asignado:', default=lambda self: self.env.user.id)
    cens_control_01 = fields.Integer(string='Control 01:', readonly=True, default=0, existing_field=True)
    cens_control_02 = fields.Char("Control 02:")
    cens_usuario_activo_id = fields.Integer(
        string='Usuario Activo', 
        compute='_compute_usuario_activo_id',
        store=False  # No almacenar en la BD
    )
    
    # ------------------------------
    # ACTUALIZA USUARIO ACTIVO
    # ------------------------------
    def _compute_usuario_activo_id(self):
        for record in self:
            record.cens_usuario_activo_id = self.env.user.id
            record.x_studio_usuario_activo_id = self.env.user.id

    # ------------------------------
    # CARGA IMAGEN DESDE URL
    # ------------------------------
    @api.model
    def _cargar_imagen_aviso(self):
        try:
            url_imagen = "https://sisac-peru.com/Aviso-Novedades-01.jpg"
            response = requests.get(url_imagen, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                return False
        except Exception as e:
            return False
    
    # ------------------------------
    # AÑADIR ADJUNTO DE IMAGEN AL CHATTER
    # ------------------------------
    def _crear_adjunto_imagen(self):
        imagen_contenido = self._cargar_imagen_aviso()
        if not imagen_contenido:
            return False
            
        # Crear el adjunto
        attachment_vals = {
            'name': 'Aviso-Novedades-01.jpg',
            'datas': base64.b64encode(imagen_contenido),
            'res_model': 'crm.lead',
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'image/jpeg',
        }
        
        attachment = self.env['ir.attachment'].create(attachment_vals)
        return attachment.id
    
    # ------------------------------
    # REGISTRAR MENSAJE CON IMAGEN ADJUNTA
    # ------------------------------
    def agregar_imagen_como_mensaje(self):
        for record in self:
            attachment_id = record._crear_adjunto_imagen()
            if not attachment_id:
                raise UserError(_('No se pudo cargar la imagen desde la URL especificada.'))
            
            # Crear mensaje con adjunto
            self.env['mail.message'].create({
                'model': 'crm.lead',
                'res_id': record.id,
                'message_type': 'comment',
                'body': _('<p>Aviso importante: Se ha adjuntado una imagen con información relevante.</p>'),
                'attachment_ids': [(4, attachment_id)],  # Usar 4 para añadir al many2many
                'author_id': self.env.user.partner_id.id,
                'email_from': self.env.user.email,
                'subtype_id': self.env.ref('mail.mt_comment').id,
            })
            
            # También actualizamos la actividad si existe
            activity = self.env['mail.activity'].search([
                ('res_id', '=', record.id),
                ('res_model', '=', 'crm.lead')
            ], limit=1)
            
            if activity:
                activity.write({
                    'attachment_ids': [(4, attachment_id)]
                })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Imagen adjuntada correctamente al historial de mensajes.'),
                    'sticky': False,
                }
            }
    
    # ------------------------------
    # ENVIAR CORREO DE ALERTA
    # ------------------------------
    def enviar_correo_solicita_ganada(self):
        self.ensure_one()
        template_id = self.env.ref('studio_customization.alerta_solicita_opor_ac464d32-6b47-4809-9432-b0fba3a7ebf4')
        if not template_id:
            _logger.error('No se encontró la plantilla de correo con ID XML: studio_customization.alerta_solicita_opor_ac464d32-6b47-4809-9432-b0fba3a7ebf4')
            return False
            
        # Enviar correo usando la plantilla
        try:
            template_id.send_mail(self.id, force_send=True)
            _logger.info('Correo de SOLICITUD CAMBIO DE ESTADO fue enviado correctamente  (ID: %s)', self.id)
            return True
        except Exception as e:
            _logger.error('Error al enviar correo de SOLICITUD: %s', str(e))
            return False

    # ------------------------------
    # ENVIAR CORREO DE ALERTA
    # ------------------------------
    def enviar_correo_alerta(self):
        self.ensure_one()
        template_id = self.env.ref('studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
        if not template_id:
            _logger.error('No se encontró la plantilla de correo con ID XML: studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
            return False
            
        # Enviar correo usando la plantilla
        try:
            template_id.send_mail(self.id, force_send=True)
            _logger.info('Correo de alerta enviado correctamente para el lead ID: %s', self.id)
            return True
        except Exception as e:
            _logger.error('Error al enviar correo de alerta: %s', str(e))
            return False
    
    # ---------------------------------------------------------------
    # MÉTODO PARA CREAR NUEVOS REGISTROS CON IMAGEN Y ENVIAR CORREO
    # ---------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super(CRMLead, self).create(vals_list)
        for record in records:

            # Enviar correo de alerta
            record.enviar_correo_alerta()

            # Adjuntar la imagen automáticamente
            record.agregar_imagen_como_mensaje()
            
        return records
