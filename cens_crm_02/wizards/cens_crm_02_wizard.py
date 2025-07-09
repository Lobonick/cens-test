from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
from io import BytesIO
import logging
_logging = logging.getLogger(__name__)

class WhatsAppInfoDialog(models.TransientModel):
    _name = 'whatsapp.info.dialog'
    _description = 'Diálogo informativo WhatsApp PMO'
    
    message = fields.Text(string='Mensaje', readonly=True)
    lead_id = fields.Many2one('crm.lead', string='Oportunidad', readonly=True)
    
    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
    
    def action_contact_support(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': 'Consulta WhatsApp PMO',
                'default_email_to': 'sistemas@cens.com.pe'
            }
        }