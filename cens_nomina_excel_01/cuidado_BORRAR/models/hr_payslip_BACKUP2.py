from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_send_payslip_email(self):
        # ---------------------------------------------------------------
        # Método para enviar las boletas por correo electrónico
        # Genera los PDFs de las boletas de pago y los envía por correo.
        # ---------------------------------------------------------------

        template = self.env.ref('email_template_payslip_mass_send', raise_if_not_found=False)

        if not template:
            _logger.error("No se encontró la plantilla de correo para boletas de pago.")

        #w_lote = self.browse(self._context.get('active_ids', []))
        w_lote = self.browse(self._context.get('active_ids', []))

        for payslip in w_lote:
            pdf_content, _ = self.env.ref('hr_payroll.action_report_payslip')._render_qweb_pdf([payslip.id])

            attachment = self.env['ir.attachment'].create({
                'name': f'Boleta_{payslip.employee_id.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'mimetype': 'application/pdf'
            })

            email_values = {
                'email_to': payslip.employee_id.work_email,
                'email_from': self.env.user.email or 'no-reply@cens.com.pe.com',
                'attachment_ids': [(4, attachment.id)]
            }
            template.send_mail(payslip.id, email_values=email_values, force_send=True)

        return True