# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

from odoo import models, fields, api
import logging
import datetime
# import random
# import string
# from datetime import datetime
# from datetime import timedelta

_logging = logging.getLogger(__name__)


class HrLeaveCustom(models.Model):
    _inherit = 'hr.leave'

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    x_cens_codiden = fields.Char(string='CÓDIGO:', readonly=True, existing_field=True)

    # ------------------------------
    # CALCULA EL CORRELATIVO
    # ------------------------------
    def calcula_correlativo(self):
        w_correlativo = ""
        for record in self:
            w_correlativo = ("000000"+str(record.id))[-6:]  
            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo
        pass

#    @api.depends('name') 
#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Obtiene la hora
#        for record in self:
#            record.x_hora = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
#        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
#        record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo + "-" + random_chars

