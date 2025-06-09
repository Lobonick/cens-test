from odoo import _, api, fields, models
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import base64
import xlrd
import xlsxwriter
from io import BytesIO
import calendar
import logging
_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_recalcula_bbss(self):
        """
        CALCULA LOS VALORES PARA: 
        - Vacaciones Truncas
        - CTS Truncas
        - Gratificaciones Truncas
        - Bonific. Gratificaciones
             w_dia_fini = fecha_inicial.day
        """
        w_fecha = datetime.now().date()
        if self.x_studio_cesado:
            w_fecha_ingr = self.x_studio_cese_fecha_ingreso
            w_fecha_cese = self.x_studio_cese_fecha
            w_total_remu = self.x_studio_salario_mensual + self.x_studio_en_asignacion_familiar 
            w_comentario = "Cálculo realizado x ODOO-CENS."

            # --------------------------------------------------
            #  CALCULA VACACIONES TRUNCAS
            # --------------------------------------------------
            w_period_vac = self.desglosa_periodo("VACACIONES TRUNCAS", w_fecha_ingr, w_fecha_cese)
            w_trunco_vac = 0.00
            w_trunco_vac += w_total_remu * w_period_vac.get('anios', 0)               #--- Por el rango Anios
            w_trunco_vac += (w_total_remu/12) * w_period_vac.get('meses', 0)          #--- Por el rango meses
            w_trunco_vac += ((w_total_remu/12)/30) * w_period_vac.get('dias', 0)      #--- Por el rango días

            # --------------------------------------------------
            #  CALCULA CTS TRUNCOS
            # --------------------------------------------------
            w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_ingr, w_fecha_cese)
            w_tota_meses = w_period_cts.get('meses', 0) + (w_period_cts.get('anios', 0) * 12)   #-- Determina Meses Trabajando
            if (w_tota_meses > 6):
                w_remu_cts = w_total_remu + (w_total_remu/6 if w_total_remu > 0 else 0.00)
            else:
                w_remu_cts = w_total_remu

            w_fecha_tope = self.determina_periodo(w_fecha_ingr, w_fecha_cese)
            w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_cese)
            w_trunco_cts = 0.00
            w_trunco_cts += ((w_remu_cts/12) * w_period_cts.get('meses', 0))                #--- Por el rango meses
            w_trunco_cts += (((w_remu_cts/12)/30) * w_period_cts.get('dias', 0))           #--- Por el rango días         

            # --------------------------------------------------
            #  CALCULA GRATIFICACIONES TRUNCAS
            # --------------------------------------------------
            w_inicio_anio  = date(2025, 1, 1)
            if (w_fecha_ingr >= w_inicio_anio):
                w_inicio_grati = w_fecha_ingr
            else:
                w_inicio_grati = w_inicio_anio
            w_period_grati = self.desglosa_periodo("GRATIFICACIONES TRUNCAS", w_inicio_grati, w_fecha_cese)
            # w_tramo_dd1  = w_period_grati.get('tramo_dd1', 0)
            # w_tramo_dd2  = w_period_grati.get('tramo_dd2', 0)
            # w_tramo_dd3  = w_period_grati.get('tramo_dd3', 0)
            # w_total_dias = (w_tramo_dd1 if w_tramo_dd1<30 else 0) + w_tramo_dd2 + (w_tramo_dd3 if w_tramo_dd3<30 else 0)

            w_trunco_grati = 0.00
            w_trunco_grati += ((w_total_remu/6) * w_period_grati.get('meses', 0))    #--- Por el rango MESES

            # --------------------------------------------------
            #  CALCULA BONIFICACIÓN DE GRATIF TRUNCAS
            # --------------------------------------------------
            w_trunco_bonif = 0.00
            w_trunco_bonif += w_trunco_grati * 0.09                             #--- Por el rango meses

        else:
            w_trunco_vac = 0.00
            w_trunco_cts = 0.00
            w_trunco_grati = 0.00
            w_trunco_bonif = 0.00
            w_comentario = ""

        # --------------------------------------------------
        #  ACTUALIZA CAMPOS
        # --------------------------------------------------
        self.ensure_one()
        self.write({
                'x_studio_cese_vaca_trunca': w_trunco_vac,
                'x_studio_cese_cts_trunco': w_trunco_cts,
                'x_studio_cese_grati_trunca': w_trunco_grati,
                'x_studio_cese_bonif_grati_trunca': w_trunco_bonif,
                'x_studio_cese_comentarios': w_comentario
            })  
        self.recompute()

        pass

    def action_recalcula_en_datos(self):
        #
        # Activa y desactiva el RECÁLCULO
        #
        #for rec in self:
        #    rec.write({'x_studio_en_recalcular': not rec.x_studio_en_recalcular})      #----- Para funciona en creación individual
        #    rec.recompute()
        if self.x_studio_fecha_ingreso_laboral:
            w_fecha = self.x_studio_fecha_ingreso_laboral
        else:
            w_fecha = datetime.now().date()                     #--- Igual la Fecha Ingreso Cálculo = Histórico 
        if self.x_studio_cese_fecha_ingreso:
            w_fecha = self.x_studio_cese_fecha_ingreso
            
        w_trunco_vac = 0.00
        w_trunco_cts = 0.00
        w_trunco_gra = 0.00
        w_trunco_bon = 0.00
        w_comentario = ""
        # --------------------------------------------------
        #  BLANQUEA CAMPOS
        # --------------------------------------------------
        self.ensure_one()
        self.write({
                'x_studio_cese_fecha_ingreso': w_fecha,
                'x_studio_cese_vaca_trunca': w_trunco_vac,
                'x_studio_cese_cts_trunco': w_trunco_cts,
                'x_studio_cese_grati_trunca': w_trunco_gra,
                'x_studio_cese_bonif_grati_trunca': w_trunco_bon,
                'x_studio_cese_comentarios': w_comentario,
                'x_studio_cesado': False
            })  
        self.recompute()
        pass

    def determina_periodo(self, fecha_inicial, fecha_final):
        ingr_fecha  = fecha_inicial
        cese_fecha  = fecha_final
        ajus_fecha_tope = cese_fecha
        w_cont = 0
        max_iterations = 1000  # Protección contra bucles infinitos

        while w_cont < max_iterations:
            w_cont += 1
            ajus_fecha_tope = ajus_fecha_tope - timedelta(days=1)  # Usar timedelta para restar días
            ajus_anio = ajus_fecha_tope.year 
            top1_param = date(ajus_anio, 5, 1)
            top2_param = date(ajus_anio, 11, 1)
            #if ((ajus_fecha_tope.month==cese_fecha.month) and (ajus_fecha_tope.month==cese_fecha.month)):
            #    w_salto = True
            #else:
            #    w_salto = False

            if (ajus_fecha_tope == top1_param) or (ajus_fecha_tope == top2_param):
                #if not w_salto: 
                break

        if (ingr_fecha >= ajus_fecha_tope):
            ajus_fecha_tope = ingr_fecha 

        return ajus_fecha_tope


    def desglosa_periodo(self, cproceso, fecha_inicial, fecha_final):
        # --------------------------------------------------
        #  CALCULA RANGOS DE TIEMPO (días, meses, años)
        # --------------------------------------------------
        w_cproceso  = cproceso.upper()
        w_dia_fini = fecha_inicial.day
        w_mes_fini = fecha_inicial.month
        w_ano_fini = fecha_inicial.year
        w_dia_ffin = fecha_final.day
        w_mes_ffin = fecha_final.month
        w_ano_ffin = fecha_final.year

        # ============================================================================================================

        w_tramo_1    = 1 if w_dia_fini>=30 else int((30 - w_dia_fini) + 1) 
        w_tramo_1_dd = 30 if w_tramo_1>=30 else w_tramo_1
        w_tramo_1_mm = 12 - w_mes_fini

        w_tramo_2    = int(30 if w_dia_ffin==31 else w_dia_ffin )
        w_tramo_2_dd = w_tramo_2
        w_tramo_2_mm = w_mes_ffin - 1

        w_calcu_aa_1 = (w_ano_ffin - w_ano_fini) - 1

        w_calcu_mm_1 = ((w_mes_ffin-w_mes_fini)-1 if w_calcu_aa_1<0 else w_tramo_1_mm + w_tramo_2_mm ) + int((w_tramo_1_dd + w_tramo_2_dd)/30)

        w_calcu_aa_2 = (0 if w_calcu_aa_1<=0 else w_calcu_aa_1) + (int(w_calcu_mm_1 / 12) if w_calcu_mm_1>=12 else 0)  
                        # =SI(D14<=0;0;D14) + SI(D15>=12;ENTERO(D15/12);0)

        w_calcu_mm_2 = int(w_calcu_mm_1 % 12) if w_calcu_mm_1>12 else w_calcu_mm_1  

        w_calcu_dd_1 = int((w_tramo_1_dd + w_tramo_2_dd) % 30)

        w_calcu_dd_2 = w_calcu_dd_1

        # ============================================================================================================

        w_total_anos = w_calcu_aa_2
        w_total_mese = w_calcu_mm_2
        w_total_dias = w_calcu_dd_2
        w_total_dd1  = w_tramo_1_dd
        w_total_dd2  = w_total_anos * 360 
        w_total_dd3  = w_tramo_2_dd

        _logger.info(f'------------------------------------------')
        _logger.info(f'PROCESO:  {w_cproceso}')
        _logger.info(f'------------------------------------------')
        _logger.info(f'          F.Fin = {fecha_inicial} ')
        _logger.info(f'          F.Ini = {fecha_final} ')
        _logger.info(f'RESULTADO:  año = {w_total_anos} ')
        _logger.info(f'            mes = {w_total_mese} ')
        _logger.info(f'            dia = {w_total_dias} ')
        _logger.info(f'------------------------------------------')
        _logger.info(f'TRAMO DÍAS: Ini = {w_total_dd1} ')
        _logger.info(f'            Med = {w_total_dd2} ')
        _logger.info(f'            Fin = {w_total_dd3} ')
        _logger.info(f'------------------------------------------')

        return {
            'anios': w_total_anos,
            'meses': w_total_mese,
            'dias': w_total_dias,
            'tramo_dd1': w_total_dd1,
            'tramo_dd2': w_total_dd2,
            'tramo_dd3': w_total_dd3
        }
    
        
    def ultimo_dia_del_mes(self, fecha):
        #primer_dia_del_mes = fecha.replace(day=1)
        #ultimo_dia_del_mes = primer_dia_del_mes + datetime.timedelta(days=31)
        #return ultimo_dia_del_mes - datetime.timedelta(days=1)
        # Validación de tipos de datos
        if not fecha or not isinstance(fecha, (date, datetime)):
            _logger.error(f"fecha no es una fecha válida: {fecha}")
            return False
        
        # Convertir a date si es datetime
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        
        # Método usando libreria CALENDAR
        ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
        return date(fecha.year, fecha.month, ultimo_dia)
    

    def action_listado_calculo_cts(self):
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
                    'title':    'NOMINA-CENS - Cálculo CTS',
                    'subject':  'Calculo de CTS a la fecha',
                    'author':   'ODOO-CENS',
                    'manager':  'Gestión Humana',
                    'company':  'CENS PERÚ',
                    'category': 'LOTE - EXCEL',
                    'keywords': 'nómina, lote, cts',
                    'created':  datetime.now(),
                    'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})
            worksheet = workbook.add_worksheet('CÁLCULO CTS 2025-A')
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
            cell_format_tito = workbook.add_format()
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
            worksheet.set_column(2, 2, 33)      #-- Nombre del Empleado
            worksheet.set_column(3, 3, 13)      #-- DNI
            worksheet.set_column(4, 4, 11)      #-- LOTE
            worksheet.set_column(5, 5, 20)      #-- UNIDAD DE NEGOCIO
            worksheet.set_column(6, 6, 8)       #-- MONEDA
            worksheet.set_column(7, 7, 13)      #-- FECHA INGRESO                   H
            worksheet.set_column(8, 8, 13)      #-- FECHA CESE                      I
            worksheet.set_column(9, 9, 12)      #-- Sueldo Básico                   J
            worksheet.set_column(10, 10, 12)    #-- Asignación Familiar             K
            worksheet.set_column(11, 11, 12)    #-- Sexto Gratificación             L
            worksheet.set_column(12, 12, 12)    #-- Total Remuneración              M
            worksheet.set_column(13, 13, 12)    #-- COSTO: años                     N
            worksheet.set_column(14, 14, 12)    #-- COSTO: meses                    O
            worksheet.set_column(15, 15, 12)    #-- COSTO: días                     P
            worksheet.set_column(16, 16, 10)    #-- Periodo: Años                   Q
            worksheet.set_column(17, 17, 10)    #-- Periodo: Meses      DESGLOSADO  R
            worksheet.set_column(18, 18, 10)    #-- Periodo: Días                   S
            worksheet.set_column(19, 19, 13)    #-- PERIODO - Fecha Inicio          T
            worksheet.set_column(20, 20, 13)    #-- PERIODO - Fecha Final           U
            worksheet.set_column(21, 21, 12)    #-- Importe CTS
            worksheet.set_column(22, 22, 50)    #-- Observaciones

            worksheet.set_column(23, 23, 5)     #--     (Seperador)

            worksheet.set_column(24, 24, 12)    #-- 
            worksheet.set_column(25, 25, 12)    #--
            worksheet.set_column(26, 26, 12)    #--     LIQUIDACIONES
            worksheet.set_column(27, 27, 12)    #--

            # ------
            worksheet.set_row(7, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A2', 'src/user/cens_nomina_excel_01/static/description/logo-tiny_96.png')
            worksheet.insert_image('AA2', 'src/user/cens_nomina_excel_01/static/description/Logo-Odoo-tiny.png', 
                                         {'x_scale': 0.7, 'y_scale': 0.7})
            worksheet.write('B3', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B4', 'Gestión Humana - Nóminas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)
            worksheet.write('H5', 'COMPENSACIÓN POR TIEMPO DE SERVICIOS - CÁLCULO CTS', cell_format_cabe)
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

            worksheet.merge_range('H7:I7', 'Merged Cells', merge_format)
            worksheet.write('H7', 'TIEMPO LABORAL', cell_format_tuti)

            worksheet.merge_range('J7:M7', 'Merged Cells', merge_format)
            worksheet.write('J7', 'REMUNERACION', cell_format_tut2)

            worksheet.merge_range('N7:P7', 'Merged Cells', merge_format)
            worksheet.write('N7', 'COSTOS UNID.TIEMPO', cell_format_tuti)

            worksheet.merge_range('Q7:S7', 'Merged Cells', merge_format)
            worksheet.write('Q7', 'DESGLOSE PERIODO', cell_format_tut2)

            worksheet.merge_range('T7:U7', 'Merged Cells', merge_format)
            worksheet.write('T7', 'PERIODO CÁLCULO', cell_format_tuti)

            worksheet.merge_range('Y7:AB7', 'Merged Cells', merge_format)
            worksheet.write('Y7', 'LIQUIDACIÓN BENEFICIOS', cell_format_tut2)
            
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
            cell_format_tito.set_font_name('Arial')
            cell_format_tito.set_font_color('white')
            cell_format_tito.set_font_size(8)
            cell_format_tito.set_text_wrap()                 # FORMATO TÍTULO - TODA LA BARRA
            cell_format_tito.set_bg_color('#2A7486')
            cell_format_tito.set_align('center')
            cell_format_tito.set_align('vcenter')
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
            worksheet.write('F8', 'UNIDAD NEGOCIO', cell_format_titu)               #-- 06
            worksheet.merge_range('G8:G9', 'Merged Cells', merge_format)
            worksheet.write('G8', 'MONEDA', cell_format_titu)                       #-- 07

            worksheet.write('H8', 'FECHA INGRESO', cell_format_tito)                #-- 05
            worksheet.write('I8', 'FECHA CESE', cell_format_tito)                   #-- 06

            worksheet.write('J8', 'SUELDO BÁSICO', cell_format_titu)                #-- 08
            worksheet.write('K8', 'ASIGNACIÓN FAMILIAR', cell_format_titu)          #-- 
            worksheet.write('L8', 'SEXTO GRATIFIC', cell_format_titu)          #-- 11
            worksheet.write('M8', 'TOTAL REMUNERACIÓN', cell_format_tit2)                   #-- 09

            worksheet.write('N8', 'AÑOS', cell_format_tito)              #-- 10
            worksheet.write('O8', 'MESES', cell_format_tito)         #-- 13
            worksheet.write('P8', 'DÍAS', cell_format_tito)

            worksheet.write('Q8', 'AÑOS', cell_format_titu)          #-- 12
            worksheet.write('R8', 'MESES', cell_format_titu)         #-- 13
            worksheet.write('S8', 'DÍAS', cell_format_titu)              #-- 14

            worksheet.write('T8', 'INICIO', cell_format_tito)               #-- 15
            worksheet.write('U8', 'FINAL', cell_format_tito)               #-- 16
            worksheet.write('V8', 'IMPORTE CTS', cell_format_tit2)             #-- 17   REGISTRO EGRESOS
            worksheet.write('W8', 'OBSERVACIONES', cell_format_titu)            #-- 18

            worksheet.write('Y8', 'VACACIONES TRUNCAS', cell_format_tit8)       #-- 38
            worksheet.write('Z8', 'CTS TRUNCO', cell_format_tit8)               #-- 39
            worksheet.write('AA8', 'GRATIFIC TRUNCA', cell_format_tit8)          #-- 40     LIQUIDACIÓN
            worksheet.write('AB8', 'BONIF.GRATI TRUNCA', cell_format_tit8)       #-- 41

            #----------------------------------------------------------------
            worksheet.write('I9', '(aaa/mm/dd)', cell_format_tut4)                 #-- 09
            worksheet.write('H9', '(aaa/mm/dd)', cell_format_tut4)         #-- 34
            worksheet.write('J9', 'S/.', cell_format_tut4)                 #-- 10
            worksheet.write('K9', 'S/.', cell_format_tut4)                 #-- 11
            worksheet.write('L9', 'S/.', cell_format_tut4)                 #-- 12
            worksheet.write('M9', 'S/.', cell_format_tut4)                 #-- 12
            worksheet.write('N9', 'S/.', cell_format_tut4)                 #-- 12
            worksheet.write('O9', 'S/.', cell_format_tut4)                 #-- 13
            worksheet.write('P9', 'S/.', cell_format_tut4)                 #-- 15
            worksheet.write('Q9', 'aa', cell_format_tut4)                  #-- 16
            worksheet.write('R9', 'mm', cell_format_tut4)                  #-- 17
            worksheet.write('S9', 'dd', cell_format_tut4)                  #-- 18
            worksheet.write('T9', '(dd/mm/aaaa)', cell_format_tut4)             #-- 19
            worksheet.write('U9', '(dd/mm/aaaa)', cell_format_tut4)             #-- 20
            worksheet.write('V9', 'S/.', cell_format_tut4)                 #-- 21
            worksheet.write('W9', '', cell_format_tut4)                    #-- 22

            worksheet.write('Y9', '(Cese)', cell_format_sub8)         #-- 40
            worksheet.write('Z9', '(Cese)', cell_format_sub8)         #-- 41
            worksheet.write('AA9', '(Cese)', cell_format_sub8)         #-- 42      LIQUIDACIONES
            worksheet.write('AB9', '(Cese)', cell_format_sub8)         #-- 43

            #-----
            # worksheet.autofilter(8, 60, 8, 65)  #--- Coloca FILTROS en RESUMEN 
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
              
                w_dato = w_boleta.employee_id.x_studio_unidad_negocio
                worksheet.write(w_fila, 5, w_dato, current_format_cent)
                
                w_dato = w_boleta.currency_id.name
                worksheet.write(w_fila, 6, w_dato, current_format_cent)

                # ----------------------------
                if not w_boleta.x_studio_cese_fecha_ingreso:
                    w_boleta.write({'x_studio_cese_fecha_ingreso': w_boleta.x_studio_fecha_ingreso_laboral})

                w_fecha_ingr = w_boleta.x_studio_cese_fecha_ingreso if w_boleta.x_studio_cese_fecha_ingreso else w_boleta.employee_id.first_contract_date 
                worksheet.write(w_fila, 7, w_fecha_ingr, current_format_fech)
                # ----------------------------

                if w_boleta.x_studio_cese_fecha:
                    w_fecha_fiin = w_boleta.x_studio_cese_fecha if w_boleta.x_studio_cesado else date(2025, 4, 30)
                else:
                    w_fecha_fiin = date(2025, 4, 30)

                if w_boleta.x_studio_cesado:
                    worksheet.write(w_fila, 8, w_fecha_fiin, current_format_fech)

                # -------------------------------------
                # --   CALCULO DE DATOS GENERALES    --
                # -------------------------------------
                worksheet.write(w_fila, 9, w_boleta.x_studio_salario_mensual, current_format_impo)
                worksheet.write(w_fila, 10, w_boleta.x_studio_en_asignacion_familiar, current_format_impo)

                w_impo_sext = 0.00
                worksheet.write(w_fila, 11, " " if w_impo_sext==0.00 else w_impo_sext, current_format_impo)
                
                w_impo_remu = w_boleta.x_studio_salario_mensual + w_boleta.x_studio_en_asignacion_familiar + w_impo_sext
                worksheet.write(w_fila, 12, w_impo_remu, current_format_imp2)
                
                w_impo_cano = w_impo_remu if w_impo_remu > 0 else 0.00
                w_impo_cmes = w_impo_remu/12 if w_impo_remu > 0 else 0.00
                w_impo_cdia = (w_impo_remu/12)/30 if w_impo_remu > 0 else 0.00
                worksheet.write(w_fila, 13, w_impo_cano, current_format_impo)
                worksheet.write(w_fila, 14, w_impo_cmes, current_format_impo)
                worksheet.write(w_fila, 15, w_impo_cdia, current_format_impo)

                # --------------------------------------------------
                #  CALCULA CTS TRUNCOS
                # --------------------------------------------------
                w_fecha_tope = self.determina_periodo(w_fecha_ingr, w_fecha_fiin)
                w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_fiin)
                w_desgl_anio = w_period_cts.get('anios', 0)
                w_desgl_mess = w_period_cts.get('meses', 0)
                w_desgl_dias = w_period_cts.get('dias', 0)
                w_trunco_cts = 0.00
                w_trunco_cts += ((w_impo_remu/12) * w_period_cts.get('meses', 0))                #--- Por el rango meses
                w_trunco_cts += (((w_impo_remu/12)/30) * w_period_cts.get('dias', 0))           #--- Por el rango días

                worksheet.write(w_fila, 16, w_desgl_anio, current_format_nume)
                worksheet.write(w_fila, 17, w_desgl_mess, current_format_nume)
                worksheet.write(w_fila, 18, w_desgl_dias, current_format_nume)

                worksheet.write(w_fila, 19, w_fecha_tope, current_format_fech)
                worksheet.write(w_fila, 20, w_fecha_fiin, current_format_fech)
                worksheet.write(w_fila, 21, w_trunco_cts, current_format_imp2)
                w_acum_tota_1 += w_trunco_cts

                if w_boleta.x_studio_cesado:
                    worksheet.write(w_fila, 22, w_boleta.x_studio_cese_comentarios + " " + w_boleta.x_studio_cese_observaciones, current_format_left)
                    # -----------------------------------------
                    # BOLETA PAGO - CONCEPTOS DE LIQUIDACIÓN  - ASIGNAR CAMPOS REALES
                    # -----------------------------------------
                    worksheet.write(w_fila, 24, w_boleta.x_studio_cese_vaca_trunca, current_format_impo)
                    worksheet.write(w_fila, 25, w_boleta.x_studio_cese_cts_trunco, current_format_impo)
                    worksheet.write(w_fila, 26, w_boleta.x_studio_cese_grati_trunca, current_format_impo)
                    worksheet.write(w_fila, 27, w_boleta.x_studio_cese_bonif_grati_trunca, current_format_impo)
                else:
                    worksheet.write(w_fila, 22, " ", current_format_left)

                w_fila += 1

            worksheet.write(5, 20, "TOTAL GENERAL:", cell_format_left) 
            worksheet.write(5, 21, w_acum_tota_1, cell_format_impo)

            worksheet.activate()
            workbook.close()
            # ------------------------------------------------------------------

            # Crear adjunto
            xlsx_data = output.getvalue()
            attachment = self.env['ir.attachment'].create({
                'name': 'CENS-CTS-2025-A.xlsx',
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
