from odoo import api, fields, models
from datetime import datetime
# from datetime import timedelta

class HrLeaveCustom(models.Model):
    _inherit = 'hr.leave'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    x_cens_codiden = fields.Char(string='CÓDIGO:', readonly=True)
    x_cens_hora = fields.Datetime(string='Hora:', readonly=True)

    @api.onchange('date_from')
    def _onchange_date_from(self):
        for record in self:
            record.x_hora = record.date_from

    @api.onchange('date_from')
    def _onchange_date_from(self):
        # Calcula el código correlativo
        w_correlativo = ""
        for record in self:
            w_correlativo = ("000000"+str(record.id))[-6:]  
            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo

    # ------------------------------
    # CALCULA EL CORRELATIVO
    # ------------------------------
    def calcula_correlativo(self):
        w_correlativo = ""
        for record in self:
            w_correlativo = ("000000"+str(record.id))[-6:]  
            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo
        return True


#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Obtiene la hora
#        for record in self:
#            record.x_hora = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

