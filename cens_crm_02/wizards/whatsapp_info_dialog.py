from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.modules import get_module_path
import base64
import os
import logging
_logger = logging.getLogger(__name__)

class WhatsAppInfoDialog(models.TransientModel):
    _name = 'whatsapp.info.dialog'
    _description = 'Diálogo informativo WhatsApp PMO'
    
    message = fields.Text(string='Mensaje', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Oportunidad', readonly=True)
    
    # Campo para imagen JPG
    whatsapp_image = fields.Binary(
        string='Imagen WhatsApp',
        default=lambda self: self._get_default_whatsapp_image(),
        readonly=True
    )
    
    # Campo para mostrar nombre del archivo de imagen
    whatsapp_image_name = fields.Char(
        string='Nombre de Imagen',
        default='logo-whatsapp_03.png',
        readonly=True
    )
    
    # Campo para título personalizado
    dialog_title = fields.Char(
        string='Título',
        default='🚧 Servicio en Desarrollo 🚧',
        readonly=True
    )
    
    #def _get_default_whatsapp_image(self):
    #    """Cargar imagen JPG desde el módulo"""
    #    try:
    #        # Obtener la ruta del módulo actual
    #        module_name = 'cens_crm_02' 
    #        module = self.env['ir.module.module'].search([('name', '=', module_name)], limit=1)
    #        _logger.info(f'MÓDULO:  {module_name}')
    #        _logger.info(f'ESTADO:  {module.state}')
    #        
    #        if module.state == 'installed':     # module and 
    #            # Construir ruta a la imagen
    #            addon_path = self.env['ir.module.module'].get_module_path(module_name)
    #            image_path = os.path.join(addon_path, 'static', 'description', 'logo-modulos.png')
    #            
    #            _logger.info(f'LOG - Carga de Imagen')
    #            _logger.info(f'---------------------------------------------------------')
    #            _logger.info('module_name  (value: %s)', module_name)
    #            _logger.info('module.state (value: %s)', module.state)
    #            _logger.info('addon_path  (value: %s)', addon_path)
    #            _logger.info('image_path  (value: %s)', image_path)
    #            _logger.info('---------------------------------------------------------')
    #
    #            # Intentar leer la imagen
    #            if os.path.exists(image_path):
    #                with open(image_path, 'rb') as image_file:
    #                    return base64.b64encode(image_file.read())
    #            else:
    #                # Si no existe, intentar con otros nombres comunes
    #                alternative_names = [
    #                    'logo-whatsapp_03.png', 
    #                    'logo-whatsapp_02.png', 
    #                    'logo-modulos.ico', 
    #                    'logo-modulos.png' 
    #                ]
    #                
    #                for alt_name in alternative_names:
    #                    alt_path = os.path.join(addon_path, 'static', 'description', alt_name)
    #                    if os.path.exists(alt_path):
    #                        with open(alt_path, 'rb') as image_file:
    #                            return base64.b64encode(image_file.read())
    #        
    #        # Si no se puede cargar imagen del módulo, usar una imagen por defecto
    #        return self._get_default_placeholder_image()
    #        
    #    except Exception as e:
    #        raise UserError(_('Error al buscar la IMAGEN: %s') % str(e))
    #        # En caso de error, usar placeholder
    #        return self._get_default_placeholder_image()

    def _get_default_whatsapp_image(self):
        """Cargar imagen - Versión simplificada"""
        module_name = 'cens_crm_02'
        
        try:
            # Usar get_module_path (función global de Odoo)
            addon_path = get_module_path(module_name)
            
            if not addon_path:
                _logger.error('❌ No se encontró el módulo: %s', module_name)
                return self._get_default_placeholder_image()
            
            # Imagen específica que buscas
            image_path = os.path.join(addon_path, 'static', 'description', 'logo-whatsapp_03.png')
            
            _logger.info('🔍 Buscando imagen en: %s', image_path)
            
            if os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as image_file:
                        image_data = base64.b64encode(image_file.read())
                        _logger.info('✅ Imagen cargada exitosamente')
                        return image_data
                except Exception as read_error:
                    _logger.error('❌ Error leyendo archivo: %s', str(read_error))
            else:
                _logger.error('❌ Archivo no existe: %s', image_path)
                
                # Listar archivos en el directorio para debug
                desc_path = os.path.join(addon_path, 'static', 'description')
                if os.path.exists(desc_path):
                    files = os.listdir(desc_path)
                    _logger.info('📁 Archivos disponibles en description: %s', files)
                else:
                    _logger.error('❌ Directorio description no existe: %s', desc_path)
            
        except Exception as e:
            _logger.error('❌ Error cargando imagen: %s', str(e))
        
        return self._get_default_placeholder_image()


    def _get_default_placeholder_image(self):
        """Crear una imagen placeholder simple si no se encuentra la imagen real"""
        try:
            # Crear una imagen simple en base64 (1x1 pixel transparente)
            placeholder = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
            return base64.b64encode(base64.b64decode(placeholder))
        except:
            return False
    
    # Métodos para botones personalizados
    def action_accept(self):
        """Botón ACEPTAR personalizado"""
        # Aquí puedes agregar lógica adicional antes de cerrar
        # Por ejemplo, marcar como visto, enviar notificación, etc.
        
        # Opcional: Crear log de que el usuario vio el mensaje
        self.env['mail.message'].create({
            'subject': f'Usuario {self.env.user.name} vio información WhatsApp PMO',
            'body': f'El usuario visualizó el diálogo informativo para la oportunidad: {self.lead_id.name if self.lead_id else "N/A"}',
            'model': 'crm.lead',
            'res_id': self.lead_id.id if self.lead_id else False,
            'message_type': 'notification',
            'author_id': self.env.user.partner_id.id,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        """Botón CANCELAR personalizado"""
        # Cerrar sin hacer nada adicional
        return {'type': 'ir.actions.act_window_close'}
    
    def action_contact_support(self):
        """Botón para contactar soporte"""
        return {
            'name': _('Contactar Soporte - WhatsApp PMO'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': f'Consulta WhatsApp PMO - {self.lead_id.name if self.lead_id else ""}',
                'default_email_to': 'sistemas@cens.com.pe',
                'default_body': f'''
Estimado equipo de Sistemas,

Tengo una consulta sobre la funcionalidad WhatsApp PMO:

Usuario: {self.env.user.name}
Fecha: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M')}
Oportunidad: {self.lead_id.name if self.lead_id else 'N/A'}

Consulta:
[Escribir consulta aquí]

Saludos cordiales.
                ''',
                'default_model': 'crm.lead',
                'default_res_id': self.lead_id.id if self.lead_id else False,
            }
        }
    
    def action_view_roadmap(self):
        """Botón para ver roadmap de desarrollo"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/whatsapp_pmo_roadmap.pdf',
            'target': 'new'
        }
    
    # Método para actualizar el mensaje dinámicamente
    @api.model
    def create(self, vals):
        """Personalizar mensaje al crear el wizard"""
        record = super(WhatsAppInfoDialog, self).create(vals)
        
        # Personalizar mensaje según el contexto
        if record.lead_id:
            lead = record.lead_id
            custom_message = f"""
🚧 SERVICIO WHATSAPP PMO - EN DESARROLLO 🚧

📋 OPORTUNIDAD: {lead.name}
👤 CLIENTE: {lead.partner_name or 'No especificado'}
💰 VALOR: S/ {lead.expected_revenue:,.2f}
📅 FECHA: {fields.Date.today().strftime('%d/%m/%Y')}

⚠️ Este servicio se encuentra en pleno desarrollo
   y muy pronto estará disponible para que sus
   solicitudes de cambio de estatus a GANADA lleguen
   directamente a los WhatsApp de los PMO. 🚧

🎯 PROGRESO: 85% completado
🚀 DISPONIBLE: Próxima actualización del sistema

💡 MIENTRAS TANTO:
   • Cambiar estatus manualmente a GANADA
   • Notificar al PMO vía email/Teams
   • Documentar en comentarios de oportunidad
            """
            record.message = custom_message.strip()
        
        return record