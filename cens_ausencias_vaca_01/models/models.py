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


class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'
    
    def action_genera_calculo_vaca(self):
        wTexto = ""

