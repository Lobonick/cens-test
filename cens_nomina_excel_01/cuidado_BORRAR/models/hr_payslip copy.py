from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_send_payslip_email(self):
        # --------------------------------------------------------
        # Método para enviar las boletas por correo electrónico
        # --------------------------------------------------------
        payslips_to_send = self.filtered(lambda p: p.state in ['draft', 'done', 'paid'])
        if not payslips_to_send:
            raise UserError('Solo se pueden enviar boletas en estado Realizado o Pagado')

        # Programar el envío masivo
        self.env['ir.cron'].sudo().create({
            'name': 'Envío masivo de boletas de pago',
            'model_id': self.env['ir.model'].search([('model', '=', 'hr.payslip')]).id,
            'state': 'code',
            'code': 'model._process_payslip_emails(%s)' % payslips_to_send.ids,
            'user_id': self.env.user.id,
            'interval_number': 1,
            'interval_type': 'minutes',
            'numbercall': 1,
            'doall': True,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Proceso iniciado',
                'message': f'Se programó el envío de {len(payslips_to_send)} boleta(s) de pago',
                'type': 'success',
                'sticky': False,
            }
        }

    def _process_payslip_emails(self, payslip_ids):
        """Método que procesa el envío de correos programado"""
        payslips = self.browse(payslip_ids)
        mail_template = self.env.ref('hr_payroll.mail_template_payslip')

        for payslip in payslips:
            try:
                # Generar PDF
                report = self.env.ref('hr_payroll.action_report_payslip')
                pdf_content, _ = report._render_qweb_pdf([payslip.id])
                
                # Preparar adjunto
                attachment = self.env['ir.attachment'].create({
                    'name': f'Boleta_{payslip.number}.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'hr.payslip',
                    'res_id': payslip.id,
                })

                # Enviar correo
                mail_template.send_mail(
                    payslip.id,
                    force_send=True,
                    email_values={'attachment_ids': [attachment.id]}
                )
                
                _logger.info(f'Boleta enviada exitosamente: {payslip.number}')
                
            except Exception as e:
                _logger.error(f'Error al enviar boleta {payslip.number}: {str(e)}')