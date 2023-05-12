# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time
import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import pytz
import base64
import json
from odoo.exceptions import UserError, ValidationError
from odoo.tools.image import image_data_uri, base64_to_image
import copy
import logging
_logger = logging.getLogger(__name__)

tz = pytz.timezone('America/Lima')

class ReportesFinancieros(models.TransientModel):
	_name = "solse.peru.reporte"
	_description = "Reporte"

	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
	partner_id = fields.Many2one('res.partner', related="company_id.partner_id", store=True)
	tipo_reporte = fields.Selection([
		("compras", "Registro Compras"), ("ventas", "Registro Ventas"), ("flujo", "Flujo Efectivo"),
		("perdidasganancias", "Estado de Perdida y Ganancias"), ("general", "Balance General")], default="compras", string="Tipo de reporte")
	
	por_periodo = fields.Boolean("Por Periodo")
	periodo_id = fields.Many2one("solse.pe.cierre", "Periodo")
	seleccion_fecha = fields.Selection([("mensual", "Mensual"), ("rango", "Rango")], default="rango", string="Modo busqueda")
	anio = fields.Integer("Año")
	mes = fields.Selection([('enero', 'Enero'), ('febrero', 'Febrero'), ('marzo', 'Marzo'), ('abril', 'Abril'), 
	('mayo', 'Mayo'), ('junio', 'Junio'), ('julio', 'Julio'), ('agosto', 'Agosto'), ('septiembre', 'Septiembre'), 
	('octubre', 'Octubre'), ('noviembre', 'Noviembre'), ('diciembre', 'Diciembre')], default='enero')

	fecha_inicio = fields.Date("Fecha inicio")
	fecha_fin = fields.Date("Fecha fin")
	excluir_cierre = fields.Boolean("Excluir asientos cierre")


	agente = fields.Many2one("res.partner", string="Agente")
	todos_los_agentes = fields.Boolean("Todos los agentes")

	def _compute_account_balance(self, accounts):
		""" compute the balance, debit
		and credit for the provided accounts
		"""
		mapping = {
			'balance':
				"COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0)"
				" as balance",
			'debit': "COALESCE(SUM(debit), 0) as debit",
			'credit': "COALESCE(SUM(credit), 0) as credit",
		}

		res = {}
		for account in accounts:
			res[account.id] = dict((fn, 0.0)
								   for fn in mapping.keys())

		context = dict(self.env.context)
		if self.fecha_inicio and self.tipo_reporte != 'general':
			context['date_from'] = self.fecha_inicio
		if self.fecha_fin:
			context['date_to'] = self.fecha_fin
			
		context['state'] = 'posted'
		if self.excluir_cierre:
			context['es_x_cierre'] = False
		
		if accounts:
			tables, where_clause, where_params = (
				self.env['account.move.line'].with_context(context)._query_get())
			tables = tables.replace(
				'"', '') if tables else "account_move_line"
			wheres = [""]
			if where_clause.strip():
				wheres.append(where_clause.strip())
			filters = " AND ".join(wheres)
			request = ("SELECT account_id as id, " +
					   ', '.join(mapping.values()) +
					   " FROM " + tables +
					   " WHERE account_id IN %s " +
					   filters +
					   " GROUP BY account_id")
			params = (tuple(accounts._ids),) + tuple(where_params)
			self.env.cr.execute(request, params)
			for row in self.env.cr.dictfetchall():
				res[row['id']] = row
		return res

	def obtener_periodo(self):
		periodo = False
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		periodo = self.env['speriodo.salonb'].search([('fecha_ini', '=', fecha_inicio), 
			('fecha_fin', '=', fecha_fin), ('company_id', '=', self.company_id.id)])

		if len(periodo) > 1:
			raise UserError("Se encontro mas de un periodo valido para este rango de fechas")

		return periodo

	def obtener_fechas(self):
		fecha_ini = False
		fecha_fin = False
		cantidades = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
		if self.seleccion_fecha == 'rango':
			fecha_ini = self.fecha_inicio
			fecha_fin = self.fecha_fin
		elif self.seleccion_fecha == 'mensual':
			fecha_ini = datetime.date(int(self.anio), int(cantidades[self.mes]),  1)
			fecha_fin = fecha_ini + relativedelta(months=1)

		return [fecha_ini, fecha_fin]

	def obtener_reporte_compras(self):
		json_datos = {}
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		cantidad_total = 0
		monto_total = 0
		comision_servicio = 0
		comision_reventa = 0
		comision_total_total = 0

		dominio_tipo_doc = [('sub_type', '=', 'purchase')]
		tipo_doc_compras = self.env['l10n_latam.document.type'].search(dominio_tipo_doc)
		for tipo_doc in tipo_doc_compras:
			dominio_facturas = [("invoice_date", ">=", fecha_inicio), ("invoice_date", "<=", fecha_fin), 
			('state','=', 'posted'), ('l10n_latam_document_type_id', '=', tipo_doc.id)]
			facturas = self.env['account.move'].search(dominio_facturas, order="invoice_date desc")

			if tipo_doc.prefijo not in json_datos:
				json_datos[tipo_doc.prefijo] = {}

			for factura in facturas:
				correlativo = factura.name.split("-")[1]
				total_usd = factura.amount_total
				tipo_cambio = factura.tipo_cambio_dolar_sistema
				inafecto = factura.pe_unaffected_amount
				valor_venta = factura.pe_taxable_amount
				igv = factura.pe_amount_tax
				if tipo_cambio:
					igv = igv * tipo_cambio
					valor_venta = valor_venta * tipo_cambio

				if factura.currency_id.id == factura.company_id.currency_id.id:
					total_usd = 0
					tipo_cambio = 0
				percep = 0
				datos_factura = {
					'correlativo': correlativo,
					'fecha': factura.date,
					'codigo': factura.l10n_latam_document_type_id.code,
					'numero': factura.l10n_latam_document_number,
					'fecha_factura': factura.invoice_date,
					'numero_ruc': factura.partner_id.doc_number,
					'razon_social': factura.partner_id.name,
					'total_usd': total_usd,
					'tipo_cambio': tipo_cambio,
					'valor_venta': valor_venta,
					'inafecto': inafecto,
					'igv': igv,
					'total_venta': abs(factura.amount_total_signed),
					'percep': percep,
					'total_pagar': abs(factura.amount_total_signed),
				}
				json_datos[tipo_doc.prefijo][factura.name] = datos_factura
		
		datos_array = []
		for item in json_datos:
			#datos[item]['monto'] = '{0:.2f}'.format(datos[item]['monto'])
			lineas_datos = []
			datos = json_datos[item]
			for subitem in datos:
				lineas_datos.append(datos[subitem])

			datos_item = {
				'serie': item,
				'datos': lineas_datos,
			}
			datos_array.append(datos_item)

		titulo = "Reporte de Compras"

		return {
			"datos": datos_array,
			"titulo": titulo,
			#"nombre_mes": "%s del %s" % (self.mes, str(self.anio)),
			"nombre_mes": "Del %s al %s" % (str(self.fecha_inicio), str(self.fecha_fin)),
		}

	def obtener_reporte_ventas(self):
		json_datos = {}
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		cantidad_total = 0
		monto_total = 0
		comision_servicio = 0
		comision_reventa = 0
		comision_total_total = 0

		dominio_facturas = [("invoice_date", ">=", fecha_inicio), ("invoice_date", "<=", fecha_fin), 
		('state','in', ['posted', 'annul', 'cancel']), ('l10n_latam_document_type_id.sub_type', '=', 'sale')]
		facturas = self.env['account.move'].search(dominio_facturas, order="invoice_date desc")

		for factura in facturas:
			correlativo = factura.name.split("-")[1]
			total_usd = factura.amount_total
			tipo_cambio = factura.tipo_cambio_dolar_sistema
			inafecto = factura.pe_unaffected_amount
			valor_venta = factura.pe_taxable_amount
			igv = factura.pe_amount_tax
			if tipo_cambio:
				igv = igv * tipo_cambio
				valor_venta = valor_venta * tipo_cambio

			if factura.currency_id.id == factura.company_id.currency_id.id:
				total_usd = 0
				tipo_cambio = 0
			percep = 0
			fecha_ref = ""
			cod_ref = ""
			doc_ref = ""

			sunat_code = factura.pe_invoice_code or '00'
			if sunat_code in ['07'] :
				origin = factura.reversed_entry_id
				origin_number = origin.ref
				#origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
				fecha_ref = origin.invoice_date.strftime('%d/%m/%Y')
				cod_ref = origin.pe_invoice_code
				doc_ref = origin_number
			elif sunat_code in ['08'] :
				origin = factura.debit_origin_id
				origin_number = origin.ref
				#origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
				fecha_ref = origin.invoice_date.strftime('%d/%m/%Y')
				cod_ref = origin.pe_invoice_code
				doc_ref = origin_number

			total_venta = abs(factura.amount_total_signed)
			total_pagar = abs(factura.amount_total_signed)
			if factura.state in ['annul', 'cancel']:
				total_usd = 0
				valor_venta = 0
				inafecto = 0
				igv = 0
				percep = 0
				total_venta = 0
				total_pagar = 0

			datos_factura = {
				'correlativo': correlativo,
				'fecha': factura.date,
				'codigo': factura.l10n_latam_document_type_id.code,
				'numero': factura.l10n_latam_document_number,
				'fecha_factura': factura.invoice_date,
				'doc_cli_id': factura.partner_id.doc_type,
				'numero_ruc': factura.partner_id.doc_number,
				'razon_social': factura.partner_id.name,
				'total_usd': total_usd,
				'tipo_cambio': tipo_cambio,
				'valor_venta': valor_venta,
				'inafecto': inafecto,
				'igv': igv,
				'total_venta': total_venta,
				'percep': percep,
				'total_pagar': total_pagar,
				'fecha_ref': fecha_ref,
				'cod_ref': cod_ref,
				'doc_ref': doc_ref,
			}
			json_datos[factura.name] = datos_factura
		
		datos_array = []
		for item in json_datos:
			#datos[item]['monto'] = '{0:.2f}'.format(datos[item]['monto'])
			lineas_datos = []
			datos = json_datos[item]

			datos_array.append(datos)

		titulo = "Reporte de Ventas"

		return {
			"datos": datos_array,
			"titulo": titulo,
			#"nombre_mes": "%s del %s" % (self.mes, str(self.anio)),
			"nombre_mes": "Del %s al %s" % (str(self.fecha_inicio), str(self.fecha_fin)),
		}

	def filtrar_cuentas_con_movimientos(self, json):
		datos = {}
		for id in json:
			reg = json[id]
			if not reg['debit'] and not reg['credit']:
				continue
			cuenta = self.env['account.account'].search([("id", "=", id)])
			datos[id] = reg
			datos[id]['nombre_cuenta'] = cuenta.name

		return datos

	def agrupar_cuentas_con_movimientos(self, datos_ingresos, fields):
		res_ingresos = {}
		fields = ['credit', 'debit', 'balance']
		for value in datos_ingresos.values():
			for field in fields:
				if field in res_ingresos:
					res_ingresos[field] += value.get(field)
				else:
					res_ingresos[field] = value.get(field)

		return res_ingresos

	def convertir_array(self, datos_mostrar):
		datos_array_ingresos = []
		for item in datos_mostrar:
			datos = datos_mostrar[item]
			
			datos_array_ingresos.append(datos)

		return datos_array_ingresos

	def obtener_datos(self, dominio):
		datos = []
		fields = ['credit', 'debit', 'balance']
		cuentas_tipo = self.env['account.account'].search(dominio)

		tipo_datos = self._compute_account_balance(cuentas_tipo)
		TIPO = self.agrupar_cuentas_con_movimientos(tipo_datos, fields)		
		tipo_detalles = self.filtrar_cuentas_con_movimientos(tipo_datos)
		tipo_detalles_array = self.convertir_array(tipo_detalles)

		return [TIPO, tipo_detalles_array]

	def obtener_reporte_perdidas_ganancias(self):
		json_datos = {}
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		if self.por_periodo:
			self.fecha_inicio = self.periodo_id.fecha_inicio
			self.fecha_fin = self.periodo_id.fecha_fin

		cantidad_total = 0
		monto_total = 0
		comision_servicio = 0
		comision_reventa = 0
		comision_total_total = 0
		### Dominios
		# OPINC = [('account_id.account_type', '=', 'income')]
		# OIN = [('account_id.account_type', '=', 'income_other')]
		# COS = [('account_id.account_type', '=', 'expense_direct_cost')]
		# LEX = EXP.balance + DEP.balance
		# EXP = [('account_id.account_type', '=', 'expense')]
		# DEP = [('account_id.account_type', '=', 'expense_depreciation')]

		### Funcion
		# INC = OPINC.balance + OIN.balance

		fields = ['credit', 'debit', 'balance']

		dominio_cuenta_opinc = [('account_type', '=', 'income')]
		opinc_rpt = self.obtener_datos(dominio_cuenta_opinc)
		OPINC = opinc_rpt[0]
		opinc_detalles_array = opinc_rpt[1]

		dominio_cuenta_oin = [('account_type', '=', 'income_other'), ('sub_cuenta_ingresos', '=', 'otros')]
		oin_rpt = self.obtener_datos(dominio_cuenta_oin)
		OIN = oin_rpt[0]
		oin_detalles_array = oin_rpt[1]

		dominio_cuenta_cos = [('account_type', '=', 'expense_direct_cost')]
		cos_rpt = self.obtener_datos(dominio_cuenta_cos)
		COS = cos_rpt[0]
		cos_detalles_array = cos_rpt[1]

		dominio_gastos_operativos = [('account_type', '=', 'expense'), ('sub_cuenta_gastos', '=', 'operativos')]
		gast_oper_rpt = self.obtener_datos(dominio_gastos_operativos)
		EXP_OP = gast_oper_rpt[0]
		gastos_oper_detalles_array = gast_oper_rpt[1]

		dominio_gastos_financieros = [('account_type', '=', 'expense'), ('sub_cuenta_gastos', '=', 'financieros')]
		gast_fin_rpt = self.obtener_datos(dominio_gastos_financieros)
		EXP_FIN = gast_fin_rpt[0]
		gastos_fin_detalles_array = gast_fin_rpt[1]

		dominio_ingresos_fin = [('account_type', '=', 'income_other'), ('sub_cuenta_ingresos', '=', 'financieros')]
		ingresos_fin = self.obtener_datos(dominio_ingresos_fin)
		OIN_FIN = ingresos_fin[0]
		ingresos_fin_array = ingresos_fin[1]

		dominio_cuenta_exp = [('account_type', '=', 'expense'), ('sub_cuenta_gastos', '=', 'otros')]
		exp_rpt = self.obtener_datos(dominio_cuenta_exp)
		EXP = exp_rpt[0]
		exp_detalles_array = exp_rpt[1]

		dominio_cuenta_dep = [('account_type', '=', 'expense_depreciation')]
		dep_rpt = self.obtener_datos(dominio_cuenta_dep)
		DEP = dep_rpt[0]
		dep_detalles_array = dep_rpt[1]

		utilidad_bruta = 0
		if "balance" in OPINC:
			utilidad_bruta = abs(OPINC["balance"])
		if "balance" in COS:
			utilidad_bruta = utilidad_bruta - abs(COS["balance"])

		margen_operativo = utilidad_bruta
		if "balance" in EXP_OP:
			margen_operativo = margen_operativo - (EXP_OP["balance"] if "balance" in EXP_OP else 0)

		otros_ingresos_egresos = 0
		if "balance" in OIN_FIN:
			otros_ingresos_egresos = abs(OIN_FIN["balance"])

		if "balance" in EXP_FIN:
			otros_ingresos_egresos = otros_ingresos_egresos - abs(EXP_FIN["balance"])

		if "balance" in OIN:
			otros_ingresos_egresos = otros_ingresos_egresos + abs(OIN["balance"])

		if "balance" in EXP:
			otros_ingresos_egresos = otros_ingresos_egresos - abs(EXP["balance"])

		#otros_ingresos_egresos = OIN_FIN["balance"] - EXP_FIN["balance"] + OIN["balance"]

		utilidad_antes_impuestos = margen_operativo + otros_ingresos_egresos

		titulo = "Reporte de Perdidas y Ganancias"

		return {
			"datos": opinc_detalles_array,
			"titulo": titulo,
			#"nombre_mes": "%s del %s" % (self.mes, str(self.anio)),
			"nombre_mes": "Del %s al %s" % (str(self.fecha_inicio), str(self.fecha_fin)),
			"ingresos": OPINC,
			"lineas_ingresos": opinc_detalles_array,
			"costo_venta": COS,
			"costo_venta_detalles": cos_detalles_array,
			"utilidad_bruta": utilidad_bruta,
			"gastos_operativos": EXP_OP,
			"gastos_operativos_detalles": gastos_oper_detalles_array,
			"margen_operativo": margen_operativo,
			"gastos_financieros": EXP_FIN,
			"gastos_financieros_detalles": gastos_fin_detalles_array,
			"ingresos_financieros": OIN_FIN,
			"ingresos_financieros_detalles": ingresos_fin_array,
			"gastos": EXP,
			"gastos_detalles": exp_detalles_array,
			"otros_ingresos": OIN,
			"otros_ingresos_detalles": oin_detalles_array,
			"otros_ingresos_egresos": otros_ingresos_egresos,
			"utilidad_antes_impuestos": utilidad_antes_impuestos,
		}

	def obtener_reporte_balance_general(self):
		json_datos = {}
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		cantidad_total = 0
		monto_total = 0
		comision_servicio = 0
		comision_reventa = 0
		comision_total_total = 0
		if not self.periodo_id:
			raise UserError("Seleccione un Periodo valido")

		self.fecha_inicio = self.periodo_id.fecha_inicio
		self.fecha_fin = self.periodo_id.fecha_fin
		### Dominios
		# OPINC = [('account_id.account_type', '=', 'income')]
		# OIN = [('account_id.account_type', '=', 'income_other')]
		# COS = [('account_id.account_type', '=', 'expense_direct_cost')]
		# LEX = EXP.balance + DEP.balance
		# EXP = [('account_id.account_type', '=', 'expense')]
		# DEP = [('account_id.account_type', '=', 'expense_depreciation')]

		### Funcion
		# INC = OPINC.balance + OIN.balance

		fields = ['credit', 'debit', 'balance']

		dominio_cuentas_corrientes = [('account_type', '=', 'asset_cash')]
		cuenta_corr_rpt = self.obtener_datos(dominio_cuentas_corrientes)
		CUECORR = cuenta_corr_rpt[0]
		cuecorr_detalles_array = cuenta_corr_rpt[1]

		dominio_fondos_fijos_transito = [('account_type', '=', 'asset_current')]
		fondos_fijos_transito = self.obtener_datos(dominio_fondos_fijos_transito)
		FFTRAN = fondos_fijos_transito[0]
		fondos_fijos_transito_array = fondos_fijos_transito[1]

		
		# Cuentas por cobrar comercial
		dominio_a_cuentas_x_cobrar_comer = [('account_type', '=', 'asset_receivable'), 
		('sub_cuenta_por_cobrar', '=', 'comerciales')]
		a_cuentas_x_cobrar_comer = self.obtener_datos(dominio_a_cuentas_x_cobrar_comer)
		A_CXCOBRARC = a_cuentas_x_cobrar_comer[0]
		a_cxcobrc_detalles_array = a_cuentas_x_cobrar_comer[1]

		# Otras cuentas por cobrar
		dominio_a_cuentas_x_cobrar_otros = [('account_type', '=', 'asset_receivable'), 
		('sub_cuenta_por_cobrar', '=', 'otros')]
		a_cuentas_x_cobrar_otros = self.obtener_datos(dominio_a_cuentas_x_cobrar_otros)
		A_CXCOBRARO = a_cuentas_x_cobrar_otros[0]
		a_cxcobro_detalles_array = a_cuentas_x_cobrar_otros[1]

		# Inmuebles
		dominio_act_inmuebles = [('account_type', '=', 'asset_fixed'), 
		('sub_cuenta_activo_fijo', '=', 'inmuebles')]
		act_inmuebles = self.obtener_datos(dominio_act_inmuebles)
		A_INMUEBLES = act_inmuebles[0]
		a_inmuebles_detalles_array = act_inmuebles[1]

		# Intangibles
		dominio_act_intangibles = [('account_type', '=', 'asset_fixed'), 
		('sub_cuenta_activo_fijo', '=', 'intangibles')]
		act_intangibles = self.obtener_datos(dominio_act_intangibles)
		A_INTANGIBLES = act_intangibles[0]
		a_intangibles_detalles_array = act_intangibles[1]

		### Pasivo

		# Tributos por pagar: liability_current => Pasivo circulante
		dominio_tributos_por_pagar = [('account_type', '=', 'liability_current')]
		tributos_por_pagar = self.obtener_datos(dominio_tributos_por_pagar)
		P_TRXPAG = tributos_por_pagar[0]
		p_trxpag_detalles_array = tributos_por_pagar[1]

		# Remuneraciones por pagar: liability_payable => Por pagar
		dominio_remuneraciones_por_pagar = [('account_type', '=', 'liability_payable'), 
		('sub_cuenta_por_pagar', '=', 'remuneraciones')]
		remuneraciones_por_pagar = self.obtener_datos(dominio_remuneraciones_por_pagar)
		P_REMXPAGAR = remuneraciones_por_pagar[0]
		p_remxpagar_detalles_array = remuneraciones_por_pagar[1]

		# Cuentas por pagar comerciales-terceros
		dominio_terceros_por_pagar = [('account_type', '=', 'liability_payable'), 
		('sub_cuenta_por_pagar', '=', 'comerciales')]
		terceros_por_pagar = self.obtener_datos(dominio_terceros_por_pagar)
		P_TERXPAGAR = terceros_por_pagar[0]
		p_terxpagar_detalles_array = terceros_por_pagar[1]

		# Otras cuentas por pagar
		dominio_otros_por_pagar = [('account_type', '=', 'liability_payable'), 
		('sub_cuenta_por_pagar', '=', 'comerciales')]
		otros_por_pagar = self.obtener_datos(dominio_otros_por_pagar)
		P_OTRXPAGAR = otros_por_pagar[0]
		p_otrxpagar_detalles_array = otros_por_pagar[1]

		## Pasivo no corriente
		# Otras cuentas por pagar: liability_non_current => Pasivos no circulantes
		dominio_pnc_otros_por_pagar = [('account_type', '=', 'liability_non_current')]
		pnc_otros_por_pagar = self.obtener_datos(dominio_pnc_otros_por_pagar)
		PNC_OTRXPAGAR = pnc_otros_por_pagar[0]
		pnc_otrxpagar_detalles_array = pnc_otros_por_pagar[1]

		## Patrimonio: equity => Capital, equity_unaffected => Ganancias del año actual 
		dominio_capital = [('account_type', 'in', ['equity', 'equity_unaffected'])]
		capital = self.obtener_datos(dominio_capital)
		CAPITAL = capital[0]
		capital_detalles_array = capital[1]

		# ganancias
		datos_ganancias = self.env['solse.peru.reporte'].new()
		datos_ganancias.fecha_inicio = self.fecha_inicio
		datos_ganancias.fecha_fin = self.fecha_fin
		datos_ganancias.tipo_reporte = 'perdidasganancias'
		datos_json = datos_ganancias.obtener_reporte_perdidas_ganancias()
		resultado_ejercicio = datos_json['utilidad_antes_impuestos']

		caja_y_bancos = abs(CUECORR['balance']) + abs(FFTRAN['balance'])
		total_activo_corriente = caja_y_bancos

		if 'balance' in A_CXCOBRARC:
			total_activo_corriente += abs(A_CXCOBRARC['balance'])

		if 'balance' in A_CXCOBRARO:
			total_activo_corriente += abs(A_CXCOBRARO['balance'])

		total_activo_fijo = 0
		if 'balance' in A_INMUEBLES:
			total_activo_fijo += (A_INMUEBLES['balance'])

		if 'balance' in A_INTANGIBLES:
			total_activo_fijo += (A_INTANGIBLES['balance'])

		total_activo = total_activo_corriente + total_activo_fijo

		total_pasivo_corriente = 0
		total_pasivo_no_corriente = 0
		_logger.info("tributossssssssssssssss por pagar 2")
		_logger.info(P_TRXPAG)
		_logger.info(P_REMXPAGAR)
		if 'balance' in P_TRXPAG:
			total_pasivo_corriente += (P_TRXPAG['balance'])

		if 'balance' in P_REMXPAGAR:
			total_pasivo_corriente += (P_REMXPAGAR['balance'])

		if 'balance' in P_TERXPAGAR:
			total_pasivo_corriente += (P_TERXPAGAR['balance'])

		if 'balance' in P_OTRXPAGAR:
			total_pasivo_corriente += (P_OTRXPAGAR['balance'])

		if 'balance' in PNC_OTRXPAGAR:
			total_pasivo_no_corriente += (PNC_OTRXPAGAR['balance'])

		total_pasivo_corriente = abs(total_pasivo_corriente)
		total_pasivo_no_corriente = abs(total_pasivo_no_corriente)
		
		total_patrimonio = resultado_ejercicio
		if 'balance' in CAPITAL:
			total_patrimonio += abs(CAPITAL['balance'])

		total_pasivo = total_pasivo_corriente + total_pasivo_no_corriente + total_patrimonio
		diferencia_activo_pasivo = total_activo - total_pasivo

		titulo = "ESTADO DE SITUACION FINANCIERA"

		return {
			"titulo": titulo,
			#"nombre_mes": "%s del %s" % (self.mes, str(self.anio)),
			"nombre_mes": "Al %s" % (str(self.fecha_fin)),
			"caja_y_bancos": caja_y_bancos,
			"cuenta_corriente": CUECORR,
			"cuenta_corriente_detalles": cuecorr_detalles_array,
			"fondos_fijos_transito": FFTRAN,
			"fondos_fijos_transito_detalles": fondos_fijos_transito_array,
			"cuenta_x_cobrar_comerciales": A_CXCOBRARC,
			"cuenta_x_cobrar_comerciales_detalles": a_cxcobrc_detalles_array,
			"cuenta_x_cobrar_otros": A_CXCOBRARO,
			"cuenta_x_cobrar_otros_detalles": a_cxcobro_detalles_array,
			"total_activo_corriente": total_activo_corriente,
			"cuenta_inmubles": A_INMUEBLES,
			"cuenta_inmubles_detalles": a_inmuebles_detalles_array,
			"cuenta_intangibles": A_INTANGIBLES,
			"cuenta_intangibles_detalles": a_intangibles_detalles_array,
			"total_activo_fijo": total_activo_fijo,
			"total_activo": total_activo,
			"tributos_x_pagar": P_TRXPAG,
			"tributos_x_pagar_detalles": p_trxpag_detalles_array,
			"remuneraciones_x_pagar": P_REMXPAGAR,
			"remuneraciones_x_pagar_detalles": p_remxpagar_detalles_array,
			"terceros_x_pagar": P_TERXPAGAR,
			"terceros_x_pagar_detalles": p_terxpagar_detalles_array,
			"otros_x_pagar": P_OTRXPAGAR,
			"otros_x_pagar_detalles": p_otrxpagar_detalles_array,
			"total_pasivo_corriente": total_pasivo_corriente,
			"pnc_otros_x_pagar": PNC_OTRXPAGAR,
			"pnc_otros_x_pagar_detalles": pnc_otrxpagar_detalles_array,
			"total_pasivo_no_corriente": total_pasivo_no_corriente,
			"capital": CAPITAL,
			"capital_detalles": capital_detalles_array,
			"total_pasivo": total_pasivo,
			"resultado_ejercicio": resultado_ejercicio,
			"total_patrimonio": total_patrimonio,
			"diferencia_activo_pasivo": diferencia_activo_pasivo,
		}
	
	def obtener_reporte_flujo_efectivo(self):
		json_datos = {}
		fechas = self.obtener_fechas()
		fecha_inicio = fechas[0]
		fecha_fin = fechas[1]

		if self.por_periodo:
			self.fecha_inicio = self.periodo_id.fecha_inicio
			self.fecha_fin = self.periodo_id.fecha_fin

		lines = self.env['account.move']._get_cash_flow_lines(fecha_inicio, fecha_fin)
		#otros_ingresos_egresos = OIN_FIN["balance"] - EXP_FIN["balance"] + OIN["balance"]

		#utilidad_antes_impuestos = margen_operativo + otros_ingresos_egresos

		titulo = "Reporte de Flujo de Caja"

		return {
			"titulo": titulo,
			#"nombre_mes": "%s del %s" % (self.mes, str(self.anio)),
			"nombre_mes": "Del %s al %s" % (str(self.fecha_inicio), str(self.fecha_fin)),
			"cash_flow_lines": lines,
		}

	def get_report_values(self):
		datos = {}
		if self.tipo_reporte in ["compras"]:
			datos = self.obtener_reporte_compras()
		elif self.tipo_reporte in ["ventas"]:
			datos = self.obtener_reporte_ventas()
		elif self.tipo_reporte in ["perdidasganancias"]:
			datos = self.obtener_reporte_perdidas_ganancias()
		elif self.tipo_reporte in ["general"]:
			datos = self.obtener_reporte_balance_general()
		elif self.tipo_reporte in ["flujo"]:
			datos = self.obtener_reporte_flujo_efectivo()

		return datos

	def solicitar_reporte(self, data):
		reporte = False
		docs = self.env['product.product'].search([], limit=10)
		if self.tipo_reporte in ["compras"]:
			reporte = self.env.ref('solse_pe_accountant_report.pdf_reporte_compras').report_action(docs, data)
		elif self.tipo_reporte in ["ventas"]:
			reporte = self.env.ref('solse_pe_accountant_report.pdf_reporte_ventas').report_action(docs, data)
		elif self.tipo_reporte in ["perdidasganancias"]:
			reporte = self.env.ref('solse_pe_accountant_report.pdf_reporte_ganancias_perdidas').report_action(docs, data)
		elif self.tipo_reporte in ["general"]:
			reporte = self.env.ref('solse_pe_accountant_report.pdf_reporte_balance_general').report_action(docs, data)
		elif self.tipo_reporte in ["flujo"]:
			reporte = self.env.ref('solse_pe_accountant_report.pdf_reporte_flujo_caja').report_action(docs, data)
		
		return reporte

	def action_pdf(self):
		data = self.get_report_values()
		return self.solicitar_reporte(data)
		
