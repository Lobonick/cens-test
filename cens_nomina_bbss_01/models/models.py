from odoo import api, fields, models
from datetime import datetime
from odoo.exceptions import UserError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_recalcula_bbss(self, vals):
        """
        CALCULA LOS VALORES PARA: 
        - Vacaciones Truncas
        - CTS Truncas
        - Gratificaciones Truncas
        - Bonific. Gratificaciones

        """
        w_fecha = datetime().date

    def action_recalcula_en_datos(self, vals):
        #
        # Activa y desactiva el RECÁLCULO
        #
        #for rec in self:
        #    rec.write({'x_studio_en_recalcular': not rec.x_studio_en_recalcular})      #----- Para funciona en creación individual
        #    rec.recompute()
        w_fecha = datetime().date
