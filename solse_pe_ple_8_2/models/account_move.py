# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import datetime
from dateutil.relativedelta import relativedelta
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def _get_pe_table_11(self):
		return self.env['pe.datas'].get_selection('PE.TABLA11')

	@api.model
	def _get_pe_table_27(self):
		return self.env['pe.datas'].get_selection('PE.TABLA27')

	@api.model
	def _get_pe_table_25(self):
		return self.env['pe.datas'].get_selection('PE.TABLA25')

	@api.model
	def _get_pe_table_33(self):
		return self.env['pe.datas'].get_selection('PE.TABLA33')

	@api.model
	def _get_pe_table_32(self):
		return self.env['pe.datas'].get_selection('PE.TABLA32')

	@api.model
	def _get_pe_table_31(self):
		return self.env['pe.datas'].get_selection('PE.TABLA31')

	# DUAs
	l10n_pe_edi_table_11_id = fields.Selection('_get_pe_table_11', string='Dependencia aduanera', help='Dependencia aduanera (Tabla 11)')
	l10n_pe_dua_emission_year = fields.Selection([(str(num), str(num)) for num in range(1981, (datetime.datetime.now().year+1))], string='Año de emisión DUA o DSI')


	# NO DOMICILIADO
	l10n_pe_is_non_domiciled = fields.Boolean(string='No domiciliado', compute='_compute_l10n_pe_is_non_domiciled', store=True)

	# aun no se llena
	l10n_pe_non_domic_sustent_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento del Sustento', help='Tipo de Comprobante de Pago o Documento que sustenta el crédito fiscal')
	l10n_pe_non_domic_sustent_serie = fields.Char(string='Serie del Sustento', help='Serie del comprobante de pago o documento que sustenta el crédito fiscal. En los casos de la Declaración Única de Aduanas (DUA) o de la Declaración Simplificada de Importación (DSI) se consignará el código de la dependencia Aduanera.')
	l10n_pe_non_domic_sustent_number = fields.Char(string='Correlativo del Sustento', help='Número del comprobante de pago o documento o número de orden del formulario físico o virtual donde conste el pago del impuesto, tratándose de la utilización de servicios prestados por no domiciliados u otros, número de la DUA o de la DSI, que sustente el crédito fiscal.')

	l10n_pe_non_domic_sustent_dua_emission_year = fields.Selection([(str(num), str(num)) for num in range(1981, (datetime.datetime.now().year+1))], string='Año de emisión DUA o DSI')

	l10n_pe_non_domic_igv_withholding_amount = fields.Float(string='Monto de retención del IGV')
	no_dom_vinculo = fields.Selection('_get_pe_table_27', string='Vínculo con el no domiciliado', help='Vínculo entre el contribuyente y el residente en el extranjero')
	l10n_pe_non_domic_brute_rent_amount = fields.Monetary(string='Renta Bruta')
	l10n_pe_non_domic_disposal_capital_assets_cost = fields.Float(string='Costo de Enajenación', help='Deducción / Costo de Enajenación de bienes de capital')
	l10n_pe_non_domic_net_rent_amount = fields.Float(string='Renta Neta')
	l10n_pe_non_domic_withholding_rate = fields.Float(string='Tasa de retención')
	l10n_pe_non_domic_withheld_tax = fields.Float(string='Impuesto retenido')
	no_dom_convenio = fields.Selection('_get_pe_table_25', string='Convenios', help='Convenios para evitar la doble imposición')
	no_dom_exoneracion = fields.Selection('_get_pe_table_33', string='Exoneración aplicada')
	no_dom_modalidad = fields.Selection('_get_pe_table_32', string='Modalidad de servicio', help='Modalidad del servicio prestado por el no domiciliado')
	no_dom_tipo_renta = fields.Selection('_get_pe_table_31', string='Tipo de renta')

	l10n_pe_non_domic_is_tax_rent_applied = fields.Boolean(string='Aplicación de Impuesto a la renta', help='Aplicación del penúltimo parrafo del Art. 76° de la Ley del Impuesto a la Renta')
	l10n_pe_non_domic_tax_rent_code = fields.Char(string='Código de aplicación de impuesto a la renta', compute='_compute_l10n_pe_non_domic_tax_rent_code', store=True)

	# Datos del proveedor
	l10n_pe_partner_name = fields.Char('Razón social del proveedor', related='partner_id.name')
	l10n_pe_partner_country_name = fields.Char('País de residencia del proveedor', related='partner_id.country_id.name')
	l10n_pe_partner_street = fields.Char('Dirección del proveedor', related='partner_id.street')
	l10n_pe_partner_vat = fields.Char('Número de identificación del proveedor', related='partner_id.vat')

	l10n_pe_no_domic_annotation_opportunity_status = fields.Selection(string='Estado PLE no domiciliado', selection=[
		('0', 'La operación (anotación optativa sin efecto en el IGV) corresponde al periodo. '),
		('9', 'Ajuste o rectificación en la anotación de la información de una operación registrada en un periodo anterior.')
	], default='0', help='Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste.')

	
	l10n_pe_project_identification = fields.Char(string='Identificación del Contrato o del proyecto', default='', help='Identificación del Contrato o del proyecto en el caso de los Operadores de las sociedades irregulares, consorcios, joint ventures u otras formas de contratos de colaboración empresarial, que no lleven contabilidad independiente.')
	l10n_pe_proof_detraction_deposit_date = fields.Date(string='Fecha de emisión de la Constancia de Depósito de Detracción (5)')
	l10n_pe_proof_detraction_deposit_number = fields.Char(string='Número de la Constancia de Depósito de Detracción (5)')
	
	l10n_pe_subject_to_withholding_code = fields.Char(string='Código de sujeto a retención', compute='_compute_subject_to_withholding_code', store=True)
	
	l10n_pe_operation_type = fields.Selection([
		('1', 'INTERNAL SALE'),
		('2', 'EXPORTATION'),
		('3', 'NON-DOMICILED'),
		('4', 'INTERNAL SALE - ADVANCES'),
		('5', 'ITINERANT SALE'),
		('6', 'GUIDE INVOICE'),
		('7', 'SALE PILADO RICE'),
		('8', 'INVOICE - PROOF OF PERCEPTION'),
		('10', 'INVOICE - SENDING GUIDE'),
		('11', 'INVOICE - CARRIER GUIDE'),
		('12', 'SALES TICKET - PROOF OF PERCEPTION'),
		('13', 'NATURAL PERSON DEDUCTIBLE EXPENSE'),
	], string='Transaction type', help='Default 1, the others are for very special types of operations, do not hesitate to consult with us for more information', default='1')
	
	l10n_pe_in_annotation_opportunity_status = fields.Selection(string='Estado PLE Compras', selection=[
		('0', 'Base imponible adquisiciones gravadas que no dan derecho a crédito fiscal, destinadas a operaciones no gravadas(campo 18)  >0'),
		('1', 'Si fecha de emisión o fecha de pago de impuesto, por operaciones que dan derecho a crédito fiscal, corresponde al período de declaración.(campo 14 o campo 16 mayores a cero)'),
		('6', 'Si fecha de emisión o fecha de pago de impuesto, por operaciones que dan derecho a crédito fiscal,  es anterior al periodo de declaración y dentro los doce meses siguientes a la emisión o pago del impuesto.(campo 14 o campo 16 mayores a cero)'),
		('7', 'Si fecha de emisión o fecha de pago de impuesto, por operaciones que no dan derecho a crédito fiscal,  es anterior al periodo de declaración y dentro los doce meses siguientes a la emisión o pago del impuesto.(campo 14 o campo 16 mayores a cero)'),
		('9', 'Si se realiza un ajuste o rectificación en la información de una operación registrada en un periodo anterior.')
	], default='1', help='Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste.', compute='_compute_in_annotation_opportunity_status', readonly=False)

	@api.depends('partner_id.country_id')
	def _compute_l10n_pe_is_non_domiciled(self):
		for record in self:
			if record.partner_id.country_id.id != 173:
				l10n_pe_is_non_domiciled = True
			else:
				l10n_pe_is_non_domiciled = False
			record.l10n_pe_is_non_domiciled = l10n_pe_is_non_domiciled


	@api.depends('tiene_retencion')
	def _compute_subject_to_withholding_code(self):
		for record in self:
			if record.tiene_retencion:
				record.l10n_pe_subject_to_withholding_code = '1'
			else:
				record.l10n_pe_subject_to_withholding_code = ''

	def _l10n_no_domic_validation(self):
		is_non_domic = self.move_type in [
			'in_invoice', 'in_refund'] and self.l10n_pe_is_non_domiciled
		if is_non_domic and not self.no_dom_convenio:
			raise UserError('Debe escribir los convenios para evitar la doble imposición.')
		if is_non_domic and not self.no_dom_tipo_renta:
			raise UserError('Debe escribir el tipo de renta.')
		if is_non_domic and not self.l10n_pe_no_domic_annotation_opportunity_status:
			raise UserError('Debe escribir el Estado PLE no domiciliados.')

	def action_post(self):
		self._l10n_no_domic_validation()
		super(AccountMove, self).action_post()

	@api.depends('l10n_pe_non_domic_is_tax_rent_applied')
	def _compute_l10n_pe_non_domic_tax_rent_code(self):
		for record in self:
			if record.l10n_pe_non_domic_is_tax_rent_applied:
				record.l10n_pe_non_domic_tax_rent_code = '1'
			else:
				record.l10n_pe_non_domic_tax_rent_code = ''

	def get_table_11_code(self):
		table_11_code = self.l10n_pe_edi_table_11_id
		if not table_11_code:
			table_11_code = ''
		return table_11_code

	def get_reversed_entry_table_11_code(self):
		origin_invoice_id = False
		if self.reversed_entry_id:
			origin_invoice_id = self.reversed_entry_id
		if self.debit_origin_id:
			origin_invoice_id = self.debit_origin_id
		if origin_invoice_id:
			table_11_code = origin_invoice_id.get_table_11_code()
		else:
			table_11_code = ''
		return table_11_code

	def _compute_in_annotation_opportunity_status(self):
		for record in self:
			l10n_pe_in_annotation_opportunity_status = False
			if record.invoice_date and record.date:
				entry_in_last_year = (record.date - relativedelta(years=1)) <= record.invoice_date
				entry_in_last_month = record.date.month == record.invoice_date.month and record.date.year == record.invoice_date.year
				# No da credito fiscal
				if record.pe_invoice_code == '03' or record.pe_amount_tax == 0:
					if entry_in_last_month:
						l10n_pe_in_annotation_opportunity_status = '0'
					elif entry_in_last_year:
						l10n_pe_in_annotation_opportunity_status = '0'
					else:
						l10n_pe_in_annotation_opportunity_status = '7'
				# Si da credito fiscal
				else:
					if entry_in_last_month:
						l10n_pe_in_annotation_opportunity_status = '1'
					elif entry_in_last_year:
						l10n_pe_in_annotation_opportunity_status = '6'
			record.l10n_pe_in_annotation_opportunity_status = l10n_pe_in_annotation_opportunity_status
			
	def ple_8_2_fields(self, contador, fecha_inicio):
		fecha_busqueda = str(self.invoice_date)
		currency_rate_id = [
			('name', '=', fecha_busqueda),
			('company_id','=', self.company_id.id),
			('currency_id','=', self.currency_id.id),
		]
		currency_rate_id = self.env['res.currency.rate'].sudo().search(currency_rate_id)
		tipo_cambio = 1.000
		if currency_rate_id:
			tipo_cambio = currency_rate_id.rate_pe

		tipo_cambio = format(tipo_cambio, '.3f')

		m_01 = self.ple_8_1_fields(contador, fecha_inicio)
		m_02 = []
		# 1-4
		m_02.extend(m_01[0:4])
		# 5-7
		m_02.extend(m_01[6:9]),
		# 8-10
		m_02.extend([m_01[23],'',m_01[23]]),
		# 11-15
		m_02.extend([
			# 11 Tipo de Comprobante de Pago o Documento que sustenta el crédito fiscal
			self.l10n_pe_non_domic_sustent_document_type_id.code or '',
			# 12 Serie del comprobante de pago o documento que sustenta el crédito fiscal. En los casos de la Declaración Única de Aduanas (DUA) o de la Declaración Simplificada de Importación (DSI) se consignará el código de la dependencia Aduanera.
			self.l10n_pe_non_domic_sustent_serie or '',
			# 13 Año de emisión de la DUA o DSI que sustenta el crédito fiscal
			self.l10n_pe_non_domic_sustent_dua_emission_year or '',
			# 14 Número del comprobante de pago o documento o número de orden del formulario físico o virtual donde conste el pago del impuesto, tratándose de la utilización de servicios prestados por no domiciliados u otros, número de la DUA o de la DSI, que sustente el crédito fiscal.
			self.l10n_pe_non_domic_sustent_number or '',
			# 15 Monto de retención del IGV
			str(self.l10n_pe_non_domic_igv_withholding_amount),
		])
		# 16-24
		m_02.extend([
				# 16 REQUIRED: Código  de la Moneda (Tabla 4)
				self.currency_id.name,
				# 17 Tipo de cambio (5)
				tipo_cambio or '',
				# 18 REQUIRED: Pais de la residencia del sujeto no domiciliado
				self.l10n_pe_partner_country_name or '',
				# 19 REQUIRED: Apellidos y nombres, denominación o razón social  del sujeto no domiciliado. En caso de personas naturales se debe consignar los datos en el siguiente orden: apellido paterno, apellido materno y nombre completo.
				self.l10n_pe_partner_name or '',
				# 20 Domicilio en el extranjero del sujeto no domiciliado
				self.l10n_pe_partner_street or '',
				# 21 REQUIRED: Número de identificación del sujeto no domiciliado
				self.l10n_pe_partner_vat or '',
				# 22 Número de identificación fiscal del beneficiario efectivo de los pagos
				'',
				# 23 Apellidos y nombres, denominación o razón social  del beneficiario efectivo de los pagos. En caso de personas naturales se debe consignar los datos en el siguiente orden: apellido paterno, apellido materno y nombre completo.
				'',
				# 24 Pais de la residencia del beneficiario efectivo de los pagos
				'',
		])
		# 25-36
		m_02.extend([
			# 25 Vínculo entre el contribuyente y el residente en el extranjero
			self.no_dom_vinculo or '',
			# 26 Renta Bruta
			str(self.l10n_pe_non_domic_brute_rent_amount),
			# 27 Deducción / Costo de Enajenación de bienes de capital
			str(self.l10n_pe_non_domic_disposal_capital_assets_cost),
			# 28 Renta Neta
			str(self.l10n_pe_non_domic_net_rent_amount),
			# 29 Tasa de retención
			str(self.l10n_pe_non_domic_withholding_rate),
			# 30 Impuesto retenido
			str(self.l10n_pe_non_domic_withheld_tax),
			# 31 REQUIRED: Convenios para evitar la doble imposición Tabla 25
			self.no_dom_convenio or '',
			# 32 Exoneración aplicada
			self.no_dom_exoneracion or '',
			# 33 REQUIRED: Tipo de Renta
			self.no_dom_tipo_renta or '',
			# 34 Modalidad del servicio prestado por el no domiciliado
			self.no_dom_modalidad or '',
			# 35 Aplicación del penultimo parrafo del Art. 76° de la Ley del Impuesto a la Renta
			self.l10n_pe_non_domic_tax_rent_code or '',
			# 36 REQUIRED: Estado que identifica la oportunidad de la anotación o indicación si ésta corresponde a un ajuste.
			self.l10n_pe_no_domic_annotation_opportunity_status or '',
			# 37 Campos de libre utilización
			''
		])
		return m_02
