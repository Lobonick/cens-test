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
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
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
            cell_format_tit1 = workbook.add_format()
            cell_format_tit2 = workbook.add_format()
            cell_format_tit3 = workbook.add_format()
            cell_format_tit4 = workbook.add_format()
            cell_format_tit5 = workbook.add_format()
            cell_format_tit6 = workbook.add_format()
            cell_format_tit7 = workbook.add_format()
            cell_format_sub1 = workbook.add_format()
            cell_format_sub2 = workbook.add_format()
            cell_format_sub3 = workbook.add_format()
            cell_format_sub4 = workbook.add_format()
            cell_format_sub5 = workbook.add_format()
            cell_format_sub6 = workbook.add_format()
            cell_format_sub7 = workbook.add_format()
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
            # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
            # -------------------------------------------------------------------------------------
            worksheet.set_column(0, 0, 9)       #-- ID Empleado
            worksheet.set_column(1, 1, 14)      #-- Boleta 
            worksheet.set_column(2, 2, 33)      #-- Npombre del Empleado
            worksheet.set_column(3, 3, 13)      #-- DNI
            worksheet.set_column(4, 4, 11)      #-- LOTE
            worksheet.set_column(5, 5, 13)      #-- FECHA INICIAL
            worksheet.set_column(6, 6, 13)      #-- FECHA GINAL
            worksheet.set_column(7, 7, 8)       #-- MONEDA
            worksheet.set_column(8, 8, 11)      #-- 
            worksheet.set_column(9, 9, 10)      #--
            worksheet.set_column(10, 10, 10)    #-- 
            worksheet.set_column(11, 11, 10)    #-- 
            worksheet.set_column(12, 12, 10)    #-- 
            worksheet.set_column(13, 13, 10)    #-- 
            worksheet.set_column(14, 14, 10)    #-- 
            worksheet.set_column(15, 15, 10)    #-- 
            worksheet.set_column(16, 16, 10)    #-- 
            worksheet.set_column(17, 17, 10)    #-- 
            worksheet.set_column(18, 18, 10)    #-- 
            worksheet.set_column(19, 19, 10)    #-- 
            worksheet.set_column(20, 20, 10)    #-- 
            worksheet.set_column(21, 21, 10)    #-- 
            worksheet.set_column(22, 22, 10)    #-- 
            worksheet.set_column(23, 23, 10)    #--
            worksheet.set_column(24, 24, 10)    #--
            worksheet.set_column(25, 25, 10)    #--
            worksheet.set_column(26, 26, 10)    #--
            worksheet.set_column(27, 27, 10)    #--
            worksheet.set_column(28, 28, 10)    #--
            worksheet.set_column(29, 29, 10)    #--
            worksheet.set_column(30, 30, 10)    #--
            worksheet.set_column(31, 31, 10)    #-- 
            worksheet.set_column(32, 32, 10)    #--
            worksheet.set_column(33, 33, 10)    #--

            worksheet.set_column(34, 34, 5)    #--     (Seperador)

            worksheet.set_column(35, 35, 12)    #--
            worksheet.set_column(36, 36, 12)    #-- 
            worksheet.set_column(37, 37, 12)    #--     INGRESOS
            worksheet.set_column(38, 38, 12)    #--
            worksheet.set_column(39, 39, 12)    #--
            worksheet.set_column(40, 40, 12)    #--
            worksheet.set_column(41, 41, 12)    #--
            worksheet.set_column(42, 42, 12)    #--
            worksheet.set_column(43, 43, 12)    #--
            worksheet.set_column(44, 44, 12)    #--

            worksheet.set_column(45, 45, 12)    #--
            worksheet.set_column(46, 46, 12)    #--     NO REMUNERATIVOS
            worksheet.set_column(47, 47, 12)    #--
            worksheet.set_column(48, 48, 12)    #--
            worksheet.set_column(49, 49, 12)    #--
            worksheet.set_column(50, 50, 12)    #--

            worksheet.set_column(51, 51, 12)    #--
            worksheet.set_column(52, 52, 12)    #--
            worksheet.set_column(53, 53, 12)    #--
            worksheet.set_column(54, 54, 12)    #--     DESCUENTOS
            worksheet.set_column(55, 55, 12)    #--
            worksheet.set_column(56, 56, 12)    #--
            worksheet.set_column(57, 57, 12)    #--
            worksheet.set_column(58, 58, 12)    #--
            worksheet.set_column(59, 59, 12)    #--

            worksheet.set_column(60, 60, 12)    #--
            worksheet.set_column(61, 61, 12)    #--     INCREMENTOS DIRECTOS
            worksheet.set_column(62, 62, 12)    #--
            worksheet.set_column(63, 63, 12)    #--

            worksheet.set_column(64, 64, 5)    #--      (Seperador)

            worksheet.set_column(65, 65, 12)    #--     
            worksheet.set_column(66, 66, 12)    #--     
            worksheet.set_column(67, 67, 12)    #--     RESUMEN
            worksheet.set_column(68, 68, 12)    #--
            worksheet.set_column(69, 69, 12)    #--

            worksheet.set_column(70, 70, 5)     #--      (Seperador)

            worksheet.set_column(71, 71, 12)    #--     APORTES     
            worksheet.set_column(72, 72, 12)    #--     
            worksheet.set_column(73, 73, 12)    #--     PROVISIONES
            worksheet.set_column(74, 74, 12)    #--
            worksheet.set_column(75, 75, 12)    #--
            worksheet.set_column(76, 76, 12)    #--

            worksheet.set_column(77, 77, 5)     #--      (Seperador)

            worksheet.set_column(78, 78, 12)    #--     COSTO MENSUAL

            # ------
            worksheet.set_row(7, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A2', 'src/user/cens_crm/static/description/logo-tiny_96.png')
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
            worksheet.merge_range('J7:V7', 'Merged Cells', merge_format)
            worksheet.write('J7', 'PARÁMETROS MENSUALES PARA EL CÁLCULO DE INGRESOS', cell_format_tut2)

            worksheet.merge_range('W7:AA7', 'Merged Cells', merge_format)
            worksheet.write('W7', 'ACUERDOS CONTRACTUALES', cell_format_tuti)

            worksheet.merge_range('AC7:AH7', 'Merged Cells', merge_format)
            worksheet.write('AC7', 'E  G  R  E  S  O  S', cell_format_tuti)

            worksheet.merge_range('AJ7:AS7', 'Merged Cells', merge_format)
            worksheet.write('AJ7', 'I  N  G  R  E  S  O  S', cell_format_sup1)
            
            worksheet.merge_range('AT7:AY7', 'Merged Cells', merge_format)
            worksheet.write('AT7', 'CONCEPTOS NO REMUNERATIVOS', cell_format_sup2)

            worksheet.merge_range('AZ7:BH7', 'Merged Cells', merge_format)
            worksheet.write('AZ7', 'D E S C U E N T O S', cell_format_sup3)

            worksheet.merge_range('BI7:BL7', 'Merged Cells', merge_format)
            worksheet.write('BI7', 'INCREMENTOS DIRECTOS', cell_format_sup4)

            worksheet.merge_range('BN7:BR7', 'Merged Cells', merge_format)
            worksheet.write('BN7', 'RESUMEN TOTALIZADO', cell_format_sup5)

            worksheet.merge_range('BT7:BU7', 'Merged Cells', merge_format)
            worksheet.write('BT7', 'APORTES', cell_format_sup5)

            worksheet.merge_range('BV7:BY7', 'Merged Cells', merge_format)
            worksheet.write('BV7', 'PROVISIONES', cell_format_sup5)

            worksheet.merge_range('CA7:CA7', 'Merged Cells', merge_format)
            worksheet.write('CA7', 'COSTO', cell_format_sup5)



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
            worksheet.write('I8', 'DIAS COMPUTADOS', cell_format_tut5)              #-- 08
            worksheet.write('J8', 'LICENCIA FALLECIMTO', cell_format_titu)          #-- 09
            worksheet.write('K8', 'LICENCIA MATR-PATR', cell_format_titu)           #-- 10
            worksheet.write('L8', 'VACACIONES', cell_format_titu)                   #-- 11
            worksheet.write('M8', 'CON GOCE', cell_format_titu)                     #-- 12
            worksheet.write('N8', 'DESCANSO MÉDICO', cell_format_titu)              #-- 13
            worksheet.write('O8', 'TIPO FERIADOS', cell_format_titu)                #-- 14
            worksheet.write('P8', 'DIAS FERIADOS', cell_format_titu)                #-- 15
            worksheet.write('Q8', 'IMPORTE FERIADOS', cell_format_titu)             #-- 16
            worksheet.write('R8', 'BONIFIC. EXTRAORD.', cell_format_titu)           #-- 17
            worksheet.write('S8', 'IMPORTE H.EXTRAS', cell_format_titu)             #-- 18
            worksheet.write('T8', 'REEMBOLSO', cell_format_titu)                    #-- 19
            worksheet.write('U8', 'REEMBOLSO MOVILIDAD', cell_format_titu)          #-- 20
            worksheet.write('V8', 'REEMBOLSO COMBUSTIB', cell_format_titu)          #-- 21
            worksheet.write('W8', 'MOVILIDAD', cell_format_titu)                    #-- 22
            worksheet.write('X8', 'VALE ALIMENTOS', cell_format_titu)               #-- 23
            worksheet.write('Y8', 'CONDICS. LABORALES', cell_format_titu)           #-- 24
            worksheet.write('Z8', 'BONIFIC. EDUCACIÓN', cell_format_titu)           #-- 25
            worksheet.write('AA8', 'UTILIDAD. VOLUNTARS', cell_format_titu)         #-- 26
            worksheet.write('AB8', 'ADELANTO GRATIFICAC.', cell_format_titu)        #-- 27
            worksheet.write('AC8', 'DIAS INASISTENCIA', cell_format_titu)           #-- 28
            worksheet.write('AD8', 'DIAS SIN GOCE', cell_format_titu)               #-- 29
            worksheet.write('AE8', 'ADELANTO SUELDO', cell_format_titu)             #-- 30
            worksheet.write('AF8', 'MINUTOS TARDANZA', cell_format_titu)            #-- 31
            worksheet.write('AG8', 'RETENCIÓN JUDICIAL', cell_format_titu)          #-- 32
            worksheet.write('AH8', 'DSCTO. PRÉSTAMOS', cell_format_titu)            #-- 33

            worksheet.write('AJ8', 'SUELDO BÁSICO', cell_format_tit1)           #-- 34
            worksheet.write('AK8', 'ASIGNACIÓN FAMILIAR', cell_format_tit1)     #-- 35
            worksheet.write('AL8', 'LICENCIA CON G.HABER', cell_format_tit1)    #-- 36
            worksheet.write('AM8', 'LICENCIA x FALLECMTO', cell_format_tit1)    #-- 37
            worksheet.write('AN8', 'LICENCIA MATER/PATER', cell_format_tit1)    #-- 38      INGRESOS
            worksheet.write('AO8', 'BONIFIC x CUPLIMTO', cell_format_tit1)      #-- 39
            worksheet.write('AP8', 'DESCANSO MÉDICO', cell_format_tit1)         #-- 40
            worksheet.write('AQ8', 'FERIADOS', cell_format_tit1)                #-- 41
            worksheet.write('AR8', 'HORAS EXTRAS', cell_format_tit1)            #-- 42
            worksheet.write('AS8', 'VACACIONES', cell_format_tit1)              #-- 43

            worksheet.write('AT8', 'ALIMENTACIÓN', cell_format_tit2)            #-- 44
            worksheet.write('AU8', 'MOVILIDAD', cell_format_tit2)               #-- 45
            worksheet.write('AV8', 'CONDIC LABORLS', cell_format_tit2)          #-- 46      NO REMUNERATIVOS
            worksheet.write('AW8', 'BONIFICAC. x EDUC', cell_format_tit2)         #-- 47
            worksheet.write('AX8', 'UTILIDAD VOLUNT', cell_format_tit2)         #-- 48
            worksheet.write('AY8', 'REEMB COMBUST', cell_format_tit2)           #-- 49

            worksheet.write('AZ8', 'LICEN SIN GOCE:', cell_format_tit3)         #-- 44
            worksheet.write('BA8', 'ADELANTO SUELDO', cell_format_tit3)         #-- 45
            worksheet.write('BB8', 'AFP / ONP', cell_format_tit3)               #-- 46      DESCUENTOS
            worksheet.write('BC8', 'INASISTENCIAS', cell_format_tit3)           #-- 47
            worksheet.write('BD8', 'TARDANZAS', cell_format_tit3)               #-- 48
            worksheet.write('BE8', 'RENTA 5TA.CAT', cell_format_tit3)           #-- 49
            worksheet.write('BF8', 'RETEN JUDIC (Alimentos)', cell_format_tit3) #-- 47
            worksheet.write('BG8', 'DESCTO NO DEDUCIBLE', cell_format_tit3)     #-- 48
            worksheet.write('BH8', 'APORTES EPS', cell_format_tit3)             #-- 49

            worksheet.write('BI8', 'REEMBOLSO', cell_format_tit4)               #-- 50
            worksheet.write('BJ8', 'REMMB MOVILIDAD', cell_format_tit4)         #-- 51      INCREMENTOS DIRECTOS
            worksheet.write('BK8', 'ADELANTO GRATIFIC', cell_format_tit4)       #-- 52
            worksheet.write('BL8', 'ESPECIAL AC', cell_format_tit4)             #-- 53

            worksheet.write('BN8', 'TOTAL INGRESOS', cell_format_tit5)         #-- 55
            worksheet.write('BO8', 'TOTAL C-N-R', cell_format_tit5)             #-- 56      
            worksheet.write('BP8', 'TOTAL DESCTOS', cell_format_tit5)           #-- 57      RESUMEN
            worksheet.write('BQ8', 'TOTAL INCR.DIREC', cell_format_tit5)        #-- 58
            worksheet.write('BR8', 'TOTAL-NETO', cell_format_tit5)              #-- 59

            worksheet.write('BT8', 'ESSALUD', cell_format_tit6)                 #-- 61      APORTES
            worksheet.write('BU8', 'EPS', cell_format_tit6)                     #-- 62      
            worksheet.write('BV8', 'CTS', cell_format_tit7)                     #-- 63      PROVISIONES
            worksheet.write('BW8', 'VACACIONES', cell_format_tit7)              #-- 64
            worksheet.write('BX8', 'GRATIFICAC', cell_format_tit7)              #-- 65
            worksheet.write('BY8', 'BONIFIC GRATIFIC', cell_format_tit7)              #-- 66

            worksheet.write('CA8', 'COSTO MENSUAL', cell_format_tit5)              #-- 68

            #----------------------------------------------------------------
            worksheet.write('J9', 'DIAS', cell_format_tut3)                 #-- 09
            worksheet.write('K9', 'DIAS', cell_format_tut3)                 #-- 10
            worksheet.write('L9', 'DIAS', cell_format_tut3)                 #-- 11
            worksheet.write('M9', 'DIAS', cell_format_tut3)                 #-- 12
            worksheet.write('N9', 'DIAS', cell_format_tut3)                 #-- 13
            # worksheet.write('O9', 'TIPO FERIADOS', cell_format_titu)      #-- 14
            worksheet.write('P9', 'DIAS', cell_format_tut3)                 #-- 15
            worksheet.write('Q9', 'S/.', cell_format_tut4)                  #-- 16
            worksheet.write('R9', 'S/.', cell_format_tut4)                  #-- 17
            worksheet.write('S9', 'S/.', cell_format_tut4)                  #-- 18
            worksheet.write('T9', 'S/.', cell_format_tut4)                  #-- 19
            worksheet.write('U9', 'S/.', cell_format_tut4)                  #-- 20
            worksheet.write('V9', 'S/.', cell_format_tut4)                  #-- 21
            worksheet.write('W9', 'S/.', cell_format_tut4)                  #-- 22
            worksheet.write('X9', 'S/.', cell_format_tut4)                  #-- 23
            worksheet.write('Y9', 'S/.', cell_format_tut4)                  #-- 24
            worksheet.write('Z9', 'S/.', cell_format_tut4)                  #-- 25
            worksheet.write('AA9', 'S/.', cell_format_tut4)                 #-- 26
            worksheet.write('AB9', 'S/.', cell_format_tut4)                 #-- 27
            worksheet.write('AC9', 'DIAS', cell_format_tut3)                #-- 28
            worksheet.write('AD9', 'DIAS', cell_format_tut3)                #-- 29
            worksheet.write('AE9', 'S/.', cell_format_tut4)                 #-- 30
            # worksheet.write('AF9', 'MINUTOS TARDANZA', cell_format_titu)  #-- 31
            worksheet.write('AG9', 'S/.', cell_format_tut4)                 #-- 32
            worksheet.write('AH9', 'S/.', cell_format_tut4)                 #-- 33

            worksheet.write('AJ9', '(+)', cell_format_sub1)         #-- 34
            worksheet.write('AK9', '(+)', cell_format_sub1)         #-- 35
            worksheet.write('AL9', '(+)', cell_format_sub1)         #-- 36
            worksheet.write('AM9', '(+)', cell_format_sub1)         #-- 37
            worksheet.write('AN9', '(+)', cell_format_sub1)         #-- 38      INGRESOS
            worksheet.write('AO9', '(+)', cell_format_sub1)         #-- 39
            worksheet.write('AP9', '(+)', cell_format_sub1)         #-- 40
            worksheet.write('AQ9', '(+)', cell_format_sub1)         #-- 41
            worksheet.write('AR9', '(+)', cell_format_sub1)         #-- 42
            worksheet.write('AS9', '(+)', cell_format_sub1)         #-- 43

            worksheet.write('AT9', '(n)', cell_format_sub2)         #-- 44
            worksheet.write('AU9', '(n)', cell_format_sub2)         #-- 45
            worksheet.write('AV9', '(n)', cell_format_sub2)         #-- 46      NO REMUNERAIVOS
            worksheet.write('AW9', '(n)', cell_format_sub2)         #-- 47
            worksheet.write('AX9', '(n)', cell_format_sub2)         #-- 48
            worksheet.write('AY9', '(n)', cell_format_sub2)         #-- 49

            worksheet.write('AZ9', '(-)', cell_format_sub3)         #-- 50
            worksheet.write('BA9', '(-)', cell_format_sub3)         #-- 51
            worksheet.write('BB9', '(-)', cell_format_sub3)         #-- 52      
            worksheet.write('BC9', '(-)', cell_format_sub3)         #-- 53
            worksheet.write('BD9', '(-)', cell_format_sub3)         #-- 54      DESCUENTOS
            worksheet.write('BE9', '(-)', cell_format_sub3)         #-- 55
            worksheet.write('BF9', '(-)', cell_format_sub3)         #-- 56      
            worksheet.write('BG9', '(-)', cell_format_sub3)         #-- 57
            worksheet.write('BH9', '(-)', cell_format_sub3)         #-- 58

            worksheet.write('BI9', '(d)', cell_format_sub4)         #-- 59
            worksheet.write('BJ9', '(d)', cell_format_sub4)         #-- 60      INCREMENTOS DIRECTOS
            worksheet.write('BK9', '(d)', cell_format_sub4)         #-- 61
            worksheet.write('BL9', '(0)', cell_format_sub4)         #-- 62

            worksheet.write('BN9', '(Acum)', cell_format_tit1)         #-- 64
            worksheet.write('BO9', '(Acum)', cell_format_tit2)         #-- 65      RESUMEN TOTALIZADO
            worksheet.write('BP9', '(Acum)', cell_format_tit3)         #-- 66
            worksheet.write('BQ9', '(Acum)', cell_format_tit4)         #-- 67
            worksheet.write('BR9', '(Acum)', cell_format_sub5)         #-- 68

            worksheet.write('BT9', '(Empr)', cell_format_sub6)         #-- 70      APORTES
            worksheet.write('BU9', '(Empr)', cell_format_sub6)         #-- 71      
            worksheet.write('BV9', '(Empr)', cell_format_sub7)         #-- 72      PROVISIONES
            worksheet.write('BW9', '(Empr)', cell_format_sub7)         #-- 73
            worksheet.write('BX9', '(Empr)', cell_format_sub7)         #-- 74
            worksheet.write('BY9', '(Empr)', cell_format_sub7)         #-- 75

            worksheet.write('CA9', '(Empr)', cell_format_sub5)         #-- 75      COSTO MENSUAL

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
 
            for w_boleta in w_lote:
                # worksheet.write(w_fila, 0, w_fila-6, cell_format_cent)
                worksheet.write(w_fila, 0, w_boleta.id, cell_format_cent)   
                worksheet.write(w_fila, 1, w_boleta.number, cell_format_cent)
                w_dato = w_boleta.employee_id.name
                worksheet.write(w_fila, 2, w_dato, cell_format_left)
                worksheet.write(w_fila, 3, w_boleta.x_studio_dni, cell_format_cent)

                # w_dato = w_boleta.payslip_run_id.name
                w_dato = ""
                w_mes = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').month
                w_dia = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').day
                w_ano = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').year
                w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)[:3]
                worksheet.write(w_fila, 4, w_dato, cell_format_cent)
                if (w_switch == 0):
                    w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)
                    worksheet.write('H5', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    worksheet.write('AT5', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    w_switch = 1
                    
                worksheet.write(w_fila, 5, w_boleta.date_from, cell_format_fech)
                worksheet.write(w_fila, 6, w_boleta.date_to, cell_format_fech)
                w_dato = w_boleta.currency_id.name
                worksheet.write(w_fila, 7, w_dato, cell_format_cent)
                # ----------------------------
                # -- REGISTRO INGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 8, w_boleta.x_studio_dias_computados, cell_format_nume)
                worksheet.write(w_fila, 9, w_boleta.x_studio_licencia_fallecimiento, cell_format_nume)
                worksheet.write(w_fila, 10, w_boleta.x_studio_licencia_materpater, cell_format_nume)
                worksheet.write(w_fila, 11, w_boleta.x_studio_dias_vacaciones, cell_format_nume)
                worksheet.write(w_fila, 12, w_boleta.x_studio_dias_con_goce, cell_format_nume)
                worksheet.write(w_fila, 13, w_boleta.x_studio_descanso_medico, cell_format_nume)

                worksheet.write(w_fila, 14, w_boleta.x_studio_edit_feriados, cell_format_cent)
                worksheet.write(w_fila, 15, w_boleta.x_studio_feriados_dias, cell_format_nume)
                worksheet.write(w_fila, 16, w_boleta.x_studio_feriados_importe, cell_format_impo)

                worksheet.write(w_fila, 17, w_boleta.x_studio_bonificacion_extraordinaria, cell_format_impo)
                worksheet.write(w_fila, 18, w_boleta.x_studio_horas_extras_importe, cell_format_impo)
                worksheet.write(w_fila, 19, w_boleta.x_studio_reembolso, cell_format_impo)
                worksheet.write(w_fila, 20, w_boleta.x_studio_reembolso_movilidad, cell_format_impo)
                worksheet.write(w_fila, 21, w_boleta.x_studio_reembolso_combustible, cell_format_impo)

                worksheet.write(w_fila, 22, w_boleta.x_studio_movilidad, cell_format_impo)
                worksheet.write(w_fila, 23, w_boleta.x_studio_vale_alimentos, cell_format_impo)
                worksheet.write(w_fila, 24, w_boleta.x_studio_condiciones_laborales, cell_format_impo)
                worksheet.write(w_fila, 25, w_boleta.x_studio_bonificacion_educacion, cell_format_impo)
                worksheet.write(w_fila, 26, w_boleta.x_studio_utilidades_voluntarias, cell_format_impo)
                worksheet.write(w_fila, 27, w_boleta.x_studio_adelanto_gratificacion, cell_format_impo)
                # ----------------------------
                # -- REGISTRO EGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 28, w_boleta.x_studio_descuento_inasistencias, cell_format_nume)
                worksheet.write(w_fila, 29, w_boleta.x_studio_dias_sin_goce, cell_format_nume)
                worksheet.write(w_fila, 30, w_boleta.x_studio_adelanto_sueldo, cell_format_impo)
                worksheet.write(w_fila, 31, w_boleta.x_studio_descuento_tardanzas_min, cell_format_nume)
                worksheet.write(w_fila, 32, w_boleta.x_studio_retencion_judicial, cell_format_impo)
                worksheet.write(w_fila, 33, w_boleta.x_studio_descuento_prestamos, cell_format_impo)
                
                # ----------------------------------------------------------------------------------------
                # -- DATOS CALCULADOS FINALES PLANILLA -- DATOS QUE INGRESAN A LA BOLETA DE PAGO
                # ----------------------------------------------------------------------------------------
                #
                # -----------------------------------------
                # BOLETA PAGO - INGRESOS
                # -----------------------------------------
                worksheet.write(w_fila, 35, w_boleta.x_studio_en_basico, cell_format_impo)
                worksheet.write(w_fila, 36, w_boleta.x_studio_en_asignacion_familiar, cell_format_impo)
                worksheet.write(w_fila, 37, w_boleta.x_studio_en_licencia_con_ghaber, cell_format_impo)
                worksheet.write(w_fila, 38, w_boleta.x_studio_en_licencia_fallecimiento, cell_format_impo)
                worksheet.write(w_fila, 39, w_boleta.x_studio_en_licencia_materpater, cell_format_impo)
                worksheet.write(w_fila, 40, w_boleta.x_studio_en_bonificacion_cumplimiento, cell_format_impo)
                worksheet.write(w_fila, 41, w_boleta.x_studio_en_descanso_medico, cell_format_impo)
                worksheet.write(w_fila, 42, w_boleta.x_studio_en_feriados, cell_format_impo)
                worksheet.write(w_fila, 43, w_boleta.x_studio_en_horas_extras, cell_format_impo)
                worksheet.write(w_fila, 44, w_boleta.x_studio_en_vacaciones, cell_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - CONCEPTOS NO REMUNERATIVOS
                # -----------------------------------------
                worksheet.write(w_fila, 45, w_boleta.x_studio_en_vale_alimentacion, cell_format_impo)
                worksheet.write(w_fila, 46, w_boleta.x_studio_en_vale_movilidad, cell_format_impo)
                worksheet.write(w_fila, 47, w_boleta.x_studio_en_condiciones_laborales, cell_format_impo)
                worksheet.write(w_fila, 48, w_boleta.x_studio_en_bonificacion_educacion, cell_format_impo)
                worksheet.write(w_fila, 49, w_boleta.x_studio_en_utilidades_voluntarias, cell_format_impo)
                worksheet.write(w_fila, 50, w_boleta.x_studio_en_reembolso_combustible, cell_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - DESCUENTOS
                # -----------------------------------------
                worksheet.write(w_fila, 51, w_boleta.x_studio_en_licencia_sin_ghaber, cell_format_impo)
                worksheet.write(w_fila, 52, w_boleta.x_studio_en_adelanto_sueldo, cell_format_impo)
                worksheet.write(w_fila, 53, w_boleta.x_studio_en_afp_onp, cell_format_impo)
                worksheet.write(w_fila, 54, w_boleta.x_studio_en_inasistencias, cell_format_impo)
                worksheet.write(w_fila, 55, w_boleta.x_studio_en_tardanzas, cell_format_impo)
                worksheet.write(w_fila, 56, w_boleta.x_studio_en_renta_5ta, cell_format_impo)
                worksheet.write(w_fila, 57, w_boleta.x_studio_en_retencion_judicial, cell_format_impo)
                worksheet.write(w_fila, 58, w_boleta.x_studio_en_descuento_prestamos, cell_format_impo)
                worksheet.write(w_fila, 59, w_boleta.x_studio_aporte_eps_2, cell_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - INCREMENTOS DIRECTOS
                # -----------------------------------------
                worksheet.write(w_fila, 60, w_boleta.x_studio_en_reembolso, cell_format_impo)
                worksheet.write(w_fila, 61, w_boleta.x_studio_en_reembolso_movilidad, cell_format_impo)
                worksheet.write(w_fila, 62, w_boleta.x_studio_en_adelanto_gratificacion, cell_format_impo)
                worksheet.write(w_fila, 63, w_boleta.x_studio_especial_ac, cell_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - TOTALIZADO RESUMEN
                # -----------------------------------------
                worksheet.write(w_fila, 65, w_boleta.x_studio_en_gross, cell_format_impo)
                worksheet.write(w_fila, 66, w_boleta.x_studio_en_total_remuneracion_bruta, cell_format_impo)
                worksheet.write(w_fila, 67, -w_boleta.x_studio_total_descuentos, cell_format_impo)
                worksheet.write(w_fila, 68, w_boleta.x_studio_sub_total_incremespeciales, cell_format_impo)
                worksheet.write(w_fila, 69, w_boleta.x_studio_en_total_remuneracion, cell_format_imp2)

                # -----------------------------------------
                # APORTES
                # -----------------------------------------
                worksheet.write(w_fila, 71, w_boleta.x_studio_aporte_a_essalud, cell_format_impo)
                worksheet.write(w_fila, 72, w_boleta.x_studio_en_aportes_eps, cell_format_impo)
                # -----------------------------------------
                # PROVISIONES
                # -----------------------------------------
                worksheet.write(w_fila, 73, w_boleta.x_studio_en_provision_cts, cell_format_impo)
                worksheet.write(w_fila, 74, w_boleta.x_studio_en_provision_vacaciones, cell_format_impo)
                worksheet.write(w_fila, 75, w_boleta.x_studio_en_provision_gratificacion, cell_format_impo)
                worksheet.write(w_fila, 76, w_boleta.x_studio_en_provision_bonigrati, cell_format_impo)
                # -----------------------------------------
                # COSTO DEL MES
                # -----------------------------------------
                worksheet.write(w_fila, 78, w_boleta.x_studio_en_total_extraordinario, cell_format_impo)
                

                w_fila += 1


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



