from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
import xlrd
import xlsxwriter
from io import BytesIO

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def export_to_xlsx(self):
        # Crear archivo Excel en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Nóminas')

        # Definir campos a exportar
        fields_to_export = [
            'id', 'number', 'name', 'date_from', 'date_to',
            'employee_id', 'contract_id', 'struct_id', 'state'
        ]

        # Escribir encabezados
        for col, field in enumerate(fields_to_export):
            worksheet.write(0, col, field)

        # Escribir datos
        for row, record in enumerate(self, start=1):
            for col, field in enumerate(fields_to_export):
                value = record[field]
                if field in ['employee_id', 'contract_id', 'struct_id']:
                    value = value.name if value else ''
                worksheet.write(row, col, str(value))

        workbook.close()
        
        # Crear adjunto
        xlsx_data = output.getvalue()
        attachment = self.env['ir.attachment'].create({
            'name': 'nominas_export.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
        })

        # Retornar acción para descargar
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def import_from_xlsx(self):
        # Mostrar wizard de importación
        return {
            'name': _('Importar Nóminas'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
