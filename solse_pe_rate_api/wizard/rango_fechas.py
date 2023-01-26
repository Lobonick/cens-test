# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import datetime
import pandas as pd

import logging
_logging = logging.getLogger(__name__)


class RangoFechas(models.TransientModel):
	_name = "solse.rango.fechas.tcambio"
	_description = "Tipo de Cambio (Generar rango fechas)"

	fecha_inicio = fields.Date("Fecha de inicio")
	fecha_fin = fields.Date("Fecha fin")

	def generar_rango_fechas(self):
		lista_fechas = [(self.fecha_inicio + timedelta(days=d)).strftime("%Y-%m-%d") for d in range((self.fecha_fin - self.fecha_inicio ).days + 1)]
		for fecha in lista_fechas:
			self.env['res.currency'].update_exchange_rate(fecha)
