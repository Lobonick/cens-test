# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logging = logging.getLogger(__name__)

class CuadrarInventario(models.Model):
	_name = "sdev.inventario"

	name = fields.Char('Nombre')
	lineas = fields.One2many('sdev.inventario.linea', 'inventario_id', 'Lineas')

	def completar_destino(self):
		for linea in self.lineas:
			stock_destino = linea.warehouse_quantity

	def procesar_cantidades_string(self, cant_strig):
		partes = cant_strig.split('')


class CuadrarInventarioLinea(models.Model):
	_name = "sdev.inventario.linea"

	producto_id = fields.Many2one('product.product', 'Producto')
	cant_orig_string = fields.Char('Cantidades de origen')
	cant_dest_string = fields.Char('Cantidades destino')
	cant_orig_json = fields.Char('Cantidades origen (json)')
	cant_dest_json = fields.Char('Cantidades destino (json)')
	cant_inv_json = fields.Char('Cantidades inventario (json)')

