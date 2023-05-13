# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re

import logging
_logging = logging.getLogger(__name__)

class SolsePeCierre(models.Model):
	_name = "solse.pe.cierre"
	_description = "Año Fiscal"

	name = fields.Char("Nombre")
	company_id = fields.Many2one(comodel_name='res.company', string='Empresa', required=True, default=lambda self:self.env.user.company_id)
	anio = fields.Integer("Año")
	fecha_inicio = fields.Date("Fecha Inicio")
	fecha_fin = fields.Date("Fecha Fin")
	state = fields.Selection([("borrador", "Borrador"), ("cerrado", "Cerrado")],
		string="Estado", default="borrador")

	asiento_cierre_transito = fields.Many2one("account.move", string="Asiento Cierre (Transito)")
	asiento_cierre_final = fields.Many2one("account.move", string="Asiento Cierre")

	def reaccinar_tipo(self):
		if self.asiento_cierre_transito:
			self.asiento_cierre_transito.es_x_cierre = True

		if self.asiento_cierre_final:
			self.asiento_cierre_final.es_x_cierre = True

	def crear_asiento_transito(self):
		cuenta_ganancia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_ganancias')
		cuenta_ganancia = int(cuenta_ganancia)

		cuenta_perdida = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_perdidas')
		cuenta_perdida = int(cuenta_perdida)

		if self.asiento_cierre_transito:
			return

		glosa = 'Asiento de cierre transito'

		dato = self.env['report.solse.peru.reporte'].new()
		dato.fecha_inicio = self.fecha_inicio
		dato.fecha_fin = self.fecha_fin
		datos_json = dato.obtener_reporte_perdidas_ganancias()
		lineas = []
		#lineas.extend(datos_json['datos'])
		lineas.extend(datos_json['lineas_ingresos'])
		lineas.extend(datos_json['costo_venta_detalles'])
		lineas.extend(datos_json['gastos_operativos_detalles'])
		lineas.extend(datos_json['gastos_financieros_detalles'])
		lineas.extend(datos_json['ingresos_financieros_detalles'])
		lineas.extend(datos_json['gastos_detalles'])
		lineas.extend(datos_json['otros_ingresos_detalles'])
		
		nuevas_lineas = []
		for item in lineas:
			dato_reg_json = {
				"account_id":  item['id'],
				"debit": item['credit'],
				"credit": item['debit'],
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg = (0, 0, dato_reg_json)
			nuevas_lineas.append(dato_reg)


		if 'utilidad_antes_impuestos' in datos_json:
			monto = datos_json['utilidad_antes_impuestos']

			dato_reg_json = {
				"account_id":  cuenta_ganancia if monto >= 0 else cuenta_perdida,
				"debit": abs(monto) if monto < 0 else 0,
				"credit": abs(monto) if monto >= 0 else 0,
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg = (0, 0, dato_reg_json)
			nuevas_lineas.append(dato_reg)

		
		datos_asiento = {
			'move_type': 'entry',
			'date': self.fecha_fin,
			'ref': glosa,
			'glosa': glosa,
			'es_x_cierre': True,
			'line_ids': nuevas_lineas,
		}
		_logging.info("datos de asiento ooooooooooooooooooooo")
		_logging.info(datos_asiento)
		asiento = self.env['account.move'].create(datos_asiento)
		self.asiento_cierre_transito = asiento

	def crear_asiento_final(self):
		cuenta_ganancia_t = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_ganancias')
		cuenta_ganancia_t = int(cuenta_ganancia_t)

		cuenta_perdida_t = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_perdidas')
		cuenta_perdida_t = int(cuenta_perdida_t)

		cuenta_ganancia = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_ganancias_cierre')
		cuenta_ganancia = int(cuenta_ganancia)

		cuenta_perdida = self.env['ir.config_parameter'].sudo().get_param('solse_pe_accountant_report.default_cuenta_perdidas_cierre')
		cuenta_perdida = int(cuenta_perdida)

		if not self.asiento_cierre_transito:
			raise UserError("Primero genere el asiento de transito")

		if self.asiento_cierre_final:
			return

		glosa = 'Asiento de cierre'
		monto_ganancia = 0
		monto_perdida = 0
		nuevas_lineas = []
		for reg in self.asiento_cierre_transito.line_ids:
			if reg.account_id.id == cuenta_ganancia_t:
				monto_ganancia = reg.credit

			if reg.account_id.id == cuenta_perdida_t:
				monto_perdida = reg.debit

		if monto_ganancia:
			dato_reg_json = {
				"account_id":  cuenta_ganancia_t,
				"debit": monto_ganancia,
				"credit": 0,
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg = (0, 0, dato_reg_json)
			nuevas_lineas.append(dato_reg)

			dato_reg_json_2 = {
				"account_id":  cuenta_ganancia,
				"debit": 0,
				"credit": monto_ganancia,
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg_2 = (0, 0, dato_reg_json_2)
			nuevas_lineas.append(dato_reg_2)

		if monto_perdida:
			dato_reg_json = {
				"account_id":  cuenta_perdida_t,
				"debit": 0,
				"credit": monto_perdida,
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg = (0, 0, dato_reg_json)
			nuevas_lineas.append(dato_reg)

			dato_reg_json_2 = {
				"account_id":  cuenta_perdida,
				"debit": monto_perdida,
				"credit": 0,
				"ref": glosa,
				"glosa": glosa,
			}
			dato_reg_2 = (0, 0, dato_reg_json_2)
			nuevas_lineas.append(dato_reg_2)

		
		datos_asiento = {
			'move_type': 'entry',
			'date': self.fecha_fin,
			'ref': glosa,
			'glosa': glosa,
			'es_x_cierre': True,
			'line_ids': nuevas_lineas,
		}
		asiento = self.env['account.move'].create(datos_asiento)
		self.asiento_cierre_final = asiento

	def confirmar_cierre(self):
		self.company_id.sudo().write(
			{
				"period_lock_date": self.fecha_fin,
				"fiscalyear_lock_date": self.fecha_fin,
				"tax_lock_date": self.fecha_fin,
			}
		)
		self.state = "cerrado"


