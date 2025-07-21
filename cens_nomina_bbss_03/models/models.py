from odoo import _, api, fields, models
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

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
       
    # ===============================================================================================
    # INICIO - Campos liquidación
    # ===============================================================================================

    # # Métodos computados
    @api.depends('x_cens_periodo_ini', 'x_cens_periodo_fin')
    def _compute_tiempo_servicio(self):
        """Calcula el tiempo de servicio en años, meses y días"""
        for record in self:
            if record.x_cens_periodo_ini and record.x_cens_periodo_fin:
                fecha_ini = record.x_cens_periodo_ini
                fecha_fin = record.x_cens_periodo_fin
                
                # Calcular diferencia usando relativedelta
            else:
                record.x_cens_periodo_aa = 0
                record.x_cens_periodo_mm = 0
                record.x_cens_periodo_dd = 0
        
    @api.depends('x_cens_remu_base')
    def _compute_gratificacion(self):
        """Calcula la gratificación como 1/6 de la remuneración base"""
        for record in self:
            if record.x_cens_remu_base:
                record.x_cens_grat_16to = record.x_cens_remu_base / 6.0
            else:
                record.x_cens_grat_16to = 0.0
    
    @api.depends('x_cens_remu_base', 'x_cens_asig_fami', 'x_cens_grat_16to')
    def _compute_remuneracion_computable(self):
        """Calcula la remuneración computable total"""
        for record in self:
            record.x_cens_remu_comp = (
                record.x_cens_remu_base + 
                record.x_cens_asig_fami + 
                record.x_cens_grat_16to
            )
    
    # Método para establecer fechas automáticamente
    @api.onchange('employee_id')
    def _onchange_employee_id_liquidacion(self):
        """Establece fechas automáticamente cuando se selecciona el empleado"""
        if self.employee_id:
            # Fecha de inicio: fecha de contratación del empleado
            if hasattr(self.employee_id, 'contract_ids') and self.employee_id.contract_ids:
                primer_contrato = self.employee_id.contract_ids.sorted('date_start')[0]
                self.x_cens_periodo_ini = primer_contrato.date_start
            
            # Fecha fin: fecha actual o fecha de fin del período de nómina
            if self.date_to:
                self.x_cens_periodo_fin = self.date_to
            else:
                self.x_cens_periodo_fin = date.today()
    
    # Método para calcular automáticamente valores desde las líneas de nómina
    def calcular_valores_desde_nomina(self):
        """Calcula los valores de liquidación desde las líneas de nómina"""
        self.ensure_one()
        
        # Buscar remuneración base en las líneas
        linea_sueldo = self.line_ids.filtered(lambda l: l.code == 'BASIC')
        if linea_sueldo:
            self.x_cens_remu_base = linea_sueldo[0].total
        
        # Buscar asignación familiar
        linea_asig_fam = self.line_ids.filtered(lambda l: l.code in ['ASIG_FAM', 'AF'])
        if linea_asig_fam:
            self.x_cens_asig_fami = linea_asig_fam[0].total
        
        return True
    
    # =============================
    # BOTÓN - GENERAR LIQUIDACIÓN
    # =============================
    def action_liquidacion_compone(self):  
        self.ensure_one()
        if self.x_studio_cesado:
            w_fecha_ingr = self.x_studio_cese_fecha_ingreso
            w_fecha_cese = self.x_studio_cese_fecha
            w_total_remu = self.x_studio_salario_mensual + self.x_studio_en_asignacion_familiar 

            w_period_tot = self.desglosa_periodo("PERIODO TOTAL", w_fecha_ingr, w_fecha_cese)
            w_periodo_aa = w_period_tot.get('anios', 0)
            w_periodo_mm = w_period_tot.get('meses', 0)
            w_periodo_dd = w_period_tot.get('dias', 0)

            w_ctotal_timeserv  = "("+str(w_periodo_aa) + " años) + (" + str(w_periodo_mm) + " meses) + (" + str(w_periodo_dd) + " dias) "
            w_ctotal_tnocomp   = ""
            w_ctotal_tliqui    = w_ctotal_timeserv

            # --------------------------------------------------
            #  CALCULA SEXTO GRATIFICACIONES  
            # --------------------------------------------------
            ajus_anio = w_fecha_cese.year 
            top1_param = date(ajus_anio, 7, 31)
            top2_param = date(ajus_anio-1, 12, 31)
            w_fecha_tope1 = top1_param if w_fecha_cese > top1_param else top2_param
            w_fecha_tope2 = self.determina_periodo_grati(w_fecha_ingr, w_fecha_tope1)
            w_period_grati = self.desglosa_periodo("ÚLTIMA GRATIFICACIÓN", w_fecha_tope2, w_fecha_tope1)
            w_sexto_canti_mm = w_period_grati.get('meses', 0)
            w_sexto_canti_dd = w_period_grati.get('dias', 0)

            w_sexto_costo_mes = w_total_remu 
            w_sexto_costo_dia = w_total_remu/30
            w_sexto_impor_mes = (w_sexto_costo_mes/6) * w_sexto_canti_mm
            w_sexto_impor_dia = (w_sexto_costo_dia/6) * w_sexto_canti_dd
            w_sexto_total = (w_sexto_impor_mes + w_sexto_impor_dia) / 6 
            w_conce_noremuner = 0.00
            w_remun_compu_cts = w_total_remu + w_conce_noremuner + w_sexto_total

            # --------------------------------------------------     
            #  CALCULA CTS TRUNCOS
            # --------------------------------------------------
            w_fecha_tope = self.determina_periodo_cts(w_fecha_ingr, w_fecha_cese)
            w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_cese)
            w_impcts_mes = ((w_remun_compu_cts/12) * w_period_cts.get('meses', 0))                #--- Por el rango meses
            w_impcts_dia = (((w_remun_compu_cts/12)/30) * w_period_cts.get('dias', 0))           #--- Por el rango días
            w_impcts_tot = w_impcts_mes + w_impcts_dia  

            w_detcts_per = "DESDE: " + str(w_fecha_tope.day) + " de " + self.mes_literal(w_fecha_tope.month) + " del " + str(w_fecha_tope.year) + " "
            w_detcts_per += "AL " + str(w_fecha_cese.day) + " de " + self.mes_literal(w_fecha_cese.month) + " del " + str(w_fecha_cese.year) + " "
            w_detcts_mes = "- Por " + str(w_period_cts.get('meses', 0)) + " meses "
            w_detcts_mes += " ( " + self.formato_moneda(w_remun_compu_cts, "S/.") + " ÷ 12 x " + str(w_period_cts.get('meses', 0)) + " )  = "
            w_detcts_dia = "- Por " + str(w_period_cts.get('dias', 0))  + " días  "
            w_detcts_dia += " ( " + self.formato_moneda(w_remun_compu_cts, "S/.") + " ÷ 12 ÷ 30 x " + str(w_period_cts.get('dias', 0)) + " )  = "

            # --------------------------------------------------
            #  CALCULA VACACIONES TRUNCAS
            # --------------------------------------------------
            w_period_vac = self.desglosa_periodo("VACACIONES TRUNCAS", w_fecha_ingr, w_fecha_cese)
            w_detvaca_per = "DESDE: " + str(w_fecha_ingr.day) + " de " + self.mes_literal(w_fecha_ingr.month) + " del " + str(w_fecha_ingr.year) + " "
            w_detvaca_per += "AL " + str(w_fecha_cese.day) + " de " + self.mes_literal(w_fecha_cese.month) + " del " + str(w_fecha_cese.year) + " "

            w_impvaca_ano = w_total_remu * w_period_vac.get('anios', 0)
            w_impvaca_mes = (w_total_remu/12) * w_period_vac.get('meses', 0)           #--- Por el rango meses
            w_impvaca_dia = ((w_total_remu/12)/30) * w_period_vac.get('dias', 0)      #--- Por el rango días
            w_impvaca_tot = w_impvaca_ano + w_impvaca_mes + w_impvaca_dia
            w_impvaca_afp = self.calcula_descuento_afp(w_impvaca_tot)
            w_impvaca_tot = w_impvaca_tot - w_impvaca_afp

            w_detvaca_ano = "- Por " + str(w_period_vac.get('anios', 0)) + " años "
            w_detvaca_ano += " ( " + self.formato_moneda(w_total_remu, "S/.") + "  x " + str(w_period_vac.get('anios', 0)) + " )  = "
            w_detvaca_mes = "- Por " + str(w_period_vac.get('meses', 0)) + " meses "
            w_detvaca_mes += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 12 x " + str(w_period_vac.get('meses', 0)) + " )  = "
            w_detvaca_dia = "- Por " + str(w_period_vac.get('dias', 0))  + " días  "
            w_detvaca_dia += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 12 ÷ 30 x " + str(w_period_vac.get('dias', 0)) + " )  = "

            # --------------------------------------------------
            #  CALCULA GRATIFICACIONES TRUNCAS
            # --------------------------------------------------    ## QUIQUE
            #w_fecha_actual = datetime.now().date()
            w_ano = w_fecha_cese.year
            w_inicio_ano = date(w_ano, 1, 1)
            w_ultimo_dia = self.ultimo_dia_del_mes(w_fecha_cese).day
            if (w_fecha_ingr >= w_inicio_ano):
                w_inicio_ano = w_fecha_ingr
            w_meses_habiles = w_fecha_cese.month 
            w_meses_habiles = w_meses_habiles if w_fecha_cese.month <= 6 else w_meses_habiles - 6 
            w_meses_habiles = w_meses_habiles if w_inicio_ano.day==1 else w_meses_habiles - 1
            w_meses_habiles = w_meses_habiles if not w_ultimo_dia in [30,31] else w_meses_habiles - 1

            w_detgrat_per = "DESDE: " + str(w_inicio_ano.day) + " de " + self.mes_literal(w_inicio_ano.month) + " del " + str(w_inicio_ano.year) + " "
            w_detgrat_per += "AL " + str(w_fecha_cese.day) + " de " + self.mes_literal(w_fecha_cese.month) + " del " + str(w_fecha_cese.year) + " "

            w_trunco_gra = 0.00
            w_trunco_gra += ((w_total_remu/6) * w_meses_habiles)                 #--- Por el rango meses

            w_detgrat_mes = "- Por " + str(w_meses_habiles) + " meses "
            w_detgrat_mes += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 12 x " + str(w_meses_habiles) + " )  = "

            # --------------------------------------------------
            #  CALCULA BONIFICACIÓN DE GRATIF TRUNCAS
            # --------------------------------------------------
            w_trunco_bon = 0.00
            w_trunco_bon += w_trunco_gra * 0.09                             #--- Por el rango meses

            w_detgrat_bon = "- Bonificación 9%"
            w_impgrat_bon = w_trunco_bon 
            w_impgrat_mes = w_trunco_gra 
            w_impgrat_tot = w_trunco_gra + w_trunco_bon

            self.write({
                    'x_cens_periodo_ini': w_fecha_ingr,
                    'x_cens_periodo_fin': w_fecha_cese,
                    'x_cens_periodo_aa': w_periodo_aa,
                    'x_cens_periodo_mm': w_periodo_mm,
                    'x_cens_periodo_dd': w_periodo_dd,
                    'x_cens_ctotal_timeserv': w_ctotal_timeserv,
                    'x_cens_ctotal_tnocomp': w_ctotal_tnocomp,
                    'x_cens_ctotal_tliqui': w_ctotal_tliqui,
                    'x_cens_remu_base': self.x_studio_salario_mensual,
                    'x_cens_asig_fami': self.x_studio_en_asignacion_familiar,
                    'x_cens_grat_16to': w_sexto_total,
                    'x_cens_none_remu': w_conce_noremuner,
                    'x_cens_remu_comp': w_remun_compu_cts,
                    'x_cens_ccts_peri': w_detcts_per,   #-----------------------    CTS
                    'x_cens_ccts_dmes': w_detcts_mes,
                    'x_cens_ccts_imes': w_impcts_mes,
                    'x_cens_ccts_ddia': w_detcts_dia,
                    'x_cens_ccts_idia': w_impcts_dia,
                    'x_cens_ccts_itot': w_impcts_tot,
                    'x_cens_moneda': '(PEN) S/.',
                    'x_cens_vaca_peri': w_detvaca_per,  #-----------------------    VACACIONES
                    'x_cens_vaca_dano': w_detvaca_ano,
                    'x_cens_vaca_iano': w_impvaca_ano,
                    'x_cens_vaca_dmes': w_detvaca_mes,
                    'x_cens_vaca_imes': w_impvaca_mes,
                    'x_cens_vaca_ddia': w_detvaca_dia,
                    'x_cens_vaca_idia': w_impvaca_dia,
                    'x_cens_vaca_dafp': 'Descuento AFP/ONP',
                    'x_cens_vaca_iafp': w_impvaca_afp,
                    'x_cens_vaca_itot': w_impvaca_tot,
                    'x_cens_grat_peri': w_detgrat_per,  #-----------------------    GRATIFICACIÓN
                    'x_cens_grat_dmes': w_detgrat_mes,
                    'x_cens_grat_imes': w_impgrat_mes,
                    'x_cens_grat_dbon': w_detgrat_bon,
                    'x_cens_grat_ibon': w_impgrat_bon,
                    'x_cens_grat_itot': w_impgrat_tot
                })  
            self.recompute()
        pass

    # ==========================
    # BOTÓN - BLANQUEA
    # ==========================
    def action_liquidacion_blanquea(self):
        self.ensure_one()
        self.write({
                'x_cens_periodo_ini': "",
                'x_cens_periodo_fin': "",
                'x_cens_periodo_aa': 0,
                'x_cens_periodo_mm': 0,
                'x_cens_periodo_dd': 0,
                'x_cens_ctotal_timeserv': '00 años, 00 meses, 00 días',
                'x_cens_ctotal_tnocomp': '00 años, 00 meses, 00 días',
                'x_cens_ctotal_tliqui': '00 años, 00 meses, 00 días',
                'x_cens_remu_base': 0.00,
                'x_cens_asig_fami': 0.00,
                'x_cens_grat_16to': 0.00,
                'x_cens_none_remu': 0.00,
                'x_cens_remu_comp': 0.00,
                'x_cens_ccts_peri': "",
                'x_cens_ccts_dmes': "",
                'x_cens_ccts_imes': 0.00,
                'x_cens_ccts_ddia': "",
                'x_cens_ccts_idia': 0.00,
                'x_cens_ccts_itot': 0.00
            })  
        self.recompute()
        pass

    # ==========================
    # BOTÓN - IMPRIMIR
    # ==========================
    def action_liquidacion_imprimir(self):
        self.ensure_one()
        pass

    # ===============================================================================================
    # FIN - Campos liquidación
    # ===============================================================================================


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
            #  CALCULA SEXTO GRATIFICACIONES  
            # --------------------------------------------------
            ajus_anio = w_fecha_cese.year 
            top1_param = date(ajus_anio, 7, 31)
            top2_param = date(ajus_anio-1, 12, 31)
            w_fecha_tope1 = top1_param if w_fecha_cese > top1_param else top2_param
            w_fecha_tope2 = self.determina_periodo_grati(w_fecha_ingr, w_fecha_tope1)
            w_period_grati = self.desglosa_periodo("ÚLTIMA GRATIFICACIÓN", w_fecha_tope2, w_fecha_tope1)
            w_sexto_canti_mm = w_period_grati.get('meses', 0)
            w_sexto_canti_dd = w_period_grati.get('dias', 0)

            w_sexto_costo_mes = w_total_remu 
            w_sexto_costo_dia = w_total_remu/30
            w_sexto_impor_mes = (w_sexto_costo_mes/6) * w_sexto_canti_mm
            w_sexto_impor_dia = (w_sexto_costo_dia/6) * w_sexto_canti_dd
            w_sexto_total = (w_sexto_impor_mes + w_sexto_impor_dia) / 6 
            w_conce_noremuner = 0.00
            w_remun_compu_cts = w_total_remu + w_conce_noremuner + w_sexto_total

            # --------------------------------------------------
            #  CALCULA VACACIONES TRUNCAS
            # --------------------------------------------------
            w_period_vac = self.desglosa_periodo("VACACIONES TRUNCAS", w_fecha_ingr, w_fecha_cese)
            if (w_period_vac.get('anios', 0) > 0):
                w_trunco_vac = 0.00
            else:    
                w_trunco_vac = 0.00
                w_trunco_vac += (w_total_remu/12) * w_period_vac.get('meses', 0)           #--- Por el rango meses
                w_trunco_vac += ((w_total_remu/12)/30) * w_period_vac.get('dias', 0)      #--- Por el rango días

            # --------------------------------------------------
            #  CALCULA CTS TRUNCOS
            # --------------------------------------------------
            w_fecha_tope = self.determina_periodo_cts(w_fecha_ingr, w_fecha_cese)
            w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_cese)
            w_trunco_cts = 0.00
            w_trunco_cts += ((w_remun_compu_cts/12) * w_period_cts.get('meses', 0))                #--- Por el rango meses
            w_trunco_cts += (((w_remun_compu_cts/12)/30) * w_period_cts.get('dias', 0))           #--- Por el rango días

            # --------------------------------------------------
            #  CALCULA GRATIFICACIONES TRUNCAS
            # --------------------------------------------------
            w_inicio_ano = date(2025, 1, 1)
            w_ultimo_dia = self.ultimo_dia_del_mes(w_fecha_cese).day
            if (w_fecha_ingr >= w_inicio_ano):
                w_inicio_ano = w_fecha_ingr
            w_meses_habiles = w_fecha_cese.month    
            w_meses_habiles = w_meses_habiles if w_fecha_cese.month <= 6 else w_meses_habiles - 6 
            w_meses_habiles = w_meses_habiles if w_inicio_ano.day==1 else w_meses_habiles - 1
            w_meses_habiles = w_meses_habiles if not w_ultimo_dia in [30,31] else w_meses_habiles - 1
            w_trunco_gra = 0.00
            w_trunco_gra += ((w_total_remu/6) * w_meses_habiles)                 #--- Por el rango meses

            # --------------------------------------------------
            #  CALCULA BONIFICACIÓN DE GRATIF TRUNCAS
            # --------------------------------------------------
            w_trunco_bon = 0.00
            w_trunco_bon += w_trunco_gra * 0.09                             #--- Por el rango meses


        else:
            w_trunco_vac = 0.00
            w_trunco_cts = 0.00
            w_trunco_gra = 0.00
            w_trunco_bon = 0.00
            w_comentario = ""

        # --------------------------------------------------
        #  ACTUALIZA CAMPOS
        # --------------------------------------------------
        self.ensure_one()
        self.write({
                'x_studio_cese_vaca_trunca': w_trunco_vac,
                'x_studio_cese_cts_trunco': w_trunco_cts,
                'x_studio_cese_grati_trunca': w_trunco_gra,
                'x_studio_cese_bonif_grati_trunca': w_trunco_bon,
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

    def determina_periodo_cts(self, fecha_inicial, fecha_final):
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

    def determina_periodo_grati(self, fecha_inicial, fecha_final):
        ingr_fecha  = fecha_inicial
        cese_fecha  = fecha_final
        ajus_fecha_tope = cese_fecha
        w_cont = 0
        max_iterations = 1000  # Protección contra bucles infinitos
        _logger.info(f'==========================================')
        _logger.info(f'DETERMINA PERIODO GRATIFICACIÓN ')
        _logger.info(f'==========================================')
        _logger.info(f'Fech.Ini:  {ingr_fecha}')
        _logger.info(f'Fech.Fin:  {cese_fecha}')

        while w_cont < max_iterations:
            w_cont += 1
            ajus_fecha_tope = ajus_fecha_tope - timedelta(days=1)  # Usar timedelta para restar días
            ajus_anio = ajus_fecha_tope.year 
            top1_param = date(ajus_anio, 7, 1)
            top2_param = date(ajus_anio, 1, 1)

            _logger.info(f'Procesado:  {ajus_fecha_tope}')
            if (ajus_fecha_tope == fecha_inicial) or (ajus_fecha_tope == top1_param) or (ajus_fecha_tope == top2_param):
                break

        if (ingr_fecha >= ajus_fecha_tope):
            ajus_fecha_tope = ingr_fecha 

        _logger.info(f'Contador :  {w_cont}')
        _logger.info(f'Top1     :  {top1_param}')
        _logger.info(f'Top2     :  {top2_param}')
        _logger.info(f'Fech.Tope:  {ajus_fecha_tope}')

        return ajus_fecha_tope

    def desglosa_periodo_old1(self, cproceso, fecha_inicial, fecha_final):
        #
        # Activa y desactiva el RECÁLCULO
        #
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

        w_difer_anos = (w_ano_ffin-w_ano_fini)-1

        w_tramo_inic = int((30-w_dia_fini)+1)   ##--- el +1 ES EL AJUSTE a los 30 o 31 días del mes
        w_tramo_medi = 0
        if (w_difer_anos>0):
            w_tramo_medi = ((w_difer_anos*360)/30) + (w_mes_ffin+w_mes_fini-2)
        elif (w_ano_ffin==w_ano_fini):
            w_tramo_medi = (w_mes_ffin-w_mes_fini)-1
        else:
            w_tramo_medi = (w_mes_ffin+(12-w_mes_fini))-1

        w_tramo_fini = 30 if w_dia_ffin==31 else w_dia_ffin
        w_total_dias = w_tramo_inic + (w_tramo_medi*30) + w_tramo_fini

        w_total_anos = int(w_total_dias/360) if w_total_dias>=360 else 0
        w_total_mese = 0 if (w_total_dias-(w_total_anos*360))<30 else int((w_total_dias - (w_total_anos*360))/30)
        w_total_dias = w_total_dias - ((w_total_anos*360)+(w_total_mese*30))

        w_total_anio = (w_ano_ffin - w_ano_fini) - 1
        w_total_anio = 0 if w_total_anio<=0 else w_total_anio 

        _logger.info(f'==========================================')
        _logger.info(f'PROCESO:  {w_cproceso}')
        _logger.info(f'------------------------------------------')
        _logger.info(f'Periodo:- inicial = {fecha_inicial} ')
        _logger.info(f'        - Final   = {fecha_final} ')
        _logger.info(f'------------------------------------------')
        _logger.info(f'Tramos: - inicial = {w_tramo_inic} dias')
        _logger.info(f'        - medio   = {w_tramo_medi} meses')
        _logger.info(f'        - final   = {w_tramo_fini} dias')
        _logger.info(f'------------------------------------------')
        _logger.info(f'RESULTADO:  año = {w_total_anio} ')
        _logger.info(f'            mes = {w_total_mese} ')
        _logger.info(f'            dia = {w_total_dias} ')
        _logger.info(f'==========================================')

        return {
            'anios': w_total_anio,
            'meses': w_total_mese,
            'dias': w_total_dias
        }
        
    def desglosa_periodo(self, cproceso, fecha_inicial, fecha_final): 
        """ Calcula el período entre dos fechas en años, meses y días usando el calendario 
            comercial (360 días/año, 30 días/mes) """ 
        # Normalización del proceso 
        w_cproceso = cproceso.upper() 
        # Extracción de componentes de fecha 
        dia_ini = fecha_inicial.day 
        mes_ini = fecha_inicial.month 
        ano_ini = fecha_inicial.year 
        dia_fin = fecha_final.day 
        mes_fin = fecha_final.month 
        ano_fin = fecha_final.year 
        # Ajuste de día final para calendario comercial 
        # Si el día es 31, se considera como 30 
        if dia_fin == 31: 
            dia_fin = 30 
        if dia_ini == 31: 
            dia_ini = 30 
        # Cálculo de diferencias (inclusivo para días) 
        dif_anos = ano_fin - ano_ini 
        dif_meses = mes_fin - mes_ini 
        dif_dias = dia_fin - dia_ini + 1 
        # +1 para incluir ambos días 
        # Ajuste si los días son negativos 
        if dif_dias < 0: 
            dif_dias += 30 
            dif_meses -= 1 
        # Ajuste si los meses son negativos 
        if dif_meses < 0: 
            dif_meses += 12 
            dif_anos -= 1 
        # Asegurar que no haya valores negativos 
        w_total_anio = max(0, dif_anos) 
        w_total_mese = max(0, dif_meses) 
        w_total_dias = max(0, dif_dias)
        if (w_total_dias >= 30):
            w_total_dias = 0
            w_total_mese += 1

        if (w_total_mese == 12):
            w_total_mese = 0
            w_total_anio += 1

        # Logging para debug 
        _logger.info(f'==========================================') 
        _logger.info(f'PROCESO: {w_cproceso}') 
        _logger.info(f'Fecha inicial: {fecha_inicial}') 
        _logger.info(f'Fecha final: {fecha_final}') 
        _logger.info(f'RESULTADO: {w_total_anio} años, {w_total_mese} meses, {w_total_dias} días') 
        _logger.info(f'==========================================') 
        
        return { 
            'anios': w_total_anio, 
            'meses': w_total_mese, 
            'dias': w_total_dias 
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
    
    # ==========================================================
    # BOTÓN - ACTIVA LISTADO DE GRATIFICACIONES 
    # ==========================================================
    # def action_listado_gratificaciones(self):
    #     # Verificar si se usa un LOTE de Julio o Diciembre
    #     w_user = self.env.user.id 
    #     w_lote = self.browse(self._context.get('active_ids', []))
    #     w_pase = False 
    #     for w_boleta in w_lote:
    #         w_mes_lote = w_boleta.date_from.month
    #         w_pase = (True if w_mes_lote == 7 else False)
        
    #     if not w_pase:
    #         raise UserError(_('CUIDADO: Debe usar un LOTE de JULIO o DICIEMBRE.'))
        
    #     self.procesa_listado_gratificaciones()

    #     pass

        # # Notificación al usuario
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'title': _('Éxito'),
        #         'message': _('Listado de Gratificaciones generado correctamente.'),
        #         'sticky': False,
        #         'type': 'success',
        #     }
        # }
        
    # ==========================================================
    # BOTÓN - ACTIVA LISTADO DE GRATIFICACIONES 
    # ==========================================================
    def action_listado_gratificaciones(self):
        # Verificar si se usa un LOTE de Julio o Diciembre
        w_user = self.env.user.id 
        w_lote = self.browse(self._context.get('active_ids', []))
        w_pase = False 
        for w_boleta in w_lote:
            w_mes_lote = w_boleta.date_from.month
            w_ano_lote = w_boleta.date_from.year
            w_pase = (True if w_mes_lote in [6, 7, 12] else False)
        
        if not w_pase:
            raise UserError(_('CUIDADO: Debe usar un LOTE de JULIO o DICIEMBRE.'))
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        w_mes_lote = 7 if w_mes_lote == 6 else w_mes_lote   #--Reajusta x el mmomento
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
                    'title':    'NOMINA-CENS - Cálculo Listado Gratificaciones',
                    'subject':  'Calculo de GRATIFICACIONES a la fecha',
                    'author':   'ODOO-CENS',
                    'manager':  'Gestión Humana',
                    'company':  'CENS PERÚ',
                    'category': 'LOTE - EXCEL',
                    'keywords': 'nómina, lote, cts, intermitente',
                    'created':  datetime.now(),
                    'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})

            w_dato = 'GRATIFICACIONES 2025-' + self.mes_literal(w_mes_lote).upper()[:3]
            worksheet = workbook.add_worksheet(w_dato)
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
            cell_format_cesado.set_bg_color('#DAEEF3')  # Color verde claro para empleados cesados
            cell_format_cesado.set_align('vcenter')

            # También crear versiones con este formato para cada tipo de dato
            cell_format_cesado_cent = workbook.add_format()
            cell_format_cesado_cent.set_bg_color('#DAEEF3')
            cell_format_cesado_cent.set_align('center')
            cell_format_cesado_cent.set_align('vcenter')
            cell_format_cesado_cent.set_text_wrap()

            cell_format_cesado_left = workbook.add_format()
            cell_format_cesado_left.set_bg_color('#DAEEF3')
            cell_format_cesado_left.set_align('vcenter')

            cell_format_cesado_impo = workbook.add_format()
            cell_format_cesado_impo.set_bg_color('#DAEEF3')
            cell_format_cesado_impo.set_num_format('#,##0.00')
            cell_format_cesado_impo.set_align('vcenter')

            cell_format_cesado_imp3 = workbook.add_format()
            cell_format_cesado_imp3.set_font_color('#A6A6A6')
            cell_format_cesado_imp3.set_bg_color('#DAEEF3')
            cell_format_cesado_imp3.set_num_format('#,##0.00')
            cell_format_cesado_imp3.set_align('vcenter')


            cell_format_cesado_fech = workbook.add_format()
            cell_format_cesado_fech.set_bg_color('#DAEEF3')
            cell_format_cesado_fech.set_num_format('dd/mm/yyyy')
            cell_format_cesado_fech.set_align('center')
            cell_format_cesado_fech.set_align('vcenter')

            cell_format_cesado_nume = workbook.add_format()
            cell_format_cesado_nume.set_bg_color('#DAEEF3')
            cell_format_cesado_nume.set_num_format('#,##0')
            cell_format_cesado_nume.set_align('center')
            cell_format_cesado_nume.set_align('vcenter')

            # -------------------------------------------------------------------------------------
            # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
            # -------------------------------------------------------------------------------------
            worksheet.set_column(0, 0, 9)       #-- ID Empleado
            worksheet.set_column(1, 1, 38)      #-- Nombre del Empleado
            worksheet.set_column(2, 2, 13)      #-- DNI
            worksheet.set_column(3, 3, 18)      #-- TIPO CONTRATO
            worksheet.set_column(4, 4, 15)      #-- CENTRO DE COSTOS
            worksheet.set_column(5, 5, 23)      #-- UNIDAD DE NEGOCIO
            worksheet.set_column(6, 6, 8)       #-- MONEDA
            worksheet.set_column(7, 7, 9)      #-- MES-1                   
            worksheet.set_column(8, 8, 9)      #-- MES-2                      
            worksheet.set_column(9, 9, 9)      #-- MES-3                   
            worksheet.set_column(10, 10, 9)    #-- MES-4             
            worksheet.set_column(11, 11, 9)    #-- MES-5             
            worksheet.set_column(12, 12, 9)    #-- MES-6              
            worksheet.set_column(13, 13, 12)    #-- IMPORTE TOTAL HORAS
            worksheet.set_column(14, 14, 12)    #-- Mes - 01                        O
            worksheet.set_column(15, 15, 12)    #-- Mes - 02                        P
            worksheet.set_column(16, 16, 12)    #-- Mes - 03                        Q
            worksheet.set_column(17, 17, 12)    #-- Mes - 04                        R
            worksheet.set_column(18, 18, 12)    #-- Mes - 05                        S
            worksheet.set_column(19, 19, 12)    #-- Mes - 06                        T
            worksheet.set_column(20, 20, 12)    #-- IMPORTE TOTAL           U
            worksheet.set_column(21, 21, 12)    #-- REMUN COMP PROMED

            worksheet.set_column(22, 22, 12)    #-- 
            worksheet.set_column(23, 23, 12)    #--  
            worksheet.set_column(24, 24, 12)    #-- 
            worksheet.set_column(25, 25, 12)    #--
            worksheet.set_column(26, 26, 12)     #-- INASISTENCIAS

            worksheet.set_column(27, 27, 16)    #-- Fecha Ingreso
            worksheet.set_column(28, 28, 16)    #-- Fecha Inicio Periodo
            worksheet.set_column(29, 29, 16)    #-- Fecha Fin Periodo

            worksheet.set_column(30, 30, 10)    #-- T.Trabajo: Cantidad Meses
            worksheet.set_column(31, 31, 10)    #-- T.Trabajo: Cantidad Días

            worksheet.set_column(32, 32, 12)    #-- Gratificación
            worksheet.set_column(33, 33, 12)    #-- Bonific Gratificación
            worksheet.set_column(34, 34, 12)    #-- Total Gratific

            worksheet.set_column(35, 35, 5)    #-- Gratificación

            worksheet.set_column(36, 36, 30)    #-- Entidad Bancaria
            worksheet.set_column(37, 37, 25)    #-- Número de Cuenta
            worksheet.set_column(38, 38, 25)    #-- CCI
   
   
            # ------
            worksheet.set_row(7, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A2', 'src/user/cens_nomina_excel_01/static/description/logo-tiny_96.png')
            worksheet.insert_image('AH2', 'src/user/cens_nomina_excel_01/static/description/Logo-Odoo-tiny.png', 
                                         {'x_scale': 0.7, 'y_scale': 0.7})
            worksheet.write('B3', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B4', 'Gestión Humana - Nóminas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)

            w_dato = 'CÁLCULO SEMESTRAL - GRATIFICACIONES DE ' + self.mes_literal(w_mes_lote).upper() + " " + str(w_ano_lote)
            worksheet.write('H5', w_dato, cell_format_cabe)
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

            worksheet.merge_range('H7:N7', 'Merged Cells', merge_format)
            worksheet.write('H7', 'DIAS TRABAJADOS INTERMITENTES', cell_format_tuti)

            worksheet.merge_range('O7:U7', 'Merged Cells', merge_format)
            worksheet.write('O7', 'HH.EE./BONO/FERIADOS - REMUNERACIÓN VARIABLE', cell_format_tut2)

            worksheet.merge_range('V7:Z7', 'Merged Cells', merge_format)
            worksheet.write('V7', 'REMUNERACIONES', cell_format_tuti)

            worksheet.merge_range('AB7:AD7', 'Merged Cells', merge_format)
            worksheet.write('AB7', 'FECHAS CÁLCULO', cell_format_tut2)

            worksheet.merge_range('AE7:AF7', 'Merged Cells', merge_format)
            worksheet.write('AE7', 'TIEMPO TRABAJO', cell_format_tuti)

            worksheet.merge_range('AG7:AI7', 'Merged Cells', merge_format)
            worksheet.write('AG7', 'GRATIFICACIÓN', cell_format_tut2)

            worksheet.merge_range('AK7:AM7', 'Merged Cells', merge_format)
            worksheet.write('AK7', 'CUENTA BANCARIA - TRANSFERENCIA', cell_format_tuti)
            
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
            worksheet.write('A8', 'ORD', cell_format_titu)                      #-- 00
            worksheet.merge_range('B8:B9', 'Merged Cells', merge_format)
            worksheet.write('B8', 'NOMBRE DEL EMPLEADO', cell_format_titu)      #-- 01
            worksheet.merge_range('C8:C9', 'Merged Cells', merge_format)
            worksheet.write('C8', 'D.N.I.', cell_format_titu)                   #-- 02
            worksheet.merge_range('D8:D9', 'Merged Cells', merge_format)
            worksheet.write('D8', 'TIPO CONTRATO', cell_format_titu)            #-- 03
            worksheet.merge_range('E8:E9', 'Merged Cells', merge_format)
            worksheet.write('E8', 'CENTRO COSTOS', cell_format_titu)            #-- 04
            worksheet.merge_range('F8:F9', 'Merged Cells', merge_format)
            worksheet.write('F8', 'UNIDAD NEGOCIO', cell_format_titu)           #-- 05
            worksheet.merge_range('G8:G9', 'Merged Cells', merge_format)
            worksheet.write('G8', 'MONEDA', cell_format_titu)                   #-- 06
            
            w_semestre = 0 if w_mes_lote==7 else 6 

            for codigo in range(72, 78):  # H,I,J,K,L,M
                w_refcel = chr(codigo)+"8"
                w_ind    = codigo-71
                w_refmes = self.mes_literal(w_semestre + w_ind).upper()[:3] + "-" + str(w_ano_lote)  #-- DIAS TRABAJADOS INTERMITENTES
                worksheet.write(w_refcel, w_refmes, cell_format_tito)
            worksheet.write('N8', 'IMPORTE TOTAL DÍAS_TRAB', cell_format_tit2)      #-- 13

            for codigo in range(79, 85):  # O,P,Q,R,S,T
                w_refcel = chr(codigo)+"8"
                w_ind    = codigo-78
                w_refmes = self.mes_literal(w_semestre + w_ind).upper()[:3] + "-" + str(w_ano_lote)  #-- HORAS EXTRAS / BONO / FERIADOS
                worksheet.write(w_refcel, w_refmes, cell_format_tito)
            worksheet.write('U8', 'TOTAL REMU.VARIABLE', cell_format_tit2)            #-- 20

            worksheet.write('V8', 'REMU-VAR PROMEDIO', cell_format_tito)        #-- 21   
            worksheet.write('W8', 'REMUNERCIÓN FIJA', cell_format_tito)         #-- 22
            worksheet.write('X8', 'ASIGN. FAMILIAR', cell_format_tito)          #-- 23
            worksheet.write('Y8', 'TOTAL REMUNERACIÓN', cell_format_tito)       #-- 24  REMUNERACIONES
            worksheet.write('Z8', 'REMU-COMPU GRATIFIC', cell_format_tit2)      #-- 25
            worksheet.write('AA8', 'INASISTENCIAS', cell_format_titu)           #-- 26

            worksheet.write('AB8', 'ALTA T_REGISTRO', cell_format_tito)         #-- 27
            worksheet.write('AC8', 'INICIO PERIODO', cell_format_tito)          #-- 28
            worksheet.write('AD8', 'FINAL PERIODO', cell_format_tito)           #-- 29

            worksheet.write('AE8', 'MESES', cell_format_titu)                   #-- 30
            worksheet.write('AF8', 'DIAS', cell_format_titu)                    #-- 31

            worksheet.write('AG8', 'GRATIFICACIÓN', cell_format_tito)           #-- 32
            worksheet.write('AH8', 'BONIFIC EXTRAORD', cell_format_tito)        #-- 33
            worksheet.write('AI8', 'TOT.GRATIF A PAGAR', cell_format_tit2)      #-- 34

            worksheet.write('AK8', 'ENTIDAD-BANCARIA', cell_format_titu)        #-- 36
            worksheet.write('AL8', 'NÚMERO DE CUENTA', cell_format_tito)        #-- 37
            worksheet.write('AM8', 'C.C.I.', cell_format_titu)                  #-- 38


            #----------------------------------------------------------------
            worksheet.write('H9', 'dd', cell_format_tut4)                       #-- 07
            worksheet.write('I9', 'dd', cell_format_tut4)                       #-- 08
            worksheet.write('J9', 'dd', cell_format_tut4)                       #-- 09
            worksheet.write('K9', 'dd', cell_format_tut4)                       #-- 10
            worksheet.write('L9', 'dd', cell_format_tut4)                       #-- 11
            worksheet.write('M9', 'dd', cell_format_tut4)                       #-- 12
            worksheet.write('N9', 'S/.', cell_format_tut4)                      #-- 13

            worksheet.write('O9', 'S/.', cell_format_tut4)                      #-- 14
            worksheet.write('P9', 'S/.', cell_format_tut4)                      #-- 15
            worksheet.write('Q9', 'S/.', cell_format_tut4)                      #-- 16
            worksheet.write('R9', 'S/.', cell_format_tut4)                      #-- 17
            worksheet.write('S9', 'S/.', cell_format_tut4)                      #-- 18
            worksheet.write('T9', 'S/.', cell_format_tut4)                      #-- 19
            worksheet.write('U9', 'S/.', cell_format_tut4)                      #-- 20

            worksheet.write('V9', 'S/.', cell_format_tut4)                      #-- 21
            worksheet.write('W9', 'S/.', cell_format_tut4)                      #-- 22
            worksheet.write('X9', 'S/.', cell_format_tut4)                      #-- 23
            worksheet.write('Y9', 'S/.', cell_format_tut4)                      #-- 24
            worksheet.write('Z9', 'S/.', cell_format_tut4)                      #-- 25
            worksheet.write('AA9', 'S/.', cell_format_tut4)                     #-- 26     

            worksheet.write('AB9', 'dd/mm/aaa', cell_format_sub8)               #-- 27
            worksheet.write('AC9', 'dd/mm/aaa', cell_format_sub8)               #-- 28
            worksheet.write('AD9', 'dd/mm/aaa', cell_format_sub8)               #-- 29

            worksheet.write('AE9', 'mm', cell_format_tut4)                      #-- 30
            worksheet.write('AF9', 'dd', cell_format_tut4)                      #-- 31

            worksheet.write('AG9', 'S/.', cell_format_tut4)                     #-- 32
            worksheet.write('AH9', 'S/.', cell_format_tut4)                     #-- 33
            worksheet.write('AI9', 'S/.', cell_format_tut4)                     #-- 34

            worksheet.write('AK9', ' ', cell_format_sub8)                     #-- 36
            worksheet.write('AL9', ' ', cell_format_sub8)                     #-- 37
            worksheet.write('AM9', ' ', cell_format_sub8)                     #-- 38


            #-----
            # worksheet.autofilter(8, 60, 8, 65)  #--- Coloca FILTROS en RESUMEN 
            #-----
            worksheet.freeze_panes(9, 3)    #--- Inmoviliza Paneles

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
                w_codi_tipoplani = w_boleta.employee_id.x_studio_tipo_planilla
                current_format_cent = cell_format_cesado_cent if w_codi_tipoplani == "INTE" else cell_format_cent
                current_format_left = cell_format_cesado_left if w_codi_tipoplani == "INTE" else cell_format_left
                current_format_impo = cell_format_cesado_impo if w_codi_tipoplani == "INTE" else cell_format_impo
                current_format_fech = cell_format_cesado_fech if w_codi_tipoplani == "INTE" else cell_format_fech
                current_format_nume = cell_format_cesado_nume if w_codi_tipoplani == "INTE" else cell_format_nume
                current_format_imp2 = cell_format_cesado_impo if w_codi_tipoplani == "INTE" else cell_format_imp2
                current_format_imp3 = cell_format_cesado_imp3 if w_codi_tipoplani == "INTE" else cell_format_impo
       
                if w_boleta.x_studio_cesado:
                    continue
                    worksheet.write(w_fila, 0, 'CESADO', cell_format_rojo)
                else:
                    worksheet.write(w_fila, 0, w_fila-8, current_format_cent)

                w_dato = w_boleta.employee_id.name
                worksheet.write(w_fila, 1, w_dato, current_format_left)                 #-- Nombre Empleado
                worksheet.write(w_fila, 2, w_boleta.x_studio_dni, current_format_cent)  #-- DNI

                w_dato = self.tipo_planilla(w_codi_tipoplani)
                worksheet.write(w_fila, 3, w_dato, current_format_left)                 #-- Tipo Contrato

                w_codi_centcosto = int(w_boleta.employee_id.x_studio_centro_de_costos)
                w_dato = self.centro_costo(w_codi_centcosto)
                worksheet.write(w_fila, 4, w_dato, current_format_left)                 #-- Centro Costos
              
                w_dato = w_boleta.employee_id.x_studio_unidad_negocio
                worksheet.write(w_fila, 5, w_dato, current_format_left)                 #-- Unidad de Negocio
                
                w_dato = w_boleta.currency_id.name
                worksheet.write(w_fila, 6, w_dato, current_format_cent)                 #-- Moneda

                #---------------------------------------------------------------------------------------------
                # ESTRA TODAS LAS BOLETAS DEL EMPLEADO CENS EN CURSO
                # --------------------------------------------------
                # Buscar todas las boletas del empleado de una vez para posteriormente extraer los datos que
                # se requieren (w_Fech_Tope, x_studio_dias_vacaciones).
                #---------------------------------------------------------------------------------------------
                w_Fech_Tope = date(w_ano_lote, 7, 1) if w_mes_lote==7 else date(w_ano_lote+1, 1, 1)
                boletas_empleado = self.env['hr.payslip'].search([
                    ('employee_id', '=', w_boleta.employee_id.id),
                    ('date_from', '>=', date(w_ano_lote, w_semestre + 1, 1)),
                    ('date_from', '<', w_Fech_Tope),  
                    ('state', 'in', ['draft', 'verify', 'done', 'paid'])
                ])
                #---------------------------------------------------------------------------------------------
                # Crear diccionario mes → días computados
                dias_por_mes = {boleta.date_from.month: boleta.x_studio_dias_computados 
                                for boleta in boletas_empleado}
                vaca_por_mes = {boleta.date_from.month: boleta.x_studio_dias_vacaciones 
                                for boleta in boletas_empleado}
                w_acum_dias = 0
                for codigo in range(72, 78):
                    w_refcel = chr(codigo) + "8"
                    w_mes = (codigo - 71)
                    w_col = 6 + (codigo - 71)
                    if (w_codi_tipoplani == "INTE"):
                        w_refmes = dias_por_mes.get(w_mes, 0) + vaca_por_mes.get(w_mes, 0)
                    else:
                        w_refmes = 0
                    w_acum_dias += w_refmes
                    if (w_refmes > 0):
                        worksheet.write(w_fila, w_col, w_refmes, current_format_cent)
                    else: 
                        worksheet.write(w_fila, w_col, " ", current_format_cent)
                w_tota_dtrab = w_acum_dias *  (w_boleta.x_studio_salario_mensual/30)
                worksheet.write(w_fila, 13, w_tota_dtrab, current_format_imp2)                #-- Total Importe Días Traba.

                #---------------------------------------------------------------------------------------------
                # Crear diccionario mes → Remuneración Variable
                hext_por_mes = {boleta.date_from.month: boleta.x_studio_en_horas_extras 
                                for boleta in boletas_empleado}
                bono_por_mes = {boleta.date_from.month: boleta.x_studio_en_bonificacion_cumplimiento 
                                for boleta in boletas_empleado}
                feri_por_mes = {boleta.date_from.month: boleta.x_studio_en_feriados 
                                for boleta in boletas_empleado}
                w_acum_rvari = 0    #--Remuneración Variable
                w_ok = 0
                for codigo in range(79, 85): 
                    w_refcel = chr(codigo)+"8"
                    w_mes    = codigo-78
                    w_col = 13 + (codigo - 78)
                    w_refmes = hext_por_mes.get(w_mes, 0) + bono_por_mes.get(w_mes, 0) + feri_por_mes.get(w_mes, 0)
                    w_acum_rvari += w_refmes
                    w_ok += (1 if w_refmes > 0.00 else 0)
                    if (w_refmes > 0):
                        worksheet.write(w_fila, w_col, w_refmes, current_format_impo)
                    else: 
                        worksheet.write(w_fila, w_col, " ", current_format_cent)
                w_acum_rvari = (w_acum_rvari if w_ok >= 3 else 0.00) 
                worksheet.write(w_fila, 20, w_acum_rvari, current_format_imp2)          #-- Total Remuneración Variable
                #---------------------------------------------------------------------------------------------
                w_prom_rvari = w_acum_rvari/6 if w_acum_rvari>0 else 0.00
                worksheet.write(w_fila, 21, w_prom_rvari, current_format_impo)          #-- Promedio Remuneración Variable

                w_dato = w_boleta.x_studio_salario_mensual
                worksheet.write(w_fila, 22, w_dato, current_format_imp3)                #-- Sueldo Básico

                w_dato = w_boleta.x_studio_en_asignacion_familiar
                worksheet.write(w_fila, 23, w_dato, current_format_imp3)                #-- Asignación Familiar

                w_tota_remu = w_boleta.x_studio_salario_mensual + w_boleta.x_studio_en_asignacion_familiar
                worksheet.write(w_fila, 24, w_tota_remu, current_format_imp3)

                if (w_codi_tipoplani == "INTE"):
                    w_remu_comp = w_tota_dtrab/6 if w_tota_dtrab>0 else 0.00
                else:
                    w_remu_comp = w_tota_remu + w_prom_rvari
                worksheet.write(w_fila, 25, w_remu_comp, current_format_imp2)           #-- Remuneración Computable

                w_dato = w_boleta.x_studio_en_inasistencias
                worksheet.write(w_fila, 26, w_dato, current_format_impo)                #-- Importe x Inasistencias 

                w_fech_ingr = w_boleta.employee_id.x_studio_contrato_actual_inicio           #-- Fecha Inicio Contrato
                worksheet.write(w_fila, 27, w_fech_ingr, current_format_fech)

                if (w_mes_lote == 7):
                    w_peri_fini = date(w_ano_lote, 1, 1)
                    w_peri_ffin = date(w_ano_lote, 6, 30) 
                else:
                    w_peri_fini = date(w_ano_lote, 7, 1)
                    w_peri_ffin = date(w_ano_lote, 12, 31)

                if (w_fech_ingr > w_peri_fini):
                    w_peri_fini = w_fech_ingr

                worksheet.write(w_fila, 28, w_peri_fini, current_format_fech)           #-- Fecha Inicio Periodo
                worksheet.write(w_fila, 29, w_peri_ffin, current_format_fech)           #-- Fecha Final Perioro

                w_time_work = self.desglosa_periodo("TIEMPO DE TRABAJO", w_peri_fini, w_peri_ffin)
                w_peri_canti_mm = w_time_work.get('meses', 0)
                w_peri_canti_dd = w_time_work.get('dias', 0)
                worksheet.write(w_fila, 30, w_peri_canti_mm, current_format_nume)       #-- Periodo en Meses
                worksheet.write(w_fila, 31, w_peri_canti_dd, current_format_nume)       #-- Perioro en días

                if (w_codi_tipoplani == "INTE"):
                    w_grati_impo = w_remu_comp
                else:
                    w_grati_impo = ((w_remu_comp/6 if w_remu_comp>0 else 0.00) * w_peri_canti_mm) + (((w_remu_comp/6)/30 if w_remu_comp>0 else 0.00) * w_peri_canti_dd) 
                w_grati_boni = w_grati_impo * 0.09
                w_grati_tota = w_grati_impo + w_grati_boni
                worksheet.write(w_fila, 32, w_grati_impo, current_format_impo)       #-- Gratificación: Importe
                worksheet.write(w_fila, 33, w_grati_boni, current_format_impo)       #-- Gratificación: Bonific
                worksheet.write(w_fila, 34, w_grati_tota, current_format_imp2)       #-- Gratificación: Total

                # -----------------------------------------
                # DETALLE CUENTA BANCARIA
                # -----------------------------------------
                w_dato = w_boleta.employee_id.x_studio_nombre_banco
                worksheet.write(w_fila, 36, w_dato, current_format_left)

                w_dato = w_boleta.employee_id.x_studio_numero_cuenta
                worksheet.write(w_fila, 37, w_dato, current_format_left)

                w_dato = w_boleta.employee_id.x_studio_cci
                worksheet.write(w_fila, 38, w_dato, current_format_left)


                w_fila += 1

            # worksheet.write(5, 20, "TOTAL GENERAL:", cell_format_left) 
            # worksheet.write(5, 21, w_acum_tota_1, cell_format_impo)

            worksheet.activate()
            workbook.close()
            # ------------------------------------------------------------------

            # Crear adjunto
            xlsx_data = output.getvalue()
            attachment = self.env['ir.attachment'].create({
                'name': 'CENS-GRATI-2025-A.xlsx',
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

    @staticmethod
    def mes_literal(nmes):
        meses = {
            1: "Enero",
            2: "Febrero", 
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Setiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre"
        }
        return meses.get(nmes, "ERROR")
    
    @staticmethod
    def centro_costo(ntipo):
        costo = {
            1:	"Costo Directo",	
            2:	"Costo Indirecto",	
            3:	"Gasto de Venta",	
            4:	"Gasto General"
        }
        return costo.get(ntipo, "ERROR")
    
    @staticmethod
    def tipo_planilla(codigo):
        tipos = {
            "GENE": "Régimen General",
            "INTE": "Régimen Intermitente", 
            "LOCA": "Locación de Servicios",
            "PRAC": "Practicantes"
        }
        return tipos.get(codigo, "ERROR")
    	

    @staticmethod
    def formato_moneda(cantidad, simbolo="S/."):
        return f"{simbolo}{cantidad:,.2f}"
    


        
                # # ----------------------------
                # if not w_boleta.x_studio_cese_fecha_ingreso:
                #     w_boleta.write({'x_studio_cese_fecha_ingreso': w_boleta.x_studio_fecha_ingreso_laboral})

                # w_fecha_ingr = w_boleta.x_studio_cese_fecha_ingreso if w_boleta.x_studio_cese_fecha_ingreso else w_boleta.employee_id.first_contract_date 
                # worksheet.write(w_fila, 7, w_fecha_ingr, current_format_fech)
                # # ----------------------------

                # if w_boleta.x_studio_cese_fecha:
                #     w_fecha_fiin = w_boleta.x_studio_cese_fecha if w_boleta.x_studio_cesado else date(2025, 4, 30)
                # else:
                #     w_fecha_fiin = date(2025, 4, 30)

                # if w_boleta.x_studio_cesado:
                #     worksheet.write(w_fila, 8, w_fecha_fiin, current_format_fech)

                # # -------------------------------------
                # # --   CALCULO DE DATOS GENERALES    --
                # # -------------------------------------
                # worksheet.write(w_fila, 9, w_boleta.x_studio_salario_mensual, current_format_impo)
                # worksheet.write(w_fila, 10, w_boleta.x_studio_en_asignacion_familiar, current_format_impo)

                # w_impo_sext = 0.00
                # worksheet.write(w_fila, 11, " " if w_impo_sext==0.00 else w_impo_sext, current_format_impo)
                
                # w_impo_remu = w_boleta.x_studio_salario_mensual + w_boleta.x_studio_en_asignacion_familiar + w_impo_sext
                # worksheet.write(w_fila, 12, w_impo_remu, current_format_imp2)
                
                # w_impo_cano = w_impo_remu if w_impo_remu > 0 else 0.00
                # w_impo_cmes = w_impo_remu/12 if w_impo_remu > 0 else 0.00
                # w_impo_cdia = (w_impo_remu/12)/30 if w_impo_remu > 0 else 0.00
                # worksheet.write(w_fila, 13, w_impo_cano, current_format_impo)
                # worksheet.write(w_fila, 14, w_impo_cmes, current_format_impo)
                # worksheet.write(w_fila, 15, w_impo_cdia, current_format_impo)

                # # --------------------------------------------------
                # #  CALCULA CTS TRUNCOS
                # # --------------------------------------------------
                # w_fecha_tope = self.determina_periodo_cts(w_fecha_ingr, w_fecha_fiin)
                # w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_fiin)
                # w_desgl_anio = w_period_cts.get('anios', 0)
                # w_desgl_mess = w_period_cts.get('meses', 0)
                # w_desgl_dias = w_period_cts.get('dias', 0)
                # w_trunco_cts = 0.00
                # w_trunco_cts += ((w_impo_remu/12) * w_period_cts.get('meses', 0))                #--- Por el rango meses
                # w_trunco_cts += (((w_impo_remu/12)/30) * w_period_cts.get('dias', 0))           #--- Por el rango días

                # worksheet.write(w_fila, 16, w_desgl_anio, current_format_nume)
                # worksheet.write(w_fila, 17, w_desgl_mess, current_format_nume)
                # worksheet.write(w_fila, 18, w_desgl_dias, current_format_nume)

                # worksheet.write(w_fila, 19, w_fecha_tope, current_format_fech)
                # worksheet.write(w_fila, 20, w_fecha_fiin, current_format_fech)
                # worksheet.write(w_fila, 21, w_trunco_cts, current_format_imp2)
                # w_acum_tota_1 += w_trunco_cts

                # if w_boleta.x_studio_cesado:
                #     worksheet.write(w_fila, 22, w_boleta.x_studio_cese_comentarios + " " + w_boleta.x_studio_cese_observaciones, current_format_left)
                #     # -----------------------------------------
                #     # BOLETA PAGO - CONCEPTOS DE LIQUIDACIÓN  - ASIGNAR CAMPOS REALES
                #     # -----------------------------------------
                #     worksheet.write(w_fila, 24, w_boleta.x_studio_cese_vaca_trunca, current_format_impo)
                #     worksheet.write(w_fila, 25, w_boleta.x_studio_cese_cts_trunco, current_format_impo)
                #     worksheet.write(w_fila, 26, w_boleta.x_studio_cese_grati_trunca, current_format_impo)
                #     worksheet.write(w_fila, 27, w_boleta.x_studio_cese_bonif_grati_trunca, current_format_impo)
                # else:
                #     worksheet.write(w_fila, 22, " ", current_format_left)
