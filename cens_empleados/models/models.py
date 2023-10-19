from odoo import api, fields, models
from datetime import timedelta

class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    x_cens_id_empleado = fields.Integer(string='ID del Empleado activo.', readonly=True)
    x_cens_vaca_anio = fields.Selection([('2019', '2019'), ('2020', '2020'), ('2021', '2021'), ('2022', '2022'), ('2023', '2023'), ('2024', '2024')], string='Año de Vacaciones', default='2023')
    x_cens_vacaciones_tomadas = fields.Many2many(
        comodel_name='hr.leave', 
        relation='x_hr_employee_hr_leave_rel', 
        column1='hr_employee_id', 
        column2='hr_leave_id', 
        string='VACACIONES TOMADAS:',
        default=lambda self: self._default_x_cens_vacaciones_tomadas() )
    x_cens_vaca_adeudadas = fields.Integer(string="Adeudadas:")
    x_cens_vaca_enero = fields.Integer(string="Enero", readonly=True)
    x_cens_vaca_febrero = fields.Integer(string="Febrero", readonly=True)
    x_cens_vaca_marzo = fields.Integer(string="Marzo", readonly=True)
    x_cens_vaca_abril = fields.Integer(string="Abril", readonly=True)
    x_cens_vaca_mayo = fields.Integer(string="Mayo", readonly=True)
    x_cens_vaca_junio = fields.Integer(string="Junio", readonly=True)
    x_cens_vaca_julio = fields.Integer(string="Julio", readonly=True)
    x_cens_vaca_agosto = fields.Integer(string="Agosto", readonly=True)
    x_cens_vaca_setiembre = fields.Integer(string="Septiembre", readonly=True)
    x_cens_vaca_octubre = fields.Integer(string="Octubre", readonly=True)
    x_cens_vaca_noviembre = fields.Integer(string="Noviembre", readonly=True)
    x_cens_vaca_diciembre = fields.Integer(string="Diciembre", readonly=True)
    x_cens_vaca_total = fields.Integer(string="TOTAL ASIGNADO:", readonly=True)
    

    # ------------------------------
    # ACCION PARA EL BOTÓN ACOMODAR
    # ------------------------------
    def action_custom_button(self):
        for record in self:
            self.blanquea_campos(record)
            record.x_cens_id_empleado = record.id

            lines  = self.x_cens_vacaciones_tomadas
            w_acum = 0
            w_anio = int(record.x_cens_vaca_anio)
            for line in lines:
                w_fech_ini = line.date_from 
                w_fech_fin = line.date_to
                # Si las fechas son del mismo mes
                if (w_fech_ini.month == w_fech_fin.month):
                    w_dias_tot = (w_fech_fin - w_fech_ini).days + 1
                    if (w_fech_ini.year == w_anio):
                        self.acumula_en_mes(record, w_fech_ini.month, w_dias_tot)
                else:
                    # Si las fechas son de diferentes meses
                    # my_date = fields.Date.today()  # Obtener la fecha actual
                    last_day_of_first_month = w_fech_ini.replace(day=28) + timedelta(days=4)
                    last_day_of_first_month = last_day_of_first_month.replace(day=1) - timedelta(days=1)
                    first_day_of_last_month = w_fech_fin.replace(day=1)
                    w_dias_mes1 = (last_day_of_first_month - w_fech_ini).days + 1
                    w_dias_mes2 = (w_fech_fin - first_day_of_last_month).days + 1

                    if (w_fech_ini.year == w_anio):
                        self.acumula_en_mes(record, w_fech_ini.month, w_dias_mes1)
                    if (w_fech_fin.year == w_anio):
                        self.acumula_en_mes(record, w_fech_fin.month, w_dias_mes2)
                    w_dias_tot = w_dias_mes1 + w_dias_mes2
            self.totaliza_campos(record)
        pass
    
    # -------------------------------
    # ACCION PARA EL BOTÓN BLANQUEAR
    # -------------------------------
    def action_custom_button_blanquea(self):
        for record in self:
            self.blanquea_campos(record)
        pass

    # ------------------------------
    # INICIALIZA LOS CAMPOS
    # ------------------------------
    def blanquea_campos(self, record):
        for record in self:
            record.x_cens_vaca_enero = 0
            record.x_cens_vaca_febrero = 0
            record.x_cens_vaca_marzo = 0
            record.x_cens_vaca_abril = 0
            record.x_cens_vaca_mayo = 0
            record.x_cens_vaca_junio = 0
            record.x_cens_vaca_julio = 0
            record.x_cens_vaca_agosto = 0
            record.x_cens_vaca_setiembre = 0
            record.x_cens_vaca_octubre = 0
            record.x_cens_vaca_noviembre = 0
            record.x_cens_vaca_diciembre = 0
            record.x_cens_vaca_total = record.x_cens_vaca_adeudadas
        return True

    # ------------------------------------
    # ACUMULA DIAS SEGÚN EL MES INDICADO
    # ------------------------------------
    def acumula_en_mes(self, record, nmes, ndias):
        w_nmes = nmes
        w_ndia = ndias
        w_result = True
        for record in self:
            if (w_nmes == 1):
                record.x_cens_vaca_enero += w_ndia         
            elif (w_nmes == 2):
                record.x_cens_vaca_febrero += w_ndia
            elif (w_nmes == 3):
                record.x_cens_vaca_marzo += w_ndia
            elif (w_nmes == 4):
                record.x_cens_vaca_abril += w_ndia
            elif (w_nmes == 5):
                record.x_cens_vaca_mayo += w_ndia
            elif (w_nmes == 6):
                record.x_cens_vaca_junio += w_ndia
            elif (w_nmes == 7):
                record.x_cens_vaca_julio += w_ndia
            elif (w_nmes == 8):
                record.x_cens_vaca_agosto += w_ndia
            elif (w_nmes == 9):
                record.x_cens_vaca_setiembre += w_ndia
            elif (w_nmes == 10):
                record.x_cens_vaca_octubre += w_ndia
            elif (w_nmes == 11):
                record.x_cens_vaca_noviembre += w_ndia
            elif (w_nmes == 12):
                record.x_cens_vaca_diciembre += w_ndia
            else:
                w_result = False
        return w_result

    # ------------------------------
    # CALCULA EL TOTALIZADO
    # ------------------------------
    def totaliza_campos(self, record):
        for record in self:
            record.x_cens_vaca_total  = record.x_cens_vaca_adeudadas
            record.x_cens_vaca_total += record.x_cens_vaca_enero + record.x_cens_vaca_febrero + record.x_cens_vaca_marzo
            record.x_cens_vaca_total += record.x_cens_vaca_abril + record.x_cens_vaca_mayo + record.x_cens_vaca_junio
            record.x_cens_vaca_total += record.x_cens_vaca_julio + record.x_cens_vaca_agosto + record.x_cens_vaca_setiembre
            record.x_cens_vaca_total += record.x_cens_vaca_octubre + record.x_cens_vaca_noviembre + record.x_cens_vaca_diciembre
        return True

    # ------------------------------
    # CARGA LAS VACACIONES TOMADAS
    # ------------------------------
    def _default_x_cens_vacaciones_tomadas(self):
        for record in self:
            record.x_cens_id_empleado = self.env.context.get('active_id')

        active_employee = self.env['hr.leave'].search([('employee_id', '=', self.env.context.get('active_id'))], limit=1)
        if active_employee:
            return [(6, 0, active_employee.x_cens_vacaciones_tomadas.ids)]
        return False

