from odoo import _, api, fields, models
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import time
import base64
import xlrd
import xlsxwriter
from io import BytesIO
import calendar
import logging
_logger = logging.getLogger(__name__)

class HrPayslipLiquidacion(models.Model):  
    _name = 'hr.payslip.liquidacion'
    _description = 'Liquidación de Beneficios Sociales'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ---------------------------------------
    # AGREGA CAMPOS AL MODELO: Liquidaciones
    # ---------------------------------------
    name = fields.Char(string="Código Liquidación", default="COD-", store=True)
    user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, index=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', 
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1).id,
                                  required=True)
    # contract_id = fields.Many2one('hr.contract', string='Contrato Activo', related='employee_id.contract_id', store=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato Activo', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Boletas Pago')
    setup_afp_id = fields.Many2one('x_hr_payslip.setup_afp', string='Configuración AFP/ONP')
    state = fields.Selection([("draft", "Borrador"), ("posted", "Confirmado"), ("annul", "Anulado")], default="draft")
    note = fields.Text(string='Observaciones', store=True, help='Observaciones adicionales')
    note_automatic = fields.Text(string='Comentarios', compute='_calcula_mensaje_nota_automatic', default='', store=True, help='Alertas al Usuario')
    note_calculos  = fields.Text(string='Comentarios', default='', store=True, help='Observaciones internas sobre el cálculo')
    generado = fields.Boolean(string='¿Generado?', default=False, store=True)

    x_cens_cargo_emple = fields.Char(string='Cargo', related='employee_id.job_title')
    x_cens_foto_empleado = fields.Binary(string="foto", related='employee_id.avatar_128')
    x_cens_fech_registro = fields.Date(string='Fecha Registro', default=fields.Date.context_today)

    contract_fingr  = fields.Date(string='Fecha Ingreso', compute='_compute_contract_info', store=True)
    contract_fcese  = fields.Date(string='Fecha de Cese', store=True)
    contract_movili = fields.Monetary(string="Movilidad", store=True)
    contract_alimen = fields.Monetary(string="Alimentación", store=True)
    contract_bonifi = fields.Monetary(string="Bonif.Educ.", store=True)
    contract_utilid = fields.Monetary(string="Utilidades", store=True)
    contract_wage = fields.Monetary(string='Sueldo Básico (Contrato)', currency_field='currency_id', store=True)

    contract_cesado = fields.Boolean(string='¿Cesado?', related='contract_id.x_empleado_cesado', store=True)
    contract_fecese = fields.Date(string='Fecha Cese', related='contract_id.x_studio_fecha_de_cese', store=True)
    contract_motivo = fields.Many2one(string='Motivo Cese', related='contract_id.x_studio_motivo_de_salida', store=True)
    contract_observ = fields.Char(string='Observaciones', related='contract_id.x_studio_observacion_cese', store=True)

    x_cens_cesado = fields.Boolean(string="¿Cesado?", related='payslip_id.x_studio_cesado')
    x_cens_periodo_ini = fields.Date(string='Período Inicio', help='Fecha de inicio del período de liquidación')
    x_cens_periodo_fin = fields.Date(string='Período Fin', help='Fecha de fin del período de liquidación')
    x_cens_periodo_aa  = fields.Integer(string='Años', store=True, help='Años de servicio del empleado')    
    x_cens_periodo_mm  = fields.Integer(string='Meses', store=True, help='Meses de servicio del empleado')
    x_cens_periodo_dd  = fields.Integer(string='Días', store=True, help='Días de servicio del empleado')
    x_cens_ctotal_timeserv = fields.Char(string='Tiempo Total Servicio', default='00 años, 00 meses, 00 días', store=True, help='Tiempo total de servicio en años')    
    x_cens_ctotal_tnocomp  = fields.Char(string='Tiempo No Computable', default='00 años, 00 meses, 00 días', store=True, help='Tiempo no computable para beneficios')
    x_cens_ctotal_tliqui   = fields.Char(string='Tiempo Liquidación', default='00 años, 00 meses, 00 días', store=True, help='Tiempo total para liquidación')
    x_cens_remu_base = fields.Monetary(string='Remuneración Base', currency_field='currency_id', help='Remuneración base del empleado')
    x_cens_asig_fami = fields.Monetary(string='Asignación Familiar', currency_field='currency_id', help='Asignación familiar del empleado')
    x_cens_grat_16to = fields.Monetary(string='Gratificación 1/6', store=True, currency_field='currency_id', help='Gratificación extraordinaria (1/6 de la remuneración)')
    x_cens_none_remu = fields.Monetary(string='Conceptos No Remunerativos', store=True, currency_field='currency_id', help='Conceptos que no forman parte de la remuneración')
    x_cens_remu_comp = fields.Monetary(compute='_calcula_total_remu_paracts', string='Remuneración Computable', store=True, currency_field='currency_id', help='Remuneración total computable para beneficios')
    
    x_cens_moneda    = fields.Char(string='Moneda', default='(PEN) S/.', store=True)
    x_cens_ccts_peri = fields.Char(string='Periodo', default='', store=True, help='Periodo de tiempo para liquidación CTS')
    x_cens_ccts_dmes = fields.Char(string='Detalle cálulo x meses', default='', store=True, help='Detalle del cálculo x meses')
    x_cens_ccts_imes = fields.Monetary(string='Importe cálulo x meses', store=True, currency_field='currency_id', help='Importe del cálculo x meses.')
    x_cens_ccts_ddia = fields.Char(string='Detalle cálulo x días', default='', store=True, help='Detalle del cálculo x días')
    x_cens_ccts_idia = fields.Monetary(string='Importe cálulo x días', store=True, currency_field='currency_id', help='Importe del cálculo x días.')
    x_cens_ccts_itot = fields.Monetary(compute='_calcula_total_ccts', string='Importe total CTS', store=True, currency_field='currency_id', help='Importe total CTS.')
    
    x_cens_vaca_peri = fields.Char(string='Periodo', default='', store=True, help='Periodo de tiempo para liquidación VACA')
    x_cens_vaca_dano = fields.Char(string='Detalle cálulo x años', default='', store=True, help='Detalle del cálculo x años')
    x_cens_vaca_iano = fields.Monetary(string='Importe cálulo x años', store=True, currency_field='currency_id', help='Importe del cálculo x años.')
    x_cens_vaca_dmes = fields.Char(string='Detalle cálulo x meses', default='', store=True, help='Detalle del cálculo x meses')
    x_cens_vaca_imes = fields.Monetary(string='Importe cálulo x meses', store=True, currency_field='currency_id', help='Importe del cálculo x meses.')
    x_cens_vaca_ddia = fields.Char(string='Detalle cálulo x días', default='', store=True, help='Detalle del cálculo x días')
    x_cens_vaca_idia = fields.Monetary(string='Importe cálulo x días', store=True, currency_field='currency_id', help='Importe del cálculo x días.')
    x_cens_vaca_dgoz = fields.Char(string='- Vacaciones Gozadas', default='', store=True, help='Vacacioes Gozadas')
    x_cens_vaca_igoz = fields.Monetary(string='Importe Vacaciones Gozadas', store=True, currency_field='currency_id', help='Importe Vacaciones Gozadas.')
    x_cens_vaca_dafp = fields.Char(string='- Descuento AFP/ONP', default='', store=True, help='Descuento AFP/ONP')
    x_cens_vaca_iafp = fields.Monetary(string='Importe AFP/ONP', store=True, currency_field='currency_id', help='Importe AFP/ONP.')
    x_cens_vaca_itot = fields.Monetary(compute='_calcula_total_vaca', string='Importe total VACA', store=True, currency_field='currency_id', help='Importe total VACA.')

    x_cens_grat_peri = fields.Char(string='Periodo', default='', store=True, help='Periodo de tiempo para liquidación GRATI')
    x_cens_grat_dmes = fields.Char(string='Detalle cálulo x meses', default='', store=True, help='Detalle del cálculo x meses')
    x_cens_grat_imes = fields.Monetary(string='Importe cálulo x meses', store=True, currency_field='currency_id', help='Importe del cálculo x meses.')
    x_cens_grat_dbon = fields.Char(string='Detalle Bonific.Extraordinaria', default='', store=True, help='Detalle Bonific.Extraordinaria.')
    x_cens_grat_ibon = fields.Monetary(string='Importe Bonific.Extraordinaria', store=True, currency_field='currency_id', help='Importe Bonific.Extraordinaria.')
    x_cens_grat_itot = fields.Monetary(compute='_calcula_total_grati', string='Importe total GRATI', store=True, currency_field='currency_id', help='Importe total VACA.')
    
    x_cens_afp_compa = fields.Many2one(string="Compañía AFP", related='employee_id.x_compania_afp')
    x_cens_afp_tcomi = fields.Selection(string="Tipo Comisión AFP", related='payslip_id.x_studio_en_tipo_comision')
    x_cens_afp_oblig = fields.Float(compute='_calcula_afp_aporte_obligatorio', default=0.00, store=True)    ## QUIQUE
    x_cens_afp_prima = fields.Float(compute='_calcula_afp_prima_seguro', default=0.00, store=True)
    x_cens_afp_mixta = fields.Float(compute='_calcula_afp_comision_mixta', default=0.00, store=True)
    x_cens_afp_flujo = fields.Float(compute='_calcula_afp_comision_flujo', default=0.00, store=True)
    x_cens_liqu_iafp = fields.Float(string='Descuento AFP', default=0.00, store=True, help='Descuento AFP.')
    x_cens_liqu_tota = fields.Float(compute='_calcula_liquidacion_total', default=0.00, store=True)
    x_cens_apor_mbas = fields.Float(compute='_calcula_Monto_Base', default=0.00, store=True)
    x_cens_apor_essa = fields.Float(compute='_calcula_aporte_essalud', default=0.00, store=True)
    x_cens_desc_otro = fields.Float(string='Otros descuentos', default=0.00, store=True, help='Al registra el importe de otros descuentos coloque una breve descripción abajo.')
    x_cens_desc_5cat = fields.Float(string='Descuento 5ta.Cat.', default=0.00, store=True, help='Impuesto a la Renta 5ta.Cat.')
    
    x_cens_tipo_calc = fields.Char(string='Tipo Cálculo', default='1', store=True)
    x_cens_en_litefe = fields.Char(string="Literal Fecha", related='payslip_id.x_studio_literal_fecha_titulo')
    x_cens_en_nbolet = fields.Char(string="Núm.BoletaPago", related='payslip_id.number')
    x_cens_en_basico = fields.Float(string="Sueldo Básico", related='payslip_id.x_studio_en_basico')
    x_cens_en_asifam = fields.Float(string="Asig.Familiar", related='payslip_id.x_studio_en_asignacion_familiar')
    x_cens_en_bonifi = fields.Float(string="Bonificación", related='payslip_id.x_studio_en_bonificacion_cumplimiento')
    x_cens_en_feriad = fields.Float(string="Bonificación", related='payslip_id.x_studio_en_feriados')
    x_cens_lite_fech = fields.Char(string='Literal Fecha', compute='_calcula_literal_fecha', default='Lima,', store=True)
    x_cens_bole_iden = fields.Char(string='Lote Boleta', compute='_calcula_boleta_identifi', default='', store=True)
    

    @api.onchange('employee_id')
    def _onchange_empleado_info(self):
        for record in self:
            #
            # Carga datos vinculados a la FICHA EMPLOYEE
            #
            if self.employee_id.x_studio_asignacin_familiar_1:
                w_tasa_AFami = self.employee_id.x_studio_asignacin_familiar_1 / 100 if self.employee_id.x_studio_asignacin_familiar_1 > 0 else 0
                w_asig_famil = self.contract_wage * w_tasa_AFami
                record['x_cens_asig_fami'] = w_asig_famil
            else:
                record['x_cens_asig_fami'] = 0.00
            #
            # Busca y posiciona SETUP AFP
            #
            if (record.x_cens_afp_compa):
                resultado_busqueda = self.env['x_hr_payslip.setup_afp'].search([('x_compania_afp', '=', record.x_cens_afp_compa.id)], order='id desc', limit=1)
            else:
                resultado_busqueda = False
            w_codi_parametro = 0
            if resultado_busqueda:
                for line in resultado_busqueda:
                    w_codi_parametro = line.id
            record['setup_afp_id'] = w_codi_parametro

            #
            # Busca y posiciona ULTIMA BOLETA
            # 
            if (record.x_cens_afp_compa):
                resultado_busqueda = self.env['hr.payslip'].search([('employee_id.id','=',record.employee_id.id)], order='id desc', limit=1)
            else:
                resultado_busqueda = False
            w_codi_parametro = 0
            if resultado_busqueda:
                for line in resultado_busqueda:
                    w_codi_parametro = line.id
            record['payslip_id'] = w_codi_parametro


    @api.depends('contract_id')
    def _compute_contract_info(self):
        for record in self:
            # Buscar el contrato activo del empleado
            # contract_id
            contract = self.env['hr.contract'].search([
                ('id', '=', record.contract_id.id)
            ], limit=1)
            # ('state', '=', 'open')  # Solo contratos activos
            # Asignar valores desde el contrato
            record.contract_fingr  = contract.x_studio_fecha_de_ingreso if contract else False
            record.contract_fcese  = contract.x_studio_fecha_de_cese if contract else False
            record.contract_movili = contract.x_studio_movilidad_mensual if contract else 0.0
            record.contract_alimen = contract.x_studio_alimentacion if contract else 0.0
            record.contract_bonifi = contract.x_studio_bonificacion_x_educacion if contract else 0.0
            record.contract_utilid = contract.x_studio_utilidades_voluntarias if contract else 0.0
            record.contract_wage   = contract.wage if contract else 0.0
            record.x_cens_cesado   = contract.x_empleado_cesado if contract else False
            #
            # Gemera Código Correlativo n el NAME.
            if (contract and record.contract_fcese):
                w_text_ano = str(record.contract_fcese.year) 
                w_text_mes = self.mes_literal(record.contract_fcese.month).upper()[:3]
                w_text_num = str(record.id or 0).zfill(6)
                record.name = "COD-" + w_text_ano + "-" + w_text_mes + "-" + w_text_num
            else:
                record.name = "COD-0000-XXX" 

    # @api.model
    # def create(self, vals):
    #     # Lógica para establecer el último registro
    #     if 'cens_renta_quinta_id' in vals:
    #         last_record = self.env['hr.payslip.renta_quinta'].search([
    #             ('employee_id', '=', vals.get('employee_id')),
    #             ('cens_anio_ejercicio', '=', self.cens_nano_ejercicio),
    #         ], limit=1, order='id desc')
    #         if last_record:
    #             vals['cens_renta_quinta_id'] = last_record.id
    #     return super(HrPayslip, self).create(vals)
    
    # @api.onchange('employee_id', 'cens_nano_ejercicio')
    # def _onchange_employee_nano_ejercicio(self):
    #     if self.employee_id and self.cens_nano_ejercicio:
    #         last_record = self.env['hr.payslip.renta_quinta'].search([
    #             ('employee_id', '=', self.employee_id.id),
    #             ('cens_anio_ejercicio', '=', self.cens_nano_ejercicio),
    #         ], limit=1, order='id desc')
    #         if last_record:
    #             self.cens_renta_quinta_id = last_record.id
    #         else:
    #             self.cens_renta_quinta_id = False  # Limpiar el campo si no hay registro activo


    
    @api.depends('x_cens_remu_base', 'x_cens_asig_fami', 'x_cens_grat_16to', 'x_cens_none_remu')
    def _calcula_total_remu_paracts(self):
        # ----------------------- CALCULA TOTAL REMUNERACIÓN PARA CTS --------------------------
        for record in self:
            w_dato = 0.00 
            w_dato += record.x_cens_remu_base
            w_dato += record.x_cens_asig_fami 
            w_dato += record.x_cens_grat_16to 
            w_dato += record.x_cens_none_remu
            record['x_cens_remu_comp'] = w_dato

    @api.depends('x_cens_ccts_imes', 'x_cens_ccts_idia')
    def _calcula_total_ccts(self):
        # ----------------------- CALCULA TOTAL CTS --------------------------
        for record in self:
            w_dato = 0.00 
            w_dato += record.x_cens_ccts_imes
            w_dato += record.x_cens_ccts_idia 
            record['x_cens_ccts_itot'] = w_dato
  
    api.depends('x_cens_vaca_iano', 'x_cens_vaca_imes', 'x_cens_vaca_idia', 'x_cens_vaca_igoz')
    def _calcula_total_vaca(self):
        # ----------------------- CALCULA TOTAL VACA --------------------------
        for record in self:
            w_dato = 0.00 
            w_dato += record.x_cens_vaca_iano
            w_dato += record.x_cens_vaca_imes
            w_dato += record.x_cens_vaca_idia
            w_dato -= record.x_cens_vaca_igoz 
            record['x_cens_vaca_itot'] = w_dato

    api.depends('x_cens_grat_imes', 'x_cens_grat_ibon')
    def _calcula_total_grati(self):
        # ----------------------- CALCULA TOTAL GRATI --------------------------
        for record in self:
            w_dato = 0.00 
            w_dato += record.x_cens_grat_imes
            w_dato += record.x_cens_grat_ibon
            record['x_cens_grat_itot'] = w_dato

    api.depends('x_cens_ccts_itot', 'x_cens_vaca_itot', 'x_cens_vaca_iafp', 'x_cens_grat_imes', 'x_cens_grat_ibon')
    def _calcula_total_resumen(self):
        # ----------------------- CALCULA TOTAL RESUMEN --------------------------
        for record in self:
            w_dato = 0.00 
            w_dato += record.x_cens_ccts_itot
            w_dato += record.x_cens_vaca_itot
            w_dato -= record.x_cens_vaca_iafp
            w_dato += record.x_cens_grat_imes
            w_dato += record.x_cens_grat_ibon
            record['x_cens_liqu_tota'] = w_dato

    @api.depends('contract_fecese')
    def _calcula_literal_fecha(self):
        # ----------------------- COMPONE CADENA LITERAL DE FECHA --------------------------
        #
        for record in self:
            if (record.contract_fecese):
                w_mes = record.contract_fecese.month
                w_dia = record.contract_fecese.day
                w_ano = record.contract_fecese.year
                w_mes_name = self.mes_literal(w_mes)
                w_Resultado = "LIMA, " + str(w_dia) + " de " + w_mes_name + " del " + str(w_ano)
            else: 
                w_Resultado = "LIMA, "
            record['x_cens_lite_fech'] = w_Resultado
    

    @api.depends('payslip_id')
    def _calcula_boleta_identifi(self):
        # ----------------------- COMPONE CADENA LITERAL DE FECHA --------------------------
        #
        for record in self:
            if (record.payslip_id):
                w_Resultado = record.payslip_id.x_studio_literal_fecha_titulo
            else: 
                w_Resultado = "NONE"
            record['x_cens_bole_iden'] = w_Resultado


    @api.depends('contract_cesado')
    def _calcula_mensaje_nota_automatic(self):
        w_mensaje = ""
        for record in self:
            if not record.contract_cesado :
                w_mensaje += "Recuerde que sólo podrá liquidar Beneficios Sociales al personal que se encuentre cesado."  + "\n"
                w_mensaje += "El BOTÓN para GENERAR los cálculos de Liquidación BB.SS. no está disponible para NO CESADOS. "  + "\n"
            else:
                w_mensaje += "Para proceder con el cálculo presione en el BOTÓN VERDE de GENERAR LIQUIDACIÓN y aparecerá el cálculo de BB.SS."

        self.write({'note_automatic': w_mensaje})


    @api.depends('x_cens_vaca_itot')
    def _calcula_afp_comision_flujo(self):
        for record in self:
            w_comi_flujo = record.setup_afp_id.x_comision_flujo
            w_tipo_comis = record.employee_id.x_studio_tipo_comision
            w_impo_flujo = 0.00
            w_SBRUTO = record.x_cens_vaca_itot 
            # + record.x_cens_vaca_iafp        #--- (Le repone el iAFP que le descontó antes)
            if record.x_cens_afp_compa :
                if (record.x_cens_afp_compa.x_name  == "ONP"):
                    w_impo_flujo = 0.00
                else:
                    if (w_tipo_comis  == "FLU"):
                        w_impo_flujo = w_SBRUTO * w_comi_flujo
                    else:
                        w_impo_flujo = 0.00
            else:
                w_impo_flujo = 0.00
            record.write({'x_cens_afp_flujo': w_impo_flujo})

    @api.depends('x_cens_vaca_itot')
    def _calcula_afp_comision_mixta(self):
        for record in self:
            w_comi_mixta = record.setup_afp_id.x_comision_mixta
            w_tipo_comis = record.employee_id.x_studio_tipo_comision
            w_impo_mixta = 0.00
            w_SBRUTO = record.x_cens_vaca_itot 
            # + record.x_cens_vaca_iafp        #--- (Le repone el iAFP que le descontó antes)
            if record.x_cens_afp_compa :
                if (record.x_cens_afp_compa.x_name == "ONP"):
                    w_impo_mixta = 0.00
                else:
                    if (w_tipo_comis  == "MIX"):
                        w_impo_mixta = w_SBRUTO * w_comi_mixta
                    else:
                        w_impo_mixta = 0.00
            else:
                w_impo_mixta = 0.00
            record.write({'x_cens_afp_mixta': w_impo_mixta})

    @api.depends('x_cens_vaca_itot')
    def _calcula_afp_prima_seguro(self):
        for record in self:
            w_segu_prima = record.setup_afp_id.x_prima_seguro
            w_tipo_comis = record.employee_id.x_studio_tipo_comision
            w_impo_prima = 0.00
            w_SBRUTO = record.x_cens_vaca_itot 
            # + record.x_cens_vaca_iafp        #--- (Le repone el iAFP que le descontó antes)
            if record.x_cens_afp_compa :
                if (record.x_cens_afp_compa.x_name  == "ONP"):
                    w_impo_prima = 0.00
                else:
                    w_impo_prima = w_SBRUTO * w_segu_prima
            else:
                w_impo_prima = 0.00
            record.write({'x_cens_afp_prima': w_impo_prima})

  
    @api.depends('x_cens_vaca_itot')
    def _calcula_afp_aporte_obligatorio(self):
        for record in self:
            w_apor_oblig = record.setup_afp_id.x_aporte_obligatorio
            w_tipo_comis = record.employee_id.x_studio_tipo_comision
            w_impo_aport = 0.00
            w_SBRUTO = record.x_cens_vaca_itot 
            # + record.x_cens_vaca_iafp        #--- (Le repone el iAFP que le descontó antes)
            w_impo_aport = w_SBRUTO * w_apor_oblig    
            record.write({'x_cens_afp_oblig': w_impo_aport})


    def calcula_descuento_afp(self, subtotal_afp):
        for record in self:
            w_comi_flujo = record.setup_afp_id.x_comision_flujo
            w_segu_prima = record.setup_afp_id.x_prima_seguro
            w_apor_oblig = record.setup_afp_id.x_aporte_obligatorio
            w_tipo_comis = record.employee_id.x_studio_tipo_comision
            w_tipo_plani = record.employee_id.x_studio_tipo_planilla
            w_impo_aport = 0.00
            w_SBRUTO = subtotal_afp
            w_Dato = 0.00
            if record.x_cens_afp_compa :
                w_Dato = 0.00
                w_Dat2 = 0
                w_Dat2 = record.x_cens_afp_compa.id    #---- Verifica si es ONP (registro 5)
                if (w_Dat2 == 5):
                    w_Dato += w_SBRUTO * w_apor_oblig
                else:
                    w_Dato += w_SBRUTO * w_apor_oblig
                    w_Dato += w_SBRUTO * w_segu_prima
                    if w_tipo_comis :
                        if w_tipo_comis != "CERO" :
                            if w_tipo_comis == "FLU" :
                                w_Dato += w_SBRUTO * w_comi_flujo
                            else:
                                w_Dato += w_SBRUTO * w_comi_flujo
            else:
                w_Dato = 0.00

            if (w_tipo_plani=="LOCA"):
                w_Dato = 0.00
        return w_Dato


    @api.depends('x_cens_ccts_itot', 'x_cens_vaca_itot', 'x_cens_grat_itot', 'x_cens_vaca_iafp', 'x_cens_desc_otro', 'x_cens_desc_5cat')
    def _calcula_liquidacion_total(self):
        for r in self: 
            r.x_cens_liqu_tota = (r.x_cens_ccts_itot + (r.x_cens_vaca_itot - r.x_cens_vaca_iafp) + r.x_cens_grat_itot) ## ORH
            r.x_cens_liqu_tota -= (r.x_cens_desc_otro + r.x_cens_desc_5cat)


    @api.depends('x_cens_vaca_iano', 'x_cens_vaca_imes', 'x_cens_vaca_idia')
    def _calcula_Monto_Base(self):
        for r in self: 
            r.x_cens_apor_mbas = (r.x_cens_vaca_iano + r.x_cens_vaca_imes + r.x_cens_vaca_idia)


    @api.depends('x_cens_apor_mbas')
    def _calcula_aporte_essalud(self):
        for r in self: 
            r.x_cens_apor_essa = (r.x_cens_apor_mbas * 0.09)

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
    # @api.onchange('employee_id')
    # def _onchange_employee_id_liquidacion(self):
    #     """Establece fechas automáticamente cuando se selecciona el empleado"""
    #     if self.employee_id:
    #         # Fecha de inicio: fecha de contratación del empleado
    #         if hasattr(self.employee_id, 'contract_ids') and self.employee_id.contract_ids:
    #             primer_contrato = self.employee_id.contract_ids.sorted('date_start')[0]
    #             self.x_cens_periodo_ini = primer_contrato.date_start
            
    #         # Fecha fin: fecha actual o fecha de fin del período de nómina
    #         if self.date_to:
    #             self.x_cens_periodo_fin = self.date_to
    #         else:
    #             self.x_cens_periodo_fin = date.today()
    
    # # Método para calcular automáticamente valores desde las líneas de nómina
    # def calcular_valores_desde_nomina(self):
    #     """Calcula los valores de liquidación desde las líneas de nómina"""
    #     self.ensure_one()
        
    #     # Buscar remuneración base en las líneas
    #     linea_sueldo = self.line_ids.filtered(lambda l: l.code == 'BASIC')
    #     if linea_sueldo:
    #         self.x_cens_remu_base = linea_sueldo[0].total
        
    #     # Buscar asignación familiar
    #     linea_asig_fam = self.line_ids.filtered(lambda l: l.code in ['ASIG_FAM', 'AF'])
    #     if linea_asig_fam:
    #         self.x_cens_asig_fami = linea_asig_fam[0].total
        
    #     return True
    
    # =============================
    # BOTÓN - GENERAR LIQUIDACIÓN
    # =============================
    def action_liquidacion_compone(self): 
        self.ensure_one()
        w_mensajes = ""
        if self.contract_cesado:
            w_fecha_ingr = self.contract_fingr
            w_fecha_cese = self.contract_fcese 
            w_total_remu = self.contract_wage + self.x_cens_asig_fami

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
            top1_param = date(ajus_anio, 6, 30)     #-- Pago Grati Julio
            top2_param = date(ajus_anio-1, 12, 31)  #-- Pago Grati Diciembre
            w_sexto_costo_mes = 0.00
            w_sexto_impor_mes = 0.00
            w_fecha_tope1 = top1_param if w_fecha_cese > top1_param else top2_param
            w_fecha_tope2 = 0
            w_fecha_tope3 = 0
            w_canti_meses = 0
            w_sexto_costo_mes = 0.00
            w_sexto_impor_mes = 0.00
            w_periodo_switch = False
            if (w_fecha_ingr <= w_fecha_tope1):  
                w_fecha_tope2 = self.determina_periodo_grati(w_fecha_ingr, w_fecha_tope1)
                if (w_fecha_ingr < w_fecha_tope2):
                    w_fecha_tope3 = self.determina_periodo_grati(w_fecha_ingr, w_fecha_tope2)   #-- New Tope2 
                    w_periodo_switch = True
                    w_period_grati = self.desglosa_periodo("ÚLTIMA GRATIFICACIÓN", w_fecha_tope2, w_fecha_tope3)
                    w_sexto_canti_mm = w_period_grati.get('meses', 0)
                    w_sexto_canti_dd = 0.00                                 #-- w_period_grati.get('dias', 0)
                    w_canti_meses = w_sexto_canti_mm + (w_period_grati.get('anios', 0)*12) 
                    if (w_canti_meses > 1):
                        w_sexto_costo_mes = w_total_remu 
                        # w_sexto_costo_dia = w_total_remu/30
                        w_sexto_impor_mes = (w_sexto_costo_mes/6) * w_sexto_canti_mm
                        # w_sexto_impor_dia = (w_sexto_costo_dia/6) * w_sexto_canti_dd

                        w_sexto_total = w_sexto_impor_mes / 6                   #-- w_sexto_total = (w_sexto_impor_mes + w_sexto_impor_dia) / 6
                    else:
                        w_sexto_total = 0.00
                        #
                        # AQUI COMENTARIO: "SEXTO: Periodo debe ser MAYOR a un mes."
                        #
                        w_mensajes += "\n" + "- SEXTO: Periodo debe ser MAYOR a un mes."
                else:
                    w_sexto_total = 0.00
                    #
                    # AQUI COMENTARIO: "SEXTO: No tiene periodo de GRATIFICACIÓN anterior."
                    #
                    w_mensajes += "\n" + "- SEXTO: No tiene periodo de GRATIFICACIÓN anterior."

            else:
                w_sexto_total = 0.00
                #
                # AQUI COMENTARIO: "SEXTO: Fecha ingreso sobrepasa fecha TOPE ({w_fecha_tope1}) para cálculo "
                #
                w_mensajes += "\n" + f"- SEXTO: Fecha de ingreso FUERA DE RANGO para cálculo. "

            w_conce_noremuner = 0.00
            w_remun_compu_cts = w_total_remu + w_conce_noremuner + w_sexto_total
                
            # -------------------------------------------------------------------------------------------------------
            w_cantidad_aa =  w_period_grati.get('anios', 0) if w_periodo_switch else 0
            w_cantidad_mm =  w_period_grati.get('meses', 0) if w_periodo_switch else 0
            w_cantidad_dd =  w_period_grati.get('dias', 0) if w_periodo_switch else 0
            _logger.info(f'=============================================')
            _logger.info(f'REMU.COMPUTAB:  {w_remun_compu_cts}')
            _logger.info(f'==============================================')
            _logger.info(f'CONTROL EN CÁLCULO SEXTO DE LA GRATIFICACIÓN ')
            _logger.info(f'==============================================')
            _logger.info(f'Fech.INGRESO :  {w_fecha_ingr}')
            _logger.info(f'Fech.CESE    :  {w_fecha_cese}')
            _logger.info(f'Año Ajustado :  {ajus_anio}')
            _logger.info(f'Topes Periodo:  {top1_param}  al  {top2_param} ')
            _logger.info(f'Fech.Tope-1 :   {w_fecha_tope1}')
            _logger.info(f'Fech.Tope-2 :   {w_fecha_tope2}')
            _logger.info(f'Fech.Tope-2 :   {w_fecha_tope3}')
            _logger.info(f'----------------------------------------------')
            _logger.info(f'Perio.Grat.aa :  {w_cantidad_aa}')
            _logger.info(f'Perio.Grat.mm :  {w_cantidad_mm}')
            _logger.info(f'Perio.Grat.dd :  {w_cantidad_dd}')
            _logger.info(f'Cantidad meses:  {w_canti_meses}')
            _logger.info(f'sexto.cost.mes:  {w_sexto_costo_mes}')
            _logger.info(f'sexto.impo.mes:  {w_sexto_impor_mes}')
            _logger.info(f'TOTAL SEXTO   :  {w_sexto_total}')
            _logger.info(f'=============================================')

            # --------------------------------------------------     
            #  CALCULA CTS TRUNCOS
            # --------------------------------------------------
            w_fecha_tope = self.determina_periodo_cts(w_fecha_ingr, w_fecha_cese)
            w_period_cts = self.desglosa_periodo("CTS TRUNCOS", w_fecha_tope, w_fecha_cese)
            w_cant_mm = w_period_cts.get('meses', 0)
            w_cant_dd = w_period_cts.get('dias', 0)
            if ((w_fecha_tope.month == w_fecha_cese.month) and (w_fecha_tope.year == w_fecha_cese.year)):
                if ((w_fecha_tope.day==1) and (w_fecha_cese.day in [30,31])):
                    w_impcts_mes = ((w_remun_compu_cts/12) * w_cant_mm)                #--- Por el rango meses
                else:
                    w_impcts_mes = 0.00
                w_impcts_dia = 0
            else:
                w_impcts_mes = ((w_remun_compu_cts/12) * w_cant_mm)                #--- Por el rango meses
                w_impcts_dia = (((w_remun_compu_cts/12)/30) * w_cant_dd)           #--- Por el rango días

            if ((w_cant_mm==0) and (w_cant_dd<30)):
                w_impcts_dia = 0.00                     #-- Ajusta a CERO si tiempo es menor a 30 días
                w_mensajes += "\n" + f"- CTS  : Tiempo laboral ({w_cant_dd} días) es menor a un mes."

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
            w_ultimo_dia2 = self.ultimo_dia_del_mes(w_fecha_cese).day

            w_cant_aa = w_period_vac.get('anios', 0)
            w_cant_mm = w_period_vac.get('meses', 0)
            w_cant_dd = w_period_vac.get('dias', 0)
            if ((w_fecha_ingr.month == w_fecha_cese.month) and (w_fecha_ingr.year == w_fecha_cese.year)):
                if ((w_fecha_ingr.day==1) and (w_fecha_cese.day in [30,31])):
                    w_impvaca_mes = (w_total_remu/12) * 1           #--- Por el rango meses
                else:
                    w_impvaca_mes = 0.00

                w_impvaca_ano = 0.00
                w_impvaca_dia = 0.00
            else:    
                #w_cant_aa = (1 if w_cant_aa>0 else 0)
                w_impvaca_ano = w_total_remu * w_cant_aa                #--- Por el rango años
                w_impvaca_mes = (w_total_remu/12) * w_cant_mm           #--- Por el rango meses
                w_impvaca_dia = ((w_total_remu/12)/30) * w_cant_dd      #--- Por el rango días

            if ((w_cant_aa==0) and (w_cant_mm==0) and (w_cant_dd<30)):
                w_impvaca_ano = 0.00
                w_impvaca_mes = 0.00
                w_impvaca_dia = 0.00
                w_cant_dd_gozados = 0
                w_cost_dd_gozados = 0.00
                w_impo_dd_gozados = 0.00
                w_deta_dd_gozados = "- Días gozados. " 
                w_mensajes += "\n" + f"- VACA : Tiempo laboral ({w_cant_dd} días) es menor a un mes."
            else:
                #
                # BUSCA LAS VACACIONES GOZADAS  (x_cens_vaca_igoz, x_cens_vaca_dgoz)
                #
                w_cant_dd_gozados = int(self.extrae_vacaciones_gozadas(w_fecha_ingr, w_fecha_cese))
                if (w_cant_dd_gozados > 0):
                    w_cost_dd_gozados = (w_total_remu/30)
                    w_impo_dd_gozados = w_cost_dd_gozados * w_cant_dd_gozados
                else:
                    w_cost_dd_gozados = 0.00
                    w_impo_dd_gozados = 0.00
                    w_mensajes += "\n" + f"- VACA : No presenta días de vacaciones gozados."

                w_deta_dd_gozados = "- Menos " + str(w_cant_dd_gozados) + " días gozados " 
                w_deta_dd_gozados += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 30 x " + str(w_cant_dd_gozados) + "días )  = "
            w_detvaca_ano = "- Por " + str(w_cant_aa) + " años "
            w_detvaca_ano += " ( " + self.formato_moneda(w_total_remu, "S/.") + "  x " + str(w_cant_aa) + " )  = "
            w_detvaca_mes = "- Por " + str(w_cant_mm) + " meses "
            w_detvaca_mes += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 12 x " + str(w_cant_mm) + " )  = "
            w_detvaca_dia = "- Por " + str(w_cant_dd)  + " días  "
            w_detvaca_dia += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 12 ÷ 30 x " + str(w_cant_dd) + " )  = "
            
            w_impvaca_tot = (w_impvaca_ano + w_impvaca_mes + w_impvaca_dia) - w_impo_dd_gozados
            w_impvaca_afp = self.calcula_descuento_afp(w_impvaca_tot)
            w_impvaca_tot = w_impvaca_tot   #-- No le restael AFP  (- w_impvaca_afp)


            # --------------------------------------------------
            #  CALCULA GRATIFICACIONES TRUNCAS
            # --------------------------------------------------    ## QUIQUITO
            w_fecha_tope1 = self.determina_periodo_grati(w_fecha_ingr, w_fecha_cese)    #-- F.inicio
            w_fecha_tope2 = w_fecha_cese                                                #-- F.final
            w_ultimo_dia2 = self.ultimo_dia_del_mes(w_fecha_tope2).day
            w_period_grati= self.desglosa_periodo("GRATIFICACIONES TRUNCAS", w_fecha_tope1, w_fecha_tope2)
            w_cant_aa = w_period_grati.get('anios', 0)
            w_cant_mm = w_period_grati.get('meses', 0)
            w_cant_dd = w_period_grati.get('dias', 0)

            if ((w_fecha_tope1.month == w_fecha_tope2.month) and (w_fecha_tope1.year == w_fecha_tope2.year)):
                if ((w_fecha_tope1.day==1) and (w_fecha_tope2.day in [30,31])):
                    w_meses_habiles = 1
                else:    
                    w_meses_habiles = 0
                    w_mensajes += "\n" + f"- GRATI: No presenta meses hábiles."
            else:
                w_meses_habiles = w_cant_mm 
                #(w_fecha_cese.month - w_fecha_tope1.month)
                #if ((w_fecha_tope1.day==1) and (w_fecha_cese.day in [30,31])):
                #    w_meses_habiles += 1

            w_detgrat_per = "DESDE: " + str(w_fecha_tope1.day) + " de " + self.mes_literal(w_fecha_tope1.month) + " del " + str(w_fecha_tope1.year) + " "
            w_detgrat_per += "AL " + str(w_fecha_tope2.day) + " de " + self.mes_literal(w_fecha_tope2.month) + " del " + str(w_fecha_tope2.year) + " "

            w_trunco_gra = 0.00
            if ((w_cant_aa==0) and (w_cant_mm==0) and (w_cant_dd<30)):
                w_mensajes += "\n" + f"- GRATI: Periodo menor de 30 días."
            else:
                if (w_meses_habiles > 0):
                    w_trunco_gra += ((w_total_remu/6) * w_meses_habiles)                 #--- Por el rango meses
                else:
                    w_mensajes += "\n" + f"- GRATI: No presenta meses hábiles."

            w_detgrat_mes = "- Por " + str(w_meses_habiles) + " meses "
            w_detgrat_mes += " ( " + self.formato_moneda(w_total_remu, "S/.") + " ÷ 6 x " + str(w_meses_habiles) + " )  = "
            
            _logger.info(f'==========================================')
            _logger.info(f'CONTROL EN CÁLCULO GRATIFICACIÓN ')
            _logger.info(f'==========================================')
            _logger.info(f'Fech.Inicial :  {w_fecha_tope1}')
            _logger.info(f'Fech.Final   :  {w_fecha_tope2}')
            _logger.info(f'Último Día   :  {w_ultimo_dia2}')
            _logger.info(f'Meses Hábiles :  {w_meses_habiles}')
            _logger.info(f'Periodo      :  {w_detgrat_per}')
            _logger.info(f'==========================================')

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
                    'x_cens_remu_base': self.contract_wage,
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
                    'x_cens_vaca_dgoz': w_deta_dd_gozados,
                    'x_cens_vaca_igoz': w_impo_dd_gozados,
                    'x_cens_vaca_dafp': '(-) Menos Descuento AFP/ONP',
                    'x_cens_vaca_iafp': w_impvaca_afp,
                    'x_cens_vaca_itot': w_impvaca_tot,
                    'x_cens_grat_peri': w_detgrat_per,  #-----------------------    GRATIFICACIÓN
                    'x_cens_grat_dmes': w_detgrat_mes,
                    'x_cens_grat_imes': w_impgrat_mes,
                    'x_cens_grat_dbon': w_detgrat_bon,
                    'x_cens_grat_ibon': w_impgrat_bon,
                    'x_cens_grat_itot': w_impgrat_tot,
                    'note_calculos': w_mensajes
                })  
                            
            self.recompute()
        else:
            w_mensajes = " Al Empleado no se le REGISTRÓ su CESE laboral."
            self.write({
                        'note_calculos': w_mensajes
                    })
        pass

    
    # ==============================================
    # BOTÓN - RECALCULA BBSS
    # ==============================================
    def action_recalcular_bbss(self):  
        self.ensure_one()
        w_mensajes = ""
        if self.contract_cesado:
            #
            self.ensure_one()
            self.write({'x_cens_tipo_calc': "1"})
            self.action_liquidacion_compone()
            self.recompute()
        pass

    # ==============================================
    # BOTÓN - ACTUALZA BOLETA PAGO CON RESUMEN BBSS
    #         Traslada los datos resumen de la Liquidación a la boleta.
    # ==============================================
    def action_actualiza_bbss_boleta(self):  
        self.ensure_one()
        w_mensajes = ""
        if self.contract_cesado:
            #
            # Busca y posiciona ULTIMA BOLETA
            # 
            resultado_busqueda = self.env['hr.payslip'].search([('employee_id.id','=',self.employee_id.id)], order='id desc', limit=1)
            if resultado_busqueda:
                for boleta_empleado in resultado_busqueda:
                    if not boleta_empleado.x_studio_cese_no_actualizar:
                        boleta_empleado.write({
                                'x_studio_cese_vaca_trunca': self.x_cens_vaca_itot,
                                'x_studio_cese_cts_trunco': self.x_cens_ccts_itot,
                                'x_studio_cese_grati_trunca': self.x_cens_grat_imes,
                                'x_studio_cese_bonif_grati_trunca': self.x_cens_grat_ibon,
                                'x_studio_cese_comentarios': 'Cálculo liquidación: ' + self.name,        #-- ORH
                                'x_studio_cese_descuento_afp': self.x_cens_vaca_iafp, 
                                'x_studio_cese_otros_descuentos': self.x_cens_desc_otro,
                                'x_studio_cese_descuento_renta_5ta': self.x_cens_desc_5cat,
                                'x_studio_cese_aporte_essalud': self.x_cens_apor_essa
                                #'x_studio_cese_no_actualizar':
                            })
                        self.recompute()
                    else:
                        raise UserError("Esta BOLETA no permite TRASLADAR los datos del cálculo de BENEFICOS SOCIALES.")
        pass


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
    
    
    def extrae_vacaciones_gozadas(self, f_ingr, f_cese):
        w_fech_ingreso = f_ingr
        w_fech_cese    = f_cese

        # Obtener todas las AUSENCIAS del Empleado
        ausencias = self.env['hr.leave'].search([
                                            ('employee_id', '=', self.employee_id.id),
                                            ('state', 'in', ['draft', 'confirm', 'refuse', 'validate1', 'validate'])  
                                        ])
        w_dias_gozados = 0
        # Procesa cada AUSENCIA y extraer los DIAS GOZADOS.
        for vacaciones_gozadas in ausencias:
            # Verificar si ya existe un registro para este empleado en el año ejercicio
            w_fech_desde = vacaciones_gozadas.request_date_from
            w_fech_hasta = vacaciones_gozadas.request_date_to
            w_dias_ausen = vacaciones_gozadas.number_of_days_display
            if (w_fech_desde >= w_fech_ingreso and w_fech_desde <= w_fech_cese):
                if (w_fech_hasta >= w_fech_ingreso and w_fech_hasta <= w_fech_cese):
                    w_dias_gozados += w_dias_ausen
                else:
                    w_fech_hasta = w_fech_cese
            else:
                w_fech_desde = w_fech_ingreso

        return w_dias_gozados
    

    # --------------------------------------
    # BOTÓN: Resumen Liquidación (Cálculos)     ----- TIPO = 1
    # --------------------------------------
    def action_recalcula_bbss(self):
        """
        RE-CALCULA LOS VALORES PARA LAS MODIFICACIONES: 
        
        """
        if self.contract_cesado:
            self.ensure_one()
            self.write({'x_cens_tipo_calc': "1"})
            self.action_liquidacion_compone()
            self.recompute()
        pass

    # --------------------------------------
    # BOTÓN: Hoja de Liquidación                ----- TIPO = 2
    # --------------------------------------
    def action_recalcula_hoja_bbss(self):
        """
        CALCULA LOS VALORES PARA: 
        - Vacaciones Truncas
        - CTS Truncas
        - Gratificaciones Truncas
        - Bonific. Gratificaciones

        Pero valiéndose del método: action_liquidacion_compone()
        
        """
        if self.contract_cesado:
            self.ensure_one()
            self.write({'x_cens_tipo_calc': "2"})
            self.write({'generado': True})
            self.action_liquidacion_compone()
            self.recompute()
        pass


    # ==========================
    # BOTÓN - BLANQUEA
    # ==========================
    def action_liquidacion_blanquea(self):
        self.ensure_one()
        self.write({'generado': False})
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
    def action_liquidacion_imprimir_v3(self):
        """
        Método usando el servicio de reportes directamente
        """
        try:
            # Validaciones
            if not getattr(self, 'contract_cesado', False):
                raise UserError("Solo se puede imprimir la liquidación para empleados cesados.")
            
            if not getattr(self, 'generado', False):
                raise UserError("Primero debes GENERAR la liquidación.")
            
            if not self.x_cens_liqu_tota or self.x_cens_liqu_tota <= 0:
                raise UserError("Debe generar primero los cálculos de liquidación.")
            
            _logger.info(f'Generando reporte para: {self.employee_id.name}')
            
            # Usar directamente el nombre de la plantilla
            report_name = 'cens_nomina_bbss_liquidaciones.liquidacion_bbss_document'
            
            # Configurar contexto
            context = dict(self.env.context)
            context.update({
                'lang': 'es_PE',
                'tz': 'America/Lima',
            })
            
            # Generar PDF usando el servicio de reportes
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                report_name, 
                self.ids,
                data={'context': context}
            )
            
            if not pdf_content:
                raise UserError("No se pudo generar el contenido del PDF")
            
            # Crear attachment para descarga
            filename = f'Liquidacion_BBSS_{self.employee_id.name}_{self.id}.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.payslip.liquidacion',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # Retornar URL para descarga
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error al generar reporte: {str(e)}")
            raise UserError(f"Error al generar el reporte: {str(e)}")


    def action_liquidacion_imprimir_v4(self):
        """
        Método alternativo usando return directo
        """
        try:
            # Validaciones
            if not getattr(self, 'x_studio_cesado', False):
                raise UserError("Solo se puede imprimir la liquidación para empleados cesados.")
            
            _logger.info(f'Generando reporte para: {self.employee_id.name}')
            
            # Retornar acción directa del reporte
            return {
                'type': 'ir.actions.report',
                'report_name': 'cens_nomina_bbss_liquidaciones.liquidacion_bbss_document',
                'report_type': 'qweb-pdf',
                'data': {'ids': self.ids},
                'context': self.env.context,
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error al generar reporte: {str(e)}")
            raise UserError(f"Error al generar el reporte: {str(e)}")

    def action_liquidacion_imprimir_v5(self):
        """
        Método usando el servicio de reportes con manejo mejorado
        """
        try:
            # Validaciones
            if not getattr(self, 'x_studio_cesado', False):
                raise UserError("Solo se puede imprimir la liquidación para empleados cesados.")
            
            # Asegurar que el registro existe y tiene datos
            self.ensure_one()
            
            _logger.info(f'Generando reporte para: {self.employee_id.name}')
            
            # Configurar el contexto del reporte
            report_context = dict(self.env.context)
            report_context.update({
                'active_model': 'hr.payslip.liquidacion',
                'active_ids': self.ids,
                'active_id': self.id,
            })
            
            # Obtener el reporte
            report_name = 'cens_nomina_bbss_liquidaciones.liquidacion_bbss_document'
            
            # Usar el servicio de reportes
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                report_name, 
                self.ids,
                data={'context': report_context}
            )
            
            if not pdf_content:
                raise UserError("No se pudo generar el contenido del PDF")
            
            # Crear el attachment
            filename = f'Liquidacion_BBSS_{self.employee_id.name}_{self.id}.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.payslip.liquidacion',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            # Retornar URL para descarga
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error al generar reporte: {str(e)}")
            raise UserError(f"Error al generar el reporte: {str(e)}")

    # ----------------------------------------------------
    # ACCIONA WIZARD - Hoja de Liquidación BBSS 
    # ----------------------------------------------------
    #def action_formato_hoja_liquidacion_BBSS(self):
    #    self.ensure_one()
    #    
    #    return {
    #        'name': _('HOJA_LIQUICACION_BBSS'), 
    #        'type': 'ir.actions.act_window',
    #        'res_model': 'hr.payslip.liquidacion', 
    #        'view_mode': 'form',
    #        'target': 'new',
    #        'context': {
    #            'default_message': _("PROCESO: Esta ventana muestra la liquidación de Beneficios Sociales \n"
    #                                "del trabajador activo. \n"
    #                        ),
    #            'default_lead_id': self.id,
    #        }
    #    }
            
    # ===============================================================================================
    # FIN - Campos liquidación
    # ===============================================================================================

  
    # -----------------------------------------------
    # IMPRIME: Genera PDF con juego caracteres UTF8
    # -----------------------------------------------
    def action_liquidacion_imprimir_v6_utf8(self):
        """
        Método mejorado con soporte completo UTF-8
        """
        try:
            # Validaciones
            if not getattr(self, 'x_studio_cesado', False):
                raise UserError("Solo se puede imprimir la liquidación para empleados cesados.")
            
            self.ensure_one()
            
            _logger.info(f'Generando reporte UTF-8 para: {self.employee_id.name}')
            
            # CORRECCIÓN CRÍTICA: Configurar contexto con encoding UTF-8
            report_context = dict(self.env.context)
            report_context.update({
                'active_model': 'hr.payslip.liquidacion',
                'active_ids': self.ids,
                'active_id': self.id,
                'lang': 'es_PE',           # Español de Perú
                'tz': 'America/Lima',
                'website_id': False,       # Evitar conflictos de website
            })
            
            # Forzar configuración de idioma para caracteres especiales
            self = self.with_context(
                lang='es_PE',
                tz='America/Lima'
            )
            
            # Obtener el reporte
            report_name = 'cens_nomina_bbss_02.liquidacion_bbss_document'
            
            # CORRECCIÓN: Usar el servicio de reportes con opciones específicas
            pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
                report_name, 
                self.ids,
                data={
                    'context': report_context,
                    'encoding': 'utf-8',
                    'disable_smart_quotes': True,  # Evitar conversión de comillas
                }
            )
            
            if not pdf_content:
                raise UserError("No se pudo generar el contenido del PDF")
            
            # Crear filename con caracteres seguros
            employee_name = self.employee_id.name or 'Empleado'
            safe_name = ''.join(c for c in employee_name if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f'Liquidacion_BBSS_UTF8_{safe_name}_{self.id}.pdf'
            
            # Crear attachment
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'hr.payslip.liquidacion',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error(f"Error al generar reporte UTF-8: {str(e)}")
            raise UserError(f"Error al generar el reporte: {str(e)}")

    # ===============================================================================================
    # FIN - Genera PDF con juego caracteres UTF8
    # ===============================================================================================



    # -----------------------------------------------
    # ACCION: Se debe modificar para que se genere las liquidaciones de modo masivo, considerando 
    #         los empleados cesados en el mes.  OJO EN PROCESO
    # -----------------------------------------------
    def action_genera_liquidación_masiva(self):
        for record in self:
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025
            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else:
                año_ingreso = 2025
                mes_ingreso = 1

        # Buscar los Empleado con el check 5ta activado
        domain = [
            ('x_studio_estado_contrato', '=', 'open')  #-- (En Proceso)
        ]
        
        # Obtener todas los Empleados con 5ta (InMemory)
        personal = self.env['hr.employee'].search(domain)
        
        _logger.info('INGRESANDO A CREAR DICCIONARIOS')
        w_fila = 0
        # Procesar cada boleta y extraer la información
        if personal:
            for empleado in personal:
                w_fila += 1
                # Verificar si ya existe un registro para este empleado en el año ejercicio
                # existing_record = self.env['hr.payslip.renta_quinta'].search([
                #    ('employee_id', '=', empleado.id),
                #    ('cens_nano_ejercicio', '=', w_AñoEje)
                # ], limit=1)
                
                # Si no existe un registro, crear uno nuevo
                #if not existing_record:
                    # Preparar valores para el nuevo registro
                vals = {
                    'name': f"RENTA {w_AñoEje} - 5TA CAT - {empleado.name}",
                    'employee_id': empleado.id,
                    'cens_anio_ejercicio': record.cens_anio_ejercicio,
                    'cens_nano_ejercicio': w_AñoEje,
                    'cens_fech_registro': fields.Date.context_today(self),
                    'cens_suel_basico': empleado.contract_id.wage if empleado.contract_id else 0.0,
                    'cens_uit_procesado': self.env.company.x_studio_unidad_impositiva_tributaria,
                    'cens_sminim_proces': self.env.company.x_studio_sueldo_minimo,
                    'state': 'draft',
                    'cens_tiene_renta5ta': True,
                    'cens_observaciones': f"Creado automáticamente desde proceso masivo el {fields.Date.to_string(fields.Date.context_today(self))}"
                }
                    
                # Crear el nuevo registro
                new_record = self.env['hr.payslip.renta_quinta'].create(vals)
                
                # Log para depuración
                _logger.info(f'Creado registro de renta quinta para empleado: {empleado.name} (ID: {empleado.id}) - Año: {w_AñoEje}')
                
                # Opcional: Desencadenar métodos adicionales si es necesario
                # Por ejemplo, si tienes un método para calcular valores iniciales:
                # new_record._compute_contract_info()
                # new_record._calculate_initial_values()
                new_record.action_rellena_datos()
                new_record.action_traslada_boletas()
                new_record.action_traslada_datos()
                #new_record.action_rellena_datos()
        else:
            _logger.info(f'Ya existe registro de renta quinta para empleado: {empleado.name} (ID: {empleado.id}) - Año: {w_AñoEje}')
        
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'message': f'Se han procesado {w_fila} empleados',
                    'type': 'success',
                    'sticky': False,
                }
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
    def formato_moneda(cantidad, simbolo="S/."):
        return f"{simbolo}{cantidad:,.2f}"    