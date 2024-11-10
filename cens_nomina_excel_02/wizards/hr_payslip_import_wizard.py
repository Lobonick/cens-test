from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
import xlrd
import xlsxwriter
from io import BytesIO

class HrPayslipImportWizard(models.TransientModel):
    _name = 'hr.payslip.import.wizard'
    _description = 'Asistente de importación de nóminas'

    xlsx_file = fields.Binary(string='Archivo XLSX', required=True)
    filename = fields.Char(string='Nombre del archivo')

    def action_import(self):
        if not self.xlsx_file:
            raise UserError(_('Por favor seleccione un archivo XLSX'))

        try:
            # Leer archivo Excel
            xlsx_data = base64.b64decode(self.xlsx_file)
            book = xlrd.open_workbook(file_contents=xlsx_data)
            sheet = book.sheet_by_index(0)

            # Obtener encabezados
            headers = [str(sheet.cell_value(0, col)) for col in range(sheet.ncols)]

            # Validar estructura del archivo
            required_fields = ['id']
            if not all(field in headers for field in required_fields):
                raise UserError(_('El archivo debe contener la columna ID'))

            # Procesar cada fila
            for row in range(1, sheet.nrows):
                record_id = int(sheet.cell_value(row, headers.index('id')))
                payslip = self.env['hr.payroll'].browse(record_id)
                
                if not payslip.exists():
                    raise UserError(_('No se encontró la nómina con ID: %s') % record_id)

                # Preparar valores a actualizar
                values = {}
                for col, header in enumerate(headers):
                    if header != 'id' and header in payslip._fields:
                        value = sheet.cell_value(row, col)
                        field_type = payslip._fields[header].type
                        
                        # Convertir tipos de datos según el campo
                        if field_type == 'many2one':
                            # Buscar el registro relacionado por nombre
                            related_model = payslip._fields[header].comodel_name
                            related_record = self.env[related_model].search(
                                [('name', '=', value)], limit=1
                            )
                            if related_record:
                                value = related_record.id
                        elif field_type == 'date':
                            # Convertir fecha de Excel a formato Odoo
                            value = xlrd.xldate.xldate_as_datetime(
                                value, book.datemode
                            ).date()
                        
                        values[header] = value

                # Actualizar registro
                payslip.write(values)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Importación completada correctamente'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError(_('Error al procesar el archivo: %s') % str(e))
