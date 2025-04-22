from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mail import email_split


class MailMessage(models.Model):
    _inherit = 'mail.message'

    def create(self, vals):
        res = super(MailMessage, self).create(vals)
        if 'model' in vals and vals['model'] == 'crm.lead':
            res.send_lead_comment_email()
        return res

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
    # ENVIO DE COMENTARIOS EMAIL
    # ------------------------------
    def send_lead_comment_email(self):
        self.ensure_one()
        email_to = 'ealcantara@cens.com.pe'
        subject = f"Nuevo comentario en la oportunidad: {self.name}"
        body = f"El usuario {self.env.user.name} ha agregado un nuevo comentario en la oportunidad: {self.name}"
        self.env['mail.mail'].create({
            'body_html': body,
            'subject': subject,
            'email_to': email_to,
            'auto_delete': True
        }).send()


# class CRMLead(models.Model):
#    _inherit = 'crm.lead'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
#    cens_control_01 = fields.Integer(string='Control 01:', readonly=True, default=0, existing_field=True)
#    cens_control_02 = fields.Char("Control 02:")

#    @api.model
#    def create(self, vals):
#        res = super(CRMLead, self).create(vals)
#        if 'message_ids' in vals:
#            self.envia_comentario_por_email()
#        else:
#            for record in self:
#                record.cens_control_02 = "NO ENTRÓ x CREATE: "
#        return res
#
#    def write(self, vals):
#        res = super(CRMLead, self).write(vals)
#        if 'message_ids' in vals:
#            self.envia_comentario_por_email()
#        else:
#            for record in self:
#                record.cens_control_02 = "NO ENTRÓ x WRITE"
#        return res
#
#    def envia_comentario_por_email(self):
#        self.ensure_one()
#        email_to = 'ealcantara@cens.com.pe'
#        subject = f"Nuevo comentario en la oportunidad: {self.name}"
#        body = f"IMPORTANTE: El usuario {self.env.user.name} ha agregado un nuevo comentario en la oportunidad: {self.name}"
#        self.env['mail.mail'].create({
#           'body_html': body,
#            'subject': subject,
#            'email_to': email_to,
#            'auto_delete': False
#        }).send()
#

# class MailLeadComment(models.Model):
#    _inherit = 'mail.message'

#    @api.model
#    def create(self, vals):
#        res = super(MailLeadComment, self).create(vals)
#        if self.model == 'crm.lead':
#            lead = self.env['crm.lead'].browse(res.res_id)
#            email_to = 'ealcantara@cens.com.pe'
#            subject = f"Nuevo comentario en la oportunidad: {lead.name}"
#            body = f"El usuario {self.author_id.name} ha agregado un nuevo comentario en la oportunidad: {lead.name}"
#            self.env['mail.mail'].create({
#                'body_html': body,
#                'subject': subject,
#                'email_to': email_to,
#                'auto_delete': True
#            }).send()
#        return res
    

# class crm_lead_Custom(models.Model):
#     _inherit = 'crm.lead'

