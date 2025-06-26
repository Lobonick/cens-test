from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import xlrd
import xlsxwriter
import math
from io import BytesIO
import logging
_logging = logging.getLogger(__name__)

class HrPayslipImportWizard(models.TransientModel):
    _name = 'hr.payslip.import.wizard'
    _description = 'Asistente de importación de nóminas'

    xlsx_file = fields.Binary(string='Archivo XLSX', required=True)
    filename = fields.Char(string='Nombre del archivo')
    control1 = fields.Char(string='Control-1:')
    control2 = fields.Char(string='Control-2:')

    def action_import(self):
        if not self.xlsx_file:
            raise UserError(_('Por favor seleccione un archivo XLSX'))

        try:
            # Leer archivo Excel
            xlsx_data = base64.b64decode(self.xlsx_file)
            book = xlrd.open_workbook(file_contents=xlsx_data)
            sheet_nomina = book.sheet_by_index(0)
            sheet_horas  = book.sheet_by_index(1)

            # Obtener encabezados de cada hoja
            headers_nomina = [str(sheet_nomina.cell_value(0, col)) for col in range(sheet_nomina.ncols)]
            headers_horas = [str(sheet_horas.cell_value(0, col)) for col in range(sheet_horas.ncols)]

            # Validar estructura para cada hoja
            required_fields_nomina = ['id']
            required_fields_horas  = ['x_studio_one2many_field_CHZUj.id', 'x_studio_mes_calculado',
                                            'x_studio_one2many_field_CHZUj.x_studio_he_fecha_trabajo', 
                                            'x_studio_one2many_field_CHZUj.x_studio_he_total_horas_extras',
                                            'x_studio_one2many_field_CHZUj.x_studio_he_dia_libre',
                                            'x_studio_one2many_field_CHZUj.x_name']

            if not all(field in headers_nomina for field in required_fields_nomina):
                raise UserError(_('El archivo debe contener la columna ID'))
            
            if not all(field in headers_horas for field in required_fields_horas):
                raise UserError(_('El archivo debe contener la columna ID + x_name + x_studio_he_fecha_trabajo'))

            # =============================================================================
            # WorkSheet: NÓMINA
            # =============================================================================
            for row in range(9, sheet_nomina.nrows):
                record_id = int(sheet_nomina.cell_value(row, headers_nomina.index('id')))
                payslip = self.env['hr.payslip'].browse(record_id)        
                
                if not payslip.exists():
                    raise UserError(_('No se encontró la nómina con ID: %s') % record_id)

                # Preparar valores a actualizar
                values = {}
                for col, header in enumerate(headers_nomina):
                    if header != 'id' and header in payslip._fields:
                        value = sheet_nomina.cell_value(row, col)
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
                # payslip.write(values)
            
                # Registrar valores para depuración
                _logging.info(f"QUIQUE, actualiza regist ID: {record_id} en fila: {row} con valores: {values}")
                
                # Actualizar registro usando método write con commit inmediato
                payslip.write(values)
                self.env.cr.commit()

            # =============================================================================
            # WorkSheet: HORAS EXTRAS
            # =============================================================================
            w_boleta_id_old = sheet_horas.cell_value(9, 0) 
            w_activa_hh_ext = False
            for row in range(9, sheet_horas.nrows):
                try:
                    # ----------------------------------
                    # Obtener y validar ID de boleta
                    # ----------------------------------
                    w_boleta_id = sheet_horas.cell_value(row, 0)
                    if not w_boleta_id:
                        w_boleta_id = w_boleta_id_old
                    else:
                        w_boleta_id_old = sheet_horas.cell_value(row, 0)

                    w_record_id = int(w_boleta_id)
                    payslip = self.env['hr.payslip'].browse(w_record_id)

                    if not payslip.exists():
                        raise UserError(_('No se encontró la nómina con ID: %s') % w_record_id)

                    # ------------------------------
                    # Obtener datos de la fila
                    # ------------------------------
                    # Convertir fecha de Excel a datetime
                    fecha_excel = sheet_horas.cell_value(row, 6)
                    w_activa_hh_ext = False
                    if fecha_excel:
                        w_activa_hh_ext = True
                        dfree_excel = sheet_horas.cell_value(row, 8)
                        dfree_excel = dfree_excel.upper()
                        descr_excel = sheet_horas.cell_value(row, 9)
                        descr_excel =  descr_excel if descr_excel else "NONE"
                        if isinstance(fecha_excel, float):
                            fecha_python = xlrd.xldate.xldate_as_datetime(fecha_excel, book.datemode)
                        else:
                            fecha_python = datetime.strptime(fecha_excel, '%Y-%m-%d')
                        # ------------------------------------------------------
                        # OJO: AQUÍ RECIBE LOS DATOS DESDE WORKSHEET - QUIQUE
                        # ------------------------------------------------------
                        # Preparar valores para el registro
                        # 'x_studio_he_total_horas_extras': float(round(sheet_horas.cell_value(row, 7))),
                        valores = {
                            'x_name': descr_excel, 
                            'x_studio_he_fecha_trabajo': fecha_python.strftime('%Y-%m-%d'),
                            'x_studio_he_total_horas_extras': float(math.ceil(sheet_horas.cell_value(row, 7))),
                            'x_studio_he_dia_libre': bool(dfree_excel=='SI'),
                            'x_hr_payslip_id': w_record_id
                        }

                        # ------------------------------------------
                        # Determina datos existen o son nuevos 
                        # -----------------------------------------
                        w_ocurren_id = sheet_horas.cell_value(row, 5)  # ID Ocurrencia
                        if w_ocurren_id:
                            # Buscar si existe el registro
                            one2many_obj = self.env['x_hr_payslip_line_b90e1']
                            registro_existente = one2many_obj.browse(int(w_ocurren_id))
    
                            if registro_existente.exists():
                                # Actualizar registro existente
                                registro_existente.write(valores)
                                _logging.info(f'Actualizado registro ID {w_ocurren_id} para nómina {w_record_id}')
                            else:
                                # Crear nuevo registro
                                nuevo_registro = one2many_obj.create(valores)
                                _logging.info(f'Creado nuevo registro ID {nuevo_registro.id} para nómina {w_record_id}')
                        else:
                            # Crear nuevo registro
                            one2many_obj = self.env['x_hr_payslip_line_b90e1']
                            nuevo_registro = one2many_obj.create(valores)
                            _logging.info(f'Creado nuevo registro ID {nuevo_registro.id} para nómina {w_record_id}')

                    # ------------------------------
                    # Activa el Check del RECALCULO
                    # ------------------------------
                    # Obtener valor actual y asignar el opuesto
                    valor_actual = payslip.x_studio_en_recalcular
                    nuevo_valor = not valor_actual

                    # Actualizar el campo en el modelo
                    payslip.write({
                        'x_studio_habilitar_horas_extras': w_activa_hh_ext,
                        'x_studio_horas_extras_tipo_calculo': 'CALCU',
                        'x_studio_en_recalcular': nuevo_valor
                    })
                    _logging.info(f'Nómina ID {w_record_id}: campo x_studio_en_recalcular actualizado de {valor_actual} a {nuevo_valor}')

                except ValueError as e:
                    raise UserError(_('Error de conversión en fila %s: %s') % (row + 1, str(e)))
                except Exception as e:
                    raise UserError(_('Error procesando fila %s: %s') % (row + 1, str(e)))

                # Confirmar cambios
                self.env.cr.commit()

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




