from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import xlrd
import xlsxwriter
from io import BytesIO

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def export_to_spreadsheet(self):
        # Crear archivo Excel en memoria
        output = BytesIO()
        #workbook = xlsxwriter.Workbook(output)
        try:
            # Crear el workbook en el buffer
            #workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            workbook = xlsxwriter.Workbook(output)
            # worksheet = workbook.add_worksheet('Hoja1')

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
            cell_format_tut3 = workbook.add_format()
            cell_format_tut4 = workbook.add_format()
            cell_format_tut5 = workbook.add_format()
            cell_format_tut6 = workbook.add_format()
            cell_format_titu = workbook.add_format()
            cell_format_sup1 = workbook.add_format()
            cell_format_sup2 = workbook.add_format()
            cell_format_sup3 = workbook.add_format()
            cell_format_sup4 = workbook.add_format()
            cell_format_sup5 = workbook.add_format()
            cell_format_sup6 = workbook.add_format()
            cell_format_sup7 = workbook.add_format()
            cell_format_sup8 = workbook.add_format()
            cell_format_tit1 = workbook.add_format()
            cell_format_tit2 = workbook.add_format()
            cell_format_tit3 = workbook.add_format()
            cell_format_tit31 = workbook.add_format()
            cell_format_tit4 = workbook.add_format()
            cell_format_tit5 = workbook.add_format()
            cell_format_tit6 = workbook.add_format()
            cell_format_tit7 = workbook.add_format()
            cell_format_tit8 = workbook.add_format()
            cell_format_sub1 = workbook.add_format()
            cell_format_sub2 = workbook.add_format()
            cell_format_sub3 = workbook.add_format()
            cell_format_sub31 = workbook.add_format()
            cell_format_sub4 = workbook.add_format()
            cell_format_sub5 = workbook.add_format()
            cell_format_sub6 = workbook.add_format()
            cell_format_sub7 = workbook.add_format()
            cell_format_sub8 = workbook.add_format()
            cell_format_tota = workbook.add_format()
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
            cell_format_imp2 = workbook.add_format()
            cell_format_imp2.set_num_format('#,##0.00')
            cell_format_imp2.set_bg_color('#FFFF99')
            cell_format_imp2.set_align('vcenter')
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
            # Añadir este formato en la sección donde se definen los formatos
            cell_format_cesado = workbook.add_format()
            cell_format_cesado.set_bg_color('#E6B8B7')  # Color verde claro para empleados cesados
            cell_format_cesado.set_align('vcenter')

            # También crear versiones con este formato para cada tipo de dato
            cell_format_cesado_cent = workbook.add_format()
            cell_format_cesado_cent.set_bg_color('#E6B8B7')
            cell_format_cesado_cent.set_align('center')
            cell_format_cesado_cent.set_align('vcenter')
            cell_format_cesado_cent.set_text_wrap()

            cell_format_cesado_left = workbook.add_format()
            cell_format_cesado_left.set_bg_color('#E6B8B7')
            cell_format_cesado_left.set_align('vcenter')

            cell_format_cesado_impo = workbook.add_format()
            cell_format_cesado_impo.set_bg_color('#E6B8B7')
            cell_format_cesado_impo.set_num_format('#,##0.00')
            cell_format_cesado_impo.set_align('vcenter')

            cell_format_cesado_fech = workbook.add_format()
            cell_format_cesado_fech.set_bg_color('#E6B8B7')
            cell_format_cesado_fech.set_num_format('dd/mm/yyyy')
            cell_format_cesado_fech.set_align('center')
            cell_format_cesado_fech.set_align('vcenter')

            cell_format_cesado_nume = workbook.add_format()
            cell_format_cesado_nume.set_bg_color('#E6B8B7')
            cell_format_cesado_nume.set_num_format('#,##0')
            cell_format_cesado_nume.set_align('center')
            cell_format_cesado_nume.set_align('vcenter')

            # -------------------------------------------------------------------------------------
            # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
            # -------------------------------------------------------------------------------------
            worksheet.set_column(0, 0, 9)       #-- ID Empleado
            worksheet.set_column(1, 1, 14)      #-- Boleta 
            worksheet.set_column(2, 2, 33)      #-- Npombre del Empleado
            worksheet.set_column(3, 3, 13)      #-- DNI
            worksheet.set_column(4, 4, 20)      #-- UNIDAD DE NEGOCIO
            worksheet.set_column(5, 5, 30)      #-- CARGO
            worksheet.set_column(6, 6, 20)      #-- DEPARTAMENTO
            worksheet.set_column(7, 7, 20)      #-- CENTRO DE COSTO
            worksheet.set_column(8, 8, 13)      #-- FECHA INGRESO
            worksheet.set_column(9, 9, 8)       #-- MONEDA
            worksheet.set_column(10, 10, 12)      #-- DIAS COMPUTADOS
            worksheet.set_column(11, 11, 12)      #-- 
            worksheet.set_column(12, 12, 12)    #-- 
            worksheet.set_column(13, 13, 12)    #-- 
            worksheet.set_column(14, 14, 12)    #-- 
            worksheet.set_column(15, 15, 12)    #-- 
            worksheet.set_column(16, 16, 12)    #-- 
            worksheet.set_column(17, 17, 12)    #-- 
            worksheet.set_column(18, 18, 12)    #-- 
            worksheet.set_column(19, 19, 12)    #-- 
            worksheet.set_column(20, 20, 12)    #-- 
            worksheet.set_column(21, 21, 12)    #-- Retención Judicial
            worksheet.set_column(22, 22, 12)    #-- Descto.Préstamos

            worksheet.set_column(23, 23, 5)    # -- (Seperador) 

            worksheet.set_column(24, 24, 12)    #-- Sueldo Básico 
            worksheet.set_column(25, 25, 12)    #-- Asig.Familiar
            worksheet.set_column(26, 26, 12)    #-- Licencia con Goce
            worksheet.set_column(27, 27, 12)    #-- Licencia x Fallecimiento
            worksheet.set_column(28, 28, 12)    #-- Licencia Mater/Paternidad
            worksheet.set_column(29, 29, 12)    #-- Bonif.x Cumplimiento    INGRESOS
            worksheet.set_column(30, 30, 12)    #-- Descanso Médico
            worksheet.set_column(31, 31, 12)    #-- Feriados
            worksheet.set_column(32, 32, 12)    #-- Horas Extras
            worksheet.set_column(33, 33, 12)    #-- Vacaciones
            worksheet.set_column(34, 34, 12)    #-- Descanzo Vaca
            worksheet.set_column(35, 35, 12)    #-- REINTEGRO AFECTO      

            worksheet.set_column(36, 36, 12)    #-- Alimentac.    
            worksheet.set_column(37, 37, 12)    #-- Movilidad    
            worksheet.set_column(38, 38, 12)    #-- Cond.Labor.       NO REMUNERATIVOS
            worksheet.set_column(39, 39, 12)    #-- Boni.Educ.
            worksheet.set_column(40, 40, 12)    #-- Util.Volunt.
            worksheet.set_column(41, 41, 12)    #-- Vale x Combustible

            worksheet.set_column(42, 42, 12)    #-- Vaca.Truncas
            worksheet.set_column(43, 43, 12)    #-- CTS Trunco
            worksheet.set_column(44, 44, 12)    #-- Gratific.Trunca      LIQUIDACIONES
            worksheet.set_column(45, 45, 12)    #-- Bonif.Grati.Trunca

            worksheet.set_column(46, 46, 12)    #-- REINTEGRO AFECTO      (LIQUIDACIONES)
            worksheet.set_column(47, 47, 12)    #-- REINTEGRO INAFECTO   (LIQUIDACIONES)

            worksheet.set_column(48, 48, 12)    #-- AFP
            worksheet.set_column(49, 49, 12)    #-- 5TA     DESCUENTOS X LBS
            worksheet.set_column(50, 50, 12)    #-- OTROS

            worksheet.set_column(51, 51, 12)    #--
            worksheet.set_column(52, 52, 12)    #--
            worksheet.set_column(53, 53, 12)    #-- Compañia
            worksheet.set_column(54, 54, 12)    #-- AFP
            worksheet.set_column(55, 55, 12)    #-- ONP
            worksheet.set_column(56, 56, 12)    #--
            worksheet.set_column(57, 57, 12)    #--     DESCUENTOS
            worksheet.set_column(58, 58, 12)    #--
            worksheet.set_column(59, 59, 12)    #--
            worksheet.set_column(60, 60, 12)    #--
            worksheet.set_column(61, 61, 12)    #--
            worksheet.set_column(62, 62, 12)    #--     Descto.Vales
            worksheet.set_column(63, 63, 12)    #--     Otros descuentos

            worksheet.set_column(64, 64, 12)    #-- Adel.Remuneración
            worksheet.set_column(65, 65, 12)    #-- Reembolso Movilidad
            worksheet.set_column(66, 66, 12)    #-- Adel.Gratific.        INCREMENTOS DIRECTOS
            worksheet.set_column(67, 67, 12)    #-- Indemnizac.Despido
            worksheet.set_column(68, 68, 12)    #-- Devoluc.Descto.Indebido
            worksheet.set_column(69, 69, 12)    #-- REINTEGROS INAFECTOS

            worksheet.set_column(70, 70, 5)    #--     (Seperador)

            worksheet.set_column(71, 71, 12)    #-- Total Ingresos
            worksheet.set_column(72, 72, 12)    #-- Total CNR
            worksheet.set_column(73, 73, 12)    #-- Total Desctos.          RESUMEN TOTALIZADO
            worksheet.set_column(74, 74, 12)    #-- Total Increment.Directos
            worksheet.set_column(75, 75, 12)    #-- Total Concepto LBS
            worksheet.set_column(76, 76, 12)    #-- TOTAL NETO

            worksheet.set_column(77, 77, 5)     #--   (Seperador)

            worksheet.set_column(78, 78, 12)    #-- ESSALUD
            worksheet.set_column(79, 79, 12)    #-- EPS         APORTES

            worksheet.set_column(80, 80, 12)    #-- CTS
            worksheet.set_column(81, 81, 12)    #-- Vacaciones
            worksheet.set_column(82, 82, 12)    #-- Gratificaciones     PROVISIONES
            worksheet.set_column(83, 83, 12)    #-- Bonific.Gratific.

            worksheet.set_column(84, 84, 5)     #--    (Seperador)

            worksheet.set_column(85, 85, 15)    #-- TOTAL COSTO

            worksheet.set_column(86, 86, 5)     #--    (Seperador)

            worksheet.set_column(87, 87, 30)    #-- Banco
            worksheet.set_column(88, 88, 30)    #-- Cuenta      DETALLE CTA BANCO
            worksheet.set_column(89, 89, 30)    #-- CCI

            worksheet.set_column(90, 90, 5)     #--    (Seperador)

            worksheet.set_column(91, 91, 12)    #-- Compañia
            worksheet.set_column(92, 92, 12)    #-- Importe Obligatorio
            worksheet.set_column(93, 93, 12)    #-- Prima Seguro
            worksheet.set_column(94, 94, 10)    #-- COMISION - Tipo
            worksheet.set_column(95, 95, 12)    #-- COMISION - Mixta   DESAGREGHADO AFP/ONP
            worksheet.set_column(96, 96, 12)    #-- COMISION - Flujo
            worksheet.set_column(97, 97, 12)    #-- Total AFP
            worksheet.set_column(98, 98, 12)    #-- Total ONP

            worksheet.set_column(99, 99, 5)    #- (Seperador)

            worksheet.set_column(100, 100, 12)    #- AFP / ONP
            worksheet.set_column(101, 101, 12)    #- FECHA DE CESE

            # ------
            worksheet.set_row(7, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A2', 'src/user/cens_nomina_excel_01/static/description/logo-tiny_96.png')
            worksheet.insert_image('CH2', 'src/user/cens_nomina_excel_01/static/description/logo-odoo-tiny.png', 
                                         {'x_scale': 0.7, 'y_scale': 0.7})
            worksheet.write('B3', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B4', 'Gestión Humana - Nóminas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)
            # worksheet.write('H5', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ', cell_format_cabe)
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

            worksheet.merge_range('L7:Q7', 'Merged Cells', merge_format)
            worksheet.write('L7', 'ACUERDOS CONTRACTUALES', cell_format_tuti)

            worksheet.merge_range('R7:W7', 'Merged Cells', merge_format)
            worksheet.write('R7', 'E  G  R  E  S  O  S', cell_format_tut2)

            worksheet.merge_range('Y7:AJ7', 'Merged Cells', merge_format)
            worksheet.write('Y7', 'I  N  G  R  E  S  O  S', cell_format_sup1)
            
            worksheet.merge_range('AK7:AP7', 'Merged Cells', merge_format)
            worksheet.write('AK7', 'CONCEPTOS NO REMUNERATIVOS', cell_format_sup2)

            worksheet.merge_range('AQ7:AY7', 'Merged Cells', merge_format)
            worksheet.write('AQ7', 'CONCEPTOS LIQUIDACIÓN', cell_format_sup8)

            worksheet.merge_range('AZ7:BL7', 'Merged Cells', merge_format)
            worksheet.write('AZ7', 'D E S C U E N T O S', cell_format_sup3)

            worksheet.merge_range('BM7:BR7', 'Merged Cells', merge_format)
            worksheet.write('BM7', 'INCREMENTOS DIRECTOS', cell_format_sup4)

            worksheet.merge_range('BT7:BY7', 'Merged Cells', merge_format)
            worksheet.write('BT7', 'RESUMEN TOTALIZADO', cell_format_sup5)

            worksheet.merge_range('CA7:CB7', 'Merged Cells', merge_format)
            worksheet.write('CA7', 'APORTES', cell_format_sup5)

            worksheet.merge_range('CC7:CF7', 'Merged Cells', merge_format)
            worksheet.write('CC7', 'PROVISIONES', cell_format_sup5)

            worksheet.merge_range('CH7:CH7', 'Merged Cells', merge_format)
            worksheet.write('CH7', 'COSTO', cell_format_sup5)

            worksheet.merge_range('CJ7:CL7', 'Merged Cells', merge_format)
            worksheet.write('CJ7', 'CUENTA BANCARIA ABONO', cell_format_sup5)

            worksheet.merge_range('CN7:CU7', 'Merged Cells', merge_format)
            worksheet.write('CN7', 'DESAGREGADO AFP / ONP', cell_format_sup5)

            worksheet.merge_range('CW7:CX7', 'Merged Cells', merge_format)
            worksheet.write('CW7', 'AFP / ONP', cell_format_sup5)


            # -------------------------------------------------------------------------------------
            # BARRA DE TITULOS
            # -------------------------------------------------------------------------------------
            cell_format_tota.set_font_name('Arial Black')
            cell_format_tota.set_font_color('black')
            cell_format_tota.set_font_size(12)
            cell_format_tota.set_text_wrap()                 # FORMATO TOTALES - TOTALIZADO
            cell_format_tota.set_align('right')
            cell_format_tota.set_align('vcenter')
            #-----
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
            #--------------------------------------------------------------------------------
            cell_format_sup1.set_font_name('Arial Black')
            cell_format_sup1.set_font_color('black')
            cell_format_sup1.set_font_size(8)
            cell_format_sup1.set_text_wrap()                 # FORMATO SUP-TÍTULO - INGRESOS
            cell_format_sup1.set_bg_color('#8DB4E2')
            cell_format_sup1.set_align('center')
            cell_format_sup1.set_align('vcenter')
            #-----
            cell_format_tit1.set_font_name('Arial')
            cell_format_tit1.set_font_color('white')
            cell_format_tit1.set_font_size(8)
            cell_format_tit1.set_text_wrap()                 # FORMATO TÍTULO - INGRESOS
            cell_format_tit1.set_bg_color('#0060A8')
            cell_format_tit1.set_align('center')
            cell_format_tit1.set_align('vcenter')
            #-----
            cell_format_sub1.set_font_name('Arial')
            cell_format_sub1.set_font_color('white')
            cell_format_sub1.set_font_size(8)
            cell_format_sub1.set_text_wrap()                 # FORMATO SUB-TÍTULO - INGRESOS
            cell_format_sub1.set_bg_color('#16365C')
            cell_format_sub1.set_align('center')
            cell_format_sub1.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup2.set_font_name('Arial Black')
            cell_format_sup2.set_font_color('black')
            cell_format_sup2.set_font_size(8)
            cell_format_sup2.set_text_wrap()                 # FORMATO SUP-TÍTULO - NO REMUNERATIVOS
            cell_format_sup2.set_bg_color('#FABF8F')
            cell_format_sup2.set_align('center')
            cell_format_sup2.set_align('vcenter')
            #-----
            cell_format_tit2.set_font_name('Arial')
            cell_format_tit2.set_font_color('white')
            cell_format_tit2.set_font_size(8)
            cell_format_tit2.set_text_wrap()                 # FORMATO TÍTULO - NO REMUNERATIVOS
            cell_format_tit2.set_bg_color('#E26B0A')
            cell_format_tit2.set_align('center')
            cell_format_tit2.set_align('vcenter')
            #-----
            cell_format_sub2.set_font_name('Arial')
            cell_format_sub2.set_font_color('white')
            cell_format_sub2.set_font_size(8)
            cell_format_sub2.set_text_wrap()                 # FORMATO SUB-TÍTULO - NO REMUNERATIVOS
            cell_format_sub2.set_bg_color('#974706')
            cell_format_sub2.set_align('center')
            cell_format_sub2.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup3.set_font_name('Arial Black')
            cell_format_sup3.set_font_color('black')
            cell_format_sup3.set_font_size(8)
            cell_format_sup3.set_text_wrap()                 # FORMATO SUP-TÍTULO - DESCUENTOS
            cell_format_sup3.set_bg_color('#C4BD97')
            cell_format_sup3.set_align('center')
            cell_format_sup3.set_align('vcenter')
            #-----
            cell_format_tit3.set_font_name('Arial')
            cell_format_tit3.set_font_color('white')
            cell_format_tit3.set_font_size(8)
            cell_format_tit3.set_text_wrap()                 # FORMATO TÍTULO - DESCUENTOS
            cell_format_tit3.set_bg_color('#948A54')
            cell_format_tit3.set_align('center')
            cell_format_tit3.set_align('vcenter')
            #-----
            cell_format_sub3.set_font_name('Arial')
            cell_format_sub3.set_font_color('white')
            cell_format_sub3.set_font_size(8)
            cell_format_sub3.set_text_wrap()                 # FORMATO SUB-TÍTULO - DESCUENTOS
            cell_format_sub3.set_bg_color('#494529')
            cell_format_sub3.set_align('center')
            cell_format_sub3.set_align('vcenter')
            #-----------------------------------------------
            cell_format_tit31.set_font_name('Arial')
            cell_format_tit31.set_font_color('white')
            cell_format_tit31.set_font_size(8)
            cell_format_tit31.set_text_wrap()                 # FORMATO TÍTULO - DESCUENTOS - AFP/ONP
            cell_format_tit31.set_bg_color('#857B4B')
            cell_format_tit31.set_align('center')
            cell_format_tit31.set_align('vcenter')
            #-----
            cell_format_sub31.set_font_name('Arial')
            cell_format_sub31.set_font_color('white')
            cell_format_sub31.set_font_size(8)
            cell_format_sub31.set_text_wrap()                 # FORMATO SUB-TÍTULO - DESCUENTOS - AFP/ONP
            cell_format_sub31.set_bg_color('#1D1B10')
            cell_format_sub31.set_align('center')
            cell_format_sub31.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup8.set_font_name('Arial Black')
            cell_format_sup8.set_font_color('black')
            cell_format_sup8.set_font_size(8)
            cell_format_sup8.set_text_wrap()                 # FORMATO SUP-TÍTULO - LIQUIDACIONES
            cell_format_sup8.set_bg_color('#CCC0DA')
            cell_format_sup8.set_align('center')
            cell_format_sup8.set_align('vcenter')
            #-----
            cell_format_tit8.set_font_name('Arial')
            cell_format_tit8.set_font_color('white')
            cell_format_tit8.set_font_size(8)
            cell_format_tit8.set_text_wrap()                 # FORMATO TÍTULO - LIQUIDACIONES
            cell_format_tit8.set_bg_color('#8064A2')
            cell_format_tit8.set_align('center')
            cell_format_tit8.set_align('vcenter')
            #-----
            cell_format_sub8.set_font_name('Arial')
            cell_format_sub8.set_font_color('white')
            cell_format_sub8.set_font_size(8)
            cell_format_sub8.set_text_wrap()                 # FORMATO SUB-TÍTULO - LIQUIDACIONES
            cell_format_sub8.set_bg_color('#60497A')
            cell_format_sub8.set_align('center')
            cell_format_sub8.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup4.set_font_name('Arial Black')
            cell_format_sup4.set_font_color('black')
            cell_format_sup4.set_font_size(8)
            cell_format_sup4.set_text_wrap()                 # FORMATO SUP-TÍTULO - INCREMENTOS DIRECTOS
            cell_format_sup4.set_bg_color('#C4D79B')
            cell_format_sup4.set_align('center')
            cell_format_sup4.set_align('vcenter')
            #-----
            cell_format_tit4.set_font_name('Arial')
            cell_format_tit4.set_font_color('white')
            cell_format_tit4.set_font_size(8)
            cell_format_tit4.set_text_wrap()                 # FORMATO TÍTULO - INCREMENTOS DIRECTOS
            cell_format_tit4.set_bg_color('#76933C')
            cell_format_tit4.set_align('center')
            cell_format_tit4.set_align('vcenter')
            #-----
            cell_format_sub4.set_font_name('Arial')
            cell_format_sub4.set_font_color('white')
            cell_format_sub4.set_font_size(8)
            cell_format_sub4.set_text_wrap()                 # FORMATO SUB-TÍTULO - INCREMENTOS DIRECTOS
            cell_format_sub4.set_bg_color('#4F6228')
            cell_format_sub4.set_align('center')
            cell_format_sub4.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup5.set_font_name('Arial Black')
            cell_format_sup5.set_font_color('black')
            cell_format_sup5.set_font_size(8)
            cell_format_sup5.set_text_wrap()                 # FORMATO SUP-TÍTULO - RESUMEN
            cell_format_sup5.set_bg_color('#DA9694')
            cell_format_sup5.set_align('center')
            cell_format_sup5.set_align('vcenter')
            #-----
            cell_format_tit5.set_font_name('Arial')
            cell_format_tit5.set_font_color('white')
            cell_format_tit5.set_font_size(8)
            cell_format_tit5.set_text_wrap()                 # FORMATO TÍTULO - RESUMEN
            cell_format_tit5.set_bg_color('#963634')
            cell_format_tit5.set_align('center')
            cell_format_tit5.set_align('vcenter')
            #-----
            cell_format_sub5.set_font_name('Arial')
            cell_format_sub5.set_font_color('white')
            cell_format_sub5.set_font_size(8)
            cell_format_sub5.set_text_wrap()                 # FORMATO SUB-TÍTULO - RESUMEN
            cell_format_sub5.set_bg_color('#632523')
            cell_format_sub5.set_align('center')
            cell_format_sub5.set_align('vcenter')
            #-----------------------------------------------
            cell_format_sup6.set_font_name('Arial Black')
            cell_format_sup6.set_font_color('black')
            cell_format_sup6.set_font_size(8)
            cell_format_sup6.set_text_wrap()                 # FORMATO SUP-TÍTULO - APORTES
            cell_format_sup6.set_bg_color('#B1A0C7')
            cell_format_sup6.set_align('center')
            cell_format_sup6.set_align('vcenter')
            #-----
            cell_format_tit6.set_font_name('Arial')
            cell_format_tit6.set_font_color('white')
            cell_format_tit6.set_font_size(8)
            cell_format_tit6.set_text_wrap()                 # FORMATO TÍTULO - APORTES
            cell_format_tit6.set_bg_color('#60497A')
            cell_format_tit6.set_align('center')
            cell_format_tit6.set_align('vcenter')
            #-----
            cell_format_sub6.set_font_name('Arial')
            cell_format_sub6.set_font_color('white')
            cell_format_sub6.set_font_size(8)
            cell_format_sub6.set_text_wrap()                 # FORMATO SUB-TÍTULO - APORTES
            cell_format_sub6.set_bg_color('#403151')
            cell_format_sub6.set_align('center')
            cell_format_sub6.set_align('vcenter')
            #------------------------------------------------
            cell_format_sup7.set_font_name('Arial Black')
            cell_format_sup7.set_font_color('black')
            cell_format_sup7.set_font_size(8)
            cell_format_sup7.set_text_wrap()                 # FORMATO SUP-TÍTULO - PROVISIONES
            cell_format_sup7.set_bg_color('#92CDDC')
            cell_format_sup7.set_align('center')
            cell_format_sup7.set_align('vcenter')
            #-----
            cell_format_tit7.set_font_name('Arial')
            cell_format_tit7.set_font_color('white')
            cell_format_tit7.set_font_size(8)
            cell_format_tit7.set_text_wrap()                 # FORMATO TÍTULO - PROVISIONES
            cell_format_tit7.set_bg_color('#31869B')
            cell_format_tit7.set_align('center')
            cell_format_tit7.set_align('vcenter')
            #-----
            cell_format_sub7.set_font_name('Arial')
            cell_format_sub7.set_font_color('white')
            cell_format_sub7.set_font_size(8)
            cell_format_sub7.set_text_wrap()                 # FORMATO SUB-TÍTULO - PROVISIONES
            cell_format_sub7.set_bg_color('#215967')
            cell_format_sub7.set_align('center')
            cell_format_sub7.set_align('vcenter')
            #-----
    
            #worksheet.set_row(7, 7) 2A7486
            #worksheet.set_column('A:M', 7)
            worksheet.merge_range('A8:A9', 'Merged Cells', merge_format)
            worksheet.write('A8', 'ORD', cell_format_titu)                           #-- 00
            worksheet.merge_range('B8:B9', 'Merged Cells', merge_format)
            worksheet.write('B8', 'BOLETA', cell_format_titu)                       #-- 01
            worksheet.merge_range('C8:C9', 'Merged Cells', merge_format)
            worksheet.write('C8', 'NOMBRE DEL EMPLEADO', cell_format_titu)          #-- 02
            worksheet.merge_range('D8:D9', 'Merged Cells', merge_format)
            worksheet.write('D8', 'D.N.I.', cell_format_titu)                       #-- 03

            worksheet.merge_range('E8:E9', 'Merged Cells', merge_format)
            worksheet.write('E8', 'UNIDAD NEGOCIO', cell_format_titu)               #-- 06
            worksheet.merge_range('F8:F9', 'Merged Cells', merge_format)
            worksheet.write('F8', 'CARGO', cell_format_titu)                       #-- 03
            worksheet.merge_range('G8:G9', 'Merged Cells', merge_format)
            worksheet.write('G8', 'DEPARTAMENTO', cell_format_titu)                       #-- 03

            worksheet.merge_range('H8:H9', 'Merged Cells', merge_format)
            worksheet.write('H8', 'CENTRO COSTO', cell_format_titu)                         #-- 04
            worksheet.merge_range('I8:I9', 'Merged Cells', merge_format)
            worksheet.write('I8', 'FECHA INGRESO', cell_format_titu)                #-- 05
            worksheet.merge_range('J8:J9', 'Merged Cells', merge_format)
            worksheet.write('J8', 'MONEDA', cell_format_titu)                       #-- 07
            worksheet.merge_range('K8:K9', 'Merged Cells', merge_format)
            worksheet.write('K8', 'DIAS COMPUTADOS', cell_format_tut5)             #-- 08

            worksheet.write('L8', 'SALARIO MENSUAL', cell_format_tit2)             #-- 32  SALARIO MENSUAL
            worksheet.write('M8', 'MOVILIDAD', cell_format_titu)                   #-- 09
            worksheet.write('N8', 'VALE ALIMENTOS', cell_format_titu)              #-- 10
            worksheet.write('O8', 'CONDICS. LABORALES', cell_format_titu)          #-- 11   ACUERDOS CONTRACTUALES
            worksheet.write('P8', 'BONIFIC. EDUCACIÓN', cell_format_titu)          #-- 12
            worksheet.write('Q8', 'UTILIDAD. VOLUNTARS', cell_format_titu)         #-- 13

            worksheet.write('R8', 'DESCTO INASISTEN', cell_format_titu)              #-- 14
            worksheet.write('S8', 'DIAS SIN GOCE', cell_format_titu)               #-- 15
            worksheet.write('T8', 'ADELANTO SUELDO', cell_format_titu)             #-- 16   REGISTRO EGRESOS
            worksheet.write('U8', 'MINUTOS TARDANZA', cell_format_titu)            #-- 17
            worksheet.write('V8', 'RETENCIÓN JUDICIAL', cell_format_titu)          #-- 18
            worksheet.write('W8', 'DSCTO. PRÉSTAMOS', cell_format_titu)            #-- 19

            worksheet.write('Y8', 'SUELDO BÁSICO', cell_format_tit1)            #-- 21
            worksheet.write('Z8', 'ASIGNACIÓN FAMILIAR', cell_format_tit1)      #-- 22
            worksheet.write('AA8', 'LICENCIA CON G.HABER', cell_format_tit1)     #-- 23
            worksheet.write('AB8', 'LICENCIA x FALLECMTO', cell_format_tit1)     #-- 24
            worksheet.write('AC8', 'LICENCIA MATER/PATER', cell_format_tit1)     #-- 25      INGRESOS
            worksheet.write('AD8', 'BONIFIC x CUPLIMTO', cell_format_tit1)      #-- 26
            worksheet.write('AE8', 'DESCANSO MÉDICO', cell_format_tit1)         #-- 27
            worksheet.write('AF8', 'FERIADOS', cell_format_tit1)                #-- 28
            worksheet.write('AG8', 'HORAS EXTRAS', cell_format_tit1)            #-- 29
            worksheet.write('AH8', 'VACACIONES', cell_format_tit1)              #-- 30
            worksheet.write('AI8', 'DESCANSO VACACIONAL', cell_format_tit1)     #-- 31
            worksheet.write('AJ8', 'REINTEGRO AFECTO', cell_format_tit1)            #-- 32   AQUI BORRAR -------------------

            worksheet.write('AK8', 'ALIMENTACIÓN', cell_format_tit2)            #-- 32
            worksheet.write('AL8', 'MOVILIDAD', cell_format_tit2)               #-- 33
            worksheet.write('AM8', 'CONDIC LABORLS', cell_format_tit2)          #-- 34      NO REMUNERATIVOS
            worksheet.write('AN8', 'BONIFICAC. x EDUC', cell_format_tit2)       #-- 35
            worksheet.write('AO8', 'UTILIDAD VOLUNT', cell_format_tit2)         #-- 36
            worksheet.write('AP8', 'VALE COMBUSTIBLE', cell_format_tit2)           #-- 37

            worksheet.write('AQ8', 'VACACIONES TRUNCAS', cell_format_sub8)       #-- 38
            worksheet.write('AR8', 'CTS TRUNCO', cell_format_sub8)               #-- 39
            worksheet.write('AS8', 'GRATIFIC TRUNCA', cell_format_sub8)          #-- 40     LIQUIDACIÓN
            worksheet.write('AT8', 'BONIF.GRATI TRUNCA', cell_format_sub8)       #-- 41

            worksheet.merge_range('AU8:AV8', 'Merged Cells', merge_format)
            worksheet.write('AU8', 'REINTEGROS', cell_format_tit8)

            worksheet.merge_range('AW8:AY8', 'Merged Cells', merge_format)
            worksheet.write('AW8', 'DESCUENTOS LBS ( - )', cell_format_sub8)

            worksheet.write('AZ8', 'LICEN SIN GOCE:', cell_format_tit3)         #-- 42
            worksheet.write('BA8', 'ADELANTO SUELDO', cell_format_tit3)         #-- 43
            worksheet.merge_range('BB8:BD8', 'Merged Cells', merge_format)
            worksheet.write('BB8', 'AFP / ONP', cell_format_tit31)
            worksheet.write('BE8', 'INASISTENCIAS', cell_format_tit3)           #-- 45
            worksheet.write('BF8', 'TARDANZAS', cell_format_tit3)               #-- 46      DESCUENTOS
            worksheet.write('BG8', 'RENTA 5TA.CAT', cell_format_tit3)           #-- 47
            worksheet.write('BH8', 'RETEN JUDIC (Alimentos)', cell_format_tit3) #-- 48
            worksheet.write('BI8', 'DESCTO NO DEDUCIBLE', cell_format_tit3)     #-- 49
            worksheet.write('BJ8', 'APORTES EPS', cell_format_tit3)             #-- 50
            worksheet.write('BK8', 'DESCUENTO VALES', cell_format_tit3)
            worksheet.write('BL8', 'OTROS DESCUENTOS', cell_format_tit3)

            worksheet.write('BM8', 'ADELANT REMUNERAC', cell_format_tit4)       #-- 51
            worksheet.write('BN8', 'REMMB MOVILIDAD', cell_format_tit4)         #-- 52      INCREMENTOS DIRECTOS
            worksheet.write('BO8', 'ADELANTO GRATIFIC', cell_format_tit4)       #-- 53
            worksheet.write('BP8', 'IDEMNIZAC DESPIDO', cell_format_tit4)       #-- 54
            worksheet.write('BQ8', 'DEVOLUCIÓN DSCTO INDEB', cell_format_tit4)  #-- 55
            worksheet.write('BR8', 'REINTEGROS INAFECTOS', cell_format_tit4)    #-- 55

            worksheet.write('BT8', 'TOTAL INGRESOS', cell_format_tit5)          #-- 57
            worksheet.write('BU8', 'TOTAL C-N-R', cell_format_tit5)             #-- 58
            worksheet.write('BV8', 'TOTAL DESCTOS', cell_format_tit5)           #-- 59      RESUMEN
            worksheet.write('BW8', 'TOTAL INCR.DIREC', cell_format_tit5)        #-- 60
            worksheet.write('BX8', 'TOT CONCEPT LBS', cell_format_tit8)         #-- 58
            worksheet.write('BY8', 'TOTAL-NETO', cell_format_tit5)              #-- 59

            worksheet.write('CA8', 'ESSALUD', cell_format_tit6)                 #-- 61      APORTES
            worksheet.write('CB8', 'EPS', cell_format_tit6)                     #-- 62
            worksheet.write('CC8', 'CTS', cell_format_tit7)                     #-- 63      PROVISIONES
            worksheet.write('CD8', 'VACACIONES', cell_format_tit7)              #-- 64
            worksheet.write('CE8', 'GRATIFICAC', cell_format_tit7)              #-- 65
            worksheet.write('CF8', 'BONIFIC GRATIFIC', cell_format_tit7)        #-- 66

            worksheet.write('CH8', 'COSTO EMPLEADO', cell_format_tit5)          #-- 68

            worksheet.write('CJ8', 'BANCO', cell_format_tit7)                   #-- 64
            worksheet.write('CK8', 'CUENTA', cell_format_tit7)                  #-- 65      DETALLE CTAS BANCARIAS
            worksheet.write('CL8', 'CCI', cell_format_tit7)                     #-- 66

            worksheet.merge_range('CN8:CN9', 'Merged Cells', merge_format)
            worksheet.write('CN8', 'COMPAÑIA', cell_format_tit7)                #-- 79
            worksheet.merge_range('CO8:CO9', 'Merged Cells', merge_format)
            worksheet.write('CO8', 'IMPORTE OBLIGATORIO', cell_format_tit7)     #-- 80
            worksheet.merge_range('CP8:CP9', 'Merged Cells', merge_format)
            worksheet.write('CP8', 'PRIMA SEGURO', cell_format_tit7)            #-- 81      DESAGREGADO AFP
            worksheet.merge_range('CQ8:CS8', 'Merged Cells', merge_format)
            worksheet.write('CQ8', 'COMISIÓN', cell_format_tit6)
            # worksheet.write('CE8', 'TIPO COMISIÓN', cell_format_tit7)           #-- 82
            # worksheet.write('CF8', 'COMISIÓN MIXTA', cell_format_tit7)          #-- 83
            # worksheet.write('CG8', 'COMISIÓN FLUJO', cell_format_tit7)          #-- 84

            worksheet.merge_range('CT8:CU8', 'Merged Cells', merge_format)
            worksheet.write('CT8', 'TOTALES', cell_format_tit31)
            # worksheet.write('CH8', 'AFP', cell_format_tit7)                     #-- 86      TOTAL AFP/ONP
            # worksheet.write('CI8', 'ONP', cell_format_tit7)                     #-- 87

            worksheet.write('CW8', 'AFP/ONP', cell_format_tit7)                     #-- 87
            worksheet.write('CX8', 'FECHA CESE', cell_format_tit7)                     #-- 87


            #----------------------------------------------------------------
            # worksheet.write('I9', 'DIAS', cell_format_tut3)                 #-- 09
            worksheet.write('L9', '(Contrato)', cell_format_sub2)         #-- 34
            worksheet.write('M9', 'S/.', cell_format_tut4)                 #-- 12
            worksheet.write('N9', 'S/.', cell_format_tut4)                 #-- 13
            worksheet.write('O9', 'S/.', cell_format_tut4)                 #-- 15
            worksheet.write('P9', 'S/.', cell_format_tut4)                  #-- 16
            worksheet.write('Q9', 'S/.', cell_format_tut4)                  #-- 17
            worksheet.write('R9', 'S/.', cell_format_tut4)                  #-- 18
            worksheet.write('S9', 'S/.', cell_format_tut4)                  #-- 19
            worksheet.write('T9', 'S/.', cell_format_tut4)                  #-- 20
            worksheet.write('U9', 'S/.', cell_format_tut4)                  #-- 21
            worksheet.write('V9', 'S/.', cell_format_tut4)                 #-- 10
            worksheet.write('W9', 'S/.', cell_format_tut4)                 #-- 11
            

            worksheet.write('Y9', '(+)', cell_format_sub1)         #-- 25
            worksheet.write('Z9', '(+)', cell_format_sub1)         #-- 26
            worksheet.write('AA9', '(+)', cell_format_sub1)         #-- 27      INGRESOS
            worksheet.write('AB9', '(+)', cell_format_sub1)         #-- 28
            worksheet.write('AC9', '(+)', cell_format_sub1)         #-- 29
            worksheet.write('AD9', '(+)', cell_format_sub1)         #-- 30
            worksheet.write('AE9', '(+)', cell_format_sub1)         #-- 31
            worksheet.write('AF9', '(+)', cell_format_sub1)         #-- 32
            worksheet.write('AG9', '(+)', cell_format_sub1)         #-- 33
            worksheet.write('AH9', '(+)', cell_format_sub1)         #-- 23
            worksheet.write('AI9', '(+)', cell_format_sub1)         #-- 24
            worksheet.write('AJ9', '(+)', cell_format_sub1)         #-- 34

            worksheet.write('AK9', '(n)', cell_format_sub2)         #-- 34
            worksheet.write('AL9', '(n)', cell_format_sub2)         #-- 35
            worksheet.write('AM9', '(n)', cell_format_sub2)         #-- 36      NO REMUNERAIVOS
            worksheet.write('AN9', '(n)', cell_format_sub2)         #-- 37
            worksheet.write('AO9', '(n)', cell_format_sub2)         #-- 38
            worksheet.write('AP9', '(n)', cell_format_sub2)         #-- 39
            
            worksheet.write('AQ9', '(Cese)', cell_format_tit8)         #-- 40
            worksheet.write('AR9', '(Cese)', cell_format_tit8)         #-- 41
            worksheet.write('AS9', '(Cese)', cell_format_tit8)         #-- 42      LIQUIDACIONES
            worksheet.write('AT9', '(Cese)', cell_format_tit8)         #-- 43

            worksheet.write('AU9', 'AFECTO', cell_format_sub8)         #--          REINTEGROS
            worksheet.write('AV9', 'INAFECTO', cell_format_sub8)

            worksheet.write('AW9', 'AFP/ONP', cell_format_tit8)
            worksheet.write('AX9', 'RENTA 5TA', cell_format_tit8)      #--          DESCUENTOS
            worksheet.write('AY9', 'OTROS', cell_format_tit8)

            worksheet.write('AZ9', '(-)', cell_format_sub3)         #-- 44
            worksheet.write('BA9', '(-)', cell_format_sub3)         #-- 45
            worksheet.write('BB9', 'COMPAÑIA', cell_format_sub31)         #-- 46
            worksheet.write('BC9', 'AFP', cell_format_sub31)         #-- 46
            worksheet.write('BD9', 'ONP', cell_format_sub31)         #-- 46
            worksheet.write('BE9', '(-)', cell_format_sub3)         #-- 47
            worksheet.write('BF9', '(-)', cell_format_sub3)         #-- 48      DESCUENTOS
            worksheet.write('BG9', '(-)', cell_format_sub3)         #-- 49
            worksheet.write('BH9', '(-)', cell_format_sub3)         #-- 50
            worksheet.write('BI9', '(-)', cell_format_sub3)         #-- 51
            worksheet.write('BJ9', '(-)', cell_format_sub3)         #-- 52
            worksheet.write('BK9', '(-)', cell_format_sub3)
            worksheet.write('BL9', '(-)', cell_format_sub3)

            worksheet.write('BM9', '(d)', cell_format_sub4)         #-- 53
            worksheet.write('BN9', '(d)', cell_format_sub4)         #-- 54      INCREMENTOS DIRECTOS
            worksheet.write('BO9', '(d)', cell_format_sub4)         #-- 55
            worksheet.write('BP9', '(d)', cell_format_sub4)         #-- 56
            worksheet.write('BQ9', '(d)', cell_format_sub4)         #-- 57
            worksheet.write('BR9', '(d)', cell_format_sub4)

            worksheet.write('BT9', '(Acum)', cell_format_tit1)         #-- 64
            worksheet.write('BU9', '(Acum)', cell_format_tit2)         #-- 65      RESUMEN TOTALIZADO
            worksheet.write('BV9', '(Acum)', cell_format_tit3)         #-- 66
            worksheet.write('BW9', '(Acum)', cell_format_tit4)         #-- 67
            worksheet.write('BX9', '(Acum)', cell_format_tit4)         #-- 67
            worksheet.write('BY9', '(Acum)', cell_format_sub5)         #-- 68

            worksheet.write('CA9', '(Empr)', cell_format_sub6)         #-- 70      APORTES
            worksheet.write('CB9', '(Empr)', cell_format_sub6)         #-- 71
            worksheet.write('CC9', '(Empr)', cell_format_sub7)         #-- 72      PROVISIONES
            worksheet.write('CD9', '(Empr)', cell_format_sub7)         #-- 73
            worksheet.write('CE9', '(Empr)', cell_format_sub7)         #-- 74
            worksheet.write('CF9', '(Empr)', cell_format_sub7)         #-- 75

            worksheet.write('CH9', '(Mensual)', cell_format_sub5)      #-- 75      COSTO MENSUAL

            worksheet.write('CJ9', 'FINANCIERA', cell_format_sub6)         #-- 70      COMISIÓN
            worksheet.write('CK9', '(Número)', cell_format_sub6)         #-- 71
            worksheet.write('CL9', '(Número)', cell_format_sub6)         #-- 72

            worksheet.write('CQ9', 'TIPO', cell_format_sub6)         #-- 70      COMISIÓN
            worksheet.write('CR9', 'MIXTA', cell_format_sub6)         #-- 71
            worksheet.write('CS9', 'FLUJO', cell_format_sub6)         #-- 72

            worksheet.write('CT9', 'AFP', cell_format_sub7)         #-- 73      TOTALES
            worksheet.write('CU9', 'ONP', cell_format_sub7)         #-- 74

            worksheet.write('CW9', 'Descuento', cell_format_sub7)         #-- 74    AFP/ONP
            worksheet.write('CX9', 'dd/mm/aaaa', cell_format_sub7)         #-- 76   FECHA DE CESES

            #-----
            #worksheet.autofilter(8, 2, 8, 8)    #--- Coloca FILTROS en datos generales
            #worksheet.autofilter(8, 22, 8, 32)  #--- Coloca FILTROS en Ingresos
            #worksheet.autofilter(8, 33, 8, 38)  #--- Coloca FILTROS en Conceptos No Remunerativos
            #worksheet.autofilter(8, 39, 8, 42)  #--- Coloca FILTROS en Liquidación
            #worksheet.autofilter(8, 43, 8, 52)  #--- Coloca FILTROS en Descuentos
            #worksheet.autofilter(8, 53, 8, 57)  #--- Coloca FILTROS en Incrementos Indirectos   
            worksheet.autofilter(8, 67, 8, 72)  #--- Coloca FILTROS en RESUMEN
            #-----
            worksheet.freeze_panes(9, 4)    #--- Inmoviliza Paneles


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
                'x_studio_dias_computados',
                'x_studio_licencia_fallecimiento',
                'x_studio_licencia_materpater',
                'x_studio_dias_vacaciones',
                'x_studio_dias_con_goce',
                'x_studio_descanso_medico',
                'x_studio_edit_feriados',
                'x_studio_feriados_dias',
                'x_studio_feriados_importe',
                'x_studio_bonificacion_extraordinaria',
                'x_studio_horas_extras_importe',
                'x_studio_reembolso',
                'x_studio_reembolso_movilidad',
                'x_studio_reembolso_combustible',
                'x_studio_movilidad',
                'x_studio_vale_alimentos',
                'x_studio_condiciones_laborales',
                'x_studio_bonificacion_educacion',
                'x_studio_utilidades_voluntarias',
                'x_studio_adelanto_gratificacion',
                'x_studio_descuento_inasistencias',
                'x_studio_dias_sin_goce',
                'x_studio_adelanto_sueldo',
                'x_studio_descuento_tardanzas_min',
                'x_studio_retencion_judicial',
                'x_studio_descuento_prestamos'
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
            w_switch = 0
            w_acum_tota_1 = 0
 
            for w_boleta in w_lote:
                current_format_cent = cell_format_cesado_cent if w_boleta.x_studio_cesado else cell_format_cent
                current_format_left = cell_format_cesado_left if w_boleta.x_studio_cesado else cell_format_left
                current_format_impo = cell_format_cesado_impo if w_boleta.x_studio_cesado else cell_format_impo
                current_format_fech = cell_format_cesado_fech if w_boleta.x_studio_cesado else cell_format_fech
                current_format_nume = cell_format_cesado_nume if w_boleta.x_studio_cesado else cell_format_nume
                current_format_imp2 = cell_format_cesado_impo if w_boleta.x_studio_cesado else cell_format_imp2
       
                if w_boleta.x_studio_cesado:
                    worksheet.write(w_fila, 0, 'CESADO', cell_format_rojo)
                    #-----
                    w_titu  = 'DETALLES DEL CESE'+'\n'+'---------------------------------------'+'\n'
                    w_comen = ''
                    # Formatear fecha de cese (DATE)
                    cese_fecha = w_boleta.x_studio_cese_fecha
                    cese_fecha_str = cese_fecha.strftime('%d/%m/%Y') if cese_fecha else ''
                    w_comen += 'F.CESE:  '+ cese_fecha_str +'\n'

                    # Obtener nombre del motivo (many2one)
                    # cese_motivo = w_boleta.x_studio_cese_motivo.name if w_boleta.x_studio_cese_motivo else ''
                    cese_motivo = w_boleta.x_studio_cese_motivo
                    w_comen += 'MOTIVO:  '+ cese_motivo +'\n'

                    # Campo CHAR (verificar si es None o False)
                    observaciones = w_boleta.x_studio_cese_observaciones or ''
                    w_comen += 'OBSERV:  '+ observaciones +'\n'

                    # Formatear fecha de ingreso (DATE)
                    fecha_ingreso = w_boleta.x_studio_fecha_ingreso_laboral
                    fecha_ingreso_str = fecha_ingreso.strftime('%d/%m/%Y') if fecha_ingreso else ''
                    w_comen += 'F.INGR:  '+ fecha_ingreso_str +'\n' +'\n'

                    # Campo TEXT (verificar si es None o False)
                    comentarios = w_boleta.x_studio_cese_comentarios or ''
                    w_comen += 'COMENTARIOS'+'\n'+'---------------------------------------'+'\n'
                    w_comen += comentarios +'\n'

                    worksheet.write_comment(w_fila, 0, w_titu + w_comen, {
                                            'author': 'CENS-PERÚ',
                                            'width': 400,  # pixels
                                            'height': 200,
                                            'color': '#f5e69b',
                                            'font_name': 'Courier New'
                                })
                else:
                    worksheet.write(w_fila, 0, w_fila-8, cell_format_cent)
                # worksheet.write(w_fila, 0, w_boleta.id, cell_format_cent)   
                worksheet.write(w_fila, 1, w_boleta.number, current_format_cent)
                w_dato = w_boleta.employee_id.name
                worksheet.write(w_fila, 2, w_dato, current_format_left)
                worksheet.write(w_fila, 3, w_boleta.x_studio_dni, current_format_cent)

                w_dato = w_boleta.employee_id.x_studio_unidad_negocio
                worksheet.write(w_fila, 4, w_dato, current_format_cent)

                w_dato = w_boleta.employee_id.job_id.name
                worksheet.write(w_fila, 5, w_dato, current_format_cent)

                w_dato = w_boleta.employee_id.department_id.name
                worksheet.write(w_fila, 6, w_dato, current_format_cent)

                # w_dato = w_boleta.payslip_run_id.name
                w_dato = ""
                w_mes = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').month
                w_dia = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').day
                w_ano = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').year
                w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)[:3]
                #worksheet.write(w_fila, 7, w_dato, current_format_cent)
                
                # w_opci 
                if (w_boleta.employee_id.x_studio_centro_de_costos):
                    w_opci = int(w_boleta.employee_id.x_studio_centro_de_costos)
                else:
                    w_opci = 0
                w_dato = self.centro_costo(w_opci).upper()
                worksheet.write(w_fila, 7, w_dato, current_format_cent)

                if (w_switch == 0):
                    w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)
                    worksheet.write('H4', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    worksheet.write('AT4', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    w_switch = 1
                
                w_dato = w_boleta.employee_id.first_contract_date
                worksheet.write(w_fila, 8, w_dato, current_format_fech)
                
                w_dato = w_boleta.currency_id.name
                worksheet.write(w_fila, 9, w_dato, current_format_cent)
                # ----------------------------
                # -- REGISTRO INGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 10, w_boleta.x_studio_dias_computados, current_format_nume)
                worksheet.write(w_fila, 11, w_boleta.x_studio_salario_mensual, current_format_impo)
                worksheet.write(w_fila, 12, w_boleta.x_studio_movilidad, current_format_impo)
                worksheet.write(w_fila, 13, w_boleta.x_studio_vale_alimentos, current_format_impo)
                worksheet.write(w_fila, 14, w_boleta.x_studio_condiciones_laborales, current_format_impo)
                worksheet.write(w_fila, 15, w_boleta.x_studio_bonificacion_educacion, current_format_impo)
                worksheet.write(w_fila, 16, w_boleta.x_studio_utilidades_voluntarias, current_format_impo)
                # ----------------------------
                # -- REGISTRO EGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 17, w_boleta.x_studio_descuento_inasistencias, current_format_impo)
                worksheet.write(w_fila, 18, w_boleta.x_studio_dias_sin_goce, current_format_impo)
                worksheet.write(w_fila, 19, w_boleta.x_studio_adelanto_sueldo, current_format_impo)
                worksheet.write(w_fila, 20, w_boleta.x_studio_descuento_tardanzas_min, current_format_impo)
                worksheet.write(w_fila, 21, w_boleta.x_studio_retencion_judicial, current_format_impo)
                worksheet.write(w_fila, 22, w_boleta.x_studio_descuento_prestamos, current_format_impo)
                
                # ----------------------------------------------------------------------------------------
                # -- DATOS CALCULADOS FINALES PLANILLA -- DATOS QUE INGRESAN A LA BOLETA DE PAGO
                # ----------------------------------------------------------------------------------------
                #
                # -----------------------------------------
                # BOLETA PAGO - INGRESOS
                # -----------------------------------------
                worksheet.write(w_fila, 24, w_boleta.x_studio_en_basico, current_format_impo)
                worksheet.write(w_fila, 25, w_boleta.x_studio_en_asignacion_familiar, current_format_impo)
                worksheet.write(w_fila, 26, w_boleta.x_studio_en_licencia_con_ghaber, current_format_impo)
                worksheet.write(w_fila, 27, w_boleta.x_studio_en_licencia_fallecimiento, current_format_impo)
                worksheet.write(w_fila, 28, w_boleta.x_studio_en_licencia_materpater, current_format_impo)
                worksheet.write(w_fila, 29, w_boleta.x_studio_en_bonificacion_cumplimiento, current_format_impo)
                worksheet.write(w_fila, 30, w_boleta.x_studio_en_descanso_medico, current_format_impo)
                worksheet.write(w_fila, 31, w_boleta.x_studio_en_feriados, current_format_impo)
                worksheet.write(w_fila, 32, w_boleta.x_studio_en_horas_extras, current_format_impo)
                worksheet.write(w_fila, 33, w_boleta.x_studio_en_vacaciones, current_format_impo)
                worksheet.write(w_fila, 34, w_boleta.x_studio_en_descanso_vacacional, current_format_impo)
                worksheet.write(w_fila, 35, w_boleta.x_studio_en_reintegro_afecto, current_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - CONCEPTOS NO REMUNERATIVOS
                # -----------------------------------------
                worksheet.write(w_fila, 36, w_boleta.x_studio_en_vale_alimentacion, current_format_impo)
                worksheet.write(w_fila, 37, w_boleta.x_studio_en_vale_movilidad, current_format_impo)
                worksheet.write(w_fila, 38, w_boleta.x_studio_en_condiciones_laborales, current_format_impo)
                worksheet.write(w_fila, 39, w_boleta.x_studio_en_bonificacion_educacion, current_format_impo)
                worksheet.write(w_fila, 40, w_boleta.x_studio_en_utilidades_voluntarias, current_format_impo)
                worksheet.write(w_fila, 41, w_boleta.x_studio_en_vale_combustible, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - CONCEPTOS DE LIQUIDACIÓN  - ASIGNAR CAMPOS REALES
                # -----------------------------------------
                worksheet.write(w_fila, 42, w_boleta.x_studio_cese_vaca_trunca, current_format_impo)
                worksheet.write(w_fila, 43, w_boleta.x_studio_cese_cts_trunco, current_format_impo)
                worksheet.write(w_fila, 44, w_boleta.x_studio_cese_grati_trunca, current_format_impo)
                worksheet.write(w_fila, 45, w_boleta.x_studio_cese_bonif_grati_trunca, current_format_impo)

                worksheet.write(w_fila, 46, w_boleta.x_studio_reintegros_afectos, current_format_impo)
                worksheet.write(w_fila, 47, w_boleta.x_studio_reintegros_inafectos, current_format_impo)

                worksheet.write(w_fila, 48, -w_boleta.x_studio_cese_descuento_afp, current_format_impo)
                worksheet.write(w_fila, 49, -w_boleta.x_studio_cese_descuento_renta_5ta, current_format_impo)
                worksheet.write(w_fila, 50, -w_boleta.x_studio_cese_otros_descuentos, current_format_impo)


                # -----------------------------------------
                # BOLETA PAGO - DESCUENTOS
                # -----------------------------------------
                worksheet.write(w_fila, 51, w_boleta.x_studio_en_licencia_sin_ghaber, current_format_impo)
                worksheet.write(w_fila, 52, w_boleta.x_studio_en_adelanto_sueldo, current_format_impo)
                if (w_boleta.x_studio_compania_afp):
                    w_nombre_cia = w_boleta.x_studio_compania_afp.x_name
                    worksheet.write(w_fila, 53, w_nombre_cia, current_format_left)
                    if (w_nombre_cia == 'ONP'):
                        worksheet.write(w_fila, 54, " ", current_format_impo)
                        worksheet.write(w_fila, 55, w_boleta.x_studio_en_afp_onp, current_format_impo)
                    else:
                        worksheet.write(w_fila, 54, w_boleta.x_studio_en_afp_onp, current_format_impo)
                        worksheet.write(w_fila, 55, " ", current_format_impo)

                worksheet.write(w_fila, 56, w_boleta.x_studio_en_inasistencias, current_format_impo)
                worksheet.write(w_fila, 57, w_boleta.x_studio_en_tardanzas, current_format_impo)
                worksheet.write(w_fila, 58, w_boleta.x_studio_en_renta_5ta, current_format_impo)
                worksheet.write(w_fila, 59, w_boleta.x_studio_en_retencion_judicial, current_format_impo)
                worksheet.write(w_fila, 60, w_boleta.x_studio_en_descuento_prestamos, current_format_impo)
                worksheet.write(w_fila, 61, w_boleta.x_studio_aporte_eps_2, current_format_impo)
                worksheet.write(w_fila, 62, w_boleta.x_studio_en_descuento_vales, current_format_impo)
                worksheet.write(w_fila, 63, w_boleta.x_studio_en_otros_descuentos, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - INCREMENTOS DIRECTOS
                # -----------------------------------------
                worksheet.write(w_fila, 64, w_boleta.x_studio_en_reembolso, current_format_impo)
                worksheet.write(w_fila, 65, w_boleta.x_studio_en_reembolso_movilidad, current_format_impo)
                worksheet.write(w_fila, 66, w_boleta.x_studio_en_adelanto_gratificacion, current_format_impo)
                worksheet.write(w_fila, 67, w_boleta.x_studio_en_indemniza_despido_arbitrario, current_format_impo)
                worksheet.write(w_fila, 68, w_boleta.x_studio_especial_ac, current_format_impo)
                worksheet.write(w_fila, 69, w_boleta.x_studio_en_reintegro_inafecto, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - TOTALIZADO RESUMEN
                # -----------------------------------------
                w_tota_lbs = 0
                w_tota_lbs += w_boleta.x_studio_cese_vaca_trunca
                w_tota_lbs += w_boleta.x_studio_cese_cts_trunco
                w_tota_lbs += w_boleta.x_studio_cese_grati_trunca
                w_tota_lbs += w_boleta.x_studio_cese_bonif_grati_trunca
                w_tota_lbs -= w_boleta.x_studio_cese_descuento_afp
                w_tota_lbs -= w_boleta.x_studio_cese_descuento_renta_5ta
                w_tota_lbs -= w_boleta.x_studio_cese_otros_descuentos

                worksheet.write(w_fila, 71, w_boleta.x_studio_en_gross, current_format_impo)
                worksheet.write(w_fila, 72, w_boleta.x_studio_en_total_remuneracion_bruta, current_format_impo)
                worksheet.write(w_fila, 73, -w_boleta.x_studio_total_descuentos, current_format_impo)
                worksheet.write(w_fila, 74, w_boleta.x_studio_sub_total_incremespeciales, current_format_impo)
                worksheet.write(w_fila, 75, w_tota_lbs, current_format_impo)
                w_tota_gen = w_boleta.x_studio_en_total_remuneracion + w_tota_lbs
                worksheet.write(w_fila, 76, w_tota_gen, current_format_imp2)
                w_acum_tota_1 += w_tota_gen

                # -----------------------------------------
                # APORTES
                # -----------------------------------------
                worksheet.write(w_fila, 78, w_boleta.x_studio_aporte_a_essalud, current_format_impo)
                worksheet.write(w_fila, 79, w_boleta.x_studio_en_aportes_eps, current_format_impo)
                # -----------------------------------------
                # PROVISIONES
                # -----------------------------------------
                worksheet.write(w_fila, 80, w_boleta.x_studio_en_provision_cts, current_format_impo)
                worksheet.write(w_fila, 81, w_boleta.x_studio_en_provision_vacaciones, current_format_impo)
                worksheet.write(w_fila, 82, w_boleta.x_studio_en_provision_gratificacion, current_format_impo)
                worksheet.write(w_fila, 83, w_boleta.x_studio_en_provision_bonigrati, current_format_impo)
                # -----------------------------------------
                # COSTO DEL MES
                # -----------------------------------------
                # CÁLCULO: Para obtener el Costo del mes
                #  
                # - Sueldo Básico                   x_studio_en_basico
                # - Asignación Familiar             x_studio_en_asignacion_familiar
                # - Lic. con Goce Haber             x_studio_en_licencia_con_ghaber
                # - Lic. x Fallecimiento            x_studio_en_licencia_fallecimiento
                # - Bonific.x Cumplimiento          x_studio_en_bonificacion_cumplimiento
                # - Descanso Médico                 x_studio_en_descanso_medico
                # - Feriados                        x_studio_en_feriados
                # - Horas Extras                    x_studio_en_horas_extras
                # - Reembolso x Movilidad           x_studio_en_reembolso_movilidad
                # - Indemnización x Despido         x_studio_en_indemniza_despido_arbitrario
                # - TOTAL No remunerativos (NR)     x_studio_en_total_remuneracion_bruta
                # - Aporte ESSALUD                  x_studio_aporte_a_essalud
                # - Aporte EPS                      x_studio_en_aportes_eps
                # - Provisión CTS                   x_studio_en_provision_cts
                # - Provisión Vacaciones            x_studio_en_provision_vacaciones
                # - Provisión Gratificacaión        x_studio_en_provision_gratificacion
                # - Provisión Bonific.Gratific.     x_studio_en_provision_bonigrati
                # - 
                w_total_costo = 0.00
                w_total_costo += w_boleta.x_studio_en_basico
                w_total_costo += w_boleta.x_studio_en_asignacion_familiar
                w_total_costo += w_boleta.x_studio_en_licencia_con_ghaber
                w_total_costo += w_boleta.x_studio_en_licencia_fallecimiento
                w_total_costo += w_boleta.x_studio_en_bonificacion_cumplimiento
                w_total_costo += w_boleta.x_studio_en_descanso_medico
                w_total_costo += w_boleta.x_studio_en_feriados
                w_total_costo += w_boleta.x_studio_en_horas_extras
                w_total_costo += w_boleta.x_studio_en_reembolso_movilidad
                w_total_costo += w_boleta.x_studio_en_indemniza_despido_arbitrario
                w_total_costo += w_boleta.x_studio_en_total_remuneracion_bruta
                w_total_costo += w_boleta.x_studio_aporte_a_essalud
                w_total_costo += w_boleta.x_studio_en_aportes_eps
                w_total_costo += w_boleta.x_studio_en_provision_cts
                w_total_costo += w_boleta.x_studio_en_provision_vacaciones
                w_total_costo += w_boleta.x_studio_en_provision_gratificacion
                w_total_costo += w_boleta.x_studio_en_provision_bonigrati
                worksheet.write(w_fila, 85, w_total_costo, current_format_imp2)

                # -----------------------------------------
                # DETALLE CUENTA BANCARIA
                # -----------------------------------------
                w_dato = w_boleta.employee_id.x_studio_nombre_banco
                worksheet.write(w_fila, 87, w_dato, current_format_imp2)

                w_dato = w_boleta.employee_id.x_studio_numero_cuenta
                worksheet.write(w_fila, 88, w_dato, current_format_imp2)

                w_dato = w_boleta.employee_id.x_studio_cci
                worksheet.write(w_fila, 89, w_dato, current_format_imp2)

                # -----------------------------------------
                # DESAGREGADO DE AFP/ONP
                # -----------------------------------------
                if (w_boleta.x_studio_compania_afp):
                    w_nombre_cia = w_boleta.x_studio_compania_afp.x_name
                    w_tota_afp = w_boleta.x_studio_cese_descuento_afp

                    worksheet.write(w_fila, 91, w_nombre_cia, current_format_left)
                    if (w_nombre_cia == 'ONP'):
                        w_tota_afp += w_boleta.x_studio_en_afp_onp
                        worksheet.write(w_fila, 98, w_tota_afp, current_format_impo)
                    else:
                        worksheet.write(w_fila, 92, w_boleta.x_studio_en_afp_aporte_obligatorio, current_format_impo)
                        worksheet.write(w_fila, 93, w_boleta.x_studio_en_afp_prima_seguro, current_format_impo)
                        # w_boleta.x_studio_en_tipo_comision
                        worksheet.write(w_fila, 94, w_boleta.x_studio_en_tipo_comision, current_format_cent)
                        if (w_boleta.x_studio_en_tipo_comision == 'MIX'):
                            worksheet.write(w_fila, 95, w_boleta.x_studio_en_comision_mixta, current_format_impo)
                        if (w_boleta.x_studio_en_tipo_comision == 'FLU'):
                            worksheet.write(w_fila, 96, w_boleta.x_studio_en_comision_flujo, current_format_impo)

                        w_tota_afp += w_boleta.x_studio_en_afp_onp
                        worksheet.write(w_fila, 97, w_tota_afp, current_format_impo)

                #
                # FECHA DE CESE
                #
                if w_boleta.x_studio_cesado:
                    worksheet.write(w_fila, 99, "Inc.Liq.", current_format_left)
                    worksheet.write(w_fila, 100, w_boleta.x_studio_cese_descuento_afp, current_format_impo)
                    worksheet.write(w_fila, 101, w_boleta.x_studio_cese_fecha, current_format_fech)

                w_fila += 1

            worksheet.write(5, 75, "TOTAL GENERAL:", cell_format_left)
            worksheet.write(5, 76, w_acum_tota_1, cell_format_impo)

            worksheet.activate()
            workbook.close()
            # ------------------------------------------------------------------

            # Crear adjunto
            xlsx_data = output.getvalue()
            attachment = self.env['ir.attachment'].create({
                'name': 'nominas_export.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(xlsx_data),
            })
            
        except Exception as e:
            raise UserError(_('Error al generar el Excel: %s') % str(e))
        finally:
            # Siempre cerrar el buffer
            output.close()

        # Retornar acción para descargar
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def centro_costo(self, ncosto):
        w_costo = ncosto
        w_costo_name = ""
        if (w_costo == 1):
            w_costo_name = "Costo Directo"
        elif (w_costo == 2):
            w_costo_name = "Costo Indirecto"
        elif (w_costo == 3):
            w_costo_name = "Gasto Ventas"
        elif (w_costo == 4):
            w_costo_name = "Gasto General"
        else:
            w_costo_name = "UNDEFINED"
        return w_costo_name
    
    def mes_literal(self, nmes):
        w_mes = nmes
        if (w_mes == 1):
            w_mes_name = "ENERO"
        elif (w_mes == 2):
            w_mes_name = "FEBRERO"
        elif (w_mes == 3):
            w_mes_name = "MARZO"
        elif (w_mes == 4):
            w_mes_name = "ABRIL"
        elif (w_mes == 5):
            w_mes_name = "MAYO"
        elif (w_mes == 6):
            w_mes_name = "JUNIO"
        elif (w_mes == 7):
            w_mes_name = "JULIO"
        elif (w_mes == 8):
            w_mes_name = "AGOSTO"
        elif (w_mes == 9):
            w_mes_name = "SETIEMBRE"
        elif (w_mes == 10):
            w_mes_name = "OCTUBRE"
        elif (w_mes == 11):
            w_mes_name = "NOVIEMBRE"
        elif (w_mes == 12):
            w_mes_name = "DICIEMBRE"
        else:
            w_mes_name = "ERROR"
        return w_mes_name



