from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_send_payslip_email(self):
        # -------------------------------------------------------
        # Método para enviar las boletas por correo electrónico
        # -------------------------------------------------------
        payslips_to_send = self.filtered(lambda p: p.state in ['draft', 'done', 'paid'])
        if not payslips_to_send:
            raise UserError('Solo se pueden enviar boletas en estado Realizado o Pagado')

        _logger.info(f'ALERTA: Encontró {len(payslips_to_send)} registros a procesar')

        # Llamar directamente al método de procesamiento
        self.with_context(async_send=True)._process_payslip_emails(payslips_to_send.ids)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Proceso iniciado',
                'message': f'Se inició el envío de {len(payslips_to_send)} boleta(s) de pago',
                'type': 'success',
                'sticky': False,
            }
        }


    @api.model
    def _process_payslip_emails(self, payslip_ids):
        #
        # Método que procesa el envío de correos
        #
        try:
            _logger.info(f'Iniciando proceso de envío para {len(payslip_ids)} boletas')
            payslips = self.browse(payslip_ids)
            
            # ------------------------------------------------------------
            # Obtener la plantilla de correo
            # ------------------------------------------------------------
            plantilla_email = self.env.ref('cens_nomina_email_masivo.email_template_payslip_mass_send', raise_if_not_found=False)
            if not plantilla_email:
                _logger.error('No se encontró la plantilla de correo para boletas')
                return False
                       
            for payslip in payslips:
                try:
                    _logger.info(f'Procesando boleta {payslip.number} para empleado {payslip.employee_id.name}')
                    
                    # ------------------------------------------------------------
                    # Verificar que el empleado tenga correo
                    # ------------------------------------------------------------
                    if not payslip.employee_id.work_email:
                        _logger.warning(f'Empleado {payslip.employee_id.name} no tiene correo configurado')
                        continue

                    # ------------------------------------------------------------
                    # Generar PDF
                    # ------------------------------------------------------------
                    report = self.env.ref('hr_payroll.action_report_payslip', raise_if_not_found=False)
                    if not report:
                        _logger.error('No se encontró el reporte de boleta de pago')
                        continue

                    _logger.info(f'Generando PDF para boleta {payslip.number}')
                    pdf_content = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report, [payslip.id])[0]
                    if not pdf_content:
                        _logger.error(f'No se pudo generar el PDF para la boleta {payslip.number}')
                        continue

                    # ------------------------------------------------------------
                    # Preparar adjunto
                    # ------------------------------------------------------------
                    _logger.info('Prepara adjunto')
                    attachment_name = f'Boleta_de_Pago_{payslip.number}.pdf'
                    attachment = self.env['ir.attachment'].create({
                        'name': attachment_name,
                        'type': 'binary',
                        'datas': base64.b64encode(pdf_content),
                        'res_model': 'hr.payslip',
                        'res_id': payslip.id,
                        'mimetype': 'application/pdf'
                    })

                    _logger.info(f'Adjunto creado: {attachment_name}')
                    
                    # ------------------------------------------------------------
                    # Enviar correo
                    # ------------------------------------------------------------
                    email_values = {
                        'email_to': payslip.employee_id.work_email,
                        'attachment_ids': [(4, attachment.id)],
                    }

                    _logger.info(f'Enviando correo a {payslip.employee_id.work_email}')
                    
                    plantilla_email.with_context(force_send=True).send_mail(
                        payslip.id,
                        email_values=email_values
                    )
                    
                    _logger.info(f'Correo enviado exitosamente para boleta {payslip.number}')
                    
                except Exception as e:
                    _logger.error(f'Error al procesar boleta {payslip.number}: {str(e)}')

        except Exception as d:
            _logger.error(f'SALTÓ Error al procesar PLANTILLA: {str(d)}')