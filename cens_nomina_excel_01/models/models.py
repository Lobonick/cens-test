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
            worksheet.set_column(4, 4, 11)      #-- LOTE
            worksheet.set_column(5, 5, 13)      #-- FECHA INGRESO
            worksheet.set_column(6, 6, 20)      #-- UNIDAD DE NEGOCIO
            worksheet.set_column(7, 7, 8)       #-- MONEDA
            worksheet.set_column(8, 8, 12)      #-- DIAS COMPUTADOS
            worksheet.set_column(9, 9, 12)      #-- 
            worksheet.set_column(10, 10, 12)    #-- 
            worksheet.set_column(11, 11, 12)    #-- 
            worksheet.set_column(12, 12, 12)    #-- 
            worksheet.set_column(13, 13, 12)    #-- 
            worksheet.set_column(14, 14, 12)    #-- 
            worksheet.set_column(15, 15, 12)    #-- 
            worksheet.set_column(16, 16, 12)    #-- 
            worksheet.set_column(17, 17, 12)    #-- 
            worksheet.set_column(18, 18, 12)    #-- 
            worksheet.set_column(19, 19, 12)    #-- 

            worksheet.set_column(20, 20, 5)    #-- (Seperador) 

            worksheet.set_column(21, 21, 12)    #-- 
            worksheet.set_column(22, 22, 12)    #-- 
            worksheet.set_column(23, 23, 12)    #--
            worksheet.set_column(24, 24, 12)    #--
            worksheet.set_column(25, 25, 12)    #--
            worksheet.set_column(26, 26, 12)    #--
            worksheet.set_column(27, 27, 12)    #--     INGRESOS
            worksheet.set_column(28, 28, 12)    #--
            worksheet.set_column(29, 29, 12)    #--
            worksheet.set_column(30, 30, 12)    #--
            worksheet.set_column(31, 31, 12)    #--

            worksheet.set_column(32, 32, 12)    #--
            worksheet.set_column(33, 33, 12)    #--
            worksheet.set_column(34, 34, 12)    #--     NO REMUNERATIVOS
            worksheet.set_column(35, 35, 12)    #--
            worksheet.set_column(36, 36, 12)    #-- 
            worksheet.set_column(37, 37, 12)    #--

            worksheet.set_column(38, 38, 12)    #-- 
            worksheet.set_column(39, 39, 12)    #--
            worksheet.set_column(40, 40, 12)    #--     LIQUIDACIONES
            worksheet.set_column(41, 41, 12)    #--

            worksheet.set_column(42, 42, 12)    #--
            worksheet.set_column(43, 43, 12)    #--
            worksheet.set_column(44, 44, 12)    #-- Compañia
            worksheet.set_column(45, 45, 12)    #-- AFP
            worksheet.set_column(46, 46, 12)    #-- ONP 
            worksheet.set_column(47, 47, 12)    #--
            worksheet.set_column(48, 48, 12)    #--     DESCUENTOS
            worksheet.set_column(49, 49, 12)    #--
            worksheet.set_column(50, 50, 12)    #--
            worksheet.set_column(51, 51, 12)    #--
            worksheet.set_column(52, 52, 12)    #--

            worksheet.set_column(53, 53, 12)    #--
            worksheet.set_column(54, 54, 12)    #--     INCREMENTOS DIRECTOS
            worksheet.set_column(55, 55, 12)    #--
            worksheet.set_column(56, 56, 12)    #--
            worksheet.set_column(57, 57, 12)    #--

            worksheet.set_column(58, 58, 5)    #--     (Seperador)

            worksheet.set_column(59, 59, 12)    #--
            worksheet.set_column(60, 60, 12)    #--
            worksheet.set_column(61, 61, 12)    #--     RESUMEN TOTALIZADO     
            worksheet.set_column(62, 62, 12)    #--
            worksheet.set_column(63, 63, 12)    #--
            worksheet.set_column(64, 64, 12)    #-- 

            worksheet.set_column(65, 65, 5)     #--     (Seperador)

            worksheet.set_column(66, 66, 12)    #--     
            worksheet.set_column(67, 67, 12)    #--    APORTES 

            worksheet.set_column(68, 68, 12)    #--
            worksheet.set_column(69, 69, 12)    #--
            worksheet.set_column(70, 70, 12)    #--    PROVISIONES  
            worksheet.set_column(71, 71, 12)    #--         

            worksheet.set_column(72, 72, 5)     #--    (Seperador)

            worksheet.set_column(73, 73, 15)    #--   TOTAL COSTO

            worksheet.set_column(74, 74, 5)     #--    (Seperador)

            worksheet.set_column(75, 75, 30)    #--    
            worksheet.set_column(76, 76, 30)    #--    DETALLE CTA BANCO
            worksheet.set_column(77, 77, 30)    #--     

            worksheet.set_column(78, 78, 5)     #--    (Seperador)

            worksheet.set_column(79, 79, 12)    #   
            worksheet.set_column(80, 80, 12)    
            worksheet.set_column(81, 81, 12)    
            worksheet.set_column(82, 82, 10)    #  
            worksheet.set_column(83, 83, 12)    
            worksheet.set_column(84, 84, 12)    #--   
            worksheet.set_column(85, 85, 12)    #-


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

            worksheet.merge_range('J7:N7', 'Merged Cells', merge_format)
            worksheet.write('J7', 'ACUERDOS CONTRACTUALES', cell_format_tuti)

            worksheet.merge_range('O7:T7', 'Merged Cells', merge_format)
            worksheet.write('O7', 'E  G  R  E  S  O  S', cell_format_tut2)

            worksheet.merge_range('V7:AF7', 'Merged Cells', merge_format)
            worksheet.write('V7', 'I  N  G  R  E  S  O  S', cell_format_sup1)
            
            worksheet.merge_range('AG7:AL7', 'Merged Cells', merge_format)
            worksheet.write('AG7', 'CONCEPTOS NO REMUNERATIVOS', cell_format_sup2)

            worksheet.merge_range('AM7:AP7', 'Merged Cells', merge_format)
            worksheet.write('AM7', 'CONCEPTOS LIQUIDACIÓN', cell_format_sup8)

            worksheet.merge_range('AQ7:BA7', 'Merged Cells', merge_format)
            worksheet.write('AQ7', 'D E S C U E N T O S', cell_format_sup3)

            worksheet.merge_range('BB7:BF7', 'Merged Cells', merge_format)
            worksheet.write('BB7', 'INCREMENTOS DIRECTOS', cell_format_sup4)

            worksheet.merge_range('BH7:BM7', 'Merged Cells', merge_format)
            worksheet.write('BH7', 'RESUMEN TOTALIZADO', cell_format_sup5)

            worksheet.merge_range('BO7:BP7', 'Merged Cells', merge_format)
            worksheet.write('BO7', 'APORTES', cell_format_sup5)

            worksheet.merge_range('BQ7:BT7', 'Merged Cells', merge_format)
            worksheet.write('BQ7', 'PROVISIONES', cell_format_sup5)

            worksheet.merge_range('BV7:BV7', 'Merged Cells', merge_format)
            worksheet.write('BV7', 'COSTO', cell_format_sup5)

            worksheet.merge_range('BX7:BZ7', 'Merged Cells', merge_format)
            worksheet.write('BX7', 'CUENTA BANCARIA ABONO', cell_format_sup5)

            worksheet.merge_range('CB7:CI7', 'Merged Cells', merge_format)
            worksheet.write('CB7', 'DESAGREGADO AFP / ONP', cell_format_sup5)


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
            worksheet.write('E8', 'LOTE', cell_format_titu)                         #-- 04
            worksheet.merge_range('F8:F9', 'Merged Cells', merge_format)
            worksheet.write('F8', 'FECHA INGRESO', cell_format_titu)                #-- 05
            worksheet.merge_range('G8:G9', 'Merged Cells', merge_format)
            worksheet.write('G8', 'UNIDAD NEGOCIO', cell_format_titu)               #-- 06
            worksheet.merge_range('H8:H9', 'Merged Cells', merge_format)
            worksheet.write('H8', 'MONEDA', cell_format_titu)                       #-- 07
            worksheet.merge_range('I8:I9', 'Merged Cells', merge_format)
            worksheet.write('I8', 'DIAS COMPUTADOS', cell_format_tut5)             #-- 08
            worksheet.write('J8', 'MOVILIDAD', cell_format_titu)                   #-- 09
            worksheet.write('K8', 'VALE ALIMENTOS', cell_format_titu)              #-- 10
            worksheet.write('L8', 'CONDICS. LABORALES', cell_format_titu)          #-- 11   ACUERDOS CONTRACTUALES
            worksheet.write('M8', 'BONIFIC. EDUCACIÓN', cell_format_titu)          #-- 12
            worksheet.write('N8', 'UTILIDAD. VOLUNTARS', cell_format_titu)         #-- 13

            worksheet.write('O8', 'DCTO INASISTEN', cell_format_titu)              #-- 14
            worksheet.write('P8', 'DIAS SIN GOCE', cell_format_titu)               #-- 15
            worksheet.write('Q8', 'ADELANTO SUELDO', cell_format_titu)             #-- 16   REGISTRO EGRESOS
            worksheet.write('R8', 'MINUTOS TARDANZA', cell_format_titu)            #-- 17
            worksheet.write('S8', 'RETENCIÓN JUDICIAL', cell_format_titu)          #-- 18
            worksheet.write('T8', 'DSCTO. PRÉSTAMOS', cell_format_titu)            #-- 19

            worksheet.write('V8', 'SUELDO BÁSICO', cell_format_tit1)            #-- 21
            worksheet.write('W8', 'ASIGNACIÓN FAMILIAR', cell_format_tit1)      #-- 22
            worksheet.write('X8', 'LICENCIA CON G.HABER', cell_format_tit1)     #-- 23
            worksheet.write('Y8', 'LICENCIA x FALLECMTO', cell_format_tit1)     #-- 24
            worksheet.write('Z8', 'LICENCIA MATER/PATER', cell_format_tit1)     #-- 25      INGRESOS
            worksheet.write('AA8', 'BONIFIC x CUPLIMTO', cell_format_tit1)      #-- 26
            worksheet.write('AB8', 'DESCANSO MÉDICO', cell_format_tit1)         #-- 27
            worksheet.write('AC8', 'FERIADOS', cell_format_tit1)                #-- 28
            worksheet.write('AD8', 'HORAS EXTRAS', cell_format_tit1)            #-- 29
            worksheet.write('AE8', 'VACACIONES', cell_format_tit1)              #-- 30
            worksheet.write('AF8', 'DESCANSO VACACIONAL', cell_format_tit1)     #-- 31

            worksheet.write('AG8', 'ALIMENTACIÓN', cell_format_tit2)            #-- 32
            worksheet.write('AH8', 'MOVILIDAD', cell_format_tit2)               #-- 33
            worksheet.write('AI8', 'CONDIC LABORLS', cell_format_tit2)          #-- 34      NO REMUNERATIVOS
            worksheet.write('AJ8', 'BONIFICAC. x EDUC', cell_format_tit2)       #-- 35
            worksheet.write('AK8', 'UTILIDAD VOLUNT', cell_format_tit2)         #-- 36
            worksheet.write('AL8', 'REEMB COMBUST', cell_format_tit2)           #-- 37

            worksheet.write('AM8', 'VACACIONES TRUNCAS', cell_format_tit8)       #-- 38
            worksheet.write('AN8', 'CTS TRUNCO', cell_format_tit8)               #-- 39
            worksheet.write('AO8', 'GRATIFIC TRUNCA', cell_format_tit8)          #-- 40     LIQUIDACIÓN
            worksheet.write('AP8', 'BONIF.GRATI TRUNCA', cell_format_tit8)       #-- 41

            worksheet.write('AQ8', 'LICEN SIN GOCE:', cell_format_tit3)         #-- 42
            worksheet.write('AR8', 'ADELANTO SUELDO', cell_format_tit3)         #-- 43
            worksheet.merge_range('AS8:AU8', 'Merged Cells', merge_format)
            worksheet.write('AS8', 'AFP / ONP', cell_format_tit31)
            worksheet.write('AV8', 'INASISTENCIAS', cell_format_tit3)           #-- 45
            worksheet.write('AW8', 'TARDANZAS', cell_format_tit3)               #-- 46      DESCUENTOS
            worksheet.write('AX8', 'RENTA 5TA.CAT', cell_format_tit3)           #-- 47
            worksheet.write('AY8', 'RETEN JUDIC (Alimentos)', cell_format_tit3) #-- 48
            worksheet.write('AZ8', 'DESCTO NO DEDUCIBLE', cell_format_tit3)     #-- 49
            worksheet.write('BA8', 'APORTES EPS', cell_format_tit3)             #-- 50

            worksheet.write('BB8', 'ADELANT REMUNERAC', cell_format_tit4)       #-- 51
            worksheet.write('BC8', 'REMMB MOVILIDAD', cell_format_tit4)         #-- 52      INCREMENTOS DIRECTOS
            worksheet.write('BD8', 'ADELANTO GRATIFIC', cell_format_tit4)       #-- 53
            worksheet.write('BE8', 'IDEMNIZAC DESPIDO', cell_format_tit4)       #-- 54
            worksheet.write('BF8', 'DEVOLUCIÓN DSCTO INDEB', cell_format_tit4)  #-- 55

            worksheet.write('BH8', 'TOTAL INGRESOS', cell_format_tit5)          #-- 57
            worksheet.write('BI8', 'TOTAL C-N-R', cell_format_tit5)             #-- 58      
            worksheet.write('BJ8', 'TOTAL DESCTOS', cell_format_tit5)           #-- 59      RESUMEN
            worksheet.write('BK8', 'TOTAL INCR.DIREC', cell_format_tit5)        #-- 60
            worksheet.write('BL8', 'TOT CONCEPT LBS', cell_format_tit8)         #-- 58
            worksheet.write('BM8', 'TOTAL-NETO', cell_format_tit5)              #-- 59

            worksheet.write('BO8', 'ESSALUD', cell_format_tit6)                 #-- 61      APORTES
            worksheet.write('BP8', 'EPS', cell_format_tit6)                     #-- 62      
            worksheet.write('BQ8', 'CTS', cell_format_tit7)                     #-- 63      PROVISIONES
            worksheet.write('BR8', 'VACACIONES', cell_format_tit7)              #-- 64
            worksheet.write('BS8', 'GRATIFICAC', cell_format_tit7)              #-- 65
            worksheet.write('BT8', 'BONIFIC GRATIFIC', cell_format_tit7)        #-- 66

            worksheet.write('BV8', 'COSTO EMPLEADO', cell_format_tit5)          #-- 68

            worksheet.write('BX8', 'BANCO', cell_format_tit7)                   #-- 64
            worksheet.write('BY8', 'CUENTA', cell_format_tit7)                  #-- 65      DETALLE CTAS BANCARIAS
            worksheet.write('BZ8', 'CCI', cell_format_tit7)                     #-- 66

            worksheet.merge_range('CB8:CB9', 'Merged Cells', merge_format)
            worksheet.write('CB8', 'COMPAÑIA', cell_format_tit7)                #-- 79
            worksheet.merge_range('CC8:CC9', 'Merged Cells', merge_format)
            worksheet.write('CC8', 'IMPORTE OBLIGATORIO', cell_format_tit7)     #-- 80
            worksheet.merge_range('CD8:CD9', 'Merged Cells', merge_format)
            worksheet.write('CD8', 'PRIMA SEGURO', cell_format_tit7)            #-- 81      DESAGREGADO AFP
            worksheet.merge_range('CE8:CG8', 'Merged Cells', merge_format)
            worksheet.write('CE8', 'COMISIÓN', cell_format_tit6)
            # worksheet.write('CE8', 'TIPO COMISIÓN', cell_format_tit7)           #-- 82
            # worksheet.write('CF8', 'COMISIÓN MIXTA', cell_format_tit7)          #-- 83
            # worksheet.write('CG8', 'COMISIÓN FLUJO', cell_format_tit7)          #-- 84

            worksheet.merge_range('CH8:CI8', 'Merged Cells', merge_format)
            worksheet.write('CH8', 'TOTALES', cell_format_tit31)
            # worksheet.write('CH8', 'AFP', cell_format_tit7)                     #-- 86      TOTAL AFP/ONP
            # worksheet.write('CI8', 'ONP', cell_format_tit7)                     #-- 87


            #----------------------------------------------------------------
            worksheet.write('I9', 'DIAS', cell_format_tut3)                 #-- 09
            worksheet.write('J9', 'S/.', cell_format_tut4)                 #-- 10
            worksheet.write('K9', 'S/.', cell_format_tut4)                 #-- 11
            worksheet.write('L9', 'S/.', cell_format_tut4)                 #-- 12
            worksheet.write('M9', 'S/.', cell_format_tut4)                 #-- 13
            worksheet.write('N9', 'S/.', cell_format_tut4)                 #-- 15
            worksheet.write('O9', 'S/.', cell_format_tut4)                  #-- 16
            worksheet.write('P9', 'S/.', cell_format_tut4)                  #-- 17
            worksheet.write('Q9', 'S/.', cell_format_tut4)                  #-- 18
            worksheet.write('R9', 'S/.', cell_format_tut4)                  #-- 19
            worksheet.write('S9', 'S/.', cell_format_tut4)                  #-- 20
            worksheet.write('T9', 'S/.', cell_format_tut4)                  #-- 21

            worksheet.write('V9', '(+)', cell_format_sub1)         #-- 23
            worksheet.write('W9', '(+)', cell_format_sub1)         #-- 24
            worksheet.write('X9', '(+)', cell_format_sub1)         #-- 25
            worksheet.write('Y9', '(+)', cell_format_sub1)         #-- 26
            worksheet.write('Z9', '(+)', cell_format_sub1)         #-- 27      INGRESOS
            worksheet.write('AA9', '(+)', cell_format_sub1)         #-- 28
            worksheet.write('AB9', '(+)', cell_format_sub1)         #-- 29
            worksheet.write('AC9', '(+)', cell_format_sub1)         #-- 30
            worksheet.write('AD9', '(+)', cell_format_sub1)         #-- 31
            worksheet.write('AE9', '(+)', cell_format_sub1)         #-- 32
            worksheet.write('AF9', '(+)', cell_format_sub1)         #-- 33

            worksheet.write('AG9', '(n)', cell_format_sub2)         #-- 34
            worksheet.write('AH9', '(n)', cell_format_sub2)         #-- 35
            worksheet.write('AI9', '(n)', cell_format_sub2)         #-- 36      NO REMUNERAIVOS
            worksheet.write('AJ9', '(n)', cell_format_sub2)         #-- 37
            worksheet.write('AK9', '(n)', cell_format_sub2)         #-- 38
            worksheet.write('AL9', '(n)', cell_format_sub2)         #-- 39
            
            worksheet.write('AM9', '(Cese)', cell_format_sub8)         #-- 40
            worksheet.write('AN9', '(Cese)', cell_format_sub8)         #-- 41
            worksheet.write('AO9', '(Cese)', cell_format_sub8)         #-- 42      LIQUIDACIONES
            worksheet.write('AP9', '(Cese)', cell_format_sub8)         #-- 43

            worksheet.write('AQ9', '(-)', cell_format_sub3)         #-- 44
            worksheet.write('AR9', '(-)', cell_format_sub3)         #-- 45
            worksheet.write('AS9', 'COMPAÑIA', cell_format_sub31)         #-- 46
            worksheet.write('AT9', 'AFP', cell_format_sub31)         #-- 46
            worksheet.write('AU9', 'ONP', cell_format_sub31)         #-- 46      
            worksheet.write('AV9', '(-)', cell_format_sub3)         #-- 47
            worksheet.write('AW9', '(-)', cell_format_sub3)         #-- 48      DESCUENTOS
            worksheet.write('AX9', '(-)', cell_format_sub3)         #-- 49
            worksheet.write('AY9', '(-)', cell_format_sub3)         #-- 50      
            worksheet.write('AZ9', '(-)', cell_format_sub3)         #-- 51
            worksheet.write('BA9', '(-)', cell_format_sub3)         #-- 52

            worksheet.write('BB9', '(d)', cell_format_sub4)         #-- 53
            worksheet.write('BC9', '(d)', cell_format_sub4)         #-- 54      INCREMENTOS DIRECTOS
            worksheet.write('BD9', '(d)', cell_format_sub4)         #-- 55
            worksheet.write('BE9', '(d)', cell_format_sub4)         #-- 56
            worksheet.write('BF9', '(d)', cell_format_sub4)         #-- 57

            worksheet.write('BH9', '(Acum)', cell_format_tit1)         #-- 64
            worksheet.write('BI9', '(Acum)', cell_format_tit2)         #-- 65      RESUMEN TOTALIZADO
            worksheet.write('BJ9', '(Acum)', cell_format_tit3)         #-- 66
            worksheet.write('BK9', '(Acum)', cell_format_tit4)         #-- 67
            worksheet.write('BL9', '(Acum)', cell_format_tit4)         #-- 67
            worksheet.write('BM9', '(Acum)', cell_format_sub5)         #-- 68


            worksheet.write('BO9', '(Empr)', cell_format_sub6)         #-- 70      APORTES
            worksheet.write('BP9', '(Empr)', cell_format_sub6)         #-- 71      
            worksheet.write('BQ9', '(Empr)', cell_format_sub7)         #-- 72      PROVISIONES
            worksheet.write('BR9', '(Empr)', cell_format_sub7)         #-- 73
            worksheet.write('BS9', '(Empr)', cell_format_sub7)         #-- 74
            worksheet.write('BT9', '(Empr)', cell_format_sub7)         #-- 75

            worksheet.write('BV9', '(Mensual)', cell_format_sub5)      #-- 75      COSTO MENSUAL

            worksheet.write('CE9', 'TIPO', cell_format_sub6)         #-- 70      COMISIÓN
            worksheet.write('CF9', 'MIXTA', cell_format_sub6)         #-- 71      
            worksheet.write('CG9', 'FLUJO', cell_format_sub6)         #-- 72      
            worksheet.write('CH9', 'AFP', cell_format_sub7)         #-- 73      TOTALES
            worksheet.write('CI9', 'ONP', cell_format_sub7)         #-- 74

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
                current_format_cent = cell_format_cesado_cent if w_boleta.x_studio_cesado else cell_format_cent
                current_format_left = cell_format_cesado_left if w_boleta.x_studio_cesado else cell_format_left
                current_format_impo = cell_format_cesado_impo if w_boleta.x_studio_cesado else cell_format_impo
                current_format_fech = cell_format_cesado_fech if w_boleta.x_studio_cesado else cell_format_fech
                current_format_nume = cell_format_cesado_nume if w_boleta.x_studio_cesado else cell_format_nume
                current_format_imp2 = cell_format_cesado_impo if w_boleta.x_studio_cesado else cell_format_imp2
       
                if w_boleta.x_studio_cesado:
                    worksheet.write(w_fila, 0, 'CESADO', cell_format_rojo)
                else:
                    worksheet.write(w_fila, 0, w_fila-8, cell_format_cent)
                # worksheet.write(w_fila, 0, w_boleta.id, cell_format_cent)   
                worksheet.write(w_fila, 1, w_boleta.number, current_format_cent)
                w_dato = w_boleta.employee_id.name
                worksheet.write(w_fila, 2, w_dato, current_format_left)
                worksheet.write(w_fila, 3, w_boleta.x_studio_dni, current_format_cent)

                # w_dato = w_boleta.payslip_run_id.name
                w_dato = ""
                w_mes = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').month
                w_dia = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').day
                w_ano = datetime.strptime(str(w_boleta.date_to), '%Y-%m-%d').year
                w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)[:3]
                worksheet.write(w_fila, 4, w_dato, current_format_cent)
                if (w_switch == 0):
                    w_dato = str(w_ano) + "-" + self.mes_literal(w_mes)
                    worksheet.write('H5', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    worksheet.write('AT5', 'PLANILLA GENERAL DE SUELDOS - EMPLEADOS CENS - ' + w_dato, cell_format_cabe)
                    w_switch = 1
                
                w_dato = w_boleta.employee_id.first_contract_date
                worksheet.write(w_fila, 5, w_dato, current_format_fech)
              
                w_dato = w_boleta.employee_id.x_studio_unidad_negocio
                worksheet.write(w_fila, 6, w_dato, current_format_cent)
                
                w_dato = w_boleta.currency_id.name
                worksheet.write(w_fila, 7, w_dato, current_format_cent)
                # ----------------------------
                # -- REGISTRO INGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 8, w_boleta.x_studio_dias_computados, current_format_nume)

                worksheet.write(w_fila, 9, w_boleta.x_studio_movilidad, current_format_impo)
                worksheet.write(w_fila, 10, w_boleta.x_studio_vale_alimentos, current_format_impo)
                worksheet.write(w_fila, 11, w_boleta.x_studio_condiciones_laborales, current_format_impo)
                worksheet.write(w_fila, 12, w_boleta.x_studio_bonificacion_educacion, current_format_impo)
                worksheet.write(w_fila, 13, w_boleta.x_studio_utilidades_voluntarias, current_format_impo)
                # ----------------------------
                # -- REGISTRO EGRESOS --
                # ----------------------------
                worksheet.write(w_fila, 14, w_boleta.x_studio_descuento_inasistencias, current_format_impo)
                worksheet.write(w_fila, 15, w_boleta.x_studio_dias_sin_goce, current_format_impo)
                worksheet.write(w_fila, 16, w_boleta.x_studio_adelanto_sueldo, current_format_impo)
                worksheet.write(w_fila, 17, w_boleta.x_studio_descuento_tardanzas_min, current_format_impo)
                worksheet.write(w_fila, 18, w_boleta.x_studio_retencion_judicial, current_format_impo)
                worksheet.write(w_fila, 19, w_boleta.x_studio_descuento_prestamos, current_format_impo)
                
                # ----------------------------------------------------------------------------------------
                # -- DATOS CALCULADOS FINALES PLANILLA -- DATOS QUE INGRESAN A LA BOLETA DE PAGO
                # ----------------------------------------------------------------------------------------
                #
                # -----------------------------------------
                # BOLETA PAGO - INGRESOS
                # -----------------------------------------
                worksheet.write(w_fila, 21, w_boleta.x_studio_en_basico, current_format_impo)
                worksheet.write(w_fila, 22, w_boleta.x_studio_en_asignacion_familiar, current_format_impo)
                worksheet.write(w_fila, 23, w_boleta.x_studio_en_licencia_con_ghaber, current_format_impo)
                worksheet.write(w_fila, 24, w_boleta.x_studio_en_licencia_fallecimiento, current_format_impo)
                worksheet.write(w_fila, 25, w_boleta.x_studio_en_licencia_materpater, current_format_impo)
                worksheet.write(w_fila, 26, w_boleta.x_studio_en_bonificacion_cumplimiento, current_format_impo)
                worksheet.write(w_fila, 27, w_boleta.x_studio_en_descanso_medico, current_format_impo)
                worksheet.write(w_fila, 28, w_boleta.x_studio_en_feriados, current_format_impo)
                worksheet.write(w_fila, 29, w_boleta.x_studio_en_horas_extras, current_format_impo)
                worksheet.write(w_fila, 30, w_boleta.x_studio_en_vacaciones, current_format_impo)
                worksheet.write(w_fila, 31, w_boleta.x_studio_en_descanso_vacacional, current_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - CONCEPTOS NO REMUNERATIVOS
                # -----------------------------------------
                worksheet.write(w_fila, 32, w_boleta.x_studio_en_vale_alimentacion, current_format_impo)
                worksheet.write(w_fila, 33, w_boleta.x_studio_en_vale_movilidad, current_format_impo)
                worksheet.write(w_fila, 34, w_boleta.x_studio_en_condiciones_laborales, current_format_impo)
                worksheet.write(w_fila, 35, w_boleta.x_studio_en_bonificacion_educacion, current_format_impo)
                worksheet.write(w_fila, 36, w_boleta.x_studio_en_utilidades_voluntarias, current_format_impo)
                worksheet.write(w_fila, 37, w_boleta.x_studio_en_reembolso_combustible, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - CONCEPTOS DE LIQUIDACIÓN  - ASIGNAR CAMPOS REALES
                # -----------------------------------------
                worksheet.write(w_fila, 38, w_boleta.x_studio_cese_vaca_trunca, current_format_impo)
                worksheet.write(w_fila, 39, w_boleta.x_studio_cese_cts_trunco, current_format_impo)
                worksheet.write(w_fila, 40, w_boleta.x_studio_cese_grati_trunca, current_format_impo)
                worksheet.write(w_fila, 41, w_boleta.x_studio_cese_bonif_grati_trunca, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - DESCUENTOS
                # -----------------------------------------
                worksheet.write(w_fila, 42, w_boleta.x_studio_en_licencia_sin_ghaber, current_format_impo)
                worksheet.write(w_fila, 43, w_boleta.x_studio_en_adelanto_sueldo, current_format_impo)
                if (w_boleta.x_studio_compania_afp):
                    w_nombre_cia = w_boleta.x_studio_compania_afp.x_name
                    worksheet.write(w_fila, 44, w_nombre_cia, current_format_left)
                    if (w_nombre_cia == 'ONP'):
                        worksheet.write(w_fila, 45, " ", current_format_impo)
                        worksheet.write(w_fila, 46, w_boleta.x_studio_en_afp_onp, current_format_impo)
                    else:
                        worksheet.write(w_fila, 45, w_boleta.x_studio_en_afp_onp, current_format_impo)
                        worksheet.write(w_fila, 46, " ", current_format_impo)

                worksheet.write(w_fila, 47, w_boleta.x_studio_en_inasistencias, current_format_impo)
                worksheet.write(w_fila, 48, w_boleta.x_studio_en_tardanzas, current_format_impo)
                worksheet.write(w_fila, 49, w_boleta.x_studio_en_renta_5ta, current_format_impo)
                worksheet.write(w_fila, 50, w_boleta.x_studio_en_retencion_judicial, current_format_impo)
                worksheet.write(w_fila, 51, w_boleta.x_studio_en_descuento_prestamos, current_format_impo)
                worksheet.write(w_fila, 52, w_boleta.x_studio_aporte_eps_2, current_format_impo)
                # -----------------------------------------
                # BOLETA PAGO - INCREMENTOS DIRECTOS
                # -----------------------------------------
                worksheet.write(w_fila, 53, w_boleta.x_studio_en_reembolso, current_format_impo)
                worksheet.write(w_fila, 54, w_boleta.x_studio_en_reembolso_movilidad, current_format_impo)
                worksheet.write(w_fila, 55, w_boleta.x_studio_en_adelanto_gratificacion, current_format_impo)
                worksheet.write(w_fila, 56, w_boleta.x_studio_en_indemniza_despido_arbitrario, current_format_impo)
                worksheet.write(w_fila, 57, w_boleta.x_studio_especial_ac, current_format_impo)

                # -----------------------------------------
                # BOLETA PAGO - TOTALIZADO RESUMEN
                # -----------------------------------------
                w_tota_lbs = 0
                w_tota_lbs += w_boleta.x_studio_cese_vaca_trunca
                w_tota_lbs += w_boleta.x_studio_cese_cts_trunco
                w_tota_lbs += w_boleta.x_studio_cese_grati_trunca
                w_tota_lbs += w_boleta.x_studio_cese_bonif_grati_trunca
                worksheet.write(w_fila, 59, w_boleta.x_studio_en_gross, current_format_impo)
                worksheet.write(w_fila, 60, w_boleta.x_studio_en_total_remuneracion_bruta, current_format_impo)
                worksheet.write(w_fila, 61, -w_boleta.x_studio_total_descuentos, current_format_impo)
                worksheet.write(w_fila, 62, w_boleta.x_studio_sub_total_incremespeciales, current_format_impo)
                worksheet.write(w_fila, 63, w_tota_lbs, current_format_impo)
                w_tota_gen = w_boleta.x_studio_en_total_remuneracion + w_tota_lbs
                worksheet.write(w_fila, 64, w_tota_gen, current_format_imp2)

                # -----------------------------------------
                # APORTES
                # -----------------------------------------
                worksheet.write(w_fila, 66, w_boleta.x_studio_aporte_a_essalud, current_format_impo)
                worksheet.write(w_fila, 67, w_boleta.x_studio_en_aportes_eps, current_format_impo)
                # -----------------------------------------
                # PROVISIONES
                # -----------------------------------------
                worksheet.write(w_fila, 68, w_boleta.x_studio_en_provision_cts, current_format_impo)
                worksheet.write(w_fila, 69, w_boleta.x_studio_en_provision_vacaciones, current_format_impo)
                worksheet.write(w_fila, 70, w_boleta.x_studio_en_provision_gratificacion, current_format_impo)
                worksheet.write(w_fila, 71, w_boleta.x_studio_en_provision_bonigrati, current_format_impo)
                # -----------------------------------------
                # COSTO DEL MES
                # -----------------------------------------
                worksheet.write(w_fila, 73, w_boleta.x_studio_en_total_extraordinario, current_format_imp2)

                # -----------------------------------------
                # DETALLE CUENTA BANCARIA
                # -----------------------------------------
                w_dato = w_boleta.employee_id.x_studio_nombre_banco
                worksheet.write(w_fila, 75, w_dato, current_format_imp2)

                w_dato = w_boleta.employee_id.x_studio_numero_cuenta
                worksheet.write(w_fila, 76, w_dato, current_format_imp2)

                w_dato = w_boleta.employee_id.x_studio_cci
                worksheet.write(w_fila, 77, w_dato, current_format_imp2)
                
                # -----------------------------------------
                # DESAGREGADO DE AFP/ONP
                # -----------------------------------------
                if (w_boleta.x_studio_compania_afp):
                    w_nombre_cia = w_boleta.x_studio_compania_afp.x_name
                    worksheet.write(w_fila, 79, w_nombre_cia, current_format_left)
                    if (w_nombre_cia == 'ONP'):
                        worksheet.write(w_fila, 86, w_boleta.x_studio_en_afp_onp, current_format_impo)
                    else:
                        worksheet.write(w_fila, 80, w_boleta.x_studio_en_afp_aporte_obligatorio, current_format_impo)
                        worksheet.write(w_fila, 81, w_boleta.x_studio_en_afp_prima_seguro, current_format_impo)
                        # w_boleta.x_studio_en_tipo_comision
                        worksheet.write(w_fila, 82, w_boleta.x_studio_en_tipo_comision, current_format_cent)
                        if (w_boleta.x_studio_en_tipo_comision == 'MIX'):
                            worksheet.write(w_fila, 83, w_boleta.x_studio_en_comision_mixta, current_format_impo)
                        if (w_boleta.x_studio_en_tipo_comision == 'FLU'):
                            worksheet.write(w_fila, 84, w_boleta.x_studio_en_comision_flujo, current_format_impo)

                        worksheet.write(w_fila, 85, w_boleta.x_studio_en_afp_onp, current_format_impo)
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



