from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta


class crm_lead_Custom(models.Model):
    _inherit = 'crm.lead'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    cens_fecha_actual = fields.Datetime(string='Fecha Actual:', readonly=True, existing_field=True)
    cens_conta_visita = fields.Integer(string='Visitas:', readonly=True, default=0, existing_field=True)
    cens_solicitudes_gasto = fields.Many2many(
        comodel_name='hr.expense', 
        relation='x_crm_lead_hr_expense_rel', 
        column1='crm_lead_id', 
        column2='hr_expense_id', 
        string='Solicitudes Gasto:',
        default=lambda self: self._default_cens_solicitudes_gasto(),
        existing_field=True )
     
    # ------------------------------
    # SOLICITA GASTO
    # ------------------------------
    def solicita_gasto(self):
        w_correlativo = ""
        return True
    
    # -------------------------------
    # ACCION PRUEBA
    # -------------------------------
    def export_to_spreadsheet(self):
        w_dato = "LLEGÓ..."
        pass

    # ------------------------------
    # CARGA SOLICITUDES DE GASTO
    # ------------------------------
    def _default_cens_solicitudes_gasto(self):
        # for record in self:
        #    record.x_cens_id_oportunidad = self.env.context.get('active_id')
        active_solicitudes = self.env['hr.expense'].search([('x_cens_oportunidad_id', '=', self.env.context.get('active_id'))], limit=1)
        if active_solicitudes:
            return [(6, 0, active_solicitudes.cens_solicitudes_gasto.ids)]
        return False

    def inicializa_variables(self):
        for record in self:
            current_datetime = datetime.now()
            record.x_studio_nro_agrupamiento = ("ON-"+("000000"+str(record.id-92))[-6:]) if record.x_studio_nro_agrupamiento in ('*','ON-') else record.x_studio_nro_agrupamiento
            record.name = "CÓDIGO: " + record.x_studio_nro_agrupamiento
            record.x_studio_usuario_actual = self.env.context.get("uid")
            record.cens_conta_visita += 1
            record.cens_fecha_actual = current_datetime

    def create(self, vals):
        record = super(crm_lead_Custom, self).create(vals)
        record.inicializa_variables()
        return record


#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        for record in self:
#            record.x_hora = record.date_from

#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Calcula el código correlativo
#        w_correlativo = ""
#        for record in self:
#            w_correlativo = ("000000"+str(record.id))[-6:]  
#            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo

#    def genera_codigo_correlativo(self):
#        w_correlativo = ""
#        for record in self:
#            w_correlativo = ("000000"+str(record.id))[-6:]  
#            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo
#        return True


#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Obtiene la hora
#        for record in self:
#            record.x_hora = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

