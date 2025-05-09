from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError
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

        """
        w_fecha = datetime.now().date()
        if self.x_studio_cesado:
            w_fecha_ingr = self.x_studio_cese_fecha_ingreso
            w_fecha_cese = self.x_studio_cese_fecha
            w_total_remu = self.x_studio_salario_mensual + self.x_studio_en_asignacion_familiar 
            w_comentario = "Cálculo realizado x ODOO-CENS."

            # --------------------------------------------------
            #  CALCULA RANGOS DE TIEMPO (días, meses, años)
            # --------------------------------------------------
            w_dia_ing = w_fecha_ingr.day
            w_mes_ing = w_fecha_ingr.month
            w_mes_ces = w_fecha_cese.month
            w_ano_ing = w_fecha_ingr.year

            # ============================================================================================================

            w_cant_dia_ini = (30 - w_dia_ing) + 1
            w_cant_dia_fin = w_fecha_cese.day

            w_mess_partmes = ((12 - w_mes_ing) + (w_mes_ces-1))         #--- (12-MES(D6)) + (MES(D7)-1)
            w_dias_partmes = (w_mess_partmes * 30) + w_cant_dia_fin     #--- (E7*30) + DIA(D7)
            w_cant_dia_fin = (w_dias_partmes % 30)                      #--- RESIDUO(F7;30) 

            _logger.info(f'Conteo: - Días inicial = {w_cant_dia_ini} ')
            _logger.info(f'        - Dias medio   = {w_dias_partmes} ')
            _logger.info(f'        - Días final   = {w_cant_dia_fin} ')
            _logger.info(f'------------------------------------------')
            _logger.info(f'Cantidad meses = {w_mess_partmes} ')
            _logger.info(f'Cantidad días  = {w_dias_partmes} ')

            w_tota_mes = int(w_dias_partmes / 30)            #--- Total rango meses
            w_tota_dia = (w_dias_partmes % 30) + w_cant_dia_ini                 #--- Total rango días
            w_tota_ddd = w_cant_dia_ini + w_dias_partmes + w_cant_dia_fin       #--- Total tiempo en días
            w_tota_ano = int(w_tota_ddd/360) if w_tota_ddd >= 360 else 0        #--- Total rango años

            _logger.info(f'------------------------------------------')
            _logger.info(f'TOTALIZADO: año = {w_tota_ano} ')
            _logger.info(f'            mes = {w_tota_mes} ')
            _logger.info(f'            dia = {w_tota_dia} ')
            _logger.info(f'            ddd = {w_tota_ddd} ')

            
            # ============================================================================================================

            # --------------------------------------------------
            #  CALCULA VACACIONES TRUNCAS
            # --------------------------------------------------
            w_trunco_vac = 0.00
            w_trunco_vac += (w_total_remu/12) * w_tota_mes                  #--- Por el rango meses
            w_trunco_vac += ((w_total_remu/12)/30)*w_tota_dia               #--- Por el rango días

            # --------------------------------------------------
            #  CALCULA CTS TRUNCOS
            # --------------------------------------------------
            w_trunco_cts = 0.00
            w_trunco_cts += ((w_total_remu/12) * w_tota_mes)                #--- Por el rango meses
            w_trunco_cts += (((w_total_remu/12)/30) * w_tota_dia)           #--- Por el rango días
            if (w_trunco_vac > 0.00):
                w_trunco_cts += w_trunco_vac/6 if w_tota_mes>6 else 0.00    #--- Por el SEXTO de

            # --------------------------------------------------
            #  CALCULA GRATIFICACIONES TRUNCAS
            # --------------------------------------------------
            w_trunco_gra = 0.00
            w_trunco_gra += ((w_total_remu/6) * w_tota_mes)                 #--- Por el rango meses

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
        for rec in self:
            rec.write({
                'x_studio_cese_vaca_trunca': w_trunco_vac,
                'x_studio_cese_cts_trunco': w_trunco_cts,
                'x_studio_cese_grati_trunca': w_trunco_gra,
                'x_studio_cese_bonif_grati_trunca': w_trunco_bon,
                'x_studio_cese_comentarios': w_comentario
            })  
            rec.recompute()

        pass

    def action_recalcula_en_datos(self):
        #
        # Activa y desactiva el RECÁLCULO
        #
        #for rec in self:
        #    rec.write({'x_studio_en_recalcular': not rec.x_studio_en_recalcular})      #----- Para funciona en creación individual
        #    rec.recompute()
        w_fecha = datetime.now().date()
