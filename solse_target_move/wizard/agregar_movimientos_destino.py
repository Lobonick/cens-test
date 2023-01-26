# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class GenerarAsientosDestino(models.TransientModel):
	_name = 'saccount.generar.asientos.destino'
	_description = 'Generar Asiento Destino'

	fecha_ini = fields.Date("Fecha inicial")
	fecha_fin = fields.Date("Fecha fin")

	
	def crear_movimientos(self):
		#self.env['account.move'].generar_asientos_destino_falantes()
		dominio = [("move_type", "=", "in_invoice"), ("state", "=", "posted"), ("target_move_count", "=", 0)]
		if self.fecha_ini and self.fecha_fin:
			dominio.extend([('invoice_date', '>=', self.fecha_ini), ('invoice_date', '<=', self.fecha_fin)])
		facturas = self.env['account.move'].search(dominio)
		for move in facturas:
			try:
				move.crear_asiento_destino()
			except Exception as e:
				raise UserError("%s (%s)" % (str(e), move.name))
