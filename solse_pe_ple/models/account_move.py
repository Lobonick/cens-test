# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model) :
	_inherit = 'account.move'

	pago_detraccion = fields.Many2one('account.payment', 'Pago de Detracción/Retención')
	solse_pe_serie = fields.Char("Serie (ple)", compute="_compute_correlativo")
	solse_pe_numero = fields.Char("Correlativo (ple)", compute="_compute_correlativo")

	@api.depends('l10n_latam_document_number', 'state', 'name')
	def _compute_correlativo(self):
		for move in self:
			inv_number = False
			if move.l10n_latam_document_number:
				inv_number = move.l10n_latam_document_number.split('-')

			if inv_number and len(inv_number) == 2:
				serie = inv_number[0]
				move.solse_pe_serie = serie
				move.solse_pe_numero = inv_number[1]
			else:
				move.solse_pe_serie = "MOV"
				move.solse_pe_numero = '0'+str(move.id).rjust(7, '0')

	"""def obtener_total_base_afecto(self):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.pe_affectation_code in ('10', '11', '12', '13', '14', '15', '16'):
				suma = suma + abs(linea.balance)
		return suma

	def obtener_total_base_inafecto(self):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.pe_affectation_code not in ('10', '11', '12', '13', '14', '15', '16'):
				suma = suma + abs(linea.balance)
		return suma"""

	
	def obtener_valor_campo_14(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.tipo_afectacion_compra.nro_col_importe_afectacion == 14:
				monto = abs(linea.price_subtotal)
				monto = monto * tipo_cambio
				suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""

		return respuesta

	def obtener_valor_campo_15(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			impuesto_afect_ids = []
			impuesto = linea.tax_ids[0]
			for item in linea.tipo_afectacion_compra.impuesto_afect_ids:
				if impuesto.id == item.impuesto_id.id and item.nro_col_importe_impuesto == 15:
					monto = abs(linea.price_total - linea.price_subtotal)
					monto = monto * tipo_cambio
					suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta

	def obtener_valor_campo_16(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.tipo_afectacion_compra.nro_col_importe_afectacion == 16:
				monto = abs(linea.price_subtotal)
				monto = monto * tipo_cambio
				suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""

		return respuesta

	def obtener_valor_campo_17(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			impuesto_afect_ids = []
			impuesto = linea.tax_ids[0]
			for item in linea.tipo_afectacion_compra.impuesto_afect_ids:
				if impuesto.id == item.impuesto_id.id and item.nro_col_importe_impuesto == 17:
					monto = abs(linea.price_total - linea.price_subtotal)
					monto = monto * tipo_cambio
					suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta

	def obtener_valor_campo_18(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.tipo_afectacion_compra.nro_col_importe_afectacion == 18:
				monto = abs(linea.price_subtotal)
				monto = monto * tipo_cambio
				suma = suma + linea

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""

		return respuesta

	def obtener_valor_campo_19(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			impuesto_afect_ids = []
			impuesto = linea.tax_ids[0]
			for item in linea.tipo_afectacion_compra.impuesto_afect_ids:
				if impuesto.id == item.impuesto_id.id and item.nro_col_importe_impuesto == 19:
					monto = abs(linea.price_total - linea.price_subtotal)
					monto = monto * tipo_cambio
					suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta

	def obtener_valor_campo_20(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.tipo_afectacion_compra.nro_col_importe_afectacion == 20:
				monto = abs(linea.price_subtotal)
				monto = monto * tipo_cambio
				suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""

		return respuesta

	def obtener_valor_campo_21(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			impuesto_afect_ids = []
			impuesto = linea.tax_ids[0]
			for item in linea.tipo_afectacion_compra.impuesto_afect_ids:
				if impuesto.id == item.impuesto_id.id and item.nro_col_importe_impuesto == 21:
					monto = abs(linea.price_total - linea.price_subtotal)
					monto = monto * tipo_cambio
					suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta

	def obtener_valor_campo_22(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			impuesto_afect_ids = []
			impuesto = linea.tax_ids[0]
			for item in linea.tipo_afectacion_compra.impuesto_afect_ids:
				if impuesto.id == item.impuesto_id.id and item.nro_col_importe_impuesto == 22:
					monto = abs(linea.price_total - linea.price_subtotal)
					monto = monto * tipo_cambio
					suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta

	def obtener_valor_campo_23(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			if linea.tipo_afectacion_compra.nro_col_importe_afectacion == 23:
				monto = abs(linea.price_subtotal)
				monto = monto * tipo_cambio
				suma = suma + monto

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""

		return respuesta

	def obtener_valor_campo_24(self, tipo_cambio):
		suma = 0
		for linea in self.invoice_line_ids:
			suma = suma + abs(linea.balance)

		respuesta = ""
		if suma > 0:
			respuesta = format(suma, '.2f')
		else:
			respuesta = ""
			
		return respuesta


	def ple_8_1_fields(self, contador, fecha_inicio):
		m_01 = []
		move = self
		try :
			sunat_number = move.ref
			sunat_number = sunat_number and ('-' in sunat_number) and sunat_number.split('-') or ['','']
			sunat_code = move.pe_invoice_code or '00'
			sunat_partner_code = move.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
			sunat_partner_vat = move.partner_id.vat
			#sunat_partner_name = move.partner_id.legal_name or move.partner_id.name
			sunat_partner_name = move.partner_id.name
			move_id = move.l10n_latam_document_number
			invoice_date = move.invoice_date
			date_due = move.invoice_date_due
			amount_untaxed = move.amount_untaxed
			amount_tax = move.amount_tax
			amount_total = move.amount_total
			#1-4
			#m_01.extend([periodo.strftime('%Y%m00'), str(number), ('A'+str(number).rjust(9,'0')), invoice.invoice_date.strftime('%d/%m/%Y')])
			m_01.extend([
				move.date.strftime('%Y%m00'),
				str(move_id),
				('M'+str(1).rjust(9,'0')),
				invoice_date.strftime('%d/%m/%Y'),
			])
			contador = contador + 1
			#5
			if date_due :
				m_01.append(date_due.strftime('%d/%m/%Y'))
			else :
				m_01.append('')
			#6-10
			m_01.extend([
				sunat_code,
				sunat_number[0],
				'',
				sunat_number[1],
				'',
			])
			#11-13
			if sunat_partner_code and sunat_partner_vat and sunat_partner_name :
				m_01.extend([
					sunat_partner_code,
					sunat_partner_vat,
					sunat_partner_name,
				])
			else :
				m_01.extend(['', '', ''])

			fecha_busqueda = str(invoice_date)
			currency_rate_id = [
				('name', '=', fecha_busqueda),
				('company_id','=', move.company_id.id),
				('currency_id','=', move.currency_id.id),
			]
			currency_rate_id = self.env['res.currency.rate'].sudo().search(currency_rate_id)
			tipo_cambio = 1.000
			if currency_rate_id:
				tipo_cambio = currency_rate_id.rate_pe

			#14-15
			#14 Base imponible de las adquisiciones gravadas que dan derecho a crédito fiscal y/o saldo a favor por exportación, 
			#destinadas exclusivamente a operaciones gravadas y/o de exportación 
			#15 Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal
			#total_sin_impuestos = abs(move.amount_untaxed_signed)
			valor_campo_14 = move.obtener_valor_campo_14(tipo_cambio)
			#total_impuestos = abs(move.amount_tax_signed)
			valor_campo_15 = move.obtener_valor_campo_15(tipo_cambio)
			m_01.extend([valor_campo_14, valor_campo_15])
			#16-23
			#16 Base imponible de las adquisiciones gravadas que dan derecho a crédito fiscal y/o saldo a favor por exportación, 
			#destinadas a operaciones gravadas y/o de exportación y a operaciones no gravadas
			#-17 Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal
			#18 Base imponible de las adquisiciones gravadas que no dan derecho a crédito fiscal y/o saldo a favor por exportación, 
			#por no estar destinadas a operaciones gravadas y/o de exportación.
			#-19 Monto del Impuesto General a las Ventas y/o Impuesto de Promoción Municipal
			#20 Valor de las adquisiciones no gravadas
			#21 Monto del Impuesto Selectivo al Consumo en los casos en que el sujeto pueda utilizarlo como deducción.
			#22 Impuesto al Consumo de las Bolsas de Plástico.
			#23 Otros conceptos, tributos y cargos que no formen parte de la base imponible.
			#adquision_no_grabada = move.obtener_total_base_inafecto()

			valor_campo_16 = move.obtener_valor_campo_16(tipo_cambio)
			valor_campo_17 = move.obtener_valor_campo_17(tipo_cambio)
			valor_campo_18 = move.obtener_valor_campo_18(tipo_cambio)
			valor_campo_19 = move.obtener_valor_campo_19(tipo_cambio)
			valor_campo_20 = move.obtener_valor_campo_20(tipo_cambio)
			valor_campo_21 = move.obtener_valor_campo_21(tipo_cambio)
			valor_campo_22 = move.obtener_valor_campo_22(tipo_cambio)
			valor_campo_23 = move.obtener_valor_campo_23(tipo_cambio)
			m_01.extend([valor_campo_16, valor_campo_17, valor_campo_18, valor_campo_19, valor_campo_20, valor_campo_21, valor_campo_22, valor_campo_23]) #ICBP
			#24
			monto_total = abs(move.amount_total_signed)
			m_01.extend([format(monto_total, '.2f')])
			#25-26 (Codigo de moneda y tipo de cambio - son opcionales)
			tipo_cambio = format(tipo_cambio, '.3f')
			m_01.extend([str(move.currency_id.name), tipo_cambio])
			#27-31
			# notas credito
			if sunat_code in ['07'] :
				origin = move.reversed_entry_id
				origin_number = origin.ref
				origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
				m_01.extend([origin.invoice_date.strftime('%d/%m/%Y'), origin.pe_invoice_code])
				m_01.append(origin_number[0])
				m_01.append('')
				m_01.append(origin_number[1])
			# notas debito
			elif sunat_code in ['08'] :
				origin = move.debit_origin_id
				origin_number = origin.ref
				origin_number = origin_number and ('-' in origin_number) and origin_number.split('-') or ['', '']
				m_01.extend([origin.invoice_date.strftime('%d/%m/%Y'), origin.pe_invoice_code])
				m_01.append(origin_number[0])
				m_01.append('')
				m_01.append(origin_number[1])
			else :
				m_01.extend(['', '', '', '', ''])
			
			#32-33 (Datos para pago de detracciones)
			if move.tiene_detraccion and move.pago_detraccion:
				m_01.extend([move.pago_detraccion.date.strftime('%d/%m/%Y'), move.pago_detraccion.transaction_number])
			else:
				m_01.extend(['', ''])
			#34 (Datos para pago de retencion)
			if move.tiene_retencion:
				m_01.extend(['1'])
			else:
				m_01.extend([''])
			#35-38
			tipo_bien_servicio = move.invoice_line_ids.filtered(lambda linea: linea.product_id.product_tmpl_id.tipo_bien_servicio)
			if tipo_bien_servicio:
				tipo_bien_servicio = tipo_bien_servicio[0].product_id.product_tmpl_id.tipo_bien_servicio
			else:
				tipo_bien_servicio = ''
			m_01.extend([tipo_bien_servicio, '', '', ''])
			#39-43
			codigo = '1'
			if invoice_date < fecha_inicio:
				codigo = '6'
			if sunat_code in ['02']:
				codigo = '0'

			m_01.extend(['', '', '',codigo, ''])
			
			#m_01.extend(['', '', '', '', '', '', '', '', '', '', codigo, ''])
		except Exception as e:
			_logging.info(":::::::::::::::::::::::::::::::::::::::::::::::::::::")
			_logging.info(e)
			raise Warning('Ocurrio un inconveniente: %s' % str(e))
			m_01 = []

		return m_01

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	glosa = fields.Char("Glosa", related="move_id.glosa", store=True)
