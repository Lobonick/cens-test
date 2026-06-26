from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import xlrd
import xlsxwriter
from io import BytesIO

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def create(self, vals):
        """
        Sobreescribe el método create para inicializar 
        campos personalizados cuando se crea un nuevo registro
        """
        # Inicializar campos de proyectos si no están presentes
        for field in [
            'x_cens_proy1_codig', 'x_cens_proy2_codig', 'x_cens_proy3_codig',
            'x_cens_proy4_codig', 'x_cens_proy5_codig', 'x_cens_proyt_total'
        ]:
            if field not in vals:
                vals[field] = ''
        
        for field in [
            'x_cens_proy1_parti', 'x_cens_proy2_parti', 'x_cens_proy3_parti',
            'x_cens_proy4_parti', 'x_cens_proy5_parti'
        ]:
            if field not in vals:
                vals[field] = 0.00
        
        return super(HrPayslip, self).create(vals)


    def export_to_xlsx(self):
        # Crear archivo Excel en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # -------------------------------------------------------------------------------------
        # CONFIGURACIÓN GENERAL DE LA WORKSHEET
        # -------------------------------------------------------------------------------------
        workbook.set_properties({
                'title':    'NOMINA-CENS - Hoja de Trabajo',
                'subject':  'Extracto a la fecha',
                'author':   'ODOO-CENS',
                'manager':  'Gestión Humana',
                'company':  'CENS PERÚ',
                'category': 'LOTE - EXCEL',
                'keywords': 'nómina, lote, worksheet',
                'created':  datetime.now(),
                'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})
        worksheet = workbook.add_worksheet('Nómina')
        w_formato_hora  = workbook.add_format({
            'num_format': 'hh:mm',
            'align'     : 'center',  
            'valign'    : 'vcenter'  
            })
        w_formato_fecha = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'align'     : 'center',  
            'valign'    : 'vcenter'
            })
        w_formato_colorfondo = workbook.add_format({
            'bg_color': '#DDD9C4'
            })

        cell_format = workbook.add_format()
        cell_format_empr = workbook.add_format({'bold': True})
        cell_format_cabe = workbook.add_format()
        cell_format_tuti = workbook.add_format()
        cell_format_tut2 = workbook.add_format()
        cell_format_titu = workbook.add_format()
        cell_format_tut3 = workbook.add_format()
        cell_format_tut4 = workbook.add_format()
        cell_format_tut5 = workbook.add_format()
        cell_format_tut6 = workbook.add_format()
        # ------
        cell_format_nume = workbook.add_format()
        cell_format_nume.set_num_format('#,##0')
        cell_format_nume.set_align('center')
        cell_format_nume.set_align('vcenter')
        # ------
        cell_format_numc = workbook.add_format()
        cell_format_numc.set_num_format('#00.00')
        cell_format_numc.set_align('center')
        cell_format_numc.set_align('vcenter')
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
        cell_format_nedi = workbook.add_format()
        cell_format_nedi.set_font_color('gray')
        cell_format_nedi.set_align('center')
        cell_format_nedi.set_align('vcenter')
        cell_format_nedi.set_text_wrap()
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

        # -------------------------------------------------------------------------------------
        # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
        # -------------------------------------------------------------------------------------
        worksheet.set_column(0, 0, 9)       #-A- ID Empleado
        worksheet.set_column(1, 1, 14)      #-B- Boleta 
        worksheet.set_column(2, 2, 33)      #-C- Npombre del Empleado
        worksheet.set_column(3, 3, 13)      #-D- DNI
        worksheet.set_column(4, 4, 11)      #-E- LOTE
        worksheet.set_column(5, 5, 13)      #-F- FECHA INICIAL
        worksheet.set_column(6, 6, 13)      #-G- FECHA GINAL
        worksheet.set_column(7, 7, 8)       #-H- MONEDA
        worksheet.set_column(8, 8, 25)      #-I- UNIDAD DE NEGOCIO

        worksheet.set_column(9, 9, 5)       #-J- Separador

        worksheet.set_column(10, 10, 12)    #-K- 
        worksheet.set_column(11, 11, 12)    #-L- 
        worksheet.set_column(12, 12, 12)    #-K- REINTEGRO AFECTO
        worksheet.set_column(13, 13, 12)    #-L- REINTEGRO INAFECTO

        worksheet.set_column(14, 14, 2)     #-M- Separador

        worksheet.set_column(15, 15, 12)    #-N- REEMBOLSO MOVILIDAD
        worksheet.set_column(16, 16, 12)    #-O- REEMBOLSO COMBUSTIBLE
        worksheet.set_column(17, 17, 2)     #-P- Separador 
        worksheet.set_column(18, 18, 12)    #-Q- 
        worksheet.set_column(19, 19, 12)    #-R- 
        worksheet.set_column(20, 20, 2)     #-S- Separador 
        worksheet.set_column(21, 21, 12)    #-T- Adelanto Gratificación
        worksheet.set_column(22, 22, 12)    #-U- Adelanto Sueldo
        worksheet.set_column(23, 23, 12)    #-V- Descuento Tardanza
        worksheet.set_column(24, 24, 12)    #-W- Retención Judicial
        worksheet.set_column(25, 25, 12)    #-X- Descuento Préstamos
        worksheet.set_column(26, 26, 2)     #-Y- Separador
        worksheet.set_column(27, 27, 12)    #-Z- Renta 5ta
        worksheet.set_column(28, 28, 12)    #-AA- Descuento x Vales
        worksheet.set_column(29, 29, 12)    #-AB- OTROS DESCUENTOS
        worksheet.set_column(30, 30, 5)     #-AC- Separador
        worksheet.set_column(31, 31, 12)    #-AD- Dias Computados
        worksheet.set_column(32, 32, 10)    #-AE-
        worksheet.set_column(33, 33, 10)    #-AF-
        worksheet.set_column(34, 34, 10)    #--


        # ------
        worksheet.set_row(7, 27)        # (Fila,Altura)
        worksheet.set_zoom(85)          # %-Zoom
        # -------------------------------------------------------------------------------------
        # CABECERA DEL REPORTE
        # -------------------------------------------------------------------------------------
        worksheet.insert_image('A2', 'src/user/cens_nomina_excel_02/static/description/logo-tiny_96.png')
        worksheet.insert_image('Z2', 'src/user/cens_nomina_excel_02/static/description/logo-odoo-tiny.png', 
                                         {'x_scale': 0.6, 'y_scale': 0.6})
        worksheet.write('B3', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
        worksheet.write('B4', 'Gestión Humana - Nóminas - CENS-PERÚ')
        cell_format_cabe.set_font_name('Arial Black')
        cell_format_cabe.set_font_size(11)
        worksheet.write('H5', 'PLANILLA DE SUELDOS - EMPLEADOS CENS - DATA WORKSHEET', cell_format_cabe)
        # ------
        worksheet.write('A6', 'FECHA:')
        worksheet.write('B6', datetime.now(), cell_format_fech)
        #-----
        worksheet.write('A7', 'USUARIO:')
        w_usuario_actual = self.env.context.get("uid")
        usuario_actual = self.env['res.users'].browse(w_usuario_actual)
        w_usuario_names = usuario_actual.name
        worksheet.write('B7', w_usuario_names)
        #-----
        merge_format = workbook.add_format({'align': 'center'})
        worksheet.merge_range('K7:Q7', 'Merged Cells', merge_format)
        worksheet.write('K7', 'I   N   G   R   E   S   O   S', cell_format_tut2)

        # worksheet.merge_range('U7:Y7', 'Merged Cells', merge_format)
        # worksheet.write('U7', 'ACUERDOS CONTRACTUALES', cell_format_tuti)

        worksheet.merge_range('S7:AD7', 'Merged Cells', merge_format)
        worksheet.write('S7', 'D   E   S   C   U   E   N   T   O   S', cell_format_tuti)

        # worksheet.merge_range('AH7:AQ7', 'Merged Cells', merge_format)
        # worksheet.write('AH7', 'DISTRIBUCIÓN DE COSTOS', cell_format_tuti)
        # -------------------------------------------------------------------------------------
        # BARRA DE TITULOS
        # -------------------------------------------------------------------------------------
        cell_format_tuti.set_font_name('Arial Black')
        cell_format_tuti.set_font_color('black')
        cell_format_tuti.set_font_size(8)
        cell_format_tuti.set_text_wrap()                 # FORMATO TÍTULO - COLUMNAS IMPORTES #B7DEE8
        cell_format_tuti.set_bg_color('#92CDDC')
        cell_format_tuti.set_align('center')
        cell_format_tuti.set_align('vcenter')
        #-----
        cell_format_tut2.set_font_name('Arial Black')
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
        cell_format_tut3.set_font_name('Arial')
        cell_format_tut3.set_font_color('white')
        cell_format_tut3.set_font_size(6)
        cell_format_tut3.set_text_wrap()                 # FORMATO SUB-TÍTULO - FONDO GRANATE
        cell_format_tut3.set_bg_color('#963634')
        cell_format_tut3.set_align('center')
        cell_format_tut3.set_align('vcenter')
        #-----
        cell_format_tut4.set_font_name('Arial')
        cell_format_tut4.set_font_color('white')
        cell_format_tut4.set_font_size(6)
        cell_format_tut4.set_text_wrap()                 # FORMATO SUB-TÍTULO - FONDO VERDE OSCURO
        cell_format_tut4.set_bg_color('#215967')
        cell_format_tut4.set_align('center')
        cell_format_tut4.set_align('vcenter')
        #-----
        cell_format_tut5.set_font_name('Arial')
        cell_format_tut5.set_font_color('white')
        cell_format_tut5.set_font_size(8)
        cell_format_tut5.set_text_wrap()                 # FORMATO SUB-TÍTULO - FONDO VERDE OSCURO
        cell_format_tut5.set_bg_color('#215967')
        cell_format_tut5.set_align('center')
        cell_format_tut5.set_align('vcenter')
        #-----
        cell_format_tut6.set_font_name('Arial')
        cell_format_tut6.set_font_color('white')
        cell_format_tut6.set_font_size(8)
        cell_format_tut6.set_text_wrap()                 # FORMATO SUB-TÍTULO - FONDO VERDE OSCURO
        cell_format_tut6.set_bg_color('#215967')
        cell_format_tut6.set_align('center')
        cell_format_tut6.set_align('vcenter')
        #-----
        #worksheet.set_row(7, 7) 2A7486
        #worksheet.set_column('A:M', 7)
        worksheet.merge_range('A8:A9', 'Merged Cells', merge_format)
        worksheet.write('A8', 'ID', cell_format_titu)                           #-- 00
        worksheet.merge_range('B8:B9', 'Merged Cells', merge_format)
        worksheet.write('B8', 'BOLETA', cell_format_titu)                       #-- 01
        worksheet.merge_range('C8:C9', 'Merged Cells', merge_format)
        worksheet.write('C8', 'NOMBRE DEL EMPLEADO', cell_format_titu)          #-- 02
        worksheet.merge_range('D8:D9', 'Merged Cells', merge_format)
        worksheet.write('D8', 'D.N.I.', cell_format_titu)                       #-- 03
        worksheet.merge_range('E8:E9', 'Merged Cells', merge_format)
        worksheet.write('E8', 'LOTE', cell_format_titu)                         #-- 04
        worksheet.merge_range('F8:F9', 'Merged Cells', merge_format)
        worksheet.write('F8', 'FECHA INICIAL', cell_format_titu)                #-- 05
        worksheet.merge_range('G8:G9', 'Merged Cells', merge_format)
        worksheet.write('G8', 'FECHA FINAL', cell_format_titu)                  #-- 06
        worksheet.merge_range('H8:H9', 'Merged Cells', merge_format)
        worksheet.write('H8', 'MONEDA', cell_format_titu)                       #-- 07
        worksheet.merge_range('I8:I9', 'Merged Cells', merge_format)
        worksheet.write('I8', 'UNIDADA DE NEGOCIO', cell_format_tut5)              #-- 08
        # worksheet.write('J8', 'LICENCIA FALLECIMTO', cell_format_titu)          #-- 09
        # worksheet.write('K8', 'LICENCIA MATR-PATR', cell_format_titu)           #-- 10
        # worksheet.write('L8', 'VACACIONES', cell_format_titu)                   #-- 11
        # worksheet.write('M8', 'CON GOCE', cell_format_titu)                     #-- 12
        # worksheet.write('N8', 'DESCANSO MÉDICO', cell_format_titu)              #-- 13
        worksheet.write('K8', 'DIAS FERIADOS', cell_format_titu)                #-- 14
        worksheet.write('L8', 'BONIFIC. EXTRAORD.', cell_format_titu)           #-- 15
        worksheet.write('M8', 'REINTEGRO AFECTO.', cell_format_titu)           #-- 15
        worksheet.write('N8', 'REIMTEGRO INAFECTO.', cell_format_titu)           #-- 15
        
        # worksheet.write('Q8', 'IMPORTE H.EXTRAS', cell_format_titu)             #-- 16
        # worksheet.write('R8', 'DESCANSO VACACIONAL', cell_format_titu)                    #-- 17
        worksheet.write('P8', 'REEMBOLSO MOVILIDAD', cell_format_titu)          #-- 18
        worksheet.write('Q8', 'REEMBOLSO COMBUSTIB', cell_format_titu)          #-- 19
        # worksheet.write('U8', 'MOVILIDAD', cell_format_titu)                    #-- 20
        # worksheet.write('V8', 'VALE ALIMENTOS', cell_format_titu)               #-- 21
        # worksheet.write('W8', 'CONDICS. LABORALES', cell_format_titu)           #-- 22
        # worksheet.write('X8', 'BONIFIC. EDUCACIÓN', cell_format_titu)           #-- 23
        # worksheet.write('Y8', 'UTILIDAD. VOLUNTARS', cell_format_titu)         #-- 24
        worksheet.write('S8', 'DIAS INASISTENCIA', cell_format_titu)           #-- 26
        worksheet.write('T8', 'DIAS SIN GOCE', cell_format_titu)               #-- 27

        worksheet.write('V8', 'ADELANTO GRATIFICAC.', cell_format_titu)        #-- 25
        worksheet.write('W8', 'ADELANTO SUELDO', cell_format_titu)             #-- 28
        worksheet.write('X8', 'DESCUENTO TARDANZA', cell_format_titu)            #-- 29
        worksheet.write('Y8', 'RETENCIÓN JUDICIAL', cell_format_titu)          #-- 30
        worksheet.write('Z8', 'DESCUENTO PRÉSTAMOS', cell_format_titu)            #-- 31

        worksheet.write('AB8', 'RENTA 5TA', cell_format_titu)
        worksheet.write('AC8', 'DESCUENTO POR VALES', cell_format_titu)
        worksheet.write('AD8', 'OTROS DESCUENTOS', cell_format_titu)

        worksheet.write('AF8', 'DIAS COMPUTADOS', cell_format_titu)

        #-----
        # worksheet.write('J9', 'DIAS', cell_format_tut3)                 #-- 09
        # worksheet.write('K9', 'DIAS', cell_format_tut3)                 #-- 10
        # worksheet.write('L9', 'DIAS', cell_format_tut3)                 #-- 11
        # worksheet.write('M9', 'DIAS', cell_format_tut3)                 #-- 12
        # worksheet.write('N9', 'DIAS', cell_format_tut3)                 #-- 13
        worksheet.write('K9', 'DIAS', cell_format_tut3)                 #-- 14
        worksheet.write('L9', 'S/.', cell_format_tut4)                  #-- 15
        worksheet.write('M9', 'S/.', cell_format_tut4)                  #-- 16
        worksheet.write('N9', 'S/.', cell_format_tut4)                  #-- 17

        worksheet.write('P9', 'S/.', cell_format_tut4)                  #-- 18
        worksheet.write('Q9', 'S/.', cell_format_tut4)                  #-- 19
        # worksheet.write('U9', 'S/.', cell_format_tut4)                  #-- 20
        # worksheet.write('V9', 'S/.', cell_format_tut4)                  #-- 21
        # worksheet.write('W9', 'S/.', cell_format_tut4)                  #-- 22
        # worksheet.write('X9', 'S/.', cell_format_tut4)                  #-- 23
        # worksheet.write('Y9', 'S/.', cell_format_tut4)                 #-- 24
        # worksheet.write('Z9', 'S/.', cell_format_tut4)                 #-- 25
        worksheet.write('S9', 'DIAS', cell_format_tut3)                #-- 26
        worksheet.write('T9', 'DIAS', cell_format_tut3)                #-- 27

        worksheet.write('V9', 'S/.', cell_format_tut4)                 #-- 28
        worksheet.write('W9', 'S/.', cell_format_tut4)                 #-- 30
        worksheet.write('X9', 'S/.', cell_format_tut4)                 #-- 31
        worksheet.write('Y9', 'S/.', cell_format_tut4)                 #-- 28
        worksheet.write('Z9', 'S/.', cell_format_tut4)                 #-- 30

        worksheet.write('AB9', 'S/.', cell_format_tut4)                 #-- 28
        worksheet.write('AC9', 'S/.', cell_format_tut4)
        worksheet.write('AD9', 'S/.', cell_format_tut4)         #-- OTROS DESCUENTOS

        worksheet.write('AF9', 'DIAS', cell_format_tut3)

        #-----
        worksheet.freeze_panes(9, 4)

        # -------------------------------------------------------------------------------------
        # INSERTA NOMBRE DE CAMPOS Y OCULTA FILA
        # -------------------------------------------------------------------------------------
        # Definir campos a exportar
        fields_to_export = [
            'id', 
            'number', 
            'employee_id.name', 
            'x_studio_documento_identidad', 
            'x_studio_mes_calculado', 
            'date_from', 
            'date_to',
            'currency_id.name',
            'employee_id.x_studio_negocio_unidad',
            'separador1',
            # 'x_studio_licencia_fallecimiento',
            # 'x_studio_licencia_materpater',
            # 'x_studio_dias_vacaciones',
            # 'x_studio_dias_con_goce',
            # 'x_studio_descanso_medico',
            'x_studio_feriados_dias',
            'x_studio_bonificacion_extraordinaria',
            'x_studio_reintegro_afecto',
            'x_studio_reintegro_inafecto',
            'separador2',
            # 'x_studio_horas_extras_importe',
            # 'x_studio_descanso_vacacional',
            'x_studio_reembolso_movilidad',
            'x_studio_reembolso_combustible',
            'separador3',
            # 'x_studio_movilidad',
            # 'x_studio_vale_alimentos',
            # 'x_studio_condiciones_laborales',
            # 'x_studio_bonificacion_educacion',
            # 'x_studio_utilidades_voluntarias',
            'x_studio_descuento_inasistencias',
            'x_studio_dias_sin_goce',
            'separador4',
            'x_studio_adelanto_gratificacion',
            'x_studio_adelanto_sueldo',
            'x_studio_descuento_tardanzas_min',
            'x_studio_retencion_judicial',
            'x_studio_descuento_prestamos',
            'separador4',
            'x_studio_importe_renta_5ta',
            'x_studio_descuento_vales',
            'x_studio_en_otros_descuentos',
            'separador4',
            'x_studio_dias_computados'
        ]

        # Escribir encabezados
        for col, field in enumerate(fields_to_export):
            worksheet.write(0, col, field)
        worksheet.set_row(0, None, None, {'hidden': 1})

        # -------------------------------------------------------------------------------------
        # CUERPO PRINCIPAL DEL REPORTE - CENS DEVELOPMENT
        # -------------------------------------------------------------------------------------
        # w_lote = self.search(self._context.get('active_domain', []))  # Obtener registros según el dominio activo en la vista
        w_lote = self.browse(self._context.get('active_ids', []))
        w_dato = ""
        w_fila = 9
        w_acum_gana = 0
        w_acum_abie = 0
        w_acum_anul = 0
        w_acum_perd = 0
        w_acum_exto = 0

        for w_boleta in w_lote:
            w_dato  = w_boleta.employee_id.name
            if w_boleta.x_studio_cesado:
                worksheet.write(w_fila, 0, w_boleta.id, cell_format_rojo)
                worksheet.write(w_fila, 1, w_boleta.number, cell_format_rojo)
                worksheet.write(w_fila, 2, w_dato, cell_format_rojo)
                worksheet.write(w_fila, 3, w_boleta.x_studio_dni, cell_format_rojo)
            else:
                worksheet.write(w_fila, 0, w_boleta.id, cell_format_cent)
                worksheet.write(w_fila, 1, w_boleta.number, cell_format_cent)
                worksheet.write(w_fila, 2, w_dato, cell_format_left)   
                worksheet.write(w_fila, 3, w_boleta.x_studio_dni, cell_format_cent)

            # w_dato = w_boleta.payslip_run_id.name
            w_dato = ""
            w_mes = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').month
            w_dia = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').day
            w_ano = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').year
            w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)[:3]
            worksheet.write(w_fila, 4, w_dato, cell_format_cent)

            worksheet.write(w_fila, 5, w_boleta.date_from, cell_format_fech)
            worksheet.write(w_fila, 6, w_boleta.date_to, cell_format_fech)
            w_dato = w_boleta.currency_id.name
            worksheet.write(w_fila, 7, w_dato, cell_format_cent)
            w_dato = w_boleta.x_studio_unidad_de_negocio
            worksheet.write(w_fila, 8, w_dato, cell_format_left)
            w_dato = 0.00
            # ----------------------------
            # -- INGRESOS --
            # ----------------------------
            # worksheet.write(w_fila, 9, w_boleta.x_studio_licencia_fallecimiento, cell_format_nume)
            # worksheet.write(w_fila, 10, w_boleta.x_studio_licencia_materpater, cell_format_nume)
            # worksheet.write(w_fila, 11, w_boleta.x_studio_dias_vacaciones, cell_format_nume)
            # worksheet.write(w_fila, 12, w_boleta.x_studio_dias_con_goce, cell_format_nume)
            # worksheet.write(w_fila, 13, w_boleta.x_studio_descanso_medico, cell_format_nume)

            worksheet.write(w_fila, 10, w_boleta.x_studio_feriados_dias, cell_format_nume)
            worksheet.write(w_fila, 11, w_boleta.x_studio_bonificacion_extraordinaria, cell_format_impo)
            worksheet.write(w_fila, 12, w_boleta.x_studio_reintegro_afecto, cell_format_impo)
            worksheet.write(w_fila, 13, w_boleta.x_studio_reintegro_inafecto, cell_format_impo)


            worksheet.write(w_fila, 15, w_boleta.x_studio_reembolso_movilidad, cell_format_impo)
            worksheet.write(w_fila, 16, w_boleta.x_studio_reembolso_combustible, cell_format_impo)

            # ----------------------------
            # -- EGRESOS --
            # ----------------------------
            worksheet.write(w_fila, 18, w_boleta.x_studio_descuento_inasistencias, cell_format_nume)
            worksheet.write(w_fila, 19, w_boleta.x_studio_dias_sin_goce, cell_format_nume)

            worksheet.write(w_fila, 21, w_boleta.x_studio_adelanto_gratificacion, cell_format_impo)
            worksheet.write(w_fila, 22, w_boleta.x_studio_adelanto_sueldo, cell_format_impo)
            worksheet.write(w_fila, 23, w_boleta.x_studio_descuento_tardanzas_min, cell_format_impo)
            worksheet.write(w_fila, 24, w_boleta.x_studio_retencion_judicial, cell_format_impo)
            worksheet.write(w_fila, 25, w_boleta.x_studio_descuento_prestamos, cell_format_impo)

            worksheet.write(w_fila, 27, w_boleta.x_studio_importe_renta_5ta, cell_format_impo)
            worksheet.write(w_fila, 28, w_boleta.x_studio_descuento_vales, cell_format_impo)
            worksheet.write(w_fila, 29, w_boleta.x_studio_en_otros_descuentos, cell_format_impo)
            
            wDato = 0
            worksheet.write(w_fila, 31, wDato, cell_format_nume)
            
            w_fila += 1

        # =========================================================================================================
        # GENERA PÁGINA:  HORAS EXTRAS
        # =========================================================================================================
        worksheet2 = workbook.add_worksheet("Horas Extras")
        worksheet2.activate()
        # -------------------------------------------------------------------------------------
        # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
        # -------------------------------------------------------------------------------------
        worksheet2.set_column(0, 0, 9)       #-- ID Boleta
        worksheet2.set_column(1, 1, 14)      #-- Boleta 
        worksheet2.set_column(2, 2, 33)      #-- Nombre del Empleado
        worksheet2.set_column(3, 3, 13)      #-- DNI
        worksheet2.set_column(4, 4, 11)      #-- LOTE
        worksheet2.set_column(5, 5, 9)       #-- ID Ocurrencia
        worksheet2.set_column(6, 6, 14)      #-- FECHA OCURRENCIA
        worksheet2.set_column(7, 7, 14)      #-- CANTIDAD HORAS
        worksheet2.set_column(8, 8, 14)      #-- ¿NO LABORABLE?
        worksheet2.set_column(9, 9, 40)      #-- DESCRIPCIÓN
        # ------
        worksheet2.set_row(7, 27)        # (Fila,Altura)
        worksheet2.set_zoom(85)          # %-Zoom
        # -------------------------------------------------------------------------------------
        # CABECERA DEL REPORTE - HORAS EXTRAS
        # -------------------------------------------------------------------------------------
        worksheet2.insert_image('A2', 'src/user/cens_crm/static/description/logo-tiny_96.png')
        worksheet2.write('B3', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
        worksheet2.write('B4', 'Gestión Humana - Nóminas - CENS-PERÚ')
        cell_format_cabe.set_font_name('Arial Black')
        cell_format_cabe.set_font_size(11)
        worksheet2.write('F5', 'PLANILLA DE SUELDOS - REGISTRO DE HORAS EXTRAS ', cell_format_cabe)
        # ------
        worksheet2.write('A6', 'FECHA:')
        worksheet2.write('B6', datetime.now(), cell_format_fech)
        #-----
        worksheet2.write('A7', 'USUARIO:')
        w_usuario_actual = self.env.context.get("uid")
        usuario_actual = self.env['res.users'].browse(w_usuario_actual)
        w_usuario_names = usuario_actual.name
        worksheet2.write('B7', w_usuario_names)
        #-----
        merge_format = workbook.add_format({'align': 'center'})
        worksheet2.merge_range('F7:J7', 'Merged Cells', merge_format)
        worksheet2.write('F7', 'REGISTRO DE LA OCURRENCIA', cell_format_tut2)
        #-----
        worksheet2.merge_range('A8:A9', 'Merged Cells', merge_format)
        worksheet2.write('A8', 'ID', cell_format_titu)                           #-- 00
        worksheet2.merge_range('B8:B9', 'Merged Cells', merge_format)
        worksheet2.write('B8', 'BOLETA', cell_format_titu)                       #-- 01
        worksheet2.merge_range('C8:C9', 'Merged Cells', merge_format)
        worksheet2.write('C8', 'NOMBRE DEL EMPLEADO', cell_format_titu)          #-- 02
        worksheet2.merge_range('D8:D9', 'Merged Cells', merge_format)
        worksheet2.write('D8', 'D.N.I.', cell_format_titu)                       #-- 03
        worksheet2.merge_range('E8:E9', 'Merged Cells', merge_format)
        worksheet2.write('E8', 'LOTE', cell_format_titu)                         #-- 04
        worksheet2.write('F8', 'ID OCURREN', cell_format_titu)
        worksheet2.write('G8', 'FECHA OCURREN', cell_format_titu)                #-- 05
        worksheet2.write('H8', 'NÚMERO DE HORAS', cell_format_titu)                  #-- 06
        worksheet2.write('I8', '¿NO LABORABLE?', cell_format_titu)                       #-- 07
        worksheet2.write('J8', 'DESCRIPCIÓN', cell_format_titu)              #-- 08
        #-----
        worksheet2.write('F9', 'No Edit', cell_format_tut5)
        worksheet2.write('G9', 'dd/mm/aaaa', cell_format_tut5)                
        worksheet2.write('H9', 'HH (Número Entero)', cell_format_tut5)                
        worksheet2.write('I9', 'SI o NO', cell_format_tut5)                
        worksheet2.write('J9', 'Breve observación', cell_format_tut5)                
        #-----
        worksheet2.freeze_panes(9, 4)

        # -------------------------------------------------------------------------------------
        # INSERTA NOMBRE DE CAMPOS HORAS EXTRAS Y OCULTA FILA
        # -------------------------------------------------------------------------------------
        # Definir campos a exportar
        fields_to_export = [
            'id', 
            'number', 
            'employee_id.name', 
            'x_studio_documento_identidad', 
            'x_studio_mes_calculado',
            'x_studio_one2many_field_CHZUj.id',           
            'x_studio_one2many_field_CHZUj.x_studio_he_fecha_trabajo', 
            'x_studio_one2many_field_CHZUj.x_studio_he_total_horas_extras',
            'x_studio_one2many_field_CHZUj.x_studio_he_dia_libre',
            'x_studio_one2many_field_CHZUj.x_name'
        ]

        # Escribir encabezados
        for col, field in enumerate(fields_to_export):
            worksheet2.write(0, col, field)
        worksheet2.set_row(0, None, None, {'hidden': 1})

        # -------------------------------------------------------------------------------------
        # CUERPO PRINCIPAL DEL REPORTE - HORAS ESTRAS
        # -------------------------------------------------------------------------------------
        # w_lote = self.search(self._context.get('active_domain', []))  # Obtener registros según el dominio activo en la vista
        w_lote = self.browse(self._context.get('active_ids', []))
        w_cant = len(w_lote) 
        w_dato = ""
        w_fila = 9
        if w_cant>0:
            for fila in range(9, w_cant+1):  
                worksheet2.write(fila, 6, None, w_formato_fecha)
                worksheet2.write(fila, 7, None, cell_format_numc) 

        for w_boleta in w_lote:
            worksheet2.write(w_fila, 0, w_boleta.id, cell_format_cent)   
            worksheet2.write(w_fila, 1, w_boleta.number, cell_format_cent)
            w_dato = w_boleta.employee_id.name
            worksheet2.write(w_fila, 2, w_dato, cell_format_left)
            worksheet2.write(w_fila, 3, w_boleta.x_studio_dni, cell_format_cent)
            
            w_dato = ""
            w_mes = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').month
            w_dia = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').day
            w_ano = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').year
            w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)[:3]
            worksheet2.write(w_fila, 4, w_dato, cell_format_cent)

            w_horas_extras = w_boleta.x_studio_one2many_field_CHZUj
            if not w_horas_extras:
                w_dato = "NO"
                worksheet2.write(w_fila, 8, w_dato, cell_format_cent)
                w_fila += 1
            else:
                for hora_extra in w_horas_extras:
                    w_iden_ocurr = hora_extra.id
                    worksheet2.write(w_fila, 5, w_iden_ocurr, cell_format_nedi)
                    w_fech_ocurr = hora_extra.x_studio_he_fecha_trabajo
                    worksheet2.write(w_fila, 6, w_fech_ocurr, cell_format_fech)
                    w_hora_ocurr = hora_extra.x_studio_he_total_horas_extras
                    worksheet2.write(w_fila, 7, w_hora_ocurr, cell_format_numc)
                    dia_libre = "SI" if hora_extra.x_studio_he_dia_libre else "NO"
                    worksheet2.write(w_fila, 8, dia_libre, cell_format_cent)
                    worksheet2.write(w_fila, 9, hora_extra.x_name, cell_format_left)
                    w_fila += 1

        if (w_fila > 9):
            w_fila_ini = 9  
            w_fila_fin = w_fila + 1  
            for fila in range(w_fila_ini, w_fila_fin + 1):
                worksheet2.conditional_format(f'A{fila+1}:J{fila+1}', {
                    'type': 'formula',
                    'criteria': f'NOT(ISBLANK($G${fila+1}))',  # Evalúa si G no está vacía
                    'format': w_formato_colorfondo
                })

        worksheet.activate()
        workbook.close()
        # ------------------------------------------------------------------

        # Crear adjunto
        xlsx_data = output.getvalue()
        attachment = self.env['ir.attachment'].create({
            'name': 'worksheet_export.xlsx',
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
