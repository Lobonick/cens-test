import logging

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'
	
	document_type_code = fields.Char(string='Code', related="l10n_latam_document_type_id.code", store=True)
	asiento_letters = fields.Many2one('letter.management', string="Seats / Letters")
	bank_id = fields.Many2one('res.bank', string='Bank')
	endorsement = fields.Many2one('res.partner', string='Endorsement')
	letter_create_id = fields.Many2one('letter.management', string='Generated from Letter Template N°', copy=False)
	debit_create_id = fields.Many2one('letter.management', string='Debit Note generated from template', copy=False)
	seat_generated_id = fields.Many2one('letter.management', string='Seat generated from template', copy=False)
	have_letters_generated_id = fields.Many2one('letter.management', string='Template Ref.', copy=False)
	bank_acc_number_id = fields.Many2one('res.partner.bank', string='Account Number')
	new_bank_id = fields.Many2one('res.bank', string='Send to Bank')
	last_tracing = fields.Many2one('letter.masterlocations', string='Tracing', readonly=True, compute='_last_tracking',
								   store=True)

	document_type_id = fields.Many2one("l10n_latam.document.type", related="l10n_latam_document_type_id")

	tracing_ids = fields.One2many('letter.locations', 'doc_letters_id', string='Tracing')

	document_number_agra = fields.Char(string='Numero de documento',
									   related='letter_create_id.letter_det_ids.document_number')
	city = fields.Char(string='Turn Place', related='company_id.city')
	phone = fields.Char(related='partner_id.phone', store=True, readonly=False, string='Phone')
	office_name = fields.Char(string='Office')
	unique_code_supplier = fields.Char(string='Unique Code')

	send_date = fields.Date(string='Shipping date')
	acceptance_date = fields.Date(string='Acceptance Date')
	date_amortize = fields.Date(string='Date Amortize', copy=False, default=lambda s: fields.Date.context_today(s))

	how_days_expires = fields.Integer(string='Expiration Days')
	# acc_number = fields.Integer(string='Account Number')

	letter_amount = fields.Monetary(string='Net', store=True, compute='_compute_first_amount', inverse='_inverse_first_amount')
	# amount_interest = fields.Float(string='Interest amount')
	amount_discount = fields.Monetary(string='Discount')
	amount_letter = fields.Monetary(string='Amount Letter')

	letter_state = fields.Selection([
		('portfolio', 'In portfolio'),
		('collection', 'In collection'),
		('warranty', 'In warranty'),
		('discount', 'In discount'),
		('protest', 'In protest'),
		], string='Letter State', default='portfolio')

	have_letters_template_cancelled = fields.Boolean(string='Template cancelled', default=False, copy=False)
	is_seat_generated = fields.Boolean(string='Asiento generado', default=False)

	templates_cancelled_ids = fields.Many2many('letter.management', string='Plantillas de letras canceladas')

	############## POLIMASTER ################
	# Campos
	payment_state = fields.Selection(selection_add=[('redeemed', 'Redeemed'), ('in_redemption', 'Partial redeemed')], ondelete={'redeemed': 'set null', 'in_redemption': 'set null'})
	acceptor_id = fields.Many2one('res.partner', string='Acceptor')
	field_invisible = fields.Boolean(compute='_is_same_partner', default=True)

	sunat_serie = fields.Char("Sunat Serie", compute="_compute_datos_sunat", store=True)
	sunat_number = fields.Char("Sunat number", compute="_compute_datos_sunat", store=True)

	sale_type = fields.Selection([
		('counted', 'Counted'),
		('credit', 'Credit')], compute="_compute_sale_type", store=True)

	def _get_rates(self):
		active_id = self.env.context.get('active_id')
		active_model = self.env.context.get('active_model')
		# rate = letter_management.currency_id._convert(1, letter_management.company_id.currency_id, letter_management.company_id, self.reconcile_date or datetime.now(), False)
		domain = [('currency_id.id', '=', self.currency_id.id),
					('name', '=', fields.Date.to_string(self.exchange_date)),
					('company_id.id', '=', self.company_id.id)]
		currency = self.env['res.currency.rate'].search(domain, limit=1)

	exchange_date = fields.Date(string='Date', default=fields.Date.context_today)
	exchange_rate = fields.Float(string="Exchange rate", digits='Exchange rate', store=True, readonly=False, default=_get_rates)

	@api.depends('l10n_latam_document_number')
	def _compute_datos_sunat(self):
		for reg in self:
			datos = reg.l10n_latam_document_number.split("-") if reg.l10n_latam_document_number else []
			if len(datos) == 2:
				reg.sunat_serie = datos[0]
				reg.sunat_number = datos[1]
			else:
				reg.sunat_serie = ""
				reg.sunat_number = ""
	

	def _get_account_for_payment(self):
		#res = super()._get_account_for_payment()
		res = self.line_ids.filtered(lambda l: l.debit > 0)[0].account_id.id
		if self.is_invoice(include_receipts=True):
			if self.document_type_code == 'LT' and self.letter_state == 'discount':
				res = self.line_ids.filtered(lambda l: l.debit > 0)[0].account_id.id
			else:
				res = self.line_ids.filtered(lambda l: l.debit > 0)[0].account_id.id
		return res

	@api.depends('tipo_transaccion')
	def _compute_sale_type(self):
		for reg in self:
			tipo = 'counted'
			if reg.tipo_transaccion == 'credito':
				tipo = 'credit'
			reg.sale_type = tipo

	@api.depends('acceptor_id')
	def _is_same_partner(self):
		for rec in self:
			if rec.partner_id == rec.acceptor_id:
				rec.field_invisible = True
			else:
				rec.field_invisible = False 

	@api.onchange('date', 'currency_id')
	def _onchange_currency(self):
		# Si cambiamos la moneda de la letras actualizamos la cuenta desde homologación
		if self.l10n_latam_document_type_id.code == 'LT' and self.letter_state == 'portfolio':
			if self.move_type == 'out_invoice':
				account_id = self.env['account.update'].search([('document_type_id','=',self.l10n_latam_document_type_id.id),('transaction_type','=','is_sale_document'),('letter_state','=',self.letter_state),('currency_id','=',self.currency_id.id)]).account_id
				if not account_id:
					account_id = self.partner_id.property_account_receivable_id.id
					
				if not account_id:
					raise UserError('No se encontro cuenta para out_invoice')
				self.line_ids.filtered(lambda l: l.debit > 0).account_id = account_id
			else:
				account_id = self.env['account.update'].search([('document_type_id','=',self.l10n_latam_document_type_id.id),('transaction_type','=','is_purchase_document'),('letter_state','=',self.letter_state),('currency_id','=',self.currency_id.id)]).account_id
				if not account_id:
					account_id = self.partner_id.property_account_payable_id.id
				if not account_id:
					raise UserError('No se encontro cuenta para not out_invoice')
				self.line_ids.filtered(lambda l: l.credit > 0).account_id = account_id

	@api.depends('invoice_line_ids.price_unit')
	def _compute_first_amount(self):
		for rec in self:
			# rec.letter_amount = 0.0
			if rec.invoice_line_ids:
				# if rec.letter_create_id.operation_methods in ['discount']:
				#     disc = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
				#     rec.invoice_line_ids[0].price_unit = disc
				# else:
				precio_unit = rec.invoice_line_ids[0].price_unit
				rec.letter_amount = rec.currency_id.round(precio_unit)

	@api.depends('tracing_ids.state_tracing')
	def _last_tracking(self):
		for rec in self:
			rec.last_tracing = False
			for line in rec.tracing_ids:
				rec.last_tracing = line.state_tracing and line.state_tracing.id or False

	@api.onchange('letter_amount')
	def _onchange_amount_letter_line(self):
		for rec in self:
			if rec.letter_create_id.operation_methods in ['portfolio']:
				if rec.letter_amount != rec.amount_total:
					rec._inverse_first_amount()
					if not rec.exchange_rate:
						rec.line_ids[1].debit = rec.letter_amount
						rec.amount_total = rec.letter_amount
				# if rec.letter_create_id.operation_methods in ['renewal', 'refinancing']:
				#     if rec.document_type_code == 'LT':
				#     if not rec.letter_create_id.is_debit_generated:
				#         rec.amount_letter = rec.letter_amount + rec.amount_discount
				#         rec.line_ids[1].debit = rec.amount_letter
				if rec.document_type_code == '08':
					if rec.letter_create_id.all_amount_interest != rec.letter_amount:
						rec.letter_amount = rec.letter_create_id.all_amount_interest
						rec.amount_letter = rec.letter_amount
						rec.line_ids[1].debit = rec.amount_letter
			# if rec.debit_create_id.operation_methods in ['renewal', 'refinancing']:
			#     if not rec.debit_create_id._tax_ids_debit:
			#         # if rec.debit_create_id.is_debit_generated:
			#         rec.amount_total = rec.letter_amount
			#         rec.line_ids[1].debit = rec.letter_amount
			# else:
			#     rec.letter_
			# else:
			#     if rec.debit_create_id._tax_ids_debit
			# if rec.letter_create_id.operation_methods not in ['discount']:
			rec._onchange_currency()

	@api.onchange('how_days_expires', 'invoice_date')
	def _onchange_how_days_expires(self):
		for rec in self:
			how_days_expires = rec.how_days_expires or 0
			if rec.invoice_date:
				rec.invoice_date_due = rec.invoice_date + timedelta(days=how_days_expires)

	@api.onchange('invoice_date_due')
	def _onchange_invoice_date_due(self):
		for rec in self:
			number_days_to_expires = False
			if rec.invoice_date_due and rec.invoice_date:
				if rec.invoice_date < rec.invoice_date_due:
					number_days_to_expires = abs((rec.invoice_date - rec.invoice_date_due).days)
				else:
					number_days_to_expires = (rec.invoice_date_due - rec.invoice_date).days
			if not rec.invoice_date_due or not rec.invoice_date or not number_days_to_expires or number_days_to_expires == 0:
				rec.how_days_expires = 0
			if number_days_to_expires:
				rec.how_days_expires = number_days_to_expires

	# @api.onchange('amount_discount')
	# def _compute_discount(self):
	#     for rec in self:
	#         if rec.letter_create_id.operation_methods in ['discount']:
	#             rec.letter_amount = 0.0
	#             rec.invoice_line_ids[0].price_unit = 0.0
	#             if rec.amount_discount != 0:
	#                 discount = abs(rec.amount_discount)
	#                 rec.amount_discount = -discount
	# rec.amount_discount = rec.currency_id.round(-discount)
	# rec.letter_amount = rec.currency_id.round(rec.amount_letter - discount)
	#     else:
	#         rec.amount_discount = 0
	#     rec.letter_amount = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
	#     rec._inverse_first_amount()
	# rec._onchange_currency()

	def _inverse_first_amount(self):
		for rec in self:
			if rec.document_type_code in ['LT']:
				# if rec.type in ['out_invoice']:
				rec.amount_residual = 0
				# if rec.letter_create_id.operation_methods in ['discount']:
				#     precio_unit = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
				# rec.invoice_line_ids[0].price_unit = precio_unit
				# else:
				precio_unit = rec.currency_id.round(rec.letter_amount)
				if rec.invoice_line_ids:
					rec.invoice_line_ids[0].price_unit = precio_unit
				rec._onchange_currency()

	# def _check_amount(self):
	#     for rec in self:
	#         for line in rec.line_ids:
	#             line._onchange_currency()

	def _account_custom_invoice(self):
		res = super(AccountMove, self)._account_custom_invoice()
		domain = [('currency_id', '=', self.currency_id.id),
				  ('document_type_id', '=', self.l10n_latam_document_type_id.id),
				  ('company_id', '=', self.company_id.id)]
		if self.document_type_code == 'LT' and self.letter_state:
			domain = expression.AND([domain, [('letter_state', '=', self.letter_state)]])
		if self.is_sale_document(include_receipts=True):
			domain = expression.AND([domain, [('transaction_type', '=', 'is_sale_document')]])
			account = self.env['account.update'].search(domain, limit=1)
			if account:
				res = account.account_id
			else:
				raise UserError('No se encontro cuenta para is_sale_document')
		else:
			domain = expression.AND([domain, [('transaction_type', '=', 'is_purchase_document')]])
			account = self.env['account.update'].search(domain, limit=1)
			if account:
				res = account.account_id
			else:
				raise UserError('No se encontro cuenta para not is_sale_document')
		return res

	def _reverse_move_vals(self, default_values, cancel=True):
		res = super(AccountMove, self)._reverse_move_vals(default_values, cancel)
		if self.move_type in ['in_invoice', 'out_invoice', 'in_refund', 'out_refund']:
			document = self.env.ref('qa_letter_management.document_type_07_letter').id
			serie = self._default_sunat_serie(document, self.env.company.id)
			if self.document_type_code == 'LT':
				if not serie:
					raise UserError('No se ha encontrado una serie de Nota de Crédito interna, por favor, crear una.')
				res['l10n_latam_document_type_id'] = document
				#res['sunat_serie'] = serie
		return res

	def download_file_letter(self):
		return self.env.ref('qa_letter_management.action_report_letter_agra').report_action(self)

	def cancel_document(self):
		for rec in self:
			if rec.have_letters_generated_id:
				template = str(rec.have_letters_generated_id.id)
				if not rec.templates_cancelled_ids:
					raise UserError(
						'Cancele primero la plantilla de letras N° ' + template + '.\n'
						'En la parte baja de este documento puede ver la trazabilidad por si es que se generaron varias plantillas de letras con este documento.')
				else:
					return super(AccountMove, self).cancel_document()
			else:
				return super(AccountMove, self).cancel_document()

	def button_draft(self):
		for rec in self:
			if rec.have_letters_generated_id:
				if rec.templates_cancelled_ids:
					_logger.info(
						f'{rec.id} {rec.name} --> Factura que tiene plantillas de letras canceladas {rec.templates_cancelled_ids}')
					return super(AccountMove, self).button_draft()
					# raise UserError('No puedes convertir a borrador un documento que ha generado letras y que ahora está cancelado')
				else:
					_logger.info(
						f'{rec.id} {rec.name} --> Factura que intentó cancelarse pero tiene plantillas de letras sin cancelar')
					raise UserError('No puedes convertir a borrador un documento que está generando letras')
			else:
				# if rec.letter_create_id and rec.letter_create_id.state != 'cancel':
				#     raise UserError(
				#         'No puedes convertir a borrador una letra que ha sido generada desde una plantilla.')
				# else:
				return super(AccountMove, self).button_draft()

	############## POLIMASTER ################
	# Funciones
	@api.depends(
		'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
		'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
		'line_ids.debit',
		'line_ids.credit',
		'line_ids.currency_id',
		'line_ids.amount_currency',
		'line_ids.amount_residual',
		'line_ids.amount_residual_currency',
		'line_ids.payment_id.state',
		'line_ids.full_reconcile_id')
	def _compute_amount(self):
		res = super(AccountMove, self)._compute_amount()
		for move in self:
			currencies = move._get_lines_onchange_currency().currency_id
			currency = len(currencies) == 1 and currencies or move.company_id.currency_id
			# Compute 'payment_state'.
			new_pmt_state = move.payment_state #'not_paid' if move.move_type != 'entry' else False

			if move.document_type_code != 'LT':
				if move.state == 'posted':
					reconciled_payments = move._get_reconciled_payments()
					if currency.is_zero(move.amount_residual):
						if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process' and move.have_letters_generated_id.operation_methods != 'discount':
							new_pmt_state = 'redeemed'
					else:
						if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process':
							new_pmt_state = 'in_redemption'
			else:
				if move.state == 'posted':
					reconciled_payments = move._get_reconciled_payments()
					if currency.is_zero(move.amount_residual):
						new_pmt_state = 'paid'
					# else:
					#     new_pmt_state = 'partial'

			# if move.is_invoice(include_receipts=True) and move.state == 'posted':
			#     reconciled_payments = move._get_reconciled_payments()
			#     if currency.is_zero(move.amount_residual):
			#         if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
			#             new_pmt_state = 'paid'
			#         else:
			#             new_pmt_state = move._get_invoice_in_payment_state()
			#     # if any(payment.document_type_code == 'LT' for payment in reconciled_payments) and move.document_type_code != 'LT':
			#     if move.document_type_code != 'LT':
			#         if currency.is_zero(move.amount_residual):
			#             if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process' and move.have_letters_generated_id.operation_methods != 'discount':
			#                 new_pmt_state = 'redeemed'
			#         else:
			#             if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process':
			#                 new_pmt_state = 'in_redemption'
			#     else:
			#         if currency.is_zero(move.amount_residual):
			#             if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process' and move.have_letters_generated_id.operation_methods == 'discount':
			#                 new_pmt_state = 'paid'
			#         else:
			#             if move.have_letters_generated_id and move.have_letters_generated_id.state == 'in_process' and move.have_letters_generated_id.operation_methods == 'discount':
			#                 new_pmt_state = 'partial'
			#         if move.have_letters_generated_id and move.have_letters_generated_id.operation_methods == 'protest':
			#             new_pmt_state = 'paid'
			#         if move.letter_create_id and move.letter_create_id.operation_methods == 'discount':
			#             if reconciled_payments.mapped('amount') == move.amount_total:
			#                 new_pmt_state = 'paid'
			#             else:
			#                 new_pmt_state = 'partial'
			move.payment_state = new_pmt_state
		return res

	def js_remove_outstanding_partial(self, partial_id):
		partial = self.env['account.partial.reconcile'].browse(partial_id)
		move_ids = partial.debit_move_id.move_id + partial.credit_move_id.move_id
		if any(line in move_ids.have_letters_generated_id.seat_generated_by_payment_ids.line_ids for line in self.line_ids):
			raise UserError(_('Can\'t unreconcile this payment because it was redeemed. Please revert the redemption and try again.'))
		return super(AccountMove, self).js_remove_outstanding_partial(partial_id)

	def unlink(self):
		for rec in self:
			if rec.document_type_code == 'LT' and rec.state == 'draft' and rec.letter_create_id and not self.env.context.get('force_delete'):
				raise UserError(_('You can\'t delete letters in draft state. Please delete them from the template they were created.' ))
		return super().unlink()