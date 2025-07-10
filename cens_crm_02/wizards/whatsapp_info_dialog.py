from odoo import models, fields, api, _
import base64
import os

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
        default='whatsapp-logo.jpg',
        readonly=True
    )
    
    # Campo para título personalizado
    dialog_title = fields.Char(
        string='Título',
        default='🚧 Servicio en Desarrollo',
        readonly=True
    )
    
    def _get_default_whatsapp_image(self):
        """Cargar imagen JPG desde el módulo"""
        try:
            # Obtener la ruta del módulo actual
            module_name = 'cens_crm_02' 
            module = self.env['ir.module.module'].search([('name', '=', module_name)], limit=1)
            
            if module and module.state == 'installed':
                # Construir ruta a la imagen
                addon_path = self.env['ir.module.module'].get_module_path(module_name)
                image_path = os.path.join(addon_path, 'static', 'description', 'logo-whatsapp_03.png')
                
                # Intentar leer la imagen
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as image_file:
                        return base64.b64encode(image_file.read())
                else:
                    # Si no existe, intentar con otros nombres comunes
                    alternative_names = [
                        'logo-whatsapp_03.png',
                        'logo-whatsapp_02.png', 
                        'whatsapp-icon.jpg',
                        'whatsapp-pmo.jpg'
                    ]
                    
                    for alt_name in alternative_names:
                        alt_path = os.path.join(addon_path, 'static', 'description', alt_name)
                        if os.path.exists(alt_path):
                            with open(alt_path, 'rb') as image_file:
                                return base64.b64encode(image_file.read())
            
            # Si no se puede cargar imagen del módulo, usar una imagen por defecto
            return self._get_default_placeholder_image()
            
        except Exception as e:
            # En caso de error, usar placeholder
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