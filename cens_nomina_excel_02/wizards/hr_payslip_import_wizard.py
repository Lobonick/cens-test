from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import xlrd
import xlsxwriter
import math
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)

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
            CAMPOS_PERMITIDOS = [
                'x_studio_licencia_fallecimiento',
                'x_studio_licencia_materpater',
                'x_studio_dias_vacaciones',
                'x_studio_dias_con_goce',
                'x_studio_descanso_medico',
                'x_studio_feriados_dias',
                'x_studio_bonificacion_extraordinaria',
                'x_studio_horas_extras_importe',
                'x_studio_descanso_vacacional',
                'x_studio_reembolso_movilidad',
                'x_studio_reembolso_combustible',
                'x_studio_adelanto_gratificacion',
                'x_studio_descuento_inasistencias',
                'x_studio_dias_sin_goce',
                'x_studio_adelanto_sueldo',
                'x_studio_descuento_tardanzas_min',
                'x_studio_retencion_judicial',
                'x_studio_descuento_prestamos'
            ]

            def tiene_valor_xlsx(valor, field_type):
                """
                Verifica si la celda del XLSX tiene un valor válido para asignar
                Retorna True si tiene valor válido, False si está vacía/inválida
                """
                # Para campos numéricos
                if field_type in ['integer', 'float', 'monetary']:
                    if isinstance(valor, (int, float)):
                        return valor > 0
                    if isinstance(valor, str):
                        try:
                            num_val = float(valor.strip())
                            return num_val > 0
                        except (ValueError, AttributeError):
                            return False
                    return False
                
                # Para campos de texto
                elif field_type in ['char', 'text']:
                    if isinstance(valor, str):
                        return valor.strip() != ''
                    return str(valor).strip() != '' if valor is not None else False
                
                # Para campos booleanos
                elif field_type == 'boolean':
                    return isinstance(valor, bool)
                
                # Para campos de fecha
                elif field_type in ['date', 'datetime']:
                    return valor is not None and valor != ''
                
                # Para campos many2one
                elif field_type == 'many2one':
                    if isinstance(valor, int):
                        return valor > 0
                    return False
                
                # Para otros tipos
                else:
                    return valor is not None and valor != ''

            def campo_vacio_en_bd(valor_bd, field_type):
                """
                Verifica si el campo en la BD está vacío/cero y puede ser actualizado
                Retorna True si está vacío y puede actualizarse, False si ya tiene datos
                """
                # Para campos numéricos
                if field_type in ['integer', 'float', 'monetary']:
                    return valor_bd is None or valor_bd == 0 or valor_bd == 0.0
                
                # Para campos de texto
                elif field_type in ['char', 'text']:
                    return valor_bd is None or valor_bd == '' or (isinstance(valor_bd, str) and valor_bd.strip() == '')
                
                # Para campos booleanos
                elif field_type == 'boolean':
                    return valor_bd is None or valor_bd == False
                
                # Para campos de fecha
                elif field_type in ['date', 'datetime']:
                    return valor_bd is None or valor_bd == False
                
                # Para campos many2one
                elif field_type == 'many2one':
                    return valor_bd is None or valor_bd == False
                
                # Para otros tipos
                else:
                    return valor_bd is None or valor_bd == False

            # ---------------------------------------------------------
            # ENTRAE CAMPOS DEL XLSX Y ACTUALIZA MODELO (hr.payslip)
            # ---------------------------------------------------------
            for row in range(9, sheet_nomina.nrows):
                try:
                    record_id = int(sheet_nomina.cell_value(row, headers_nomina.index('id')))
                    payslip = self.env['hr.payslip'].browse(record_id)        
                    
                    if not payslip.exists():
                        _logger.warning(f'No se encontró la nómina con ID: {record_id}')
                        continue

                    # Preparar valores a actualizar
                    values_to_update = {}
                    campos_procesados = 0
                    campos_actualizados = 0
                    
                    for col, header in enumerate(headers_nomina):
                        # Solo procesar campos permitidos (excluir 'id')
                        if header == 'id' or header not in CAMPOS_PERMITIDOS:
                            continue
                        
                        # Verificar que el campo existe en el modelo
                        if header not in payslip._fields:
                            _logger.warning(f'Campo {header} no existe en el modelo hr.payslip')
                            continue
                        
                        campos_procesados += 1
                        
                        # Obtener valor del XLSX
                        valor_xlsx = sheet_nomina.cell_value(row, col)
                        
                        # Obtener tipo de campo y valor actual en BD
                        field_type = payslip._fields[header].type
                        valor_actual_bd = getattr(payslip, header, None)
                        
                        _logger.debug(f'Procesando campo: {header}')
                        _logger.debug(f'  - Tipo: {field_type}')
                        _logger.debug(f'  - Valor XLSX: {valor_xlsx} (tipo: {type(valor_xlsx)})')
                        _logger.debug(f'  - Valor BD: {valor_actual_bd}')
                        
                        # Convertir tipos de datos según el campo (solo si es necesario)
                        valor_procesado = valor_xlsx
                        if field_type == 'many2one' and isinstance(valor_xlsx, str) and valor_xlsx.strip():
                            # Buscar el registro relacionado por nombre
                            related_model = payslip._fields[header].comodel_name
                            related_record = self.env[related_model].search(
                                [('name', '=', valor_xlsx.strip())], limit=1
                            )
                            if related_record:
                                valor_procesado = related_record.id
                            else:
                                _logger.warning(f'No se encontró registro {related_model} con nombre: {valor_xlsx}')
                                continue
                                
                        elif field_type == 'date' and isinstance(valor_xlsx, (int, float)):
                            try:
                                valor_procesado = xlrd.xldate.xldate_as_datetime(
                                    valor_xlsx, book.datemode
                                ).date()
                            except Exception as e:
                                _logger.error(f'Error convirtiendo fecha en {header}: {e}')
                                continue
                        
                        # VALIDACIÓN PRINCIPAL: Solo actualizar si cumple ambas condiciones
                        tiene_valor_valido = tiene_valor_xlsx(valor_procesado, field_type)
                        campo_esta_vacio = campo_vacio_en_bd(valor_actual_bd, field_type)
                        
                        if tiene_valor_valido and campo_esta_vacio:
                            values_to_update[header] = valor_procesado
                            campos_actualizados += 1
                            
                            _logger.info(f'✅ ACTUALIZARÁ {header}: "{valor_actual_bd}" -> "{valor_procesado}"')
                        else:
                            if not tiene_valor_valido:
                                _logger.debug(f'⚠️  {header}: Valor XLSX inválido/vacío ({valor_xlsx})')
                            if not campo_esta_vacio:
                                _logger.debug(f'⚠️  {header}: Campo BD ya tiene datos ({valor_actual_bd})')

                    # Actualizar registro solo si hay cambios
                    if values_to_update:
                        try:
                            payslip.write(values_to_update)
                            self.env.cr.commit()
                            
                            _logger.info(f'✅ ACTUALIZADO payslip ID {record_id} (fila {row}):')
                            _logger.info(f'   - Campos procesados: {campos_procesados}')
                            _logger.info(f'   - Campos actualizados: {campos_actualizados}')
                            _logger.info(f'   - Campos: {list(values_to_update.keys())}')
                            
                        except Exception as e:
                            self.env.cr.rollback()
                            _logger.error(f'❌ Error actualizando payslip ID {record_id}: {e}')
                            raise UserError(f'Error actualizando registro {record_id}: {str(e)}')
                    else:
                        _logger.info(f'ℹ️  Payslip ID {record_id} (fila {row}): Sin cambios - {campos_procesados} campos procesados')
                        
                except Exception as e:
                    _logger.error(f'❌ Error procesando fila {row}: {e}')
                    continue

            _logger.info('🎉 Procesamiento de XLSX completado')

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
                                _logger.info(f'Actualizado registro ID {w_ocurren_id} para nómina {w_record_id}')
                            else:
                                # Crear nuevo registro
                                nuevo_registro = one2many_obj.create(valores)
                                _logger.info(f'Creado nuevo registro ID {nuevo_registro.id} para nómina {w_record_id}')
                        else:
                            # Crear nuevo registro
                            one2many_obj = self.env['x_hr_payslip_line_b90e1']
                            nuevo_registro = one2many_obj.create(valores)
                            _logger.info(f'Creado nuevo registro ID {nuevo_registro.id} para nómina {w_record_id}')

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
                    _logger.info(f'Nómina ID {w_record_id}: campo x_studio_en_recalcular actualizado de {valor_actual} a {nuevo_valor}')

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








            # =============================================================================
            # WorkSheet: NÓMINA
            # =============================================================================
            # for row in range(9, sheet_nomina.nrows):
            #     record_id = int(sheet_nomina.cell_value(row, headers_nomina.index('id')))
            #     payslip = self.env['hr.payslip'].browse(record_id)        
                
            #     if not payslip.exists():
            #         raise UserError(_('No se encontró la nómina con ID: %s') % record_id)

            #     # Preparar valores a actualizar
            #     values = {}
            #     for col, header in enumerate(headers_nomina):
            #         if header != 'id' and header in payslip._fields:
            #             value = sheet_nomina.cell_value(row, col)
            #             field_type = payslip._fields[header].type
            #             field_valu = getattr(payslip, header)
                        
            #             # Convertir tipos de datos según el campo
            #             if field_type == 'many2one':
            #                 # Buscar el registro relacionado por nombre
            #                 related_model = payslip._fields[header].comodel_name
            #                 related_record = self.env[related_model].search(
            #                     [('name', '=', value)], limit=1
            #                 )
            #                 if related_record:
            #                     value = related_record.id
            #             elif field_type == 'date':
            #                 # Convertir fecha de Excel a formato Odoo
            #                 value = xlrd.xldate.xldate_as_datetime(
            #                     value, book.datemode
            #                 ).date()
                        
            #             # values[header] = value

            #             # =============================================================================
            #             # VALIDACIÓN DE VALORES ANTES DE ASIGNACIÓN
            #             # =============================================================================
            #             def existe_valor(val, field_type):
            #                 """
            #                 Función para determinar si un valor es válido para asignación
            #                 Retorna True si el valor es válido, False si debe ser ignorado
            #                 """
            #                 # Para campos numéricos (int, float, monetary)
            #                 w_result = False
            #                 if field_type in ['integer', 'float', 'monetary']:
            #                     # Verificar si es número y mayor que 0
            #                     if isinstance(val, (int, float)):
            #                         return val > 0
            #                     # Si es string, intentar convertir
            #                     if isinstance(val, str):
            #                         try:
            #                             num_val = float(val)
            #                             return num_val > 0
            #                         except ValueError:
            #                             return False
            #                     return False
                            
            #                 # Para campos de texto (char, text)
            #                 elif field_type in ['char', 'text']:
            #                     # Verificar si es string no vacío
            #                     if isinstance(val, str):
            #                         return val.strip() != ''
            #                     # Si no es string, convertir y verificar
            #                     return str(val).strip() != ''
                            
            #                 # Para campos booleanos
            #                 elif field_type == 'boolean':
            #                     return not isinstance(val, bool)
                            
            #                 # Para campos de fecha
            #                 elif field_type in ['date', 'datetime']:
            #                     return False
                            
            #                 # Para campos many2one
            #                 elif field_type == 'many2one':
            #                     # Verificar si es un ID válido (mayor que 0)
            #                     if isinstance(val, int):
            #                         return val > 0
            #                     return False
                            
            #                 # Para otros tipos de campo, aceptar cualquier valor no nulo
            #                 else:
            #                     return False

            #             if existe_valor(value, field_type):
            #                 if not existe_valor(field_valu, field_type):
            #                     values[header] = value
            #                     _logger.info(f"ACTUALIZA Valor Existente = {values[header]} por Valor Nuevo = {value}, tipo {field_type} Valor Campo = {field_valu}   ")

            #     # Actualizar registro
            #     # payslip.write(values)
            
            #     # Registrar valores para depuración
            #     _logger.info(f"QUIQUE, actualiza regist ID: {record_id} en fila: {row} con valores: {values}")
                
            #     # Actualizar registro usando método write con COMMIT inmediato
            #     payslip.write(values)
            #     self.env.cr.commit()

