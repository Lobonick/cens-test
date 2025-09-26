from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import base64
import xlrd
import openpyxl
from io import BytesIO
import io
from odoo.exceptions import UserError


class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'
    cens_ingreso_laboral = fields.Date(string='Ingreso Laboral')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Sobrescribe fields_view_get para inicializar el campo al abrir el formulario"""
        res = super(HrEmployeeCustom, self).fields_view_get(view_id=view_id, view_type=view_type, 
                                                           toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            # Obtener el registro actual y actualizar si es necesario
            if self._context.get('active_id'):
                employee = self.browse(self._context['active_id'])
                if employee and not employee.cens_ingreso_laboral and employee.first_contract_date:
                    employee.write({'cens_ingreso_laboral': employee.first_contract_date})
        
        return res
    
    #@api.onchange('first_contract_date')
    #def _onchange_first_contract_date(self):
    #    if not self.cens_ingreso_laboral and self.first_contract_date:  # Actualiza cens_ingreso_laboral 
    #        self.cens_ingreso_laboral = self.first_contract_date        # con first_contract_date si está vacío

    #@api.model_create_multi
    #def create(self, vals_list):
    #    for vals in vals_list:
    #        if not vals.get('cens_ingreso_laboral') and vals.get('first_contract_date'):    # Sobrescribe el método create 
    #            vals['cens_ingreso_laboral'] = vals['first_contract_date']                  # para inicializar cens_ingreso_laboral
    #    return super().create(vals_list)

    
class HrLeaveExtended(models.Model):
    _inherit = 'hr.leave'

    file_data = fields.Binary("File")
    file_name = fields.Char("File Name")
     
    # -------------------------------------------------------------------------------------------------------
    # ACCION - EXPORTAR REPORTE HACIA HOJA DE CALCULO EN EXCEL (Usa librería: xlsxwriter, base64, BytesIO)
    # -------------------------------------------------------------------------------------------------------
    def export_to_spreadsheet(self):
        w_path = "user/cens_vacaciones_excel_01/report/"
        w_ruta = "/home/odoo/src/user/cens_vacaciones_excel_01/report/"
        w_file = "CENS-VACACIONES-HISTÓRICO.xlsx"
        w_erro = ""

        # Crear un buffer en memoria para almacenar el archivo
        output = BytesIO()
        
        try:
            # ANTERIOR: workbook = xlsxwriter.Workbook(w_file)
            # Crear el workbook y worksheet
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        except:
            w_erro = "ERROR ARCHIVO: " + w_ruta + w_file  
        else:
            # -------------------------------------------------------------------------------------
            # CONFIGURACIÓN GENERAL DE LA WORKSHEET
            # -------------------------------------------------------------------------------------
            workbook.set_properties({
                'title':    'VACACIONES-CENS - Hoja de Trabajo',
                'subject':  'Extracto a la fecha',
                'author':   'ODOO-CENS',
                'manager':  'Gestión Humana',
                'company':  'CENS PERÚ',
                'category': 'LOTE - EXCEL',
                'keywords': 'nómina, lote, worksheet',
                'created':  datetime.now(),
                'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})
            worksheet = workbook.add_worksheet("DATA-CENS")
            cell_format = workbook.add_format()
            # w_formato_colorfondo = workbook.add_format({'bg_color': '#DDD9C4'})
            cell_format_empr = workbook.add_format({'bold': True})
            cell_format_cabe = workbook.add_format()
            cell_format_tuti = workbook.add_format()
            cell_format_tut2 = workbook.add_format()
            cell_format_titu = workbook.add_format()
            # ------
            cell_format_nume = workbook.add_format()
            cell_format_nume.set_num_format('#,##0')
            cell_format_nume.set_align('center')
            cell_format_nume.set_align('vcenter')
            # ------
            cell_format_impo = workbook.add_format()
            cell_format_impo.set_num_format('#,##0.00')
            cell_format_impo.set_align('vcenter')
            # ------
            cell_format_tcam = workbook.add_format()
            cell_format_tcam.set_num_format('##0.000')
            cell_format_tcam.set_align('vcenter')
            # ------
            cell_format_cent = workbook.add_format()
            cell_format_cent.set_align('center')
            cell_format_cent.set_align('vcenter')
            cell_format_cent.set_text_wrap()
            # ------
            cell_format_tiny = workbook.add_format()
            cell_format_tiny.set_align('center')
            cell_format_tiny.set_align('vcenter')
            cell_format_tiny.set_text_wrap()
            cell_format_tiny.set_font_size(8)
            # ------
            cell_format_left = workbook.add_format()
            cell_format_left.set_align('vcenter')
            # ------
            cell_format_porc = workbook.add_format()
            cell_format_porc = workbook.add_format({'num_format': '0%'})
            cell_format_porc.set_align('center')
            cell_format_porc.set_align('vcenter')
            # ------
            cell_format_xcen = workbook.add_format()
            cell_format_xcen = workbook.add_format({'num_format': '0.00%'})
            cell_format_xcen.set_align('center')
            cell_format_xcen.set_align('vcenter')
            # ------
            cell_format_fech = workbook.add_format()
            cell_format_fech.set_num_format('dd/mm/yyyy')
            cell_format_fech.set_align('center')
            cell_format_fech.set_align('vcenter')
            # ------
            cell_format_verd = workbook.add_format()
            cell_format_verd.set_font_color('white')
            cell_format_verd.set_bg_color('#30C381')    ##--- Semáforo en VERDE
            cell_format_verd.set_align('center')
            cell_format_verd.set_align('vcenter')
            # ------
            cell_format_rojo = workbook.add_format()
            cell_format_rojo.set_font_color('white')
            cell_format_rojo.set_bg_color('#ff0026')    ##--- Semáforo en ROJO
            cell_format_rojo.set_align('center')
            cell_format_rojo.set_align('vcenter')
            # ------
            cell_format_amba = workbook.add_format()
            cell_format_amba.set_font_color('black')
            cell_format_amba.set_bg_color('#ffa600')    ##--- Semáforo en AMBAR
            cell_format_amba.set_align('center')
            cell_format_amba.set_align('vcenter')
            # ------
            cell_format_perd = workbook.add_format()
            cell_format_perd.set_font_color('red')        ##--- Motivo de la Pérdida
            cell_format_perd.set_align('vcenter')
            cell_format_perd.set_text_wrap()
            # ------                                (ColIni,ColFin,Ancho) --- AJUSTA EL ANCHO DE LAS COLUMNAS
            worksheet.set_column(0, 0, 9)       #-- Ord
            worksheet.set_column(1, 1, 33)      #-- Npombre del Empleado
            worksheet.set_column(2, 2, 13)      #-- DNI
            worksheet.set_column(3, 3, 15)      #-- CARGO
            worksheet.set_column(4, 4, 15)      #-- FECHA INGRESO
            worksheet.set_column(5, 5, 23)      #-- UNIDAD DE NEGOCIO
            worksheet.set_column(6, 6, 13)      #-- 1
            worksheet.set_column(7, 7, 13)      #-- 2
            worksheet.set_column(8, 8, 13)      #-- 3
            worksheet.set_column(9, 9, 13)      #-- 4
            worksheet.set_column(10, 10, 13)     #-- 5
            worksheet.set_column(11, 11, 13)    #-- CODIGO AUSENCIA
            worksheet.set_column(12, 12, 15)    #-- PERIODO
            worksheet.set_column(13, 13, 15)    #-- FECHA INICIAL
            worksheet.set_column(14, 14, 15)    #-- FECHA FINAL
            worksheet.set_column(15, 15, 8)     #-- NRO DE DÍAS
            worksheet.set_column(16, 16, 15)    #-- ESTATUS
            worksheet.set_column(17, 17, 40)    #-- COMENTARIOS
            worksheet.set_column(18, 18, 20)    #-- Creado Por
            worksheet.set_column(19, 19, 15)    #-- Creado En
            # ------
            worksheet.set_row(6, 39)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A1', 'src/user/cens_vacaciones_excel_01/static/description/logo-tiny_96.png')
            worksheet.insert_image('S2', 'src/user/cens_vacaciones_excel_01/static/description/logo-odoo-tiny.png', 
                                         {'x_scale': 0.6, 'y_scale': 0.6})
            worksheet.write('B2', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B3', 'Gestión Humana - Nóminas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)
            worksheet.write('H4', 'HISTÓRICO DE VACACIONES - EMPLEADOS CENS', cell_format_cabe)
            # ------
            worksheet.write('A5', 'FECHA:')
            worksheet.write('B5', datetime.now(), cell_format_fech)
            #-----
            worksheet.write('A6', 'USUARIO:')
            w_usuario_actual = self.env.context.get("uid")
            usuario_actual = self.env['res.users'].browse(w_usuario_actual)
            w_usuario_names = usuario_actual.name
            worksheet.write('B6', w_usuario_names)
            #-----
            merge_format = workbook.add_format({'align': 'center'})
            worksheet.merge_range('G6:K6', 'Merged Cells', merge_format)
            worksheet.write('G6', 'CÁLCULO ACUMULADO', cell_format_tut2)

            worksheet.merge_range('L6:R6', 'Merged Cells', merge_format)
            worksheet.write('L6', 'PERIODOS GOZADOS', cell_format_tuti)

            worksheet.merge_range('S6:T6', 'Merged Cells', merge_format)
            worksheet.write('S6', 'DEL REGISTRO', cell_format_tut2)
            # -------------------------------------------------------------------------------------
            # BARRA DE TITULOS
            # -------------------------------------------------------------------------------------
            cell_format_tuti.set_font_name('Arial')
            cell_format_tuti.set_font_color('black')
            cell_format_tuti.set_font_size(8)
            cell_format_tuti.set_text_wrap()                 # FORMATO TÍTULO - COLUMNAS IMPORTES #B7DEE8
            cell_format_tuti.set_bg_color('#92CDDC')
            cell_format_tuti.set_align('center')
            cell_format_tuti.set_align('vcenter')
            #-----
            cell_format_tut2.set_font_name('Arial')
            cell_format_tut2.set_font_color('black')
            cell_format_tut2.set_font_size(8)
            cell_format_tut2.set_text_wrap()                 # FORMATO TÍTULO 2 - COLUMNAS IMPORTES #B7DEE8
            cell_format_tut2.set_bg_color('#B7DEE8')
            cell_format_tut2.set_align('center')
            cell_format_tut2.set_align('vcenter')
            #-----
            cell_format_titu.set_font_name('Arial')
            cell_format_titu.set_font_color('white')
            cell_format_titu.set_font_size(8)
            cell_format_titu.set_text_wrap()                 # FORMATO TÍTULO - TODA LA BARRA
            cell_format_titu.set_bg_color('#31869B')
            cell_format_titu.set_align('center')
            cell_format_titu.set_align('vcenter')
            #-----
            #worksheet.set_row(7, 7)
            #worksheet.set_column('A:M', 7)
            worksheet.write('A7', 'ORD', cell_format_titu)                                  #-- 00
            worksheet.write('B7', 'NOMBRE DEL EMPLEADO', cell_format_titu)                  #-- 01
            worksheet.write('C7', 'D.N.I.', cell_format_titu)                               #-- 02
            worksheet.write('D7', 'CARGO', cell_format_titu)                                #-- 03
            worksheet.write('E7', 'FECHA INICIO LABORAL', cell_format_titu)                 #-- 04
            worksheet.write('F7', 'UNIDAD DE NEGOCIO', cell_format_titu)
            worksheet.write('G7', 'Total dias vacaciones acumuladas', cell_format_titu)     #-- 06
            worksheet.write('H7', 'Días Vacaciones Gozadas', cell_format_titu)              #-- 07
            worksheet.write('I7', 'Días vacaciones acumuladas truncas', cell_format_titu)   #-- 08
            worksheet.write('J7', 'Días Vacaciones pendientes', cell_format_titu)           #-- 09
            worksheet.write('K7', 'Total días Vacaciones Vencidas', cell_format_titu)       #-- 10
            worksheet.write('L7', 'CÓDIGO', cell_format_titu)                               #-- 11
            worksheet.write('M7', 'PERIODO', cell_format_titu)                              #-- 12
            worksheet.write('N7', 'FECHA INICIAL', cell_format_titu)                        #-- 13
            worksheet.write('O7', 'FECHA FINAL', cell_format_titu)                          #-- 14
            worksheet.write('P7', 'TOTAL DÍAS', cell_format_titu)                           #-- 15
            worksheet.write('Q7', 'ESTADO', cell_format_titu)                               #-- 16
            worksheet.write('R7', 'COMENTARIOS', cell_format_titu)                          #-- 17
            worksheet.write('S7', 'CREADO POR', cell_format_tuti)                          #-- 18
            worksheet.write('T7', 'CREADO EN', cell_format_tuti)                          #-- 19
            worksheet.freeze_panes(7, 6)    # (fil,col)

            # -------------------------------------------------------------------------------------
            # CUERPO PRINCIPAL DEL REPORTE
            # -------------------------------------------------------------------------------------
            # Obtener los registros seleccionados
            w_lote = self.browse(self._context.get('active_ids', []))
            
            # Ordenar los registros por employee_id
            # sorted_leaves = w_lote.sorted(key=lambda r: r.employee_id.id)
            sorted_leaves = w_lote.sorted(key=lambda r: r.employee_id.name)
            
            # Inicializar variables
            current_employee = None
            counter = 0
            w_dato = ""
            w_fila = 7
            w_nord = 0
            w_agrupa_ausencias = []
            base_color = '#DDD9C4'
            # w_tipo = leave.holiday_type

            # ------------------------------------------------------
            # PROCESA CADA REGISTRO SELECCIONADO EN EL LIST-TREE
            # ------------------------------------------------------
            for leave in sorted_leaves:
                # ------------------------------
                # HABILITA DATOS DEL EMPLEADO
                # ------------------------------
                if current_employee != leave.employee_id:
                    if current_employee:
                        # Ordenar la lista por ausencia_periodo
                        w_agrupa_ausencias_ordenada = sorted(w_agrupa_ausencias, key=lambda x: x['ausencia_periodo'])

                        # ---------------------------------------------
                        # IMPRIME AUSENCIAS ACUMULADAS EN LA MATRIZ
                        # ---------------------------------------------
                        w_actual = None
                        w_switch = 1
                        for ausencia in w_agrupa_ausencias_ordenada:
                            if not w_actual == ausencia['ausencia_periodo'] :
                                w_actual = ausencia['ausencia_periodo']
                                w_switch = (1 if w_switch == 0 else 0)
                            
                            worksheet.write(w_fila, 11, ausencia['ausencia_codigo'], cell_format_tiny)
                            worksheet.write(w_fila, 12, ausencia['ausencia_periodo'], cell_format_cent)
                            worksheet.write(w_fila, 13, ausencia['ausencia_desde'] if self.estatus_ausencia(ausencia['ausencia_state'])=="Aprobado" else '01/01/1900', cell_format_fech)
                            worksheet.write(w_fila, 14, ausencia['ausencia_hasta'] if self.estatus_ausencia(ausencia['ausencia_state'])=="Aprobado" else '01/01/1900', cell_format_fech)
                            worksheet.write(w_fila, 15, ausencia['ausencia_numdias'], cell_format_nume)
                            worksheet.write(w_fila, 16, self.estatus_ausencia(ausencia['ausencia_state']), cell_format_perd if ausencia['ausencia_state'] == 'refuse' else cell_format_left)
                            if ausencia['ausencia_comenta']:
                                worksheet.write(w_fila, 17, ausencia['ausencia_comenta'], cell_format_left)
                            worksheet.write(w_fila, 18, ausencia['ausencia_creadopor'], cell_format_left)
                            worksheet.write(w_fila, 19, ausencia['ausencia_creadoen'], cell_format_fech)
                            # ----------------------------------
                            # Colorea el Background de la fila
                            # ----------------------------------
                            if (w_nord % 2 == 0):  
                                w_formato_colorfila = workbook.add_format({'bg_color': '#EBF1DE',})
                            else:
                                w_formato_colorfila = workbook.add_format({'bg_color': '#D8E4BC'})

                            worksheet.conditional_format(f'A{w_fila+1}:J{w_fila+1}', {
                                    'type': 'formula',
                                    'criteria': f'NOT(ISBLANK($M${w_fila}))',  # Evalúa si M no está vacía #D8E4BC
                                    'format': w_formato_colorfila
                                })
                            
                            w_formato_colorfuente1 = workbook.add_format({'bg_color': '#EBF1DE' if (w_nord % 2 == 0) else '#D8E4BC',
                                                                             'font_color': '#E26B0A'})
                            w_formato_colorfuente2 = workbook.add_format({'bg_color': '#EBF1DE' if (w_nord % 2 == 0) else '#D8E4BC',
                                                                             'font_color': '#963634'})
                            
                            worksheet.conditional_format(f'K{w_fila+1}:T{w_fila+1}', {
                                    'type': 'formula',
                                    'criteria': f'NOT(ISBLANK($M${w_fila}))',  # Evalúa si M no está vacía
                                    'format': w_formato_colorfuente1 if w_switch == 0 else w_formato_colorfuente2
                                })


                            w_fila += 1

                    # ------------------------------------
                    # DATOS DEL NUEVO EMPLEADO DE LA LISTA
                    # ------------------------------------    
                    w_nord += 1
                    # Reiniciar contador para nuevo empleado
                    worksheet.write(w_fila, 0, w_nord, cell_format_cent)   
                    worksheet.write(w_fila, 1, leave.employee_id.name, cell_format_left)
                    worksheet.write(w_fila, 2, leave.employee_id.x_studio_documento_identidad, cell_format_cent)
                    if (leave.employee_id.job_id.name):
                        worksheet.write(w_fila, 3, leave.employee_id.job_id.name, cell_format_cent)
                    if leave.employee_id.first_contract_date :
                        worksheet.write(w_fila, 4, leave.employee_id.first_contract_date, cell_format_fech)
                    if leave.employee_id.x_studio_negocio_unidad.x_name :
                        w_dato = leave.employee_id.x_studio_negocio_unidad.x_name
                        worksheet.write(w_fila, 5, w_dato, cell_format_fech)
                       
                    current_employee = leave.employee_id
                    counter = 1
                    w_agrupa_ausencias = []
                else:
                    # Incrementar contador para el empleado actual
                    counter += 1

                # ----------------------------------------
                # Captura en Matriz la Ausencia
                # ----------------------------------------
                if current_employee:
                    if self.estatus_ausencia(leave.state)=="Aprobado":
                        w_dato = f"{leave.request_date_from.year-1}-{leave.request_date_from.year}"
                    else:
                        w_dato = "NONE"
                    w_agrupa_ausencias.append({
                            'ausencia_codigo' : leave.x_cens_codiden,
                            'ausencia_periodo': w_dato,
                            'ausencia_desde'  : leave.request_date_from,
                            'ausencia_hasta'  : leave.request_date_to,
                            'ausencia_numdias': leave.number_of_days,
                            'ausencia_state'  : leave.state,
                            'ausencia_comenta': leave.name,
                            'ausencia_creadopor': leave.create_uid.name,
                            'ausencia_creadoen' : leave.create_date
                    })
                    # 'ausencia_periodo': f"{leave.request_date_from.year-1}-{leave.request_date_from.year}",
            # ------------------------------------------------------
            # IMPRIME LO ÚLTIMO DE LA LISTA
            # ------------------------------------------------------
            # Ordenar la lista por ausencia_periodo
            w_agrupa_ausencias_ordenada = sorted(w_agrupa_ausencias, key=lambda x: x['ausencia_periodo'])

            # ---------------------------------------------
            # IMPRIME AUSENCIAS ACUMULADAS EN LA MATRIZ
            # ---------------------------------------------
            w_actual = None
            w_switch = 1
            for ausencia in w_agrupa_ausencias_ordenada:
                if not w_actual == ausencia['ausencia_periodo'] :
                    w_actual = ausencia['ausencia_periodo']
                    w_switch = (1 if w_switch == 0 else 0)
                
                worksheet.write(w_fila, 11, ausencia['ausencia_codigo'], cell_format_tiny)
                worksheet.write(w_fila, 12, ausencia['ausencia_periodo'], cell_format_cent)
                worksheet.write(w_fila, 13, ausencia['ausencia_desde'] if self.estatus_ausencia(ausencia['ausencia_state'])=="Aprobado" else '01/01/1900', cell_format_fech)
                worksheet.write(w_fila, 14, ausencia['ausencia_hasta'] if self.estatus_ausencia(ausencia['ausencia_state'])=="Aprobado" else '01/01/1900', cell_format_fech)
                worksheet.write(w_fila, 15, ausencia['ausencia_numdias'], cell_format_nume)
                worksheet.write(w_fila, 16, self.estatus_ausencia(ausencia['ausencia_state']), cell_format_perd if ausencia['ausencia_state'] == 'refuse' else cell_format_left)
                if ausencia['ausencia_comenta']:
                    worksheet.write(w_fila, 17, ausencia['ausencia_comenta'], cell_format_left)
                worksheet.write(w_fila, 18, ausencia['ausencia_creadopor'], cell_format_left)
                worksheet.write(w_fila, 19, ausencia['ausencia_creadoen'], cell_format_fech)

                # ----------------------------------
                # Colorea el Background de la fila
                # ----------------------------------
                if (w_nord % 2 == 0):  
                    w_formato_colorfila = workbook.add_format({'bg_color': '#EBF1DE',})
                else:
                    w_formato_colorfila = workbook.add_format({'bg_color': '#D8E4BC'})

                worksheet.conditional_format(f'A{w_fila+1}:J{w_fila+1}', {
                        'type': 'formula',
                        'criteria': f'NOT(ISBLANK($M${w_fila}))',  # Evalúa si M no está vacía #D8E4BC
                        'format': w_formato_colorfila
                    })
                
                w_formato_colorfuente1 = workbook.add_format({'bg_color': '#EBF1DE' if (w_nord % 2 == 0) else '#D8E4BC',
                                                                    'font_color': '#E26B0A'})
                w_formato_colorfuente2 = workbook.add_format({'bg_color': '#EBF1DE' if (w_nord % 2 == 0) else '#D8E4BC',
                                                                    'font_color': '#963634'})
                
                worksheet.conditional_format(f'K{w_fila+1}:T{w_fila+1}', {
                        'type': 'formula',
                        'criteria': f'NOT(ISBLANK($M${w_fila}))',  # Evalúa si M no está vacía
                        'format': w_formato_colorfuente1 if w_switch == 0 else w_formato_colorfuente2
                    })

            worksheet.activate()
            workbook.close()

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Obtener los datos binarios del archivo 
        # -------------------------------------------------------------------------------------
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Crear un registro temporal para almacenar el archivo 
        # -------------------------------------------------------------------------------------
        attachment = self.env['ir.attachment'].create({
            'name': 'CENS-HISTÓRICO-VACACIONES.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'CENS-HISTÓRICO-VACACIONES.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Devolver una acción para descargar el archivo 
        # -------------------------------------------------------------------------------------
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    @staticmethod
    def estatus_ausencia(tipo_state):
        w_resultado = ""
        if (tipo_state == 'draft'):
            w_resultado = "Por enviar"
        elif (tipo_state == 'confirm'):
            w_resultado = "Por aprobar"
        elif (tipo_state == 'refuse'):
            w_resultado = "Rechazado"
        elif (tipo_state == 'validate1'):
            w_resultado = "1ra Aprobación"
        else:
            w_resultado = "Aprobado"

        return w_resultado

    @staticmethod
    def ajustar_color_fondo(color_base, incremento):

        # Convertir color hex a RGB
        r = int(color_base[1:3], 16)
        g = int(color_base[3:5], 16)
        b = int(color_base[5:7], 16)
        
        # Ajustar cada componente RGB
        #r = max(0, min(255, r + incremento))           ESTA FUNCIÓN YA NO ES USADA
        #g = max(0, min(255, g + incremento))
        #b = max(0, min(255, b + incremento))

        # Calcular factor de ajuste (entre 0.8 y 1.2)
        factor = 1 + (incremento % 10) * 0.05
        # Ajustar manteniendo la proporción del color original
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        
        # Convertir de vuelta a hexadecimal
        return f'#{r:02x}{g:02x}{b:02x}'

    def mes_literal(self, nmes):
        w_mes = nmes
        if (w_mes == 1):
            w_mes_name = "ENE"
        elif (w_mes == 2):
            w_mes_name = "FEB"
        elif (w_mes == 3):
            w_mes_name = "MAR"
        elif (w_mes == 4):
            w_mes_name = "ABR"
        elif (w_mes == 5):
            w_mes_name = "MAY"
        elif (w_mes == 6):
            w_mes_name = "JUN"
        elif (w_mes == 7):
            w_mes_name = "JUL"
        elif (w_mes == 8):
            w_mes_name = "AGO"
        elif (w_mes == 9):
            w_mes_name = "SET"
        elif (w_mes == 10):
            w_mes_name = "OCT"
        elif (w_mes == 11):
            w_mes_name = "NOV"
        elif (w_mes == 12):
            w_mes_name = "DIC"
        else:
            w_mes_name = "ERR"
        return w_mes_name



            # ------------------------------------------
            # CAMBIA COLOR BACKGROUND DE LA FILA EXCEL
            # ------------------------------------------
 #           base_color = '#DDD9C4'
 #           if (w_fila > 7):
 #               w_fila_ini = 7   
 #               w_fila_fin = w_fila + 1  
 #               for fila in range(w_fila_ini, w_fila_fin + 1):
 #                   color_ajustado = self.ajustar_color_fondo(base_color, fila)
 #                   w_formato_colorfondo = workbook.add_format({'bg_color': color_ajustado})
 #                   worksheet.conditional_format(f'A{fila+1}:N{fila+1}', {
 #                       'type': 'formula',
 #                       'criteria': f'NOT(ISBLANK($A${fila+1}))',  # Evalúa si G no está vacía
 #                       'format': w_formato_colorfondo
 #                   })