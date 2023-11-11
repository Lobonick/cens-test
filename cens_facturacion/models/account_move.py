# -*- coding: utf-8 -*-
# Complemento de adaptación ODOO-CENS (r)-2023

from odoo import models, fields, api
import logging
import datetime
_logging = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'

	# ------------------------------
    # ACCION PARA EL BOTÓN NUMERADOR
    # ------------------------------
	def action_custom_button(self):
		for record in self:
			lines  = self.invoice_line_ids
			w_nro_orden = 0
			for line in lines:
				w_nro_orden += 1
				line.x_studio_nro_orden = w_nro_orden
		pass

