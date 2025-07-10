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

# ----------------------------------------------------------------------------------------------------------------------
#
# ======================================================================================================================

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mail import email_split
from datetime import datetime
import base64
import logging
from io import BytesIO
import os

_logger = logging.getLogger(__name__)

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    cens_preventa_1 = fields.Many2one('res.users', string='PreVenta Asignado:', default=lambda self: self.env.user.id)
    cens_control_01 = fields.Integer(string='Control 01:', readonly=True, default=0, existing_field=True)
    cens_control_02 = fields.Char("Control 02:")
    cens_usuario_activo_id = fields.Integer(
        string='Usuario Activo', 
        compute='_compute_usuario_activo_id',
        store=False,
        compute_sudo=True  # Mejora rendimiento ejecutando como sudo
    )
    
    # ------------------------------
    # ACTUALIZA USUARIO ACTIVO
    # ------------------------------
    @api.depends('create_date')  # Agregando dependencia para optimizar cálculo
    def _compute_usuario_activo_id(self):
        """Computa el usuario activo actual para el registro"""
        user_id = self.env.user.id
        for record in self:
            record.cens_usuario_activo_id = user_id
            record.x_studio_usuario_activo_id = user_id

    # ------------------------------
    # CARGAR IMAGEN DESDE MÓDULO LOCAL
    # ------------------------------
    @api.model
    def _cargar_imagen_aviso(self):
        """Obtiene la imagen de aviso desde el módulo"""
        # Verificar si la imagen ya está en caché (ir.attachment)
        attachment = self.env['ir.attachment'].sudo().search([
            ('name', '=', 'aviso-novedades-01.jpg'),
            ('res_model', '=', 'crm.lead.cache'),  # Modelo "virtual" para caching
        ], limit=1)
        
        if attachment:
            return base64.b64decode(attachment.datas)
        
        # Si no está en caché, cargamos desde el módulo
        try:
            # Obtener la ruta del módulo actual
            module_path = self.env['ir.module.module'].search([
                ('name', '=', 'CENS-CRM-02')
            ], limit=1)
            
            if not module_path:
                _logger.error("No se pudo encontrar el módulo CENS-CRM-02")
                return False
                
            # Construir la ruta a la imagen dentro del módulo
            file_path = module_path.get_module_path('CENS-CRM-02') + '/static/description/aviso-novedades-01.jpg'
            
            # Leer la imagen del sistema de archivos
            try:
                with open(file_path, 'rb') as image_file:
                    imagen_contenido = image_file.read()
                    
                # Guardar en caché para futuros usos
                self.env['ir.attachment'].sudo().create({
                    'name': 'aviso-novedades-01.jpg',
                    'datas': base64.b64encode(imagen_contenido),
                    'res_model': 'crm.lead.cache',
                    'res_id': 0,
                    'type': 'binary',
                    'mimetype': 'image/jpeg',
                })
                return imagen_contenido
            except (IOError, FileNotFoundError) as e:
                _logger.error("Error al leer archivo de imagen local: %s", str(e))
                return False
        except Exception as e:
            _logger.error("Error al cargar imagen desde módulo: %s", str(e))
            return False
    
    # ------------------------------
    # AÑADIR ADJUNTO DE IMAGEN AL CHATTER
    # ------------------------------
    def _crear_adjunto_imagen(self):
        self.ensure_one()
        # Primero intentamos el método principal, luego el alternativo
        imagen_contenido = self._cargar_imagen_aviso() or self._cargar_imagen_aviso_alternativo()
        if not imagen_contenido:
            _logger.error("No se pudo cargar la imagen del módulo para el lead ID: %s", self.id)
            return False
            
        # Crear el adjunto
        attachment_vals = {
            'name': 'aviso-novedades-01.jpg',
            'datas': base64.b64encode(imagen_contenido),
            'res_model': 'crm.lead',
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'image/jpeg',
        }
        
        attachment = self.env['ir.attachment'].sudo().create(attachment_vals)
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
            self.env['mail.message'].sudo().create({
                'model': 'crm.lead',
                'res_id': record.id,
                'message_type': 'comment',
                'body': _('<p>Aviso importante: Se ha adjuntado una imagen con información relevante.</p>'),
                'attachment_ids': [(4, attachment_id)],
                'author_id': self.env.user.partner_id.id,
                'email_from': self.env.user.email,
                'subtype_id': self.env.ref('mail.mt_comment').id,
            })
            
            # También actualizamos la actividad si existe
            activity = self.env['mail.activity'].sudo().search([
                ('res_id', '=', record.id),
                ('res_model', '=', 'crm.lead')
            ], limit=1)
            
            if activity:
                activity.sudo().write({
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
    def enviar_correo_alerta(self):
        self.ensure_one()
        template_id = self.env.ref('studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
        if not template_id:
            _logger.error('No se encontró la plantilla de correo con ID XML: studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
            return False
            
        # Enviar correo usando la plantilla sin bloquear el proceso
        try:
            template_id.with_context(custom_layout='mail.mail_notification_light').send_mail(
                self.id, 
                force_send=False  # No forzar envío inmediato
            )
            _logger.info('Correo de alerta programado para el lead ID: %s', self.id)
            return True
        except Exception as e:
            _logger.error('Error al programar correo de alerta: %s', str(e))
            return False
    
    # --------------------------------------------------------------------------
    # IMPORTANTE: Alternativa más simple para cargar la imagen desde el módulo
    # --------------------------------------------------------------------------
    @api.model
    def _cargar_imagen_aviso_alternativo(self):
        """Obtiene la imagen de aviso desde el módulo (método más simple)"""
        # Verificar si la imagen ya está en caché (ir.attachment)
        attachment = self.env['ir.attachment'].sudo().search([
            ('name', '=', 'aviso-novedades-01.jpg'),
            ('res_model', '=', 'crm.lead.cache'),
            ('res_id', '=', 0),
        ], limit=1)
        
        if attachment:
            return base64.b64decode(attachment.datas)
        
        # Si no está en caché, usamos el sistema de assets de Odoo
        try:
            # Obtener la imagen usando el sistema de assets de Odoo
            imagen_path = 'CENS-CRM-02/static/description/aviso-novedades-01.jpg'
            imagen_contenido = self.env['ir.attachment']._file_read(imagen_path)
            
            if imagen_contenido:
                # Guardar en caché para futuros usos
                self.env['ir.attachment'].sudo().create({
                    'name': 'aviso-novedades-01.jpg',
                    'datas': base64.b64encode(imagen_contenido),
                    'res_model': 'crm.lead.cache',
                    'res_id': 0,
                    'type': 'binary',
                    'mimetype': 'image/jpeg',
                })
                return imagen_contenido
            else:
                _logger.warning("No se encontró la imagen en el módulo")
                return False
        except Exception as e:
            _logger.error("Error al cargar imagen desde módulo (alternativo): %s", str(e))
            return False
    @api.model_create_multi
    def create(self, vals_list):
        records = super(CRMLead, self).create(vals_list)
        
        # Programar operaciones asíncronas mediante un cron ligero
        self.env['ir.cron'].sudo().create({
            'name': f'Procesar nuevas oportunidades {records.ids}',
            'model_id': self.env['ir.model'].search([('model', '=', 'crm.lead')], limit=1).id,
            'state': 'code',
            'code': f"env['crm.lead'].browse({records.ids})._procesar_nuevas_oportunidades()",
            'interval_number': 1,
            'interval_type': 'minutes',
            'numbercall': 1,
            'doall': True,
            'active': True,
        })
        
        return records
    
    def _procesar_nuevas_oportunidades(self):
        """Método a ejecutar de forma asíncrona para procesar nuevas oportunidades"""
        for record in self:
            # Enviar correo de alerta
            record.enviar_correo_alerta()

            # Adjuntar la imagen automáticamente
            try:
                record.with_context(background_process=True).agregar_imagen_como_mensaje()
            except Exception as e:
                _logger.error('Error al adjuntar imagen para lead ID %s: %s', record.id, str(e))




