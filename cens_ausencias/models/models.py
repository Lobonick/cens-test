from odoo import api, fields, models
from datetime import timedelta

class HrEmployeeCustom(models.Model):
    _inherit = 'hr.leave'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    x_cens_codiden = fields.Char(string='CÓDIGO:', readonly=True)
 
    # ------------------------------
    # CALCULA EL CORRELATIVO
    # ------------------------------
    def calcula_correlativo(self, record):
        for record in self:
            record.x_cens_codiden = "AU-"
        return True
