from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mail import email_split

class MailLeadComment(models.Model):
    _inherit = 'mail.message'

    cens_control_01 = fields.Integer(string='Control 01:', readonly=True, default=0, existing_field=True)
    cens_control_02 = fields.Char("Control 02:")
    
    @api.model
    def create(self, vals):
        res = super(MailLeadComment, self).create(vals)
        if self.model == 'crm.lead':
            lead = self.env['crm.lead'].browse(res.res_id)
            email_to = 'ealcantara@cens.com.pe'
            subject = f"Nuevo comentario en la oportunidad: {lead.name}"
            body = f"El usuario {self.author_id.name} ha agregado un nuevo comentario en la oportunidad: {lead.name}"
            self.env['mail.mail'].create({
                'body_html': body,
                'subject': subject,
                'email_to': email_to,
                'auto_delete': True
            }).send()
        return res