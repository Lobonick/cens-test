from odoo import api, fields, models
from datetime import datetime
import time
import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    cens_nano_ejercicio  = fields.Integer(string="Año Ejercicios", default=2025)
    cens_renta_quinta_id = fields.Many2one('hr.payslip.renta_quinta', string="Configuración Renta 5ta.Cat")
    cens_tiene_renta5ta = fields.Boolean(
        string='¿Tiene Renta 5ta.Cat.?', 
        related='cens_renta_quinta_id.cens_tiene_renta5ta', 
        store=True
    )
    cens_logo_sunat = fields.Binary(string='', related='company_id.x_studio_datos_sunat')
    cens_sueldo_minimo  = fields.Float(string="Sueldo Mínimo", related='cens_renta_quinta_id.cens_sueldo_minimo')
    cens_uit_importe = fields.Float(string="UIT", related='cens_renta_quinta_id.cens_unidad_impositiva_tributaria')
    cens_renta5ta_ene = fields.Float(string="Enero", related='cens_renta_quinta_id.cens_reten_ene', default=0.00)
    cens_renta5ta_feb = fields.Float(string="Febrero", related='cens_renta_quinta_id.cens_reten_feb', default=0.00)
    cens_renta5ta_mar = fields.Float(string="Marzo", related='cens_renta_quinta_id.cens_reten_mar', default=0.00)
    cens_renta5ta_abr = fields.Float(string="Abril", related='cens_renta_quinta_id.cens_reten_abr', default=0.00)
    cens_renta5ta_may = fields.Float(string="Mayo", related='cens_renta_quinta_id.cens_reten_may', default=0.00)
    cens_renta5ta_jun = fields.Float(string="Junio", related='cens_renta_quinta_id.cens_reten_jun', default=0.00)
    cens_renta5ta_jul = fields.Float(string="Julio", related='cens_renta_quinta_id.cens_reten_jul', default=0.00)
    cens_renta5ta_ago = fields.Float(string="Agosto", related='cens_renta_quinta_id.cens_reten_ago', default=0.00)
    cens_renta5ta_set = fields.Float(string="Setiembre", related='cens_renta_quinta_id.cens_reten_set', default=0.00)
    cens_renta5ta_oct = fields.Float(string="Octubre", related='cens_renta_quinta_id.cens_reten_oct', default=0.00)
    cens_renta5ta_nov = fields.Float(string="Noviembre", related='cens_renta_quinta_id.cens_reten_nov', default=0.00)
    cens_renta5ta_dic = fields.Float(string="Diciembre", related='cens_renta_quinta_id.cens_reten_dic', default=0.00)
    cens_renta5ta_tot = fields.Float(string="TOTAL RENTA ANUAL:", related='cens_renta_quinta_id.cens_reten_tot', default=0.00)
    

    @api.model
    def create(self, vals):
        # Lógica para establecer el último registro
        if 'cens_renta_quinta_id' in vals:
            last_record = self.env['hr.payslip.renta_quinta'].search([
                ('employee_id', '=', vals.get('employee_id')),
                ('cens_anio_ejercicio', '=', self.cens_nano_ejercicio),
            ], limit=1, order='id desc')
            if last_record:
                vals['cens_renta_quinta_id'] = last_record.id
        return super(HrPayslip, self).create(vals)
    
    @api.onchange('employee_id', 'cens_nano_ejercicio')
    def _onchange_employee_nano_ejercicio(self):
        if self.employee_id and self.cens_nano_ejercicio:
            last_record = self.env['hr.payslip.renta_quinta'].search([
                ('employee_id', '=', self.employee_id.id),
                ('cens_anio_ejercicio', '=', self.cens_nano_ejercicio),
            ], limit=1, order='id desc')
            if last_record:
                self.cens_renta_quinta_id = last_record.id
            else:
                self.cens_renta_quinta_id = False  # Limpiar el campo si no hay registro activo


class renta_quinta_Custom(models.Model):
    _name = 'hr.payslip.renta_quinta'
    _description = 'Renta 5ta.categoría'
    # ---------------------------------------
    # AGREGA CAMPOS AL MODELO RENTA QUINTA
    # ---------------------------------------
    name = fields.Char("Descripción", default="RENTA" )
    user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)
    state = fields.Selection([("draft", "Borrador"), ("posted", "Confirmado"), ("annul", "Anulado")], default="draft")
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, index=True)
    #employee_id = fields.Many2one('hr.employee', string='Empleado', 
    #                                            required=True, 
    #                                            index=True,
    #                                            domain="[('x_studio_sujeto_a_renta_5cat', '=', True), ('x_studio_estado_contrato', '=', 'open')]")
    currency_id = fields.Many2one('res.currency', string='Moneda', 
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'PEN')], limit=1).id,
                                  required=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato Activo', compute='_compute_contract_info', store=True)
    contract_name = fields.Char(string='Nombre del Contrato', compute='_compute_contract_info', store=True)
    contract_date_start = fields.Date(string='Fecha Inicio Contrato', compute='_compute_contract_info', store=True)
    contract_date_end = fields.Date(string='Fecha Fin Contrato', compute='_compute_contract_info', store=True)
    contract_date_ingreso = fields.Date(string='Fecha Ingreso', compute='_compute_contract_info', store=True)
    contract_date_cese = fields.Date(string='Fecha de Cese', compute='_compute_contract_info', store=True)
    contract_movili = fields.Float(string="Movilidad", compute='_compute_contract_info', store=True)
    contract_alimen = fields.Float(string="Alimentación", compute='_compute_contract_info', store=True)
    contract_bonifi = fields.Float(string="Bonif.Educ.", compute='_compute_contract_info', store=True)
    contract_utilid = fields.Float(string="Utilidades", compute='_compute_contract_info', store=True)
    contract_wage = fields.Monetary(string='Sueldo Básico (Contrato)', currency_field='currency_id', 
                                  compute='_compute_contract_info', store=True)
    cens_marcador_cabecera = fields.Binary(string="Imagen", related='company_id.x_studio_renta_5ta_cat')
    cens_foto_empleado = fields.Binary(string="foto", related='employee_id.avatar_128')
    cens_fech_registro = fields.Date(string='Fecha Registro', default=fields.Date.context_today)
    cens_anio_ejercicio = fields.Selection([("2023", "Ejercicio 2023"),
                                            ("2024", "Ejercicio 2024"), 
                                            ("2025", "Ejercicio 2025"), 
                                            ("2026", "Ejercicio 2026"), 
                                            ("2027", "Ejercicio 2027")],
                                            default="2025")
    cens_nano_ejercicio = fields.Integer("Año Ejercicio", default=2025, index=True) 
    cens_suel_basico    = fields.Float("Sueldo Básico")
    cens_observaciones  = fields.Char("Observaciones")
    cens_unidad_impositiva_tributaria = fields.Float(string="UIT", related='company_id.x_studio_unidad_impositiva_tributaria')
    cens_uit_procesado  = fields.Float(string="UIT Procesado", default=0.00)
    cens_sueldo_minimo  = fields.Float(string="Sueldo Mínimo", related='company_id.x_studio_sueldo_minimo')
    cens_sminim_proces  = fields.Float(string="Sueldo Mínimo Procesado", default=0.00)
    cens_tiene_renta5ta = fields.Boolean(string='¿Tiene Renta 5ta.Cat.?', default=True)
    cens_reten_ene = fields.Float('Enero', default=0.00)
    cens_reten_feb = fields.Float('Febrero', default=0.00)
    cens_reten_mar = fields.Float('Marzo', default=0.00)
    cens_reten_abr = fields.Float('Abril', default=0.00)
    cens_reten_may = fields.Float('Mayo', default=0.00)
    cens_reten_jun = fields.Float('Junio', default=0.00)
    cens_reten_jul = fields.Float('Julio', default=0.00)
    cens_reten_ago = fields.Float('Agosto', default=0.00)
    cens_reten_set = fields.Float('Setiembre', default=0.00)
    cens_reten_oct = fields.Float('Octubre', default=0.00)
    cens_reten_nov = fields.Float('Noviembre', default=0.00)
    cens_reten_dic = fields.Float('Diciembre', default=0.00)
    cens_reten_tot = fields.Float('Total Renta anual', default=0.00)

    @api.depends('employee_id')
    def _compute_contract_info(self):
        for record in self:
            # Buscar el contrato activo del empleado
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'open')  # Solo contratos activos
            ], limit=1)
            
            # Asignar valores desde el contrato
            record.contract_id = contract.id if contract else False
            record.contract_name = contract.name if contract else False
            record.contract_date_start = contract.date_start if contract else False
            record.contract_date_end = contract.date_end if contract else False
            record.contract_date_ingreso = contract.x_studio_fecha_de_ingreso if contract else False
            record.contract_date_cese = contract.x_studio_fecha_de_cese if contract else False
            record.contract_movili = contract.x_studio_movilidad_mensual if contract else 0.0
            record.contract_alimen = contract.x_studio_alimentacion if contract else 0.0
            record.contract_bonifi = contract.x_studio_bonificacion_x_educacion if contract else 0.0
            record.contract_utilid = contract.x_studio_utilidades_voluntarias if contract else 0.0
            record.contract_wage = contract.wage if contract else 0.0

   
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Actualiza el sueldo básico cuando cambia el empleado"""
        if self.contract_id:
            self.cens_suel_basico = self.contract_wage

    @api.onchange('cens_anio_ejercicio')
    def _onchange_cens_anio_ejercicio(self):
        for record in self:
            record.write({'name': "RENTA " + record.cens_anio_ejercicio + " - 5TA CAT - "})
            record.write({'cens_nano_ejercicio': int(record.cens_anio_ejercicio)}) 

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_id' not in vals:
                vals['user_id'] = self.env.user.id
            if 'company_id' not in vals:
                vals['company_id'] = self.env.company.id
            if 'name' not in vals:
                vals['name'] = "RENTA " + self.cens_anio_ejercicio + " - 5TA CAT - "
            if vals.get('cens_uit_procesado', 0.00) == 0.00:
                vals['cens_uit_procesado'] = self.env.company.x_studio_unidad_impositiva_tributaria
            if vals.get('cens_sminim_proces', 0.00) == 0.00:
                vals['cens_sminim_proces'] = self.env.company.x_studio_sueldo_minimo
            if 'cens_fech_registro' not in vals:
                vals['cens_fech_registro'] = fields.Date.context_today(self)
        return super(renta_quinta_Custom, self).create(vals_list)
    
    @api.model
    def traslada_retenciones_finales(self):        
        lines = self.cens_renta_quinta_id.renta_detail_ids
        retencion_mesual  = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
        for line in lines:
            if (line.name == 'RETENCIÓN MENSUAL'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    valor_retencion = getattr(line, w_nombre_campo, 0)     # LEE contenido de la línea actual
                    retencion_mesual[x_mes-1] = valor_retencion 
                    # setattr(line, w_nombre_campo, resultado)     Guardamos el resultado en la línea actual

    # -----------------------------------------
    # HABILITA ACCESO A VER RENTA 5TA CAT
    # -----------------------------------------
    def activa_renta_ficha_empleado(self):
        for record in self:
            w_acum_renta_anual = record.cens_reten_tot
            # --------------------------------------------
            # BUSCA AL EMPLEADO Y ACTUALIZA SU FICHA 
            # Activa check para acceso a ver Renta 5ta.
            # --------------------------------------------
            if record.employee_id:
                record.employee_id.write({'x_studio_sujeto_a_renta_5cat': w_acum_renta_anual > 0})
                _logger.info(f'Actualizada Ficha empleado ID: {record.employee_id.id} con CHECK renta 5ta: {"Verdad" if w_acum_renta_anual > 0 else "Falso"}')
            else:
                _logger.info('No hay empleado asociado a este registro')

    # ------------------------------
    # ACCION PARA EL BOTÓN RELLENAR
    # ------------------------------
    def action_rellena_datos(self):
        self.carga_rellena_datos()
        self.carga_rellena_datos_nr()
        self.activa_renta_ficha_empleado()

    # ------------------------------
    # ACCION PARA TRASLADAR DATOS
    # ------------------------------
    def action_traslada_datos(self):
        self.pasa_noremurativo_datos()
        self.carga_rellena_datos()


    # -----------------------------------------------
    # ACCION PARA GENERAR PROYECTADO DE 5TA A 
    #        LOS EMPLEADOS MARCADOS CON CHECK
    # -----------------------------------------------
    def action_genera_con_check_renta(self):
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
            ('x_studio_estado_contrato', '=', 'open')   # , ('x_studio_sujeto_a_renta_5cat', '=', True)
        ]
        
        # Obtener todas los Empleados con 5ta (InMemory)
        personal = self.env['hr.employee'].search(domain)
        
        _logger.info('INGRESANDO A CREAR DICCIONARIOS')
        w_fila = 0
        # Procesar cada boleta y extraer la información
        for empleado in personal:
            w_fila += 1
            # Verificar si ya existe un registro para este empleado en el año ejercicio
            existing_record = self.env['hr.payslip.renta_quinta'].search([
                ('employee_id', '=', empleado.id),
                ('cens_nano_ejercicio', '=', w_AñoEje)
            ], limit=1)
            
            # Si no existe un registro, crear uno nuevo
            if not existing_record:
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

    # -----------------------------------------------
    # ACCION PARA TRASLADA DATOS DESDE BOLETAS
    # -----------------------------------------------
    def action_traslada_boletas(self):
        self.carga_datos_desde_boletas()

    # -----------------------------------------------
    # EXTRAE DATOS DESDE LAS BOLETAS DE CADA MES
    # -----------------------------------------------
    def carga_datos_desde_boletas(self):
        for record in self:
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025
            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else:
                año_ingreso = 2025
                mes_ingreso = 1
        # ----------------------------------------------------------
        # EXTRACCIÓN DE LOS VALORES DE LOS CAMPOS DE LAS BOLETAS
        # Crea un diccionario patra cada campo extraido.
        # ----------------------------------------------------------
        # Buscar las boletas del empleado para el año especificado
        domain = [
            ('employee_id', '=', record.employee_id.id),
            ('date_from', '>=', f'{w_AñoEje}-01-01'),
            ('date_to', '<=', f'{w_AñoEje}-12-31'),
            ('state', 'in', ['draft', 'verify', 'done', 'paid'])
        ]
        
        # Obtener todas las boletas del año (InMemory)
        payslips = self.env['hr.payslip'].search(domain)
        
        # Crear un diccionario para almacenar los valores por mes
        sueldobasico_por_mes = {mes: 0.00 for mes in range(1, 13)}
        impmovilidad_por_mes = {mes: 0.00 for mes in range(1, 13)}
        impalimentac_por_mes = {mes: 0.00 for mes in range(1, 13)}
        impeducacion_por_mes = {mes: 0.00 for mes in range(1, 13)}
        imputilidade_por_mes = {mes: 0.00 for mes in range(1, 13)}

        congocehaber_por_mes = {mes: 0.00 for mes in range(1, 13)}
        lic_fallecim_por_mes = {mes: 0.00 for mes in range(1, 13)}
        lic_paternid_por_mes = {mes: 0.00 for mes in range(1, 13)}
        bonif_cumpli_por_mes = {mes: 0.00 for mes in range(1, 13)}
        descans_medi_por_mes = {mes: 0.00 for mes in range(1, 13)}
        bonif_feriad_por_mes = {mes: 0.00 for mes in range(1, 13)}
        horas_extras_por_mes = {mes: 0.00 for mes in range(1, 13)}
        
        _logger.info('INGRESANDO A CREAR DICCIONARIOS')
        # Procesar cada boleta y extraer la información
        for payslip in payslips:
            # Determinar el mes de la boleta
            mes_boleta = payslip.date_from.month
            _logger.info(f'EXTRAE VALOR de Boleta Mes: {mes_boleta} ')

            # Extraer información de SUELDO BÁSICO del mes
            sueldobasico_valor = payslip.x_studio_en_basico or 0.00
            sueldobasico_por_mes[mes_boleta] += sueldobasico_valor

            # Extraer información de MOVILIDAD del mes
            impmovilidad_valor = payslip.x_studio_en_vale_movilidad or 0.00
            impmovilidad_por_mes[mes_boleta] += impmovilidad_valor

            # Extraer información de ALIMENTACION del mes
            impalimentac_valor = payslip.x_studio_en_vale_alimentacion or 0.00
            impalimentac_por_mes[mes_boleta] += impalimentac_valor

            # Extraer información de EDUCACION del mes
            impeducacion_valor = payslip.x_studio_en_bonificacion_educacion or 0.00
            impeducacion_por_mes[mes_boleta] += impeducacion_valor

            # Extraer información de UTILIDADES del mes
            imputilidade_valor = payslip.x_studio_en_utilidades_voluntarias or 0.00
            imputilidade_por_mes[mes_boleta] += imputilidade_valor

            #-----------------------------------------------------------------

            # Extraer información de Con Goce Haber
            congocehaber_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            congocehaber_por_mes[mes_boleta] += congocehaber_valor

            # Extraer información de Licencia Fallecimiento
            lic_fallecim_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            lic_fallecim_por_mes[mes_boleta] += lic_fallecim_valor

            # Extraer información de Licencia x Paternidad
            lic_paternid_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            lic_paternid_por_mes[mes_boleta] += lic_paternid_valor

            # Extraer información de Bonificación x Cumplimiento
            bonif_cumpli_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            bonif_cumpli_por_mes[mes_boleta] += bonif_cumpli_valor

            # Extraer información de Dencanso Médico
            descans_medi_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            descans_medi_por_mes[mes_boleta] += descans_medi_valor

            # Extraer información de Bonific. x Feriados
            bonif_feriad_valor = payslip.x_studio_en_licencia_con_ghaber or 0.00
            bonif_feriad_por_mes[mes_boleta] += bonif_feriad_valor
            
            # Extraer información de Horas Extras
            horas_extras_valor = payslip.x_studio_en_horas_extras or 0.00
            horas_extras_por_mes[mes_boleta] += horas_extras_valor

        # ----------------------------------------------------------
        # POSICIONA EL LOS DATOS ENCONTRADOS EN NUESTRA MATRIX
        # ----------------------------------------------------------
        #lines  = self.renta_detail_ids
        #for line in lines:
        #    if (line.name == 'Sueldo Básico del mes'):
        #        for x_mes in range(1, 13):
        #            w_nombre_campo = self.mes_literal(x_mes).lower() 
        #            w_conten_campo = sueldobasico_por_mes[x_mes] #-- Asigna Dato
        #            _logger.info(f'Sueldo Básico del Mes: {x_mes} Importe: {w_conten_campo} ') 
        #            if año_ingreso < w_AñoEje: 
        #                w_importe_dato = w_conten_campo
        #            elif año_ingreso == w_AñoEje: 
        #                if x_mes < mes_ingreso:         
        #                    w_importe_dato = 0
        #                else:                           
        #                    w_importe_dato = w_conten_campo
        #            else:                               
        #                w_importe_dato = 0
        #            if (sueldobasico_por_mes[x_mes] > 0):
        #                setattr(line, w_nombre_campo, w_importe_dato)

        lines  = self.nremu_detail_ids  #---- Habilita tabla NO REMUNERATIVOS (nremu)
        for line in lines:
            if (line.name == 'Movilidad'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = impmovilidad_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Movilidad del Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    if (impmovilidad_por_mes[x_mes] > 0):
                        setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Alimentación'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = impalimentac_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Alimentación del Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    if (impalimentac_por_mes[x_mes] > 0):
                        setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Bonific. x Educación'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = impeducacion_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Educación del Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    if (impeducacion_por_mes[x_mes] > 0):
                        setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Utilidades Voluntarias'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = imputilidade_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Utilidades del Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    if (imputilidade_por_mes[x_mes] > 0):
                        setattr(line, w_nombre_campo, w_importe_dato)

            # ----------------------------------------------------------

            if (line.name == 'Lic.con Goce Haber'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = congocehaber_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Lic.con Goce Haber Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Lic.x Fallecimiento'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = lic_fallecim_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Lic.x Fallecimiento Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Lic.x Paternidad'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = lic_paternid_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Lic.x Paternidad Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Bonific.x Cumplimiento'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = bonif_cumpli_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Bonific.x Cumplimiento Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Descanso Médico'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = descans_medi_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Deccanso Médico Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Feriados'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    w_conten_campo = bonif_feriad_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Feriados Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Horas Extras'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    w_conten_campo = horas_extras_por_mes[x_mes]
                    _logger.info(f'Horas Extras Mes: {x_mes} Importe: {w_conten_campo} ')
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso: 
                            w_importe_dato = 0
                        else:        
                            w_importe_dato = w_conten_campo
                    else:    
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)


    # ----------------------------------
    # ACCION PARA EL BOTÓN RELLENAR NR
    # ----------------------------------
    def carga_rellena_datos_nr(self):
        for record in self:
            w_movili = record.contract_movili
            w_alimen = record.contract_alimen
            w_bonifi = record.contract_bonifi
            w_utilid = record.contract_utilid
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025

            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else:
                año_ingreso = 2025     
                mes_ingreso = 1

        lines  = self.nremu_detail_ids      #-- Habilita tabla NO REMUNERATIVOS (nremu)
        for line in lines:
            if (line.name == 'Movilidad'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_movili
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_movili
                    else:                               
                        w_importe_dato = 0
                    #w_importe_dato = w_movili
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Alimentación'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_alimen
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_alimen
                    else:                               
                        w_importe_dato = 0
                    #w_importe_dato = w_alimen
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Bonific. x Educación'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_bonifi
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_bonifi
                    else:                               
                        w_importe_dato = 0
                    #w_importe_dato = w_bonifi
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Utilidades Voluntarias'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_utilid
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_utilid 
                    else:                               
                        w_importe_dato = 0
                    #w_importe_dato = w_utilid
                    setattr(line, w_nombre_campo, w_importe_dato)
        pass

    # ------------------------------
    # TRASLADA DATOS A MATRIZ
    # ------------------------------
    def pasa_noremurativo_datos(self):
        for record in self:
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025
            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else: 
                año_ingreso = 2025
                mes_ingreso = 1

        lines  = self.renta_detail_ids
        for line in lines:
            if (line.name == 'Conceptos No Remunerativos'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    # Extra Datos acumylados CNR
                    w_acumulado_CNR = self.calcula_total_CNR(x_mes)
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_acumulado_CNR
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_acumulado_CNR
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, (w_importe_dato * 12))
    
    # ------------------------------
    # FUNCIÓN CALCULA CNR
    # ------------------------------   
    #@staticmethod
    def calcula_total_CNR(self, w_mes):
        for record in self:
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025
            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else:
                año_ingreso = 2025
                mes_ingreso = 1
        w_acumula_impo = 0.00
        lines = self.nremu_detail_ids
        for line in lines:
            w_nombre_campo = self.mes_literal(w_mes).lower()
            w_import_campo = getattr(line, w_nombre_campo, 0.00)  # Obtener el valor del mes
            
            if año_ingreso < w_AñoEje: 
                w_importe_dato = w_import_campo
            elif año_ingreso == w_AñoEje: 
                if w_mes < mes_ingreso:         
                    w_importe_dato = 0
                else:                           
                    w_importe_dato = w_import_campo
            else:                               
                w_importe_dato = 0
            w_acumula_impo += w_importe_dato

        return w_acumula_impo
    
    # ------------------------------
    # CARGA DATOS A RELLENAR
    # ------------------------------
    def carga_rellena_datos(self):
        for record in self:
            w_basico_oficia = record.cens_sminim_proces
            w_sueldo_basico = record.contract_wage
            w_extrae_asigfam = record.employee_id.x_studio_asignacin_familiar_1
            if (w_extrae_asigfam and (w_extrae_asigfam > 0)):
                w_asigna_famili = w_basico_oficia * w_extrae_asigfam if w_basico_oficia>0 else 0.00      #--- Calcula Asignación Familiar
            else:
                w_asigna_famili = 0.00
            w_importe_uit   = record.cens_uit_procesado 
            w_Ingres = record.contract_date_ingreso
            w_AñoEje = int(record.cens_anio_ejercicio) if record.cens_anio_ejercicio else 2025
            if w_Ingres:
                año_ingreso = w_Ingres.year     #-- Obtener el año y mes de ingreso
                mes_ingreso = w_Ingres.month
            else:
                año_ingreso = 2025     #-- Obtener el año y mes de ingreso QUIQUE
                mes_ingreso = 1

        # ----------------------------------------------------------------
        domain = [
            ('employee_id', '=', record.employee_id.id),
            ('date_from', '>=', f'{w_AñoEje}-01-01'),
            ('date_to', '<=', f'{w_AñoEje}-12-31'),
            ('state', 'in', ['draft', 'verify', 'done', 'paid'])
        ]
        
        # Obtener todas las boletas del año (InMemory)
        payslips = self.env['hr.payslip'].search(domain)
        
        # Crear un diccionario para almacenar los valores por mes
        sueldobasico_por_mes = {mes: 0.00 for mes in range(1, 13)}
        w_tipo_empleado = "NONE"
        
        for payslip in payslips:
            # Determinar el mes de la boleta
            mes_boleta = payslip.date_from.month
            w_tipo_empleado = payslip.x_studio_tipo_planilla
            _logger.info(f'EXTRAE VALOR de Boleta Mes: {mes_boleta} ')

            # Extraer información de SUELDO BÁSICO del mes
            sueldobasico_valor = payslip.x_studio_en_basico or 0.00
            sueldobasico_por_mes[mes_boleta] += sueldobasico_valor
        # ----------------------------------------------------------------

        lines  = self.renta_detail_ids
        for line in lines:
            if (line.name == 'Sueldo Básico del mes'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    w_conten_campo = sueldobasico_por_mes[x_mes] #-- Asigna Dato
                    _logger.info(f'Sueldo Básico del Mes: {x_mes} Importe: {w_conten_campo} ') 
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_conten_campo
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_conten_campo
                    else:                               
                        w_importe_dato = 0
                    if (w_tipo_empleado == 'INTE'):
                        if (sueldobasico_por_mes[x_mes] > 0):
                            setattr(line, w_nombre_campo, w_importe_dato)
                        else: 
                            setattr(line, w_nombre_campo, w_sueldo_basico)
                    else:
                        setattr(line, w_nombre_campo, w_sueldo_basico)
        
            if (line.name == 'Asignación Famiiar'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    if año_ingreso < w_AñoEje: 
                        w_importe_dato = w_asigna_famili
                    elif año_ingreso == w_AñoEje: 
                        if x_mes < mes_ingreso:         
                            w_importe_dato = 0
                        else:                           
                            w_importe_dato = w_asigna_famili
                    else:                               
                        w_importe_dato = 0
                    setattr(line, w_nombre_campo, w_importe_dato)

            if (line.name == 'Número de meses que faltan'):
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, 13-x_mes)

            if (line.name == 'REMUNERACIÓN PROYECTADA'):
                # Buscamos primero las líneas que necesitamos
                sueldo_basico_line = next((l for l in lines if l.name == 'Sueldo Básico del mes'), None)
                asignacion_familiar_line = next((l for l in lines if l.name == 'Asignación Famiiar'), None)
                meses_faltan_line = next((l for l in lines if l.name == 'Número de meses que faltan'), None)

                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    
                    # Obtenemos los valores de cada línea para el mes actual
                    valor_sueldo = getattr(sueldo_basico_line, w_nombre_campo, 0)
                    valor_asignacion = getattr(asignacion_familiar_line, w_nombre_campo, 0)
                    meses_restantes = getattr(meses_faltan_line, w_nombre_campo, 0)
                    
                    # Calculamos: (Sueldo + Asignación) * Meses restantes
                    resultado = (valor_sueldo + valor_asignacion) * meses_restantes
                    
                    # Guardamos el resultado en la línea actual
                    setattr(line, w_nombre_campo, resultado)

            if (line.name == 'Gratificación Ordinaria Julio'):
                # Buscamos primero las líneas que necesitamos
                sueldo_basico_line = next((l for l in lines if l.name == 'Sueldo Básico del mes'), None)
                asignacion_familiar_line = next((l for l in lines if l.name == 'Asignación Famiiar'), None)

                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    
                    # Obtenemos los valores de cada línea para el mes actual
                    valor_sueldo = getattr(sueldo_basico_line, w_nombre_campo, 0)
                    valor_asignacion = getattr(asignacion_familiar_line, w_nombre_campo, 0)
                    
                    # Calculamos: (Sueldo + Asignación)
                    #resultado = (valor_sueldo + valor_asignacion)
                    resultado = (w_sueldo_basico + valor_asignacion)
                    
                    # Guardamos el resultado en la línea actual
                    setattr(line, w_nombre_campo, resultado)

            if (line.name == 'Gratificación Ordinaria Diciembre'):
                # Buscamos primero las líneas que necesitamos
                sueldo_basico_line = next((l for l in lines if l.name == 'Sueldo Básico del mes'), None)
                asignacion_familiar_line = next((l for l in lines if l.name == 'Asignación Famiiar'), None)

                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    
                    # Obtenemos los valores de cada línea para el mes actual
                    valor_sueldo = getattr(sueldo_basico_line, w_nombre_campo, 0)
                    valor_asignacion = getattr(asignacion_familiar_line, w_nombre_campo, 0)
                    
                    # Calculamos: (Sueldo + Asignación)
                    #resultado = (valor_sueldo + valor_asignacion)
                    resultado = (w_sueldo_basico + valor_asignacion)
                    
                    # Guardamos el resultado en la línea actual
                    setattr(line, w_nombre_campo, resultado)

            if (line.name == 'Bonificacion Gratificac Julio'):
                gratificación_julio_line = next((l for l in lines if l.name == 'Gratificación Ordinaria Julio'), None)
                for x_mes in range(6, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    valor_sueldo = round(getattr(gratificación_julio_line, w_nombre_campo, 0) * 0.09,2)
                    setattr(line, w_nombre_campo, valor_sueldo)

            if (line.name == 'Bonificacion Gratificac Diciembre'):
                gratificación_diciembre_line = next((l for l in lines if l.name == 'Gratificación Ordinaria Diciembre'), None)
                x_mes = 12
                w_nombre_campo = self.mes_literal(x_mes).lower()
                valor_sueldo = round(getattr(gratificación_diciembre_line, w_nombre_campo, 0) * 0.09,2)
                setattr(line, w_nombre_campo, valor_sueldo)

            if (line.name == 'Remuneración Percibida meses anteriores'):
                sueldo_basico_line = next((l for l in lines if l.name == 'Sueldo Básico del mes'), None)
                asignacion_familiar_line = next((l for l in lines if l.name == 'Asignación Famiiar'), None)
                participacion_utilidades_line = next((l for l in lines if l.name == 'Participación Utilidades recibidas en el mes'), None)
                remuneraciones_percibidas_line = next((l for l in lines if l.name == 'Remuneración Percibida meses anteriores'), None)
                for x_mes in range(1, 13):
                    if (x_mes > 1):
                        w_campo_xmes_actual = self.mes_literal(x_mes).lower()
                        w_campo_xmes_anteri = self.mes_literal(x_mes-1).lower()
                        
                        # Obtenemos los valores de cada línea para el mes ANTERIOR
                        valor_sueldo = getattr(sueldo_basico_line, w_campo_xmes_anteri, 0)
                        valor_asignacion = getattr(asignacion_familiar_line, w_campo_xmes_anteri, 0)
                        valor_utilidades = getattr(participacion_utilidades_line, w_campo_xmes_anteri, 0)
                        valor_percibidas = getattr(remuneraciones_percibidas_line, w_campo_xmes_anteri, 0)
                        
                        # Calculamos: (Sueldo + Asignación)
                        resultado = (valor_sueldo + valor_asignacion + valor_utilidades) + valor_percibidas
                        
                        # Guardamos el resultado en la línea actual
                        setattr(line, w_campo_xmes_actual, resultado)

            if (line.name == 'Deducción 7 UIT'):
                w_importe_uit = w_importe_uit
                for x_mes in range(1, 13):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    valor_uit = round(w_importe_uit * 7,2)
                    setattr(line, w_nombre_campo, valor_uit)

        # -----------------------------------------
        # LLAMA A TOTALIZA LAS COLUMNAS
        # -----------------------------------------
        self.totaliza_colunna_mensual()
            

    # ---------------------------------------
    # PROCEDIMIENTO PARA TOTALIZAR COLUMNA 
    # ---------------------------------------
    def totaliza_colunna_mensual(self):
        for record in self:
            w_sueldo_basico = record.contract_wage
            w_asigna_famili = record.cens_sueldo_minimo * 0.10
            w_importe_uit   = record.cens_uit_procesado
            w_tasa_impuesto = [0.08, 0.14, 0.17, 0.20, 0.30]
            w_denominador_retencion = [12, 12, 12, 9, 8, 8, 8, 5, 4, 4, 4, 1]
            w_total = 0.00
            record.write({'cens_reten_tot': w_total})

        w_retenciones_efectuadas = 0.00
        w_acum_ret_mensual1 = 0
        w_acum_ret_mensual2 = 0
        w_acum_ret_mensual3 = 0
        w_acum_ret_mensual4 = 0
        lines  = self.renta_detail_ids
        for x_mes in range(1, 13):
            w_remuneracion_mensual = 0.00
            w_impuesto_anual = 0.00
            w_impuesto_pagar = 0.00
            w_impuesto_neto  = 0.00
            w_acum_ret_mensual = 0.00

            w_acumula_total = 0.00
            w_renta_proyectada = 0.00
            w_7uits_deduccion  = 0.00
            w_renta_neta_proy  = 0.00
            w_rango1 = 0.00
            w_rango2 = 0.00
            w_rango3 = 0.00
            w_rango4 = 0.00
            w_rango5 = 0.00
            for line in lines:
                w_nombre_campo = self.mes_literal(x_mes).lower()  
                x_valor_campo = getattr(line, w_nombre_campo, 0.0)  
                
                if (line.name == 'Sueldo Básico del mes'):
                    w_remuneracion_mensual += x_valor_campo

                if (line.name == 'Asignación Famiiar'):
                    w_remuneracion_mensual += x_valor_campo

                if (line.name == 'REMUNERACIÓN PROYECTADA'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Gratificación Ordinaria Julio'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Gratificación Ordinaria Diciembre'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Bonificacion Gratificac Julio'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Bonificacion Gratificac Diciembre'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Vacaciones'):
                    w_acumula_total += x_valor_campo

                if (line.name == 'Conceptos No Remunerativos'):
                    w_acumula_total += x_valor_campo
            
                if (line.name == 'Remuneración Percibida meses anteriores'):
                    w_acumula_total += x_valor_campo                    

                # ------------------------------------------
                # TOTALIZA - RENTA ANUAL PROYECTADA
                # ------------------------------------------
                if (line.name == 'RENTA ANUAL PROYECTADA'):
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_acumula_total)
                    w_renta_proyectada = w_acumula_total

                if (line.name == 'Deducción 7 UIT'):
                    w_7uits_deduccion  = x_valor_campo

                # ------------------------------------------
                # TOTALIZA - RENTA NETA ANUAL PROYECTADA
                # ------------------------------------------
                if (line.name == 'Renta Neta Anual Proyectada'):
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    w_renta_neta_proy  = w_renta_proyectada - w_7uits_deduccion 
                    if (w_renta_neta_proy <= 0):
                         w_renta_neta_proy  = 0.00
                    setattr(line, w_nombre_campo, w_renta_neta_proy)
                
                # ------------------------------------------
                # RANGO-1 - HASTA 05 UIT
                # ------------------------------------------
                if (line.name == 'Tasa Hasta 05 UIT  (8%)'):
                    w_rango1 = 0.00
                    if (w_renta_neta_proy > (w_importe_uit * 5)):
                        w_rango1 = round((w_importe_uit * 5) * w_tasa_impuesto[0],2)
                    else:
                        w_rango1 = round(w_renta_neta_proy * w_tasa_impuesto[0],2)
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_rango1)

                # ------------------------------------------
                # RANGO-2 - HASTA 20 UIT
                # ------------------------------------------
                if (line.name == 'Tasa Hasta 20 UIT  (14%)'):
                    w_rango2 = 0.00
                    if ((w_renta_neta_proy-(w_importe_uit * 5)) > (w_importe_uit * 15)):
                        w_rango2 = round((w_importe_uit * 15) * w_tasa_impuesto[1],2)
                    else:
                        if ((w_renta_neta_proy-(w_importe_uit * 5)) <= 0.00):
                            w_rango2 = 0.00 
                        else:
                            if ((w_renta_neta_proy-(w_importe_uit * 5)) < (w_importe_uit * 15)):
                                w_rango2 = round((w_renta_neta_proy-(w_importe_uit * 5)) * w_tasa_impuesto[1],2)
                            else:
                                w_rango2 = 0.00
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_rango2)

                # ------------------------------------------
                # RANGO-3 - HASTA 35 UIT
                # ------------------------------------------
                if (line.name == 'Tasa Hasta 35 UIT  (17%)'):
                    w_rango3 = 0.00
                    if ((w_renta_neta_proy-(w_importe_uit * 20)) > (w_importe_uit * 15)):
                        w_rango3 = round((w_importe_uit * 15) * w_tasa_impuesto[2],2)
                    else:
                        if ((w_renta_neta_proy-(w_importe_uit * 20)) <= 0.00):
                            w_rango3 = 0.00 
                        else:
                            if ((w_renta_neta_proy-(w_importe_uit * 20)) < (w_importe_uit * 15)):
                                w_rango3 = round((w_renta_neta_proy-(w_importe_uit * 20)) * w_tasa_impuesto[2],2)
                            else:
                                w_rango3 = 0.00
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_rango3)

                # ------------------------------------------
                # RANGO-4 - HASTA 45 UIT
                # ------------------------------------------
                if (line.name == 'Tasa Hasta 45 UIT  (20%)'):
                    w_rango4 = 0.00
                    if ((w_renta_neta_proy-(w_importe_uit * 35)) > (w_importe_uit * 10)):
                        w_rango4 = round((w_importe_uit * 10) * w_tasa_impuesto[3],2)
                    else:
                        if ((w_renta_neta_proy-(w_importe_uit * 35)) <= 0.00):
                            w_rango4 = 0.00 
                        else:
                            if ((w_renta_neta_proy-(w_importe_uit * 35)) < (w_importe_uit * 10)):
                                w_rango4 = round((w_renta_neta_proy-(w_importe_uit * 35)) * w_tasa_impuesto[3],2)
                            else:
                                w_rango4 = 0.00
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_rango4)

                # ------------------------------------------
                # RANGO-5 - EXCESO 45 UIT
                # ------------------------------------------
                if (line.name == 'Tasa Exceso 45 UIT (30%)'):
                    w_rango5 = 0.00
                    if ((w_renta_neta_proy-(w_importe_uit * 45)) > 0.00):
                        w_rango5 = round((w_renta_neta_proy-(w_importe_uit * 45)) * w_tasa_impuesto[4],2)
                    else:
                        w_rango5 = 0.00
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    setattr(line, w_nombre_campo, w_rango5)

                # ------------------------------------------
                # TOTALIZA - IMPUESTO ANUAL
                # ------------------------------------------
                if (line.name == 'IMPUESTO ANUAL'):
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    w_importe_dato = w_rango1 + w_rango2 + w_rango3 + w_rango4 + w_rango5
                    w_impuesto_anual = w_importe_dato 
                    setattr(line, w_nombre_campo, w_importe_dato)

                # ------------------------------------------
                # TOTALIZA - RETENCIONES EFECTUADAS
                # ------------------------------------------
                if (line.name == 'Retenciones efectuadas'):
                    w_importe_dato = 0.00
                    w_nombre_campo = self.mes_literal(x_mes).lower()  
                    if (x_mes in [1,2,3]):
                        w_importe_dato = 0.00
                    elif (x_mes == 4):
                        w_importe_dato = w_acum_ret_mensual1     #--- Acumulado de ENE+FEB+MAR
                    elif (x_mes == 5):
                        w_importe_dato = w_acum_ret_mensual1 + w_acum_ret_mensual2
                        w_acum_ret_mensual1 = 0.00
                        w_acum_ret_mensual2 = 0.00
                    elif (x_mes in [6,7]):
                        w_importe_dato = w_retenciones_efectuadas
                    elif (x_mes == 8):
                        w_importe_dato = w_retenciones_efectuadas + w_acum_ret_mensual2
                    elif (x_mes == 9):
                        w_importe_dato = w_retenciones_efectuadas + w_acum_ret_mensual2
                        w_acum_ret_mensual3 = w_importe_dato
                    elif (x_mes == 10):
                        w_importe_dato = w_retenciones_efectuadas
                    elif (x_mes == 11):
                        w_importe_dato = w_retenciones_efectuadas
                    else:
                        w_importe_dato = w_acum_ret_mensual3 + w_acum_ret_mensual4

                    w_retenciones_efectuadas = w_importe_dato 
                    setattr(line, w_nombre_campo, w_importe_dato)

                # ------------------------------------------
                # TOTALIZA - IMPUESTO A PAGAR
                # ------------------------------------------
                if (line.name == 'IMPUESTO A PAGAR'):
                    w_nombre_campo = self.mes_literal(x_mes).lower() 

                    if (w_remuneracion_mensual == 0):
                        w_importe_dato = 0.00
                    elif (w_retenciones_efectuadas >  w_impuesto_anual):
                        w_importe_dato = w_impuesto_anual - w_retenciones_efectuadas
                    elif (w_impuesto_anual >  0):
                        w_importe_dato = w_impuesto_anual - w_retenciones_efectuadas
                    elif (w_impuesto_anual-w_retenciones_efectuadas == 0):
                        w_importe_dato = 0.00
                    w_impuesto_pagar = w_importe_dato
                    setattr(line, w_nombre_campo, w_importe_dato)

                # ---------------------------------------------------------
                # TOTALIZA - DENOMINADOR PARA EL CALCULO DE LA RETENCION
                # ---------------------------------------------------------
                if (line.name == 'Denominador para determinar Retención'):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    w_importe_dato = w_denominador_retencion[x_mes-1]
                    setattr(line, w_nombre_campo, w_importe_dato)

                # ---------------------------------------------------------
                # TOTALIZA - RETENCIÓN MENSUAL A PLICAR EN LA BOLETA
                # ---------------------------------------------------------
                if (line.name == 'RETENCIÓN MENSUAL'):
                    w_nombre_campo = self.mes_literal(x_mes).lower()
                    w_importe_dato = w_denominador_retencion[x_mes-1]

                    if (w_impuesto_pagar>0):
                        w_importe_dato = (w_impuesto_pagar / w_denominador_retencion[x_mes-1]) + w_impuesto_neto
                    elif ((w_impuesto_pagar + w_impuesto_neto)>0):
                        w_importe_dato = w_impuesto_pagar + w_impuesto_neto
                    else:
                        w_importe_dato = 0.00
                    w_importe_dato = round(w_importe_dato,0)
                    w_acum_ret_mensual += w_importe_dato
                    w_acum_ret_mensual1 += w_importe_dato 
                    #if (x_mes == 4):
                    #    w_acum_ret_mensual2 = w_acum_ret_mensual1
                    if (x_mes in [5,6,7]):
                        w_acum_ret_mensual2 += w_importe_dato
                    if (x_mes == 8):
                        w_acum_ret_mensual2 = w_importe_dato
                    if (x_mes in [9,10,11]):
                        w_acum_ret_mensual4 += w_importe_dato

                    setattr(line, w_nombre_campo, w_importe_dato)
                    
                    # --------------------------------------------
                    # TRASLADA EL TOTAL FINAL (Retención a pagar) 
                    # hacia el campo correspondiente QUIQUE
                    # --------------------------------------------
                    for record in self:
                        w_nombre_campo = "cens_reten_" + self.mes_literal(x_mes)[:3].lower()
                        record.write({w_nombre_campo: w_importe_dato})
                        w_total = record.cens_reten_tot + w_importe_dato    #-- Acumula Renta del Mes para Totalizar
                        record.write({'cens_reten_tot': w_total})
                        # --------------------------------------------
                        # BUSCA LA BOLETA DEL MES Y ACTUALIZA RENTA 
                        # Verifica primero que el mes esté disponible
                        # --------------------------------------------
                        if (x_mes>8):
                            boleta = self.env['hr.payslip'].search([
                                            ('employee_id', '=', record.employee_id.id),
                                            ('date_from', '=', f"{record.cens_nano_ejercicio}-{x_mes:02d}-01"),
                                            ('state', 'in', ['draft', 'verify'])  # Boletas en borrador o verificadas
                                        ], limit=1)

                                           # ('date_from', '>=', f"{record.cens_nano_ejercicio}-{x_mes:02d}-01"),
                                           # ('date_to', '<=', f"{record.cens_nano_ejercicio}-{x_mes:02d}-28"),

                            # Si encontramos la boleta, actualizamos el campo de renta 5ta
                            if boleta:
                                boleta.write({'x_studio_importe_renta_5ta': w_importe_dato})
                                _logger.info(f'Actualizada boleta ID: {boleta.id} con importe renta 5ta: {w_importe_dato}')
                            else:
                                _logger.info(f'No se encontró boleta para el empleado {record.employee_id.name} en el mes {x_mes}')
        

    # ------------------------------
    # ACCION PARA EL BOTÓN RETIRAR
    # ------------------------------
    def action_retirar_datos(self):
        lines  = self.renta_detail_ids
        for line in lines:
            for x_mes in range(1, 13):
                w_nombre_campo = self.mes_literal(x_mes).lower()  
                setattr(line, w_nombre_campo, 0.00)

    def mes_literal(self, nmes):
        w_mes = nmes
        if (w_mes == 1):
            w_mes_name = "enero"
        elif (w_mes == 2):
            w_mes_name = "febrero"
        elif (w_mes == 3):
            w_mes_name = "marzo"
        elif (w_mes == 4):
            w_mes_name = "abril"
        elif (w_mes == 5):
            w_mes_name = "mayo"
        elif (w_mes == 6):
            w_mes_name = "junio"
        elif (w_mes == 7):
            w_mes_name = "julio"
        elif (w_mes == 8):
            w_mes_name = "agosto"
        elif (w_mes == 9):
            w_mes_name = "setiembre"
        elif (w_mes == 10):
            w_mes_name = "octubre"
        elif (w_mes == 11):
            w_mes_name = "noviembre"
        elif (w_mes == 12):
            w_mes_name = "diciembre"
        else:
            w_mes_name = "ERR"
        return w_mes_name


class HrPayslipRentaQuintaDetail(models.Model):
    _name = 'hr.payslip.renta_quinta.detail'
    _description = 'Detalle de Renta de Quinta Categoría'

    renta_id = fields.Many2one('hr.payslip.renta_quinta', string='Renta Quinta', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    periodo = fields.Char('Periodo', default="2025")
    name = fields.Char('Detalle')
    enero = fields.Float('Enero')
    febrero = fields.Float('Febrero')
    marzo = fields.Float('Marzo')
    abril = fields.Float('Abril')
    mayo = fields.Float('Mayo')
    junio = fields.Float('Junio')
    julio = fields.Float('Julio')
    agosto = fields.Float('Agosto')
    setiembre = fields.Float('Setiembre')
    octubre = fields.Float('Octubre')
    noviembre = fields.Float('Noviembre')
    diciembre = fields.Float('Diciembre')

class HrPayslipRentaQuintaDetaNR(models.Model):
    _name = 'hr.payslip.renta_quinta.detanr'
    _description = 'Detalle de Conceptos No Remunerativos'

    renta_id = fields.Many2one('hr.payslip.renta_quinta', string='Renta Quinta', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    periodo = fields.Char('Periodo', default="2025")
    name = fields.Char('Detalle')
    enero = fields.Float('Enero')
    febrero = fields.Float('Febrero')
    marzo = fields.Float('Marzo')
    abril = fields.Float('Abril')
    mayo = fields.Float('Mayo')
    junio = fields.Float('Junio')
    julio = fields.Float('Julio')
    agosto = fields.Float('Agosto')
    setiembre = fields.Float('Setiembre')
    octubre = fields.Float('Octubre')
    noviembre = fields.Float('Noviembre')
    diciembre = fields.Float('Diciembre')

class HrPayslipRentaQuinta(models.Model):
    _inherit = 'hr.payslip.renta_quinta'
    
    nremu_detail_ids = fields.One2many(
        'hr.payslip.renta_quinta.detanr',
        'renta_id',
        string='Conceptos No Remunerativos'
    )

    renta_detail_ids = fields.One2many(
        'hr.payslip.renta_quinta.detail',
        'renta_id',
        string='Detalle de Renta'
    )

    @api.model
    def create(self, vals):
        record = super(HrPayslipRentaQuinta, self).create(vals)
        # Crear líneas predeterminadas
        default_lines1 = [
            'Movilidad',
            'Alimentación',
            'Bonific. x Educación',
            'Utilidades Voluntarias',
            'Lic.con Goce Haber',
            'Lic.x Fallecimiento',
            'Lic.x Paternidad',
            'Bonific.x Cumplimiento',
            'Descanso Médico',
            'Feriados',
            'Horas Extras'
        ]
        for line in default_lines1:
            self.env['hr.payslip.renta_quinta.detanr'].create({
                'renta_id': record.id,
                'name': line
            })

        default_lines2 = [
            'Sueldo Básico del mes',
            'Asignación Famiiar',
            'Número de meses que faltan',
            'REMUNERACIÓN PROYECTADA',
            'Gratificación Ordinaria Julio',
            'Gratificación Ordinaria Diciembre',
            'Bonificacion Gratificac Julio',
            'Bonificacion Gratificac Diciembre',
            'Vacaciones',
            'Conceptos No Remunerativos',
            'Remuneración Percibida meses anteriores',
            'RENTA ANUAL PROYECTADA',
            'Deducción 7 UIT',
            'Renta Neta Anual Proyectada',
            'Tasa Hasta 05 UIT  (8%)',
            'Tasa Hasta 20 UIT  (14%)',
            'Tasa Hasta 35 UIT  (17%)',
            'Tasa Hasta 45 UIT  (20%)',
            'Tasa Exceso 45 UIT (30%)',
            'Menos (Saldo a favor Ejerc. Anterior)',
            'IMPUESTO ANUAL',
            'Retenciones efectuadas',
            'IMPUESTO A PAGAR',
            'Denominador para determinar Retención',
            'RETENCIÓN MENSUAL'
        ]
        for line in default_lines2:
            self.env['hr.payslip.renta_quinta.detail'].create({
                'renta_id': record.id,
                'name': line
            })

        return record
    


