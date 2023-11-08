import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, Warning
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_round
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)

STATE_SELECTION = [('draft', 'Draft'), ('in_process', 'In Process'), ('posted', 'Posted'), ('cancel', 'Cancelado')]
PAYMENT_TYPE_SELECTION = [('outbound', 'Send money'), ('inbound', 'Receive money')]
MOVE_TYPE_SELECTION = [('entry', 'Journal Entry'),
		('out_invoice', 'Customer Invoice'), ('out_refund', 'Customer Credit Note'), ('out_receipt', 'Sales Receipt'),
		('in_invoice', 'Vendor Bill'), ('in_refund', 'Vendor Credit Note'), ('in_receipt', 'Purchase Receipt')]
OPERATION_METHOD_SELECTION = [('portfolio', 'Exchange'), ('collection', 'Collection'), ('discount', 'Discount'),
		('refinancing', 'Refinancing'), ('renewal', 'Renewal'), ('protest', 'Protest'), ('return', 'Return')]


class LetterManagement(models.Model):
	_name = 'letter.management'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = "Template for the generation of type documents: letters and debit notes"
	_rec_name = 'id'

	name = fields.Char(string='Template Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	date = fields.Date(string='Date ', required=True, copy=False, default=lambda s: fields.Date.context_today(s))
	exchange_date = fields.Date(string="Exchange Date")
	document_type_id = fields.Many2one('l10n_latam.document.type', 'Doc. type')

	exchange_type = fields.Selection([('collection', 'Collection'), ('payment', 'Payment')],
									 string='Exchange Type')
	journal_id_type_bank_id = fields.Many2one('account.journal', string='Bank', readonly=True,
											  states={'draft': [('readonly', False)]}, tracking=True,
											  domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
	state = fields.Selection(STATE_SELECTION, string='State', default='draft', tracking=True)
	partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Supplier')], string='Partner Type')
	payment_type = fields.Selection(PAYMENT_TYPE_SELECTION, string="Way to pay", required=True, readonly=True)
	operation_methods = fields.Selection(OPERATION_METHOD_SELECTION, string='Operation Method', default='portfolio', required=True, readonly=True)
	move_type = fields.Selection(MOVE_TYPE_SELECTION, string="Type")
	internal_type = fields.Selection([('wizard', 'Emergente'), ('window', 'Pantalla')], readonly=True, default='window',
									 string='View Type')

	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
	currency_id = fields.Many2one('res.currency', string='Currency', required=True,
								  default=lambda self: self.env.company.currency_id)
	partner_id = fields.Many2one('res.partner', string='Business')
	debit_notes_serie_id = fields.Many2one(comodel_name='ir.sequence', string="Serie", ondelete="restrict")
	invoice_user_id = fields.Many2one('res.users', copy=False, string='Salesperson', default=lambda self: self.env.user)
	journal_id = fields.Many2one('account.journal', string='Journal to pay',
								 related="company_id.bridge_journal", readonly=True)
	account_id = fields.Many2one('account.account', string='Journal / Account')
	bank_id = fields.Many2one('res.bank', string='Bank')
	endorsement = fields.Many2one('res.partner', string='Endorsement')
	another_journal_id = fields.Many2one('account.journal', string='Journal', readonly=True,
										 states={'draft': [('readonly', False)]},
										 domain="[  ('company_id', '=', company_id)]")
	# move_expenses_id = fields.Many2one('account.move', string="Expenses Entry")
	seat_generated_by_payment = fields.Many2one('account.move', string="Payment entry")
	bank_acc_number_id = fields.Many2one('res.partner.bank', string='Account Number')
	journal_debit_note_id = fields.Many2one('account.journal', string='Journal Debit note', readonly=True,
											states={'draft': [('readonly', False)]},
											domain="[  ('company_id', '=', company_id)]")
	letters_serie_id = fields.Many2one(comodel_name='ir.sequence', string="Serie for letters", ondelete="restrict")

	letter_det_ids = fields.One2many('letter.management.det', 'letter_fact_id', string="Invoices")
	# let_asiento_ids = fields.One2many('account.move', 'asiento_letters', string='Entries - Letter')
	list_letters_ids = fields.One2many('account.move', 'letter_create_id', string='Generate Letters')
	list_debit_notes_ids = fields.One2many('account.move', 'debit_create_id', string='Generate Debit Note')
	seat_generated_by_payment_ids = fields.One2many('account.move', 'seat_generated_id', string="Payment entry")

	mora_interest_rate = fields.Integer(string='Moratorium Rate',
										help='Tasa de interes hacia los docs por cobrar a canjear')
	comp_interest_rate = fields.Integer(string='Compensatory Rate')
	free_days = fields.Integer(string='Free days')
	letter_number = fields.Integer(string='Amount of Letters')
	days_to_first = fields.Integer(string='Payment days to first letter')
	days_range = fields.Integer(string='Payment term between letters')

	total_amount_letras = fields.Monetary(string='Letters Amount', compute='_compute_amount_all_letter', readonly=True)
	difference_amount = fields.Monetary(string='Difference', compute='_compute_difference_amount', readonly=True)
	all_amount_interest = fields.Monetary(string='Interests', compute='_compute_amount_debit_note', readonly=True)
	# Campo monetario solo tiene 2 decimales y genera 
	# exchange_rate = fields.Monetary(string="Exchange rate", digits=(12, 4), store=True, readonly=False)
	exchange_rate = fields.Float(string="Exchange rate", digits='Exchange rate', store=True, readonly=False)
	# amount_total_to_pay = fields.Float(string='Remaining amount')
	total_amount_fact = fields.Monetary(string='Amount Docs. Receivable', readonly=True, compute='_compute_amount_docs')

	city = fields.Char(string='Turn Place', related='company_id.city', readonly=True)
	# import_text = fields.Char(string='Importe a Texto')
	phone = fields.Char(related='partner_id.phone', store=True, readonly=False, string='Phone')
	office_name = fields.Char(string='Office')
	unique_code_supplier = fields.Char(string='Unique Code')

	other_currency = fields.Boolean(string="Other Corrency", compute="_compute_other_currency")
	user_exchange_rate = fields.Boolean(string="Exchange Rate User")

	is_generated = fields.Boolean(string='Generated letters o debit notes', default=False)
	generate_interest = fields.Boolean(string='Generate Interest')
	letters_is_created = fields.Boolean(string='Created letters', default=False)
	include_interests_in_letter = fields.Boolean(string='Include interest in the letter', default=False)

	# Ribbons
	is_exchanged = fields.Boolean(string='Is exchanged', default=False, compute='template_is_posted')

	is_letter = fields.Boolean(string='Is Letter', default=False)
	is_debit = fields.Boolean(string='Is Debit', default=False,
							  help='nota de debito generada en la Pestaña de letras - Caso 3')
	is_debit_generated = fields.Boolean(string='Debit generated', default=False,
										help='nota de debito generada, ubicada en un campo en la pestaña Nota de debito- Caso 4')
	all_debit_generated_posted = fields.Boolean(string='Debit generated is Posted', default=False,
												compute='_compute_debit_generated_posted')
	debit_notes_in_docs = fields.Boolean(string='Debit in Docs', default=False, compute='_compute_debit_note_in_docs',
										 help='nota de debito seleccionada, en la pestaña de docs. por cobrar - Caso 1 y 2')
	is_same_partner = fields.Boolean(string='Same partner', default=False, compute='_compute_same_partner')
	# is_template_cancelled = fields.Boolean(string='Template cancelled', default=False)

	_tax_ids_debit = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")

	# Campos especiales para crear asientos de adelantos y enviar letras al cliente
	renewal_percentage = fields.Float('Renewal Percentage %')
	advanced_payment_move_id = fields.Many2one('account.move', string='Advanced Payment Move', tracking=True)
	user_id = fields.Many2one(string='User', related='invoice_user_id',
		help='Technical field used to fit the generic behavior in mail templates.')
	is_move_sent = fields.Boolean(
		readonly=True,
		default=False,
		copy=False,
		tracking=True,
		help="It indicates that the invoice/payment has been sent.",
	)
	
	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			self = self.with_company(vals['company_id'])
		if vals.get('name', _('New')) == _('New'):
			seq_date = None
			if 'date' in vals:
				seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
			if self.env.context.get('default_operation_methods') == 'portfolio':
				if self.env.context.get('active_domain') == [['move_type', '=', 'out_invoice']]:
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.sale', sequence_date=seq_date) or _('New')
				else:
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.purchase', sequence_date=seq_date) or _('New')
			else:
				if self.env.context.get('default_operation_methods') == 'discount':
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.bank', sequence_date=seq_date) or _('New')
				if self.env.context.get('default_operation_methods') == 'renewal':
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.renewal', sequence_date=seq_date) or _('New')
				if self.env.context.get('default_operation_methods') == 'protest':
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.protest', sequence_date=seq_date) or _('New')
				if self.env.context.get('default_operation_methods') == 'refinancing':
					vals['name'] = self.env['ir.sequence'].next_by_code('letter.management.refinancing', sequence_date=seq_date) or _('New')

		result = super(LetterManagement, self).create(vals)
		return result

	# ---- Depends ----                
	@api.depends('currency_id')
	def _compute_other_currency(self):
		for rec in self:
			if rec.company_id.currency_id and rec.currency_id and rec.currency_id != rec.company_id.currency_id:
				rec.other_currency = True
			else:
				rec.other_currency = False

	@api.depends('list_letters_ids.letter_amount', 'list_letters_ids.exchange_rate', 'total_amount_fact')
	def _compute_amount_all_letter(self):
		for rec in self:
			rec.total_amount_letras = 0.0
			# if rec.operation_methods not in ['discount']:
			# rec.list_letters_ids._compute_amount()
			############## POLIMASTER ################
			# Se calcula el monto total dependiendo de la moneda de la letra
			total = 0
			for l in rec.list_letters_ids:
				if l.currency_id == rec.currency_id:
					total += l.letter_amount
				else:
					if l.currency_id == self.env.company.currency_id:
						exchange_rate = self.env.context.get('exchange_rate') or rec.exchange_rate
						total += l.currency_id.round(l.letter_amount / exchange_rate)
					else:
						total += l.currency_id.round(l.letter_amount * l.exchange_rate)
			rec.total_amount_letras = total
			# if rec.include_interests_in_letter:
			#     if rec.operation_methods in ['portfolio']:
			#         rec.total_amount_letras = rec.currency_id.round(sum((rec.list_letters_ids.mapped('letter_amount'))))

			# else:
			#     rec.total_amount_letras = rec.currency_id.round(sum(rec.list_letters_ids.mapped('letter_amount')))

	@api.depends('letter_det_ids.amount_payable', 'letter_det_ids.interest_on_arrears',
				 'letter_det_ids.compensatory_interest')
	def _compute_amount_docs(self):
		for rec in self:
			rec.total_amount_fact = 0.0
			for payment in rec.letter_det_ids:
				if payment.amount_payable <= 0:
					payment.amount_payable = payment.paid_amount
					payment.new_amount_to_pay = payment.amount_payable + payment.interest_on_arrears + payment.compensatory_interest

			if rec.generate_interest:
				if rec.is_debit_generated or rec.debit_notes_in_docs or rec.is_debit or rec.include_interests_in_letter or not rec.include_interests_in_letter:
					rec.total_amount_fact = rec.currency_id.round(sum(rec.letter_det_ids.mapped('amount_payable')))
			else:
				rec.total_amount_fact = rec.currency_id.round(sum(rec.letter_det_ids.mapped('new_amount_to_pay')))

	@api.depends('total_amount_fact', 'all_amount_interest', 'total_amount_letras','exchange_rate')
	def _compute_difference_amount(self):
		for rec in self:
			for letter in self.list_letters_ids:
				letter.exchange_rate = self.exchange_rate
			rec.difference_amount = 0.0
			invoice = rec.currency_id.round(rec.total_amount_fact + rec.all_amount_interest)
			letter = rec.currency_id.round(rec.total_amount_letras)
			if rec.is_debit or rec.is_debit_generated or rec.debit_notes_in_docs:
				# if invoice == letter:
				rec.difference_amount = abs(invoice) - abs(letter)
			if not rec.is_debit and not rec.is_debit_generated and not rec.debit_notes_in_docs:
				rec.difference_amount = rec.currency_id.round(rec.total_amount_fact - rec.total_amount_letras)

	@api.depends('letter_det_ids.interest_on_arrears', 'letter_det_ids.compensatory_interest')
	def _compute_amount_debit_note(self):
		self.all_amount_interest = 0.0
		for rec in self:
			if rec.operation_methods in ['portfolio']:
				_interest_arrears = 0
				_interest_compensatory = 0
				_interest_arrears = rec.currency_id.round(sum(rec.letter_det_ids.mapped('interest_on_arrears')))
				_interest_compensatory = rec.currency_id.round(sum(rec.letter_det_ids.mapped('compensatory_interest')))
				if rec.is_debit:
					for debit in rec.list_letters_ids:
						if debit.document_type_code in ['08']:
							rec.all_amount_interest = rec.currency_id.round(debit.amount_total)
				if rec.debit_notes_in_docs:  # si se escogio una nota de debito
					# if rec.include_interests_in_letter
					rec.total_amount_fact = rec.currency_id.round(sum(rec.letter_det_ids.mapped('amount_payable')))
					# rec.all_amount_interest = 0
				if not rec.is_debit and not rec.is_debit_generated:
					rec.all_amount_interest = _interest_arrears + _interest_compensatory

				if rec.is_debit_generated:
					rec.all_amount_interest = rec.currency_id.round(
						sum(rec.list_debit_notes_ids.mapped('amount_total')))

				if rec.letters_is_created:
					rec.list_letters_ids._onchange_amount_letter_line()

	@api.depends('list_debit_notes_ids.state')
	def _compute_debit_generated_posted(self):
		for rec in self:
			rec.all_debit_generated_posted = False
			if len(rec.list_debit_notes_ids.mapped('id')) > 0:
				if len(rec.list_debit_notes_ids.mapped('id')) == (rec.list_debit_notes_ids.mapped('state')).count(
						'posted'):
					rec.all_debit_generated_posted = True
			rec._compute_debit_note_in_docs()

	@api.depends('letter_det_ids.partner_id')
	def _compute_same_partner(self):
		for rec in self:
			rec.is_same_partner = False
			if rec.operation_methods in ['portfolio']:
				if rec.partner_id:
					if len(rec.letter_det_ids.mapped('partner_id')) < 1:
						rec.is_same_partner = False
					if len(rec.letter_det_ids.mapped('partner_id')) == 1:
						rec.is_same_partner = True

	@api.depends('letter_det_ids.move_id')
	def _compute_debit_note_in_docs(self):
		for rec in self:
			rec.debit_notes_in_docs = False
			if len(list(rec.letter_det_ids.mapped('move_id.id'))) > 0:
				if (rec.letter_det_ids.mapped('move_id.document_type_code')).count('08') >= 1:
					# rec.generate_interest = True
					# rec.include_interests_in_letter = True
					rec.debit_notes_in_docs = True

	@api.depends('state')
	def template_is_posted(self):
		for rec in self:
			# Se creó ésta validacion por si intentaban duplicar una plantilla posteada
			# if rec.state not in ['posted']:
			rec.is_exchanged = False
			if rec.state in ['posted', 'cancel']:
				if rec.operation_methods in ['portfolio']:
					rec.is_exchanged = True

	@api.depends('_writeoff_account_id')
	def _check_expenses_account(self):
		for rec in self:
			rec.is_expenses_account = False
			if rec._writeoff_account_id:
				if rec._writeoff_account_id.code[:2] in ['62', '63', '64', '65', '67', '68']:
					rec.is_expenses_account = True  # Cuando este campo se activa, la cuenta ni etiqueta analitica sera exigible

	# ---- Model ----
	@api.model
	def default_get(self, fields):  # canje >> facturas y notas de debito,
		# print('Default Base')
		res = super(LetterManagement, self).default_get(fields)
		inv_ids = self._context.get('active_ids')
		vals = []
		invoice_ids = self.env['account.move'].browse(inv_ids)
		if invoice_ids:
			if 'operation_methods' in res:
				_logger.info(res['operation_methods'])

				letter_payable_module = self.env['ir.module.module'].sudo().search(
					[('name', '=', 'qa_letter_management_payables'), ('state', '=', 'installed')], limit=1)
				letter_receivable_module = self.env['ir.module.module'].sudo().search(
					[('name', '=', 'qa_letter_management_receivable'), ('state', '=', 'installed')], limit=1)

				if len(letter_payable_module) == 0 and len(letter_receivable_module) == 0:
					raise UserError(_('The Letters Receivable or Payable modules were not found to be installed.'))

				if list(invoice_ids.mapped('move_type'))[0] == 'out_invoice':  # Si son clientes
					if len(letter_receivable_module) == 1:
						# print('modulo por cobrar instalado')
						res['exchange_type'] = 'collection'
						res['partner_type'] = 'customer'
						res['payment_type'] = 'inbound'
						res['move_type'] = 'out_invoice'
					else:
						raise UserError(
							_('For this process, you need to have the Letters Receivable module installed.'))

				if list(invoice_ids.mapped('move_type'))[0] == 'in_invoice':  # Si son proveedores
					if len(letter_payable_module) == 1:
						# print('modulo por pagar instalado')
						res['exchange_type'] = 'payment'
						res['partner_type'] = 'supplier'
						res['payment_type'] = 'outbound'
						res['move_type'] = 'in_invoice'
					else:
						raise UserError(_('For this process, you need to have the Letters Payable module installed.'))

				if len(list(invoice_ids.mapped('currency_id'))) > 1:
					raise UserError(_("Documents cannot have different currencies"))
				for inv in invoice_ids:
					if res['operation_methods']:
						if inv.state in ('draft', 'cancel'):
							raise UserError(_('Only documents with posted state'))
						if inv.amount_residual == 0:  # INICIO 00005
							raise UserError(_('In the selected documents, there are some paid'))
						if res['operation_methods'] in ['portfolio']:
							# if len(invoice_ids) > 1:
							if len(list(invoice_ids.mapped('partner_id'))) > 1:
								raise UserError(_('For this operation, select those that have the same partner'))
							# if invoice_ids.mapped('document_type_code').count('LT') >= 1:
							#     raise UserError(_('To exchange documents, select invoices, debit notes, tickets'))
							if len(invoice_ids) >= 1:
								if inv.l10n_latam_document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08','DIP','00','LT','DIXC']:
									raise UserError(_(
										'To exchange documents, select invoices, debit notes, tickets'))

						if len(list(invoice_ids.mapped('partner_id'))) == 1:
							res['partner_id'] = invoice_ids.mapped('partner_id.id')[0]
							res['is_same_partner'] = True
						elif len(list(invoice_ids.mapped('partner_id'))) > 1:
							res['is_same_partner'] = False
						if inv.payment_state in ('not_paid', 'partial', 'in_redemption', 'redeemed') and inv.amount_residual != 0:
							tipo = 'counted' if inv.tipo_transaccion == 'contado' else 'credit' if inv.tipo_transaccion == 'credito' else False
							vals.append((0, 0, {
								'move_id': inv and inv.id or False,
								# 'move_type': inv.type,
								'document_type_id': inv.l10n_latam_document_type_id and inv.l10n_latam_document_type_id.id or False,
								'document_type_code': inv.document_type_code or False,
								'document_number': inv.l10n_latam_document_number or False,
								'partner_id': inv.partner_id and inv.partner_id.id or False,
								'company_id': inv.company_id and inv.company_id.id or False,
								'currency_id': inv.currency_id and inv.currency_id.id or False,
								'paid_amount': inv.amount_residual or 0.0,
								'invoice_date': inv.invoice_date or False,
								'expiration_date': inv.invoice_date_due or False,
								# 'letter_state': inv.letter_state or False,
								'payment_term': tipo
								}))
							res.update({
								'letter_det_ids': vals,
								'currency_id': invoice_ids.mapped('currency_id.id')[0] or False,
								'invoice_user_id': invoice_ids[0].invoice_user_id.id if invoice_ids and invoice_ids[
									0].invoice_user_id else ''
								})
				
				if res['operation_methods'] in ['protest']:
					if len(invoice_ids.letter_create_id.mapped('journal_id_type_bank_id')) > 1 or any(inv.letter_create_id == False for inv in invoice_ids):
						raise UserError(_('Protest only letters discounted in the same bank.'))
		# if 'exchange_type' in res:
		#     _logger.info(res['exchange_type'])
		#     if res['exchange_type'] in ['collection']:
		#         res['move_type'] = 'out_invoice'
		#     _type = res['move_type']
		#     res.update({
		#         'move_type': _type,
		#     })
		return res

	# --- constrains ---
	@api.constrains('exchange_rate')
	def _check_rate(self):
		for rec in self:
			if rec.other_currency:
				if rec.exchange_rate == 0:
					raise UserError(_('The exchange rate cannot be 0'))

	# ---- Onchange ----
	@api.onchange('exchange_type')
	def _onchange_exchange_type(self):
		for rec in self:
			if rec.exchange_type:
				check_modules = True
				self._check_letter_management_modules_are_installed(check_modules)
				if rec.operation_methods:
					# LETRAS POR PAGAR - PROVEEDORES
					if rec.exchange_type in ['payment']:
						# por si esta CREANDO una plantilla
						if rec.operation_methods in ['portfolio']:
							rec.partner_type = 'supplier'
							rec.payment_type = 'outbound'
							rec.move_type = 'in_invoice'
						else:
							raise UserError(_(
								'Los procesos de Cobranza, Descuento, Renovación, Refinanciamiento, Protesto y Devolucion no estan disponibles para Proveedores'))

					if rec.exchange_type in ['collection']:
						rec.partner_type = 'customer'
						rec.payment_type = 'inbound'
						rec.move_type = 'out_invoice'
				else:
					rec.operation_methods = 'portfolio'

	@api.onchange('currency_id', 'exchange_date', 'user_exchange_rate')
	def _get_exchange_rate(self):
		for rec in self:
			if rec.other_currency:
				if not rec.user_exchange_rate:
					if not rec.exchange_date:
						rec.exchange_date = rec.date
			# if not rec.date: # Fecha de PAGO
			#     rec.date = date.today()
			if rec.currency_id == rec.company_id.currency_id:
				rec.user_exchange_rate = False
			if rec.exchange_date:
				if rec.currency_id != rec.company_id.currency_id and not rec.user_exchange_rate:
					domain = [('currency_id.id', '=', rec.currency_id.id),
							  ('name', '=', fields.Date.to_string(rec.exchange_date)),
							  ('company_id.id', '=', rec.company_id.id)]
					currency = rec.env['res.currency.rate'].search(domain, limit=1)
					if currency:
						rec.exchange_rate = currency.rate_pe
						# rec.write({'exchange_rate': currency.rate_pe})
					else:
						if rec.currency_id:
							rec.exchange_date = False
							rec.exchange_rate = 0
							# raise UserError("No se encontro el tipo de cambio para la fecha seleccionada")
							# message = _('No se encontro el tipo de cambio para la fecha seleccionada')
							# warning_mess = {'title': _('Payment is Pending!'), 'message': message}
							# return {'warning': warning_mess}
				else:
					rec.exchange_rate = 0
					rec.exchange_date = False
			else:
				rec.exchange_rate = 0
				rec.exchange_date = False

	@api.onchange('letter_det_ids.amount_payable')
	def _onchange_amount_letters(self):
		for rec in self:
			total_letras = rec.total_amount_letras
			total_facturas = rec.total_amount_fact
			if rec.is_exchanged == False:
				if rec.letters_is_created:
					if total_letras != total_facturas:
						for letra in rec.list_letters_ids:
							if rec.operation_methods == 'portfolio':
								nuevo_monto_letra = rec.total_amount_fact / rec.letter_number
								letra.letter_amount = nuevo_monto_letra
								letra.amount_total = letra.letter_amount
						rec.list_letters_ids._inverse_first_amount()

	@api.onchange('generate_interest', 'include_interests_in_letter')
	def _onchange_generate_interest(self):
		for rec in self:
			# rec.include_interests_in_letter = False
			# rec.generate_interest = False
			if not rec.generate_interest:
				rec.include_interests_in_letter = False
				rec.debit_notes_serie_id = False
				# rec.document_type_id = False
				rec._tax_ids_debit = False
				for docs in rec.letter_det_ids:
					docs.interest_on_arrears = 0.0
					docs.compensatory_interest = 0.0

	@api.onchange('bank_id', 'new_bank_id')
	def _onchange_bank_id(self):
		for rec in self:
			if rec.operation_methods in ['portfolio']:
				rec.bank_acc_number_id = False

	@api.onchange('currency_id', 'date')
	def _onchange_date_exchange(self):
		for rec in self:
			rec.exchange_date = rec.date
			rec._get_exchange_rate()

	def _check_letter_management_modules_are_installed(self, check_modules):
		for rec in self:
			letter_payable_module = self.env['ir.module.module'].sudo().search(
				[('name', '=', 'qa_letter_management_payables'), ('state', '=', 'installed')], limit=1)
			letter_receivable_module = self.env['ir.module.module'].sudo().search(
				[('name', '=', 'qa_letter_management_receivable'), ('state', '=', 'installed')], limit=1)
			# Es muy improbable que los dos modulos esten desinstalados y que se sigan usando :v
			if len(letter_payable_module) == 0 and len(letter_receivable_module) == 0:
				raise (_('The Letters Receivable or Payable modules were not found to be installed.'))
			if check_modules:
				if rec.exchange_type in ['payment']:
					if len(letter_payable_module) != 1:
						raise UserError(_('For this process, you need to have the Letters Payable module installed.'))
				if rec.exchange_type in ['collection']:
					if len(letter_receivable_module) != 1:
						raise UserError(
							_('For this process, you need to have the Letters Receivable module installed.'))

	def btn_cancel_template(self):
		for rec in self:
			# generated_seats = reverted_or_cancelled_seats = 0
			rec._change_order_invoice_status()
			if rec.state in ['posted']:
				# generated_seats = len(rec.seat_generated_by_payment_ids)
				# ############## POLIMASTER ################
				# # Agregamos al total de asiento el asiento de anticipo si lo tuviera
				# generated_seats = len(rec.seat_generated_by_payment_ids) + (1 if self.advanced_payment_move_id else 0)
				# for seat in rec.seat_generated_by_payment_ids:
				#     seat_refund = self.env['account.move'].search([('state', 'in', ['posted']),
				#                                                    ('move_type', '=', 'entry'),
				#                                                    ('reversed_entry_id', '=', seat.id)], limit=1)
				#     # TRCP / 0301 / 03 / 2021
				#     if seat_refund:
				#         reverted_or_cancelled_seats += 1
				#     else:
				#         if seat.state in ['cancel']:
				#             reverted_or_cancelled_seats += 1

				# ############## POLIMASTER ################
				# # Revisar si el canje tenia un asiento de anticipo por letras de terceros y si este esta revertido
				# if self.advanced_payment_move_id:
				#     seat_refund = self.env['account.move'].search([('state', 'in', ['posted']),
				#                                                     ('move_type', '=', 'entry'),
				#                                                     ('reversed_entry_id', '=', self.advanced_payment_move_id.id)], limit=1)
				# if seat_refund or self.advanced_payment_move_id.state == 'cancel':
				#     reverted_or_cancelled_seats += 1


				# if generated_seats == reverted_or_cancelled_seats:
				# rec.write({'state': 'cancel'})
				rec.write({'state': 'in_process'})
				for docs in rec.letter_det_ids:
					docs.move_id.templates_cancelled_ids = [(4, rec.id)]
					msg_body = _(
						"Cancelaron / Revirtieron las letras y asientos generados en la plantilla N°:") + " <a href=# data-oe-model=letter.management data-oe-id=%d>%s</a>" % (
									rec.id, rec.id)
					docs.move_id.message_post(body=msg_body)
				##### AUTOMATIZACIÓN DE CANCELACIÓN DE ASIENTOS #####
				if any(letter.payment_state != 'not_paid' for letter in rec.list_letters_ids):
					raise UserError(_('Can\'t cancel a template wich letters have a payment state different than "not paid"'))
				else:
					# if rec.operation_methods == 'portfolio':
					for letter in rec.list_letters_ids:
						letter.button_draft()
						# letter.invoice_serie = letter.invoice_serie + ' C'
						# letter.invoice_number = (letter.invoice_number + '- Cancelled -' + self.name) if letter.invoice_number else letter.invoice_number
						# letter.button_cancel()
						# letter.with_context(force_delete=True).unlink()
					for seat in rec.seat_generated_by_payment_ids:
						seat.button_draft()
						seat.with_context(force_delete=True).unlink()
					rec.advanced_payment_move_id.button_draft()
					rec.advanced_payment_move_id.with_context(force_delete=True).unlink()


	def _prepare_invoice_vals(self, invoice_lines, amount):
		self.ensure_one()
		invoice_obj = self.env['account.move']
		document = False
		serie = False

		# Caso 3:
		if self.is_debit:  # Se generara una nota de debito en pestaña Letras
			# se activa en el boton de generar notas de debito
			document = self.env.ref('l10n_pe.document_type08').id
			serie = self.debit_notes_serie_id.id

		if self.is_debit_generated:  # Se generara una nota de debito en pestaña Notas de debito - Caso 4
			# se activa en el boton de generar notas de debito
			if not self.is_letter:
				document = self.env.ref('l10n_pe.document_type08').id
				serie = self.debit_notes_serie_id.id
			# else:

		if self.is_letter:  # se crearan letras (se activa en generate_letters)
			if not self.letters_is_created:
				document = self.env.ref('qa_letter_management.document_type_lt1').id
				serie = self._get_serie()

		vals = {
			'state': 'draft',
			'move_type': self.move_type,
			'l10n_latam_document_type_id': document or False,
			# 'sunat_serie': serie or False,
			# 'sunat_number_temp': invoice_obj._get_correlativo_temporal(serie, document, 2) or False,

			# 'partner_id': self.partner_id and self.partner_id.id or False,
			'endorsement': self.endorsement and self.endorsement.id or False,
			'invoice_date': self.date,
			# 'invoice_date': fields.Date.today(),
			'office_name': self.office_name,
			# 'invoice_date_due': date_due,
			'company_id': self.company_id and self.company_id.id or False,
			'currency_id': self.currency_id and self.currency_id.id or False,
			# 'letter_create_id': self and self.id or False,
			'letter_amount': amount or 0,
			'invoice_line_ids': invoice_lines,
			}

		#vals['sunat_serie'] = serie
		"""if self.exchange_type in ['collection']:
			number_temp = invoice_obj._get_correlativo_temporal(serie, document, 2) or False,  # Tuple
			vals['sunat_number_temp'] = number_temp[0]"""

		# if self.exchange_type in ['payment']:
		#vals['invoice_serie'] = False
		#vals['invoice_number'] = False

		if self.exchange_rate > 0:
			if self.exchange_date:
				vals['exchange_date'] = self.exchange_date
			if self.user_exchange_rate:
				vals['user_exchange_rate'] = self.user_exchange_rate
			vals['exchange_rate'] = self.exchange_rate

		if self.is_letter:
			if not self.letters_is_created:
				# document = self.env.ref('qa_letter_management.document_type_lt1').id
				# if self.letters_serie:
				#     serie_doc = self.letters_serie.id
				vals['journal_id'] = self.another_journal_id and self.another_journal_id.id or False,
				vals['letter_create_id'] = self and self.id or False
				# if self.operation_methods in ['renewal', 'refinancing', 'return']:
				#     vals['letter_state'] = 'portfolio'
				#     vals['letter_create_id'] = self and self.id or False
				# else:
				if self.operation_methods in ['refinancing', 'renewal', 'return']:
					vals['letter_state'] = 'portfolio'
				else:
					vals['letter_state'] = self.operation_methods

				# vals['letter_create_id'] = self and self.id or False
				# if self.operation_methods in ['portfolio', 'refinancing']:
				#     vals['document_type_id'] = document or False
				# vals['sunat_serie'] = serie_doc or False
				# vals['sunat_number_temp'] = invoice_obj._get_correlativo_temporal(serie_doc, document, 2)

		# Dato que tendran los documentos generados desde la plantilla de LETRAS

		return vals

	def action_generate_letters_and_open_form(self):
		# print('Abriendo form')
		self.ensure_one()
		self._compute_amount_docs()
		action = {'type': 'ir.actions.act_window_close'}
		check_modules = True
		self._check_letter_management_modules_are_installed(check_modules)
		if self._context.get('open_payment', False):
			if self.exchange_type in ['collection']:
				action = self.env.ref(
					'qa_letter_management_receivable.action_qa_letter_management_inherit_receivables').read()[0]
			if self.exchange_type in ['payment']:
				action = self.env.ref(
					'qa_letter_management_payables.action_qa_letter_management_inherit_payables').read()[0]
			self.generate_letters()
			form_view = [(self.env.ref('qa_letter_management.qa_letter_management_form_view_no_create').id, 'form')]

			action['context'] = dict(safe_eval(action.get('context')), is_modal=False)
			action['views'] = form_view
			action['res_id'] = self.id
			# action['tag'] = 'reload'
		return action

	def action_generate_debit_notes_and_open_form(self):
		# print('Abriendo form')
		self.ensure_one()
		action = {'type': 'ir.actions.act_window_close'}
		check_modules = True
		self._check_letter_management_modules_are_installed(check_modules)
		if self._context.get('open_payment', False):
			if self.exchange_type in ['collection']:
				action = self.env.ref(
					'qa_letter_management_receivable.action_qa_letter_management_inherit_receivables').read()[0]
			if self.exchange_type in ['payment']:
				action = self.env.ref(
					'qa_letter_management_payables.action_qa_letter_management_inherit_payables').read()[0]
			self.btn_generate_debit_note()
			form_view = [(self.env.ref('qa_letter_management.qa_letter_management_form_view_no_create').id, 'form')]
			action['context'] = dict(safe_eval(action.get('context')), is_modal=False)
			action['views'] = form_view
			action['res_id'] = self.id
		return action

	def generate_letters(self):
		for rec in self:
			date_temp = False
			rec._check_products_company()
			rec._check_bridge_journal()
			check_modules = True
			rec._check_letter_management_modules_are_installed(check_modules)
			# if rec.operation_methods in ['portfolio']:
			#     if not rec.letters_serie_id:
			#         raise UserError(_('Choose a series for the letters'))
			if not rec.currency_id:
				raise UserError(_('Select a type of Currency'))
			if len(list(rec.letter_det_ids.mapped('move_id.id'))) < 1:
				raise UserError(_('There is no document to generate letters'))
			for amount in rec.letter_det_ids:
				if amount.amount_payable == 0:
					if amount.move_id.amount_residual > 0.0:
						raise UserError(_(
							'To generate the letters, the documents must have a amount payable (can be partial payment)'))
				if amount.move_id.amount_residual <= 0.0:
					raise UserError(_('To generate the letters, the documents must have a balance due'))
			# self._check_products_company()
			if rec.state in ['draft', 'in_process']:
				rec._check_journals_to_generate_letters()
				rec._check_if_debit_notes_were_generated()
				if rec.operation_methods:
					rec.delete_letters()
					rec.is_letter = True
					rec._check_letter_number_and_days_range()
					_logger.info("========== antes de generar")
					rec._generate_letters_in_template()
					_logger.info("despues de generar")

					if rec.list_letters_ids:
						rec.letters_is_created = True
						rec.state = 'in_process'
			_logger.info("_generate_letter_numbers")
			rec._generate_letter_numbers()
			_logger.info("_change_order_invoice_status")
			rec._change_order_invoice_status()
	
	def _change_order_invoice_status(self):
		for rec in self:
			for line in rec.letter_det_ids:
				sale_ids = line.move_id.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
				sale_order_id = self.env['sale.order'].search([('id','in', sale_ids.ids)], limit=1)
				sale_order_id._compute_invoice_status()

	@api.depends('list_letters_ids')
	def _generate_letter_numbers(self):
		for rec in self:
			counter = 1
			name = self.name
			while not name.isdigit():
				name = name[1:]
				if name == '':
					break
			if not name:
				raise UserError(_('The name of the template does not have any digits. It is not posible to create the letters.'))
			for letter in self.list_letters_ids.sorted('invoice_date_due'):
				sunat_number = name + str(counter).zfill(2) + '00'
				letter.name = sunat_number
				#letter.sunat_number = name + str(counter).zfill(2) + '00'
				#letter.document_number = (letter.sunat_serie.name + '-') if letter.sunat_serie else '' + letter.sunat_number
				counter += 1



	def generate_debit_notes(self):
		for rec in self:
			debit_notes = []
			new_debit_notes = []
			self._check_products_company()
			self._check_bridge_journal()
			product_interest = rec.company_id.letter_interest
			if rec.is_debit:  # Caso 3
				_interest = 0
				_interest_arrears = 0
				_interest_compensatory = 0
				_interest_arrears = sum(rec.letter_det_ids.mapped('interest_on_arrears'))
				_interest_compensatory = sum(rec.letter_det_ids.mapped('compensatory_interest'))
				_interest = _interest_arrears + _interest_compensatory
				debit_notes = rec._get_invoices_lines(product_interest, _interest, [])

				# invoice_lines = [(0, 0, {
				#     'product_id': rec.company_id.letter_interest.id,
				#     'name': rec.company_id.letter_interest.display_name,
				#     'account_id': rec.company_id.letter_interest.property_account_income_id.id,
				#     'tax_ids': rec._tax_ids_debit and rec._tax_ids_debit.ids or False,
				#     'product_uom_id': rec.company_id.letter_interest.uom_id and rec.company_id.letter_interest.uom_id.id or False,
				#     'price_unit': _interest
				#     })]
				# # if rec.is_debit:
				# debit_notes = rec._prepare_invoice_vals(invoice_lines, _interest)

				debit_notes['partner_id'] = rec.letter_det_ids[0].move_id.partner_id and rec.letter_det_ids[
					0].move_id.partner_id.id or False
				debit_notes['journal_id'] = self.journal_debit_note_id and self.journal_debit_note_id.id or False,
				debit_notes['letter_amount'] = _interest
				debit_notes['invoice_date'] = rec.date
				debit_notes['amount_letter'] = debit_notes['letter_amount']
				self.env['account.move'].create(debit_notes)

			if rec.is_debit_generated:  # Caso 4
				amount_interest = 0
				for move in rec.letter_det_ids:
					if move.interest_on_arrears > 0 or move.compensatory_interest > 0:
						amount_interest = move.interest_on_arrears + move.compensatory_interest
						new_debit_notes = rec._get_invoices_lines(product_interest, amount_interest, [])

						# invoice_lines = [(0, 0, {
						#     'product_id': rec.company_id.letter_interest.id,
						#     'name': rec.company_id.letter_interest.display_name,
						#     'account_id': rec.company_id.letter_interest.property_account_income_id.id,
						#     'tax_ids': rec._tax_ids_debit and rec._tax_ids_debit.ids or False,
						#     'product_uom_id': rec.company_id.letter_interest.uom_id and rec.company_id.letter_interest.uom_id.id or False,
						#     'price_unit': amount_interest
						#     })]
						# new_debit_notes = rec._prepare_invoice_vals(invoice_lines, amount_interest)

						new_debit_notes['debit_create_id'] = self and self.id or False,
						##new_debit_notes['debit_note_type'] = '1'
						new_debit_notes['invoice_date'] = fields.date.today()
						##new_debit_notes['refund_invoice_document_type_id'] = move.move_id.document_type_id.id,
						##new_debit_notes['refund_invoice_invoice_date'] = move.move_id.invoice_date
						serie = number = ''
						datos = move.move_id.l10n_latam_document_number.split("-")
						if rec.exchange_type == 'collection':
							serie = datos[0]
							number = datos[1]
						if rec.exchange_type == 'payment':
							serie = datos[0]
							number = datos[1]
						##new_debit_notes['refund_invoice_sunat_serie'] = serie
						##new_debit_notes['refund_invoice_sunat_number'] = number
						new_debit_notes['partner_id'] = move.move_id.partner_id.id
						new_debit_notes[
							'journal_id'] = self.journal_debit_note_id and self.journal_debit_note_id.id or False,
						debit_generated = self.env['account.move'].create(new_debit_notes)
						# print(new_debit_notes)
						# debit_generated = self.env['account.move'].create(new_debit_notes)
						# debit_generated._check_amount()

	def _generate_debit_notes_in_template(self):
		for rec in self:
			self._check_products_company()()
			self._check_bridge_journal()
			account_move = self.env['account.move']
			interest_amount = 0
			interest_arrears = 0
			interest_compensatory = 0
			debit_note = False
			doc_number = 0
			for doc in rec.letter_det_ids:
				product_interest = rec.company_id.letter_interest
				if rec.is_debit:
					if doc_number == 0:
						# se genera una sola nota de debito
						interest_arrears = sum(rec.letter_det_ids.mapped('interest_on_arrears'))
						interest_compensatory = sum(rec.letter_det_ids.mapped('compensatory_interest'))
						interest_amount = interest_arrears + interest_compensatory

						debit_note = rec._get_invoices_lines(product_interest, interest_amount, [])

				if rec.is_debit_generated:
					if doc.interest_on_arrears > 0 or doc.compensatory_interest > 0:
						interest_amount = doc.interest_on_arrears + doc.compensatory_interest

						debit_note = rec._get_invoices_lines(product_interest, interest_amount, [])

				if debit_note:  # si ya se tienen datos de la nota de debito generada

					if rec.is_debit:
						if doc_number == 0:
							# if doc.move_id.id == rec.letter_det_ids[0].move_id.id:
							docs = rec.letter_det_ids
							datos = docs[0].move_id.l10n_latam_document_number.split("-")
							if rec.exchange_type in ['collection']:
								serie_refund = datos[0]
								number_refund = datos[1]
							if rec.exchange_type in ['payment']:
								serie_refund = datos[0]
								number_refund = datos[1]
							doc_number += 1

							##debit_note['refund_invoice_document_type_id'] = docs[0].move_id.document_type_id.id
							##debit_note['refund_invoice_invoice_date'] = docs[0].move_id.invoice_date
							debit_note['letter_create_id'] = rec and rec.id or False
							debit_note['partner_id'] = docs[0].move_id.partner_id and docs[
								0].move_id.partner_id.id or False
							debit_note['invoice_date'] = rec.date
							debit_note['letter_amount'] = interest_amount
							debit_note['amount_letter'] = debit_note['letter_amount']

					if rec.is_debit_generated:
						if rec.exchange_type in ['collection']:
							serie_refund = doc.move_id.sunat_serie.name
							number_refund = doc.move_id.sunat_number
						if rec.exchange_type in ['payment']:
							serie_refund = doc.move_id.invoice_serie
							number_refund = doc.move_id.invoice_number

						##debit_note['refund_invoice_document_type_id'] = doc.move_id.l10n_latam_document_type_id.id
						##debit_note['refund_invoice_invoice_date'] = doc.move_id.invoice_date
						debit_note['debit_create_id'] = rec and rec.id or False
						debit_note['partner_id'] = doc.move_id.partner_id.id
						debit_note['invoice_date'] = fields.date.today()

					##debit_note['refund_invoice_sunat_serie'] = serie_refund
					##debit_note['refund_invoice_sunat_number'] = number_refund
					##debit_note['debit_note_type'] = '1'
					debit_note['journal_id'] = rec.journal_debit_note_id and rec.journal_debit_note_id.id or False

					# if debit_note:
					account_move.create(debit_note)

	# Function in case the user add more documents in the Documents receivable tab >> por si es que el usuario agrega mas documentos
	# @api.onchange('letter_det_ids.partner_id', 'letter_det_ids.document_type_id')
	def _validate_documents_receivable(self):
		for rec in self:
			if rec.operation_methods == 'portfolio':
				if len(list(rec.letter_det_ids.mapped('partner_id'))) > 1:
					raise UserError(_('For this operation, select those that have the same partner'))
				if len(list(rec.letter_det_ids.mapped('move_id.id'))) >= 1:
					for line in rec.letter_det_ids:
						if line.move_id.l10n_latam_document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08']:
							raise UserError(_('To exchange documents, select invoices, debit notes, tickets'))
			if len(list(rec.letter_det_ids.mapped('partner_id'))) == 1:
				rec.partner_id = rec.letter_det_ids[0].partner_id.id

	def btn_generate_debit_note(self):
		for rec in self:
			self._check_products_company()
			self._check_bridge_journal()
			if not rec.generate_interest:
				raise UserError(_('Click on Generate Interests'))
			if rec.state not in ['draft', 'in_process']:
				raise UserError(_('Only in Draft and In Process state'))
			if not rec.debit_notes_serie_id.id:
				raise UserError(_('Choose a series of for the Debit Note'))
			if not rec.journal_debit_note_id:
				raise UserError(_('Choose a debit note journal'))

			if rec.operation_methods in ['portfolio', 'renewal', 'refinancing']:
				if rec.all_amount_interest <= 0:
					raise UserError(_('Enter values in the interests of the tab >> Docs. receivable <<'))

				# Caso 3:
				if rec.state == 'in_process':
					if rec.letters_is_created:
						if not rec.include_interests_in_letter:
							if rec.debit_notes_serie_id.id:
								rec.is_debit = True  # Caso 3
								rec.generate_debit_notes()
						else:
							# if rec.letters_is_created:
							raise UserError(_(
								'The debit note cannot be created because the letters were generated with interest included'))
					else:
						raise UserError(_('You have to generate the letters'))
				# Caso 4:
				if rec.state == 'draft':
					if not rec.letters_is_created:
						# if not rec.letters_is_created:
						# if rec.include_interests_in_letter:
						if rec.debit_notes_serie_id.id:
							rec.is_debit_generated = True
							rec.generate_debit_notes()
						else:
							raise UserError(_('Select a series for debit notes'))
						# else:
						#     raise UserError(_(
						#         'If you want to generate a debit note before the letters, you must check the box include interest in the letter'))

				rec.state = 'in_process'
		# return self.reload_page()

	def _check_products_company(self):
		for rec in self:
			if rec.company_id:
				action = self.env.ref('base_setup.action_general_configuration')
				msg = 'No encuentra un producto para la generación de documentos, debe configurarlo. Pulse el botón para ir a la configuración de su empresa.'
				if rec.operation_methods in ['portfolio']:
					if not rec.company_id.letter_portfolio:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))
				if rec.generate_interest:
					if not rec.company_id.letter_interest:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))

	def _check_bridge_journal(self):
		for rec in self:
			if rec.company_id:
				if not rec.company_id.bridge_journal:
					action = self.env.ref('account.action_account_config')
					msg = _(
						'No BRIDGE JOURNAL was found associated with this company, you must configure it. Settings // Accounting configuration')
					raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

	def _check_advanced_journal(self):
		for rec in self:
			if rec.company_id:
				if not rec.company_id.advanced_journal_id:
					action = self.env.ref('account.action_account_config')
					msg = _(
						'No ADVANCED JOURNAL was found associated with this company, you must configure it. Settings // Accounting configuration')
					raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

	def delete_letters(self):
		for rec in self:
			if rec.state == 'posted':
				raise UserError(_('The template is published, the letters cannot be deleted'))
			else:
				if rec.letters_is_created:
					rec.list_letters_ids.with_context(force_delete=True).unlink()
					rec.is_letter = False
					rec.is_debit = False
					rec.letters_is_created = False
					if rec.is_debit_generated:
						rec.state = 'in_process'
					else:
						rec.state = 'draft'
			for move in self.letter_det_ids.move_id:
				move._compute_amount()
			rec._change_order_invoice_status()

	def delete_debit_notes_generated(self):
		for rec in self:
			if rec.state == 'posted':
				raise UserError(_('The template is published, debit notes cannot be deleted'))
				# raise v('La plantilla esta publicada, no se pueden borrar las notas de debito')
			else:
				if rec.letters_is_created:
					raise UserError(_('Letters are generated, debit notes cannot be deleted\n'
									  'Delete the letters generated first'))
				else:
					rec.list_debit_notes_ids.unlink()
					rec.is_debit_generated = False
					rec.state = 'draft'

	def posted_debit_generate(self):
		for rec in self:
			self._check_products_company()
			self._check_bridge_journal()
			check_modules = True
			self._check_letter_management_modules_are_installed(check_modules)
			if rec.is_debit_generated:
				if rec.state == 'in_process':
					if sum(self.list_debit_notes_ids.mapped('letter_amount')) != sum(
							self.letter_det_ids.mapped('compensatory_interest') + self.letter_det_ids.mapped(
								'interest_on_arrears')):
						raise UserError(_(
							'Interest amounts in Docs. receivables other than the amount of the debit notes generated,\n'
							'delete and regenerate debit notes'))
					for line in rec.list_debit_notes_ids:
						"""if line.sunat_serie and not rec.debit_notes_serie_id:
							raise UserError(_(
								'You have generated a debit note in the Letters tab, but there is no Series value selected in the template'))
						if line.sunat_serie != rec.debit_notes_serie_id:
							raise UserError(_(
								'You have generated a debit note in the Letters tab, but it is different from the Series selected in the template'))
						"""
						if line.invoice_line_ids.mapped('tax_ids') and not rec._tax_ids_debit:
							raise UserError(_(
								'You have generated a debit note in the Letters tab, but there is no Tax value selected in the template'))
						if line.invoice_line_ids.mapped('tax_ids') != rec._tax_ids_debit:
							raise UserError(_(
								'You have generated a debit note in the Letters tab, but it is different from the Tax selected in the template'))
						# raise UserError(
						#     'Montos de intereses en Docs. por cobrar diferentes de el importe de las notas de debito generadas, \n'
						#     'borra y vuelve a generar las notas de debito')
					rec.list_debit_notes_ids._post()
					rec.all_debit_generated_posted = True

	def _create_discount_move(self, letter):
		lines = []
		if letter.currency_id != self.env.company.currency_id:
			amount_currency_credit = letter.amount_total - letter.amount_discount
			amount_credit = letter.currency_id.round(amount_currency_credit * self.exchange_rate)
		else:
			amount_currency_credit = 0
			amount_credit = letter.amount_total - letter.amount_discount

		lines.append((0, 0, {
			'account_id': letter.invoice_line_ids[0].account_id.id,
			'amount_currency': amount_currency_credit,
			'currency_id': letter.currency_id.id,
			'debit': amount_credit
			}))
		lines.append((0, 0, {
			'account_id': letter.invoice_line_ids[0].account_id.id,
			'amount_currency': -amount_currency_credit,
			'currency_id': letter.currency_id.id,
			'credit': amount_credit
			}))
		dict_entry = {
			'date': self.date or fields.Date.today() or False,
			'journal_id': self.another_journal_id.id,
			'move_type': 'entry',
			'partner_id': self.partner_id.id,
			'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			#'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			'line_ids': lines,
			}
		discount_move_entry = self.env['account.move'].create(dict_entry)
		if discount_move_entry:
			discount_move_entry.post()

		# self.move_expenses_id = discount_move_entry and discount_move_entry.id or False
		# Se postea un mensaje en el asiento de gastos financieros generado
		for entry in discount_move_entry:
			msg_body = _("This entry for renewal discount was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			# self.id, self.id, data['operacion'])
			entry.message_post(body=msg_body)
			entry.seat_generated_id = self and self.id or False

	############## POLIMASTER ################
	# Nueva validación
	def _check_for_letters(self):
		for rec in self:
			if not rec.list_letters_ids and rec.state == 'in_process':
				raise UserError(_('There is no letters to redeem the invoices, probably they were deleted before. Please press the "DELETE LETTERS" button and generate them again.'))

	# Asiento de pago para refinanciamientos, tiene que ser individual porque no se
	# sabe cual es el estado de la letra y por lo tanto pueden tener cuentas distintas
	def _create_refinancing_payment(self, line):
		lines = []
		account_id = line.account_id
		# Obtenemos el tipo de cambio del contexto
		exchange_rate = self.env.context.get('exchange_rate')
		if self.currency_id != self.env.company.currency_id:
			amount_currency_credit = line.amount_currency
			amount_credit = self.currency_id.round(amount_currency_credit * exchange_rate)
		else:
			amount_currency_credit = 0
			amount_credit = line.debit

		lines.append((0, 0, {
			'account_id': self.journal_id.default_account_id.id,
			'amount_currency': amount_currency_credit,
			'currency_id': self.currency_id.id,
			'debit': amount_credit
			}))
		lines.append((0, 0, {
			'account_id': account_id.id,
			'amount_currency': -amount_currency_credit,
			'currency_id': self.currency_id.id,
			'credit': amount_credit
			}))
		dict_entry = {
			'date': self.date or fields.Date.today() or False,
			'journal_id': self.journal_id.id, #bank_journal_id.id,
			'move_type': 'entry',
			'partner_id': self.partner_id.id,
			'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			#'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			'line_ids': lines,
			}
		payment_entry = self.env['account.move'].create(dict_entry)
		if payment_entry:
			payment_entry.account_analytic_destino()
			payment_entry.post()
			# Conciliamos la linea de la letra anterior con el pago
			line += payment_entry.line_ids.filtered(lambda l: l.credit >0)
			line.reconcile()

		for entry in payment_entry:
			msg_body = _("This entry for protest was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)
			gloss_entry = self._assigning_gloss_to_payment(entry.partner_id.vat, line[0].move_id)
			entry.gloss = entry.ref = gloss_entry
			seat = entry or False
			seat.is_seat_generated = True
			entry.seat_generated_id = self and self.id or False

	# Asiento de pago de letra ante un protesto
	def _create_protest_payment(self, line):
		lines = []
		account_id = line.account_id
		# Obtenemos el tipo de cambio del contexto
		exchange_date = self.env.context.get('exchange_date')
		exchange_rate = self.env.context.get('exchange_rate')
		if self.currency_id != self.env.company.currency_id:
			amount_currency_credit = abs(line.amount_currency)
			amount_credit = self.currency_id.round(amount_currency_credit * exchange_rate)
		else:
			amount_currency_credit = 0
			amount_credit = line.credit

		lines.append((0, 0, {
			'account_id': account_id.id,
			'amount_currency': amount_currency_credit,
			'currency_id': self.currency_id.id,
			'debit': amount_credit
			}))
		lines.append((0, 0, {
			'account_id': self.journal_id.default_account_id.id,
			'amount_currency': -amount_currency_credit,
			'currency_id': self.currency_id.id,
			'credit': amount_credit
			}))
		dict_entry = {
			'date': exchange_date or self.date or fields.Date.today() or False,
			'journal_id': self.journal_id.id, #bank_journal_id.id,
			'move_type': 'entry',
			'partner_id': self.partner_id.id,
			'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			 #'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			'line_ids': lines,
			}
		payment_entry = self.env['account.move'].create(dict_entry)
		if payment_entry:
			payment_entry.account_analytic_destino()
			payment_entry.post()
			# Conciliamos la linea de la letra anterior con el pago
			line += payment_entry.line_ids.filtered(lambda l: l.debit >0)
			line.reconcile()

		for entry in payment_entry:
			msg_body = _("This entry for protest was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)
			entry.seat_generated_id = self and self.id or False

	# Asiento de cargo del banco ante un protesto
	def _create_protest_charge(self):
		lines = []
		# Obtenemos el tipo de cambio del contexto
		exchange_rate = self.env.context.get('exchange_rate')
		exchange_date = self.env.context.get('exchange_date')
		# Para los protestos obtenemos el diario los intereses y gastos financieros 
		# asi como la cuenta de gastos y las analiticas
		bank_journal_id = self.env.context.get('bank_journal_id')
		bank_interests = self.env.context.get('bank_interests')
		financial_expenses = self.env.context.get('financial_expenses')
		_writeoff_account_id = self.env.context.get('_writeoff_account_id')
		analytic_account_id = self.env.context.get('analytic_account_id')
		analytic_tag_ids = self.env.context.get('analytic_tag_ids')
		bank_account_id = bank_journal_id.payment_credit_account_id
		if self.currency_id != self.env.company.currency_id:
			amount_currency_credit = self.total_amount_letras
			amount_credit = self.currency_id.round(amount_currency_credit * exchange_rate)
			bank_interests_credit = self.currency_id.round(bank_interests * exchange_rate)
			financial_expenses_credit = self.currency_id.round(financial_expenses * exchange_rate)
		else:
			amount_currency_credit = 0
			amount_credit = self.total_amount_letras

		if not amount_credit:
			return

		line_name = _('Protested letter ') + self.currency_id.symbol + str(self.total_amount_letras) + ' - ' + self.partner_id.name + ' - ' + str(self.date or fields.Date.today())
		bank_partner = self.letter_det_ids[0].move_id.letter_create_id.journal_id_type_bank_id.bank_partner_id
		lines.append((0, 0, {
			'partner_id': self.partner_id.id,
			'name': line_name,
			'account_id': self.letter_det_ids[0].move_id.invoice_line_ids.account_id.id, # TODO la cuenta de la responsabilidad letter.invoice_line_ids[0].account_id.id,
			'amount_currency': amount_currency_credit,
			'currency_id': self.currency_id.id,
			'debit': amount_credit
			}))
		lines.append((0, 0, {
			'partner_id': bank_partner.id if bank_partner else self.partner_id.id,
			'name': line_name,
			'account_id': bank_account_id.id,
			'amount_currency': -amount_currency_credit,
			'currency_id': self.currency_id.id,
			'credit': amount_credit
			}))
		lines.append((0, 0, {
			'partner_id': bank_partner.id if bank_partner else self.partner_id.id,
			'name': line_name,
			'account_id': bank_account_id.id,
			'amount_currency': -bank_interests,
			'currency_id': self.currency_id.id,
			'credit': bank_interests_credit
			}))
		lines.append((0, 0, {
			'partner_id': bank_partner.id if bank_partner else self.partner_id.id,
			'name': line_name,
			'account_id': bank_account_id.id,
			'amount_currency': -financial_expenses,
			'currency_id': self.currency_id.id,
			'credit': financial_expenses_credit
			}))
		lines.append((0, 0, {
			'partner_id': self.partner_id.id,
			'name': _('Protested letter ') + self.currency_id.symbol + ' - ' + self.partner_id.name + ' - ' + str(self.date or fields.Date.today()),
			'account_id': _writeoff_account_id.id,
			'analytic_account_id': analytic_account_id and analytic_account_id.id or False,
			'analytic_tag_ids': analytic_tag_ids and analytic_tag_ids.ids or False,
			'amount_currency': financial_expenses + bank_interests,
			'currency_id': self.currency_id.id,
			'debit': financial_expenses_credit + bank_interests_credit
			}))
		lines_to_remove = []
		for line in lines:
			if 'debit' in line[2] and line[2]['debit'] == 0:
				lines_to_remove.append(line)
			if 'credit' in line[2] and line[2]['credit'] == 0:
				lines_to_remove.append(line)
		for line in lines_to_remove:
			lines.remove(line)
		dict_entry = {
			'date': exchange_date or self.date or fields.Date.today() or False,
			'exchange_date': self.env.context.get('exchange_date'),
			'exchange_rate': self.env.context.get('exchange_rate'),
			'journal_id': bank_journal_id.id,
			'move_type': 'entry',
			'partner_id': self.partner_id.id,
			'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			#'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			'line_ids': lines,
			}
		discount_move_entry = self.env['account.move'].create(dict_entry)
		if discount_move_entry:
			discount_move_entry.account_analytic_destino()
			discount_move_entry.post()

		# Conciliar todas las letras en descuento con la linea en 45
		lines = discount_move_entry.line_ids.filtered(lambda l: l.account_id == self.letter_det_ids[0].move_id.invoice_line_ids.account_id)
		for letter in self.letter_det_ids:
			if letter.letter_state == 'discount':
				lines += letter.move_id.line_ids.filtered(lambda l: l.credit > 0)
		lines.reconcile()

		for entry in discount_move_entry:
			msg_body = _("This entry for protest was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)
			entry.seat_generated_id = self and self.id or False

	# Asiento por diferencias creadas al canjear letras de los agentes de aduanas
	# Solo debe funcionar si es menor o mayor a 0.01
	def _create_difference_move(self):
		if abs(self.difference_amount) > 0.01:
			raise UserError(_('Difference amount can\'t be greather than 0.01'))
		lines = []
		# Obtenemos el tipo de cambio del contexto
		exchange_rate = self.env.context.get('exchange_rate')
		_writeoff_account_id=self.env.context.get('_writeoff_account_id')
		analytic_account_id=self.env.context.get('analytic_account_id')
		analytic_tag_ids=self.env.context.get('analytic_tag_ids')
		if self.currency_id != self.env.company.currency_id:
			amount_currency_credit = abs(self.difference_amount)
			amount_credit = self.currency_id.round(amount_currency_credit * exchange_rate)
		else:
			amount_currency_credit = 0
			amount_credit = self.difference_amount
		# Si falta un centavo en las letras tomamos la cuenta por pagar de las facturas
		# sino utilizamos la cuenta del diario transitorio
		if self.difference_amount > 0:
			account_id = self.letter_det_ids[0].move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable').account_id
		else:
			account_id = self.journal_id.payment_credit_account_id
		lines.append((0, 0, {
			'partner_id': self.partner_id.id,
			'account_id': account_id.id,
			'amount_currency': amount_currency_credit if self.difference_amount > 0 else -amount_currency_credit,
			'currency_id': self.currency_id.id,
			'credit': amount_credit if self.difference_amount < 0 else 0,
			'debit': amount_credit if self.difference_amount > 0 else 0
			}))
		lines.append((0, 0, {
			'partner_id': self.partner_id.id,
			# 'name': _('Difference ') + self.currency_id.symbol + ' - ' + self.partner_id.name + ' - ' + str(self.date or fields.Date.today()),
			'account_id': _writeoff_account_id.id,
			'analytic_account_id': analytic_account_id and analytic_account_id.id or False,
			'analytic_tag_ids': analytic_tag_ids and analytic_tag_ids.ids or False,
			'amount_currency': amount_currency_credit if self.difference_amount < 0 else -amount_currency_credit,
			'currency_id': self.currency_id.id,
			'credit': amount_credit if self.difference_amount > 0 else 0,
			'debit': amount_credit if self.difference_amount < 0 else 0
			}))
		dict_entry = {
			'date': self.date or fields.Date.today() or False,
			'journal_id': self.journal_id.id,
			'move_type': 'entry',
			'partner_id': self.partner_id.id,
			'ref': _('Adjustment for difference in letters on customs agent import N° %s exchange %s') %(self.letter_det_ids[0].move_id.import_number_id.name, str(self.name)),
			#'gloss': _('Adjustment for difference in letters on customs agent import N° %s exchange %s') %(self.letter_det_ids[0].move_id.import_number_id.name, str(self.name)),
			'line_ids': lines,
			}
		payment_entry = self.env['account.move'].create(dict_entry)
		if payment_entry:
			payment_entry.account_analytic_destino()
			payment_entry.post()
			# Conciliamos la linea de la diferencia con la factura en caso no cuadre por el centavo
			# pero debemos saber cual de las facturas no se concilio completamente
			if self.difference_amount > 0:
				for inv in self.letter_det_ids:
					if inv.move_id.amount_residual > 0:
						invoice_to_reconcile = inv.move_id
						break
			# line = self.letter_det_ids[0].move_id.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable' and not l.reconciled)
				line = invoice_to_reconcile.line_ids.filtered(lambda l: l.account_id.internal_type == 'payable' and not l.reconciled)
				line += payment_entry.line_ids.filtered(lambda l: l.debit > 0 and l.account_id.internal_type == 'payable')
				line.reconcile()

		for entry in payment_entry:
			msg_body = _("This entry for difference was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)
			entry.seat_generated_id = self and self.id or False

	def exchange_process(self):
		for rec in self:
			############## POLIMASTER ################
			# Buscamos una fecha y un tipo de cambio para la conciliación de los asientos
			if rec.operation_methods in ['discount','renewal','portfolio'] or rec.date != fields.Date.context_today(self) or (rec.operation_methods == 'protest' and any(letter.move_id.letter_state == 'discount' for letter in rec.letter_det_ids)) or (rec.exchange_type == 'payment' and rec.difference_amount != 0) or any(letter.field_invisible == False for letter in rec.list_letters_ids):
				context = {'active_ids': rec.ids, 'active_model': 'letter.management', 'active_id': rec.id, 'currency': False if rec.currency_id != self.env.company.currency_id else True, 'protest': True if rec.operation_methods == 'protest' else False}
				if rec.exchange_type == 'payment' and rec.difference_amount != 0:
					context['difference_payment'] = True
				return self.env['date.rate.wizard']\
					.with_context(context)\
					.get_post_date_and_rate()
			else:
				# self.env.context['exchange_date'] = self.date
				# self.env.context['exchange_rate'] = self.exchange_rate
				rec.with_context(exchange_date=rec.date, exchange_rate=rec.exchange_rate, bank_interests=0, financial_expenses=0)._exchange_process_after()

	def _exchange_process_after(self):
		# total = 0
		for rec in self:
			############## POLIMASTER ################
			# Obtenemos la fecha y el tipo de cambio del contexto
			exchange_date = self.env.context.get('exchange_date')
			user_exchange_rate = self.env.context.get('user_exchange_rate')
			exchange_rate = self.env.context.get('exchange_rate')
			self.exchange_date = exchange_date
			self.user_exchange_rate = user_exchange_rate
			self.exchange_rate = exchange_rate
			# Cambiamos las fechas a todos los asientos creados en letras
			for letter in rec.list_letters_ids:
				letter.date = exchange_date
				letter.acceptance_date = exchange_date
				if exchange_rate and letter.currency_id != self.env.company.currency_id:
					letter.exchange_rate = exchange_rate
					# # Reemplazamos la linea de abajo por lo siguiente
					# letter.line_ids.filtered(lambda l: l.debit > 0).with_context(check_move_validity=False).debit = letter.line_ids.filtered(lambda l: l.debit > 0).amount_currency * exchange_rate
					# letter.line_ids.filtered(lambda l: l.credit > 0).with_context(check_move_validity=False).credit = letter.line_ids.filtered(lambda l: l.credit > 0).amount_currency * exchange_rate
					letter.with_context(check_move_validity=False)._onchange_currency()
			self._check_products_company()
			self._check_bridge_journal()
			check_modules = True
			rec._check_letter_management_modules_are_installed(check_modules)
			############## POLIMASTER ################
			# Agregamos validación por si las letras fueron borradas cuando estaban en borrador
			rec._check_for_letters()
			# letter_payable_module = self.env['ir.module.module'].sudo().search(
			#     [('name', '=', 'qa_letter_management_payables'), ('state', '=', 'installed')], limit=1)
			# letter_receivable_module = self.env['ir.module.module'].sudo().search(
			#     [('name', '=', 'qa_letter_management_receivable'), ('state', '=', 'installed')], limit=1)
			#
			# if len(letter_payable_module) == 0 and len(letter_receivable_module) == 0:
			#     raise UserError(_('The Letters Receivable or Payable modules were not found to be installed.'))

			# for letters_docs in rec.list_letters_ids:
			#     if rec.exchange_type in ['payment']:
					# if len(letter_payable_module) == 1:
						# if rec.letters_is_created:
							# if not letters_docs.invoice_serie:
							#     raise UserError(_('Add the Invoice serie to validate'))
							# if not letters_docs.invoice_number:
							#     raise UserError(_('Add the Invoice Number to validate'))
					# else:
					#     raise UserError(_('Please install the Letters payables module'))
				# if rec.exchange_type in ['collection']:
				#     if not len(letter_receivable_module) == 1:
				#         raise UserError(_('Please install the Letters receivables module'))

			# if not rec.state == 'in_process':
			#     raise UserError(_('only validates when the template is in the >> in process << state'))
			# if not rec.letters_is_created:
			#     raise UserError(_('Generate the letters first'))
			# if not rec.another_journal_id:
			#     raise UserError(_('Choose a journal for the letters generate'))
			rec._check_if_ribbon_is_activated()
			# if rec.operation_methods in ['portfolio', 'refinancing']:
			rec._check_if_difference_exists()
			rec._check_before_to_processing_the_payment()
			
			# for amount in rec.letter_det_ids:
				# if amount.amount_payable == 0:
				#     if amount.move_id.amount_residual > 0.0:
				#         raise UserError(_(
				#             'The documents must have a amount payable (can be partial payment)'))
				# if amount.move_id.amount_residual <= 0.0:
				#     raise UserError(_('The documents must have a balance due'))
			# if rec.operation_methods in ['portfolio']:
			#     if rec.is_debit_generated:
			#         if not rec.include_interests_in_letter:
			#             if rec.total_amount_fact != rec.total_amount_letras:
			#                 raise UserError(_(
			#                     'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge and Letters <<'))
			#         else:
			#             doc_plus_interest = rec.currency_id.round(_create_discount_move
			#                 rec.total_amount_fact + rec.all_amount_interest)  # monto de los documentos mas los intereses
			#             if doc_plus_interest != rec.total_amount_letras:  #
			#                 raise UserError(_(
			#                     'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge + interest << and Letters'))
			#     elif rec.difference_amount != 0:
			#         raise UserError(_('You cannot validate, there is a difference in the amounts'))

			if rec.state in ['in_process']:
				new_payment_ids = []
				# docs_receivable = [].amount_discount), letter.currency_id
				# Metodo de Pago - General
				payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
				if not payment_method_id:
					payment_method_id = self.env['account.payment.method'].search([], limit=1)

				### Iteracion por factura a pagar ###
				# for doc in docs_receivable:
				############## POLIMASTER ################
				# Revisamos si hay diferencia para llevar el control de los pagos por facturas
				total_bills = rec.total_amount_letras
				# Ordenamos la lista antes de crear los pagos
				for invoice in rec.letter_det_ids.sorted(key=lambda x: (x.move_id.invoice_date_due, x.move_id.create_date)):
				# for invoice in rec.letter_det_ids:
					payment_data = rec._assigning_values_for_payment(exchange_date, exchange_rate, invoice=invoice, payment_method_id=payment_method_id)
					if rec.operation_methods == 'portfolio':
						# Controlamos los pagos para no exceder las facturas
						aux = total_bills - payment_data['amount']
						if aux < 0:
							payment_data['amount'] = total_bills
							payment_id = self.env['account.payment'].create(payment_data)
							new_payment_ids.append((payment_id, invoice))
							break
						else:
							total_bills -= payment_data['amount']
					# if rec.operation_methods == 'protest' and invoice.letter_state == 'discount':
					#     payment_data['destination_account_id'] = invoice.move_id.line_ids.filtered(lambda l: l.debit > 0).account_id.id
					# if rec.operation_methods != 'protest' and invoice.letter_state != 'discount' and rec.operation_methods != 'refinancing':
					if rec.operation_methods == 'protest' and invoice.move_id.letter_state == 'discount':
						payment_data['destination_account_id'] = invoice.move_id.line_ids.filtered(lambda l: l.debit > 0).account_id.id
					if rec.operation_methods == 'renewal':
						payment_data['payment_type'] = 'inbound'
						payment_data['partner_type'] = 'customer'
					payment_id = self.env['account.payment'].create(payment_data)
					# if rec.operation_methods == 'protest' and invoice.letter_state == 'discount':
					#     move_id = payment_id.move_id
					#     move_id.line_ids.filtered(lambda l: l.debit > 0).account_id = invoice.move_id.line_ids.filtered(lambda l: l.debit > 0).account_id
					new_payment_ids.append((payment_id, invoice))

				############## POLIMASTER ################
				# Si es una renovación tambien disminuimos la resposabilidad por las letras Renovadas
				if rec.operation_methods == 'renewal':
					for letter in self.letter_det_ids:
						if letter.letter_state == 'discount':
							payment_data['payment_type'] = 'outbound'
							payment_data['partner_type'] = 'supplier'
							payment_data['amount'] = abs(letter.move_id.amount_residual)
							payment_data['destination_account_id'] = letter.move_id.line_ids.filtered(lambda l: l.credit > 0).account_id.id
							payment_id = self.env['account.payment'].create(payment_data)
							payment_id.action_post()
							lines = payment_id.move_id.line_ids.filtered(lambda l: l.debit > 0)
							line2 = letter.move_id.line_ids.filtered(lambda l: l.credit > 0)
							lines += letter.move_id.line_ids.filtered(lambda l: l.credit > 0)
							lines.reconcile()
							gloss_entry = self._assigning_gloss_to_payment(letter.partner_id.vat, payment_id.reconciled_invoice_ids)
							#payment_id.move_id.gloss = payment_id.move_id.ref = gloss_entry
							seat = payment_id.move_id or payment_id.payment_seat_id or False
							seat.is_seat_generated = True
							seat.seat_generated_id = self and self.id or False
							# new_payment_ids.append((payment_id, letter))
				# Para los refinanciamientos de letras
				# if rec.operation_methods == 'refinancing':
				#     for letter in rec.letter_det_ids:
				#         if letter.move_id.letter_state == 'discount':
				#             rec._create_refinancing_payment(letter.move_id.line_ids.filtered(lambda l: l.debit > 0))

				# Si es un protesto creamos el asiento de cargo con gastos financieros
				if rec.operation_methods == 'protest':
					protest_account_id = self.env['account.update'].search([('letter_state','=','protest'),('currency_id','=',self.currency_id.id),('transaction_type','=', 'is_sale_document' if self.exchange_type == 'collection' else 'is_purchase_document')], limit=1).account_id
					if not protest_account_id:
						raise UserError("No se encontro cuenta")
					for letter in self.list_letters_ids:
						letter.line_ids.filtered(lambda l: l.account_id.internal_type in ('receivable','payable')).account_id = protest_account_id
					if any(letter.letter_state == 'discount' for letter in rec.letter_det_ids):
						rec._create_protest_charge()
						

				# si se marcó que los intereses se incluyen en las letras generadas
				# se procede a realizar el cobro de las notas de debito generadas
				# if rec.include_interests_in_letter:
				for debit in rec.list_debit_notes_ids:
					payment_data = rec._assigning_values_for_payment(exchange_date, exchange_rate, debit_note=debit, payment_method_id=payment_method_id)
					payment_id = self.env['account.payment'].create(payment_data)
					new_payment_ids.append((payment_id, debit))

				rec.check_values_to_post_docs()

				# Postea la letra generada
				# if rec.operation_methods in ['portfolio']:
					# if not rec.generate_interest:
					#     if rec.currency_id.round(rec.total_amount_fact) != rec.currency_id.round(
					#             rec.total_amount_letras):
					#         raise UserError(_(
					#             'Total amount of Docs receivable is different from the total amount of Letters generated\n'
					#             'Edit the amount of the letter so that there are no differences\n'
					#             'Otherwise, you will not be able to validate.'))
					# if rec.list_letters_ids.mapped('invoice_date_due').count(False) >= 1:
					#     raise UserError(_('Acceptance date is missing'))seat_generated_id
					# for days in rec.list_letters_ids:rate if rate else 
					#     if days.sunat_serie.id == False:
					#         raise UserError(_('Regenerate the letters, the series is missing'))
						# if days.how_days_expires == False:
						#     raise UserError(_('Values are missing in the Due Days field'))

					# dominio = [('state', 'like', 'draft'),
					#            ('letter_create_id', 'like', self.id),
					#            ('document_type_code', 'in', ['LT', '08'])]
					# invoices_to_post = rec.list_letters_ids.search(dominio, order="id asc")reconcile_date
					# rec.list_letters_ids.post()
					# if rec.operation_methods in ['portfolio']:
					#     rec.is_exchanged = True

				# Se postea un mensaje en el doc por cobrar diciendo que se genero letras en X plantilla
				# data = {}
				# process = {
				#     'portfolio': _('Exchange'),
				#     }
				# data['operacion'] = process.get(self.operation_methods, "") if self.operation_methods else ""
				# for docs_r in rec.letter_det_ids:
				#     msg_body = _(
				#         "Letters have been generated in template N°:") + " <a href=# data-oe-model=letter.management data-oe-id=%d>%s</a> %s" % (
				#                    self.id, self.id, data['operacion'])
				#     docs_r.move_id.message_post(body=msg_body)
				#     docs_r.move_id.have_letters_generated_id = self and self.id or False
				# Publicamos los pagos preparados
				# for pay in new_payment_ids:
				#     pay.post()
				#     pay.move_line_ids.move_id.is_seat_generated = True
				#     pay.move_line_ids.move_id.seat_generated_id = self and self.id or False
				#     pay.move_line_ids.move_id.gloss = False
				#     ruc = pay.partner_id.vat
				#     operation_type = pay.invoice_ids[0].operation_type_id and pay.invoice_ids[
				#         0].operation_type_id.id or False
				#     if rec.exchange_type in ['collection']:
				#         serie = pay.invoice_ids[0].sunat_serie and pay.invoice_ids[0].sunat_serie.id or False
				#         number_fact = pay.invoice_ids[0].sunat_number
					# if rec.exchange_type in ['payment']:
					#     serie = pay.invoice_ids[0].invoice_serie or False
					#     number_fact = pay.invoice_ids[0].invoice_number
					# gloss_entry = 'Ingreso de ' + str(ruc) + '-' + str(operation_type) + '-' + str(serie) + '-' + str(
					#     number_fact)
					# pay.move_line_ids.move_id.gloss = gloss_entry
				
				# Realizamos un cambio de cuenta antes de conciliar para las letras en descuento
				if self.operation_methods == 'discount':
					account_id = self.journal_id_type_bank_id.responsibility_account_id
					if not account_id:
						raise UserError(_('Bank journal %s does not have a responsibility account.') %self.journal_id_type_bank_id.name)
					for letter in self.list_letters_ids:
						letter.line_ids.filtered(lambda l: l.credit > 0).account_id = account_id
						# Agregamos estas lineas para poder pagar la 45 que esta como linea de factura
						letter.line_ids.filtered(lambda l: l.credit > 0).amount_residual = -letter.amount_residual_signed
						letter.line_ids.filtered(lambda l: l.credit > 0).amount_residual_currency = -letter.amount_residual

				# Realizamos un cambio de cuenta antes de conciliar para las letras renovadas en descuento
				if self.operation_methods == 'renewal':
					for letter in self.list_letters_ids:
						account_id = letter.origin_id.invoice_line_ids[0].account_id
						letter.invoice_line_ids
						letter.line_ids.filtered(lambda l: l.credit > 0).account_id = account_id
						# Agregamos estas lineas para poder pagar la 45 que esta como linea de factura
						letter.line_ids.filtered(lambda l: l.credit > 0).amount_residual = -letter.amount_residual_signed
						letter.line_ids.filtered(lambda l: l.credit > 0).amount_residual_currency = -letter.amount_residual
						# for payment, invoice in new_payment_ids:
						#     aux_account_id = payment.destination_account_id
						#     payment.partner_type = 'customer'
						#     payment.destination_account_id = aux_account_id

				# Realizamos los procesos de cierre
				# Se postea un mensaje en el doc seleccionado
				rec.assigning_message_in_selected_docs()
				rec.paying_generated_payments(new_payment_ids)
				############## POLIMASTER ################
				# Si el tipo de canje es pago y hay una diferencia en el wizard va a solicitar
				# las cuentas para el descuadre entonces creamos el asiento.
				if rec.exchange_type == 'payment' and self.env.context.get('difference_payment'):
					rec._create_difference_move()
				rec.state = 'posted'
				rec._change_order_invoice_status()
		return True

	def _copy_invoice_user_id_to_letter(self):
		for rec in self:
			invoice_user_id = rec.invoice_user_id.id or False
			if invoice_user_id:
				if rec.list_letters_ids:
					for line in rec.list_letters_ids:
						line.invoice_user_id = invoice_user_id
						line.user_id = invoice_user_id
					_logger.info(f'actualizado la plantilla nro {rec.id} -- vendedor {invoice_user_id}')
			else:
				_logger.info(f'no se encontró vendedor en la plantilla nro {rec.id}')

	# ----
	def _check_if_ribbon_is_activated(self):
		for rec in self:
			if rec.is_exchanged:
				raise UserError(_('Selected documents cannot be exchanged if they have already been exchanged'))

	def _check_if_difference_exists(self):
		for rec in self:
			if rec.operation_methods in ['portfolio', 'refinancing']:
				if rec.is_debit_generated:
					if not rec.include_interests_in_letter:
						if rec.total_amount_fact != rec.total_amount_letras:
							raise UserError(_(
								'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge and Letters <<'))
					else:
						doc_plus_interest = rec.currency_id.round(rec.total_amount_fact + rec.all_amount_interest)
						if doc_plus_interest != rec.total_amount_letras:
							raise UserError(_(
								'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge + interest << and Letters'))
				elif rec.difference_amount != 0:
					############## POLIMASTER ################
					# Quitamos el error de usuario y creamos el asiento de anticipo si el monto de letras supera el de las facturas
					# raise UserError(_('You cannot validate, there is a difference in the amounts'))
					if rec.total_amount_fact < rec.total_amount_letras and rec.exchange_type == 'collection':
						payment_data = rec._create_advanced_payment_difference_amount()
						payment_id = self.env['account.payment'].create(payment_data)
						payment_id.action_post()
						self.advanced_payment_move_id = payment_id.move_id

	############## POLIMASTER ################
	# Nueva función para la creacion del anticipo
	# Obtenemos la cunenta desde la homologación
	def _create_advanced_payment_difference_amount(self):
		# Obtenemos la fecha y el tipo de cambio del contexto
		exchange_date = self.env.context.get('exchange_date')
		exchange_rate = self.env.context.get('exchange_rate')
		account_advanced_payment_id = self.env['account.update'].search([('anticipo_provider','=','True'),('currency_id','=',self.currency_id.id),('transaction_type','=', 'is_sale_document' if self.exchange_type == 'collection' else 'is_purchase_document')], limit=1).account_id
		if not account_advanced_payment_id:
			action = self.env.ref('solse_pe_edi.account_update_action')
			msg = _('The account for advanced payments is not configured in homologation. Please add an advanced payment account for %s') %self.currency_id.name
			raise RedirectWarning(msg, action.id, _('Go to Homologation'))
		self._check_advanced_journal()
		payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
		if not payment_method_id:
			payment_method_id = self.env['account.payment.method'].search([], limit=1)
		payment_values = {
			'partner_id': self.partner_id.id,
			'amount': abs(self.difference_amount),
			'destination_account_id':  account_advanced_payment_id.id,
			'payment_type': self.payment_type,
			'partner_type': self.partner_type,
			'payment_method_id': payment_method_id and payment_method_id.id or False,
			'state': 'draft',
			'company_id': self.company_id and self.company_id.id or False,
			'date': exchange_date if exchange_date else (self.date.strftime("%Y-%m-%d") if self.date else False),
			'currency_id': self.currency_id and self.currency_id.id or False,
			'other_currency': self.other_currency if self.other_currency else False,
			'journal_id': self.env.company.advanced_journal_id and self.env.company.advanced_journal_id.id or False, #self.journal_id and self.journal_id.id or False,
			}
		if payment_values['other_currency']:
			payment_values['exchange_date'] = exchange_date if exchange_date else (self.exchange_date.strftime("%Y-%m-%d") if self.exchange_date else False)
			payment_values['user_exchange_rate'] = self.user_exchange_rate if self.user_exchange_rate else False
			payment_values['exchange_rate'] = exchange_rate if exchange_rate else self.exchange_rate
		if not isinstance(payment_values.get('amount'), (float, int)):  # type(monto) != type(float or int)
			payment_values['amount'] = payment_values['amount'][0]
		return payment_values

	def _check_before_to_processing_the_payment(self):
		for rec in self:
			if rec.state not in ['in_process']:
				raise UserError(_('only validates when the template is in the >> in process << state'))
			if rec.state in ['in_process']:
				if not rec.another_journal_id:
					raise UserError(_('Choose a journal for the letters generate'))
				if not rec.letters_is_created:
					raise UserError(_('Generate the letters first'))

				for doc in rec.letter_det_ids:
					if doc.amount_payable == 0:
						if doc.move_id.amount_residual > 0.0:
							raise UserError(_('The documents must have a amount payable (can be partial payment)'))
					if doc.move_id.amount_residual <= 0.0:
						raise UserError(_('The documents must have a balance due'))

				"""if rec.exchange_type in ['payment']:
					for letters_docs in rec.list_letters_ids:
						if rec.letters_is_created:
							if not letters_docs.invoice_serie:
								raise UserError(_('Add the Invoice serie to validate'))
							if not letters_docs.invoice_number:
								raise UserError(_('Add the Invoice Number to validate'))"""


	def _assigning_values_for_payment(self, date=False, rate=False, invoice=False, debit_note=False, payment_method_id=False):
		for rec in self:
			payment_values = {
				'payment_type': rec.payment_type,
				'partner_type': rec.partner_type or 'customer',
				'payment_method_id': payment_method_id and payment_method_id.id or False,
				'state': 'draft',
				'company_id': rec.company_id and rec.company_id.id or False,
				'date': date if date else (rec.date.strftime("%Y-%m-%d") if rec.date else False),
				'currency_id': rec.currency_id and rec.currency_id.id or False,
				#'other_currency': rec.other_currency if rec.other_currency else False,
				'journal_id': rec.journal_id and rec.journal_id.id or False,
				}
			if invoice:
				_logger.info("invoice")
				_logger.info(invoice)
				payment_values['partner_id'] = invoice.move_id.partner_id and invoice.move_id.partner_id.id or False
				payment_values['amount'] = invoice.amount_payable,
				payment_values['destination_account_id'] = invoice.move_id._get_account_for_payment()
				# if rec.partner_type in ['customer']:
				#     payment_values['reconciled_invoice_ids'] = [(6, 0, [invoice.move_id.id])]
				# if rec.partner_type in ['supplier']:
				#     payment_values['reconciled_bill_ids'] = [(6, 0, [invoice.move_id.id])]

			if debit_note:
				_logger.info("debit_note")
				_logger.info(debit_note)
				payment_values['partner_id'] = debit_note.partner_id and debit_note.partner_id.id or False
				payment_values['amount'] = debit_note.amount_residual,
				payment_values['destination_account_id'] = debit_note._get_account_for_payment()
				# payment_values['invoice_ids'] = [(6, 0, [debit_note.id])]

			if 'other_currency' in payment_values and payment_values['other_currency']:
				payment_values['exchange_date'] = date if date else (rec.exchange_date.strftime("%Y-%m-%d") if rec.exchange_date else False)
				payment_values['user_exchange_rate'] = rec.user_exchange_rate if rec.user_exchange_rate else False
				payment_values['exchange_rate'] = rate if rate else rec.exchange_rate
			if not isinstance(payment_values.get('amount'), (float, int)):  # type(monto) != type(float or int)
				payment_values['amount'] = payment_values['amount'][0]
			# Para poder descargar la cuenta de responsabilidad en una renovación
			if rec.operation_methods == 'renewal':
				payment_values['payment_type'] = 'outbound'
				payment_values['partner_type'] = 'supplier'

			_logger.info("===============================")
			_logger.info(payment_values)
			return payment_values

	def check_values_to_post_docs(self):
		for rec in self:
			if rec.exchange_type in ['payment']:
				for doc in rec.list_letters_ids:
					if not doc.invoice_serie:
						raise UserError(_('Indica una serie en los documentos generados >> Pestaña Letras <<'))
					if not doc.how_days_expires:
						raise UserError(_('Values are missing in the Due Days field'))
					if not doc.invoice_date_due:
						raise UserError(_('Date due is missing'))
					# if not doc.unique_code_supplier:
					#     raise UserError(_('Enter the Unique Code'))
					# if not doc.sunat_serie:
					#     raise UserError(_('Regenerate the letters, the series is missing'))
				rec.posting_docs_in_portfolio()

	def posting_docs_in_portfolio(self):  # Letras en Cartera (antes de publicarlas)
		for rec in self:
			# if not rec.generate_interest and rec.operation_methods in ['portfolio', 'refinancing']:
			#     if rec.currency_id.round(rec.total_amount_fact) != rec.currency_id.round(rec.total_amount_letras):
			#         raise UserError(
			#             _('Total amount of Docs receivable is different from the total amount of Letters generated\n'
			#               'Edit the amount of the letter so that there are no differences\n'
			#               'Otherwise, you will not be able to validate.'))
			domain = [('state', 'like', 'draft'),
					  ('letter_create_id', 'like', self.id),
					  ('document_type_code', 'in', ['LT', '08'])]

			lista = rec.list_letters_ids
			_logger.info("====================================")
			_logger.info(domain)
			_logger.info(lista)
			if not lista:
				continue

			invoices_to_post = lista.search(domain, order='id asc')
			if rec.operation_methods in ['portfolio']:
				rec.is_exchanged = True
				print(f' --- {invoices_to_post}')
				invoices_to_post.action_post()

	def assigning_message_in_selected_docs(self):
		data = {}
		for rec in self:
			process = rec._get_process()

			if process:
				data['operacion'] = process.get(rec.operation_methods, '') if rec.operation_methods else ''
			if data['operacion']:
				for doc in rec.letter_det_ids:
					msg_body = _(
						"Letters have been generated in template N°:") + " <a href=# data-oe-model=letter.management data-oe-id=%d>%s</a> %s" % (
								   rec.id, rec.id, data['operacion'])
					doc.move_id.message_post(body=msg_body)
					doc.move_id.have_letters_generated_id = rec and rec.id or False

	def _get_process(self):
		process = {'portfolio': _('Exchange')}
		return process

	def paying_generated_payments(self, new_payment_ids):
		############## POLIMASTER ################
		# Para verificar si los montos son exactos al momento de canjear
		payments = self.env['account.move']
		for payment_id in new_payment_ids:
			payments += payment_id[0].move_id
		if sum(self.list_letters_ids.line_ids.mapped('debit')) != sum(payments.line_ids.mapped('debit')):
			difference = sum(self.list_letters_ids.line_ids.mapped('debit')) - sum(payments.line_ids.mapped('debit')) 
			if difference and self.total_amount_fact == self.total_amount_letras:
				payments[0].with_context(check_move_validity=False).line_ids.filtered(lambda l: l.debit > 0).debit += difference
				payments[0].with_context(check_move_validity=False).line_ids.filtered(lambda l: l.credit > 0).credit += difference
		for payment, line in new_payment_ids:
			payment.action_post()
			# conciliando los pagos con las facturas para que éstas estén pagadas
			payment_line = payment.move_id.line_ids.filtered(
				lambda line: line.account_id.id == payment.destination_account_id.id)
			if payment_line and line:
				if line._name == 'account.move':  # nota de debito
					line.js_assign_outstanding_line(payment_line.id)
				else:
					x = line.move_id.js_assign_outstanding_line(payment_line.id)
			# asiento contable
			seat = payment.move_id or payment.payment_seat_id or False
			seat.is_seat_generated = True
			seat.seat_generated_id = self and self.id or False
			#seat.gloss = seat.ref = False
			ruc = payment.partner_id.vat
			first_line_in_pay = False
			if payment.reconciled_invoice_ids or payment.reconciled_bill_ids:
				if payment.partner_type in ['customer']:
					############## POLIMASTER ################
					# Filtro para evitar los asientos de responsabilidad que no tienen facturas conciliadas
					if payment.reconciled_invoice_ids:
						first_line_in_pay = payment.reconciled_invoice_ids[0]
				if payment.partner_type in ['supplier']:
					first_line_in_pay = payment.reconciled_bill_ids[0] if payment.reconciled_bill_ids else payment.reconciled_invoice_ids[0]
			gloss_entry = self._assigning_gloss_to_payment(ruc, first_line_in_pay)
			#seat.gloss = seat.ref = gloss_entry
				# total = self.list_letters_ids[0].with_context(check_move_validity=False).line_ids.filtered(lambda l: l.debit > 0).debit + difference
				# exchange_rate = total / self.list_letters_ids[0].amount_residual 
				# self.list_letters_ids[0].exchange_rate = exchange_rate
		# One2many field
		# self.seat_generated_by_payment_ids.append(seat.id)

	def _assigning_gloss_to_payment(self, ruc, first_line_in_pay):
		for rec in self:
			if first_line_in_pay:
				#operation_type = first_line_in_pay.operation_type_id and first_line_in_pay.operation_type_id.id or False
				operation_type = False
				serie, number = rec._get_serie_and_number_of_invoices(first_line_in_pay)
				if serie and number:
					label = rec.partner_type in ['customer'] and 'Ingreso de ' or 'Egreso de '
					gloss_entry = f'{label} {ruc} - {operation_type} - {serie} - {number}'
					return gloss_entry

	def _get_serie_and_number_of_invoices(self, first_line_in_pay):
		for rec in self:
			serie = number = ''
			if rec.exchange_type in ['payment']:
				serie = first_line_in_pay.invoice_serie or False
				number = first_line_in_pay.invoice_number
			if rec.exchange_type in ['collection']:
				"""serie = first_line_in_pay.sunat_serie.name if first_line_in_pay.sunat_serie else False
				number = first_line_in_pay.sunat_number"""
				numero = first_line_in_pay.l10n_latam_document_number.split(" ")
				if len(numero) == 2:
					serie = numero[0]
					number = numero[1]
				else:
					serie = "F"
					number = first_line_in_pay.name
			return serie, number

	def _check_journals_to_generate_letters(self):
		for rec in self:
			if not rec.journal_id:
				raise UserError(_('Journal to Pay missing'))
			if not rec.another_journal_id:  # Diario de Letras >> Otro Diario
				raise UserError(_('The journal with which the letters will are generated is missing'))

	def _check_if_debit_notes_were_generated(self):
		for rec in self:
			if rec.operation_methods in ['portfolio', 'refinancing']:
				if rec.generate_interest:  # Si marca generar intereses y quiere generar las letras pero sin generar antes la nota de debito
					# if not rec.debit_notes_in_docs:
					if not rec.is_debit_generated:
						raise UserError(
							_('Generate and publish the debit note before generating the letters'))
					else:
						for debit_note_generated in rec.list_debit_notes_ids:
							if debit_note_generated.state != 'posted':
								raise UserError(_('Publish the debit note first'))

	def _check_letter_number_and_days_range(self):
		for rec in self:
			if rec.operation_methods in ['portfolio', 'refinancing']:
				# if rec.letter_number <= 0 and rec.days_range <= 0:
				#     raise UserError(_(
				#         'The values entered in Letters to generate and Range of days must be greater than 0'))
				if rec.letter_number <= 0:
					raise UserError(
						_('The value entered in Letters to be generated must be greater than 0'))
				if rec.days_to_first <= 0:
					raise UserError(_('Values entered in the Day to first letter must be greater than 0'))
				if rec.days_range <= 0 and rec.letter_number > 1:
					raise UserError(_('Values entered in the Day Range must be greater than 0'))

	def _generate_letters_in_template(self):
		for rec in self:
			if rec.exchange_type in ['payment']:
				if rec.operation_methods in ['portfolio']:
					# operation_method = ['portfolio']
					rec._generate_letters_portfolio(rec.operation_methods)
				else:
					raise UserError('Error causado por el metodo de operacion escogido')

	def _generate_letters_portfolio(self, operation_methods):
		for rec in self:
			account_move = self.env['account.move']
			# if rec.operation_methods in operation_methods:
			date_temp = rec.date + timedelta(days=rec.days_to_first - rec.days_range)
			amount_temp = 0
			amount_total = 0

			# asignacion de montos: al llegar al ultimo, se restara el monto que paga el usuario
			# con el monto acumulado
			for line in range(0, rec.letter_number):
				if line == rec.letter_number - 1:
					if rec.include_interests_in_letter:
						amount_total = rec.currency_id.round(
							(rec.total_amount_fact + rec.all_amount_interest) - amount_temp)
					else:
						amount_total = rec.currency_id.round(rec.total_amount_fact - amount_temp)
				else:
					if rec.include_interests_in_letter:
						amount_total = rec.currency_id.round(
							(rec.total_amount_fact + rec.all_amount_interest) / rec.letter_number)
					else:
						amount_total = rec.currency_id.round(
							rec.total_amount_fact / rec.letter_number)

					amount_temp += amount_total
				date_due = date_temp = date_temp + timedelta(days=rec.days_range)
				product_portfolio = rec.company_id.letter_portfolio
				letter = []
				letter = rec._get_invoices_lines(product_portfolio, amount_total, letter, is_letter=True)
				# print(letter)
				# letras = inv_lines
				letter['partner_id'] = rec.partner_id and rec.partner_id.id or False
				letter['acceptor_id'] = rec.partner_id and rec.partner_id.id or False
				letter['invoice_date_due'] = date_due
				days_expires = letter['invoice_date_due'] - letter['invoice_date']
				letter['how_days_expires'] = days_expires.days
				letter['bank_acc_number_id'] = self.bank_acc_number_id.id
				letter['bank_id'] = self.journal_id_type_bank_id.bank_id and self.journal_id_type_bank_id.bank_id.id or False
				#letter['gloss'] = _('Exchange letter template ') + rec.name
				_logger.info("datos para crear letraaaaa")
				_logger.info(letter)
				account_move.create(letter)

			# if rec.list_letters_ids:
			#     rec.letters_is_created = True
			#     rec.state = 'in_process'

	# def get_origin(self, letter):
	#     if not letter.origin_id:
	#         self.get_origin()

	def _get_invoices_lines(self, product_letter, amount_total, letter, is_letter=False):
		# if self.operation_methods == 'renewal':
		#     account_id = letter.invoice_line_ids[0].account_id
		# else:
		account_id = product_letter.property_account_income_id
		line = {
			'product_id': product_letter.id,
			'name': product_letter.display_name,
			# 'account_id': product_letter.property_account_income_id.id,
			############## POLIMASTER ################
			# Obtener cuenta desde el diario. Por cada banco una cuenta de responsabilidad distinta
			'account_id': account_id.id,
			'price_unit': amount_total,
			'product_uom_id': product_letter.uom_id and product_letter.uom_id.id or False,
			}
		if self._tax_ids_debit and not is_letter:
			line.update({'tax_ids': self._tax_ids_debit and self._tax_ids_debit.ids or False})
		invoices_lines = [(0, 0, line)]
		doc_created = self._prepare_invoice_vals(invoices_lines, amount_total)
		if doc_created:
			return doc_created
		else:
			raise UserError('Error inesperado, por favor, vuelva a generar las letras')

	def _get_serie(self):
		serie = False
		return serie

	# Funciones para enviar las letras por correo al Clientes

	def action_letter_sent(self):
		""" Open a window to compose an email, with the letter template
			message loaded by default
		"""
		self.ensure_one()
		template = self.env.ref('qa_letter_management.email_template_letters', raise_if_not_found=False)
		lang = False
		if template:
			lang = template._render_lang(self.ids)[self.id]
		if not lang:
			lang = get_lang(self.env).code
		compose_form = self.env.ref('qa_letter_management.account_letter_send_wizard_form', raise_if_not_found=False)
		ctx = dict(
			default_model='letter.management',
			default_res_id=self.id,
			# For the sake of consistency we need a default_res_model if
			# default_res_id is set. Not renaming default_model as it can
			# create many side-effects.
			default_res_model='letter.management',
			default_use_template=bool(template),
			default_template_id=template and template.id or False,
			default_record_name=self.name,
			default_composition_mode='comment',
			mark_invoice_as_sent=True,
			custom_layout="mail.mail_notification_light",
			model_description=self.with_context(lang=lang).partner_type.title() + ' Bills of Exchange',
			force_email=True
		)
		return {
			'name': _('Send Letter'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.letter.send',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}

	def action_invoice_print(self):
		""" Print the template and mark it as sent, so that we can see more
			easily the next step of the workflow
		"""
		self.write({'is_move_sent': True})
		return self.env.ref('qa_letter_management.action_account_boe_report').report_action(self)

	def _get_report_base_filename(self):
		return 'Boe_report'

	def actualizar(self):
		move_ids = self.env['account.move'].search([('state','=','posted'),('currency_id.id','=', '2')], order='create_date desc').filtered(lambda m: m.amount_total_signed > round(m.amount_total * m.exchange_rate,2) + 0.02)
		print('*************************************************************************')
		print('******************** Total: ',len(move_ids), ' **************************')
		print('*************************************************************************')
		c=1
		total = len(move_ids)
		for move in move_ids:
			if len(move.line_ids) > 2:
				c+=1
				print(str(c)+'/'+str(total))
				continue
			match_lines_debit = self.env['account.move.line']
			match_lines_credit = self.env['account.move.line']
			line_debit = move.line_ids.filtered(lambda l: l.debit > 0)
			line_credit = move.line_ids.filtered(lambda l: l.credit > 0)
			if line_debit.reconciled and line_debit.account_id.reconcile:
				match_lines_debit += line_debit.matched_credit_ids.credit_move_id
				line_debit.remove_move_reconcile()
			if line_credit.reconciled and line_credit.account_id.reconcile:
				match_lines_credit += line_credit.matched_debit_ids.debit_move_id
				line_credit.remove_move_reconcile()
			line_debit.with_context(check_move_validity=False).debit = abs(line_debit.amount_currency) * move.exchange_rate
			line_credit.with_context(check_move_validity=False).credit = abs(line_credit.amount_currency) * move.exchange_rate
			match_lines_debit += line_debit
			if line_debit.account_id.reconcile:
				match_lines_debit.filtered(lambda l: l.move_id.state == 'posted').reconcile()
			match_lines_credit += line_credit
			if line_credit.account_id.reconcile:
				match_lines_credit.filtered(lambda l: l.move_id.state == 'posted').reconcile()
			c+=1
			print(str(c)+'/'+str(total))

		lm_ids = self.env['letter.management'].search([('state','=','in_process'),('currency_id','=',2)])        
		print('*************************************************************************')
		print('******************** Total: ',len(lm_ids), ' ****************************')
		print('*************************************************************************')
		c=1
		total = len(lm_ids)
		for lm in lm_ids:
			last_number = self.get_last_number(lm.exchange_date, lm.another_journal_id)
			if any(letter.state == 'posted' for letter in lm.list_letters_ids):
				# if any(letter.payment_state == 'paid' for letter in lm.list_letters_ids):
				#     print(str(c)+'/'+str(total))
				#     c+=1
				#     continue
				for letter in lm.list_letters_ids:
					if letter.payment_state == 'not_paid':
						letter.button_draft()
						letter.name='/'
					else:
						letter.name = '/'
						letter.date = lm.exchange_date
						letter.name=letter.name[:11]+str(lm.exchange_date.month).zfill(2)+'/'+str(last_number).zfill(4)
						last_number+=1
				lm.with_context(exchange_date=lm.exchange_date, exchange_rate=lm.exchange_rate).exchange_process()
			print(str(c)+'/'+str(total))
			c+=1
		return 

	def get_last_number(self, date, journal):
		number = self.env['account.move'].search([('journal_id','=',journal.id),('name','like',journal.code + '/2022/' + str(date.month).zfill(2))], order="name desc")
		return int(number[0].name[14:])+1

	def actualiza_banco(self):
		moves = self.env['account.move'].search([('l10n_latam_document_type_id','=',49),('letter_state','in',('discount','protest')),('new_bank_id','=',False)])
		for move in moves:
			print(move.letter_create_id.journal_id_type_bank_id.bank_id)
			move.new_bank_id = move.letter_create_id.journal_id_type_bank_id.bank_id
			if not move.new_bank_id and move.letter_create_id:
				bank_id = self._obtener_envio(move.letter_create_id.letter_det_ids[0].move_id)
				print(bank_id)
				move.new_bank_id = bank_id
	
	def _obtener_envio(self, move):
		if not move.letter_create_id.journal_id_type_bank_id.bank_id and move.letter_create_id:
			move2 = move.letter_create_id.letter_det_ids[0].move_id
			bank_id = self._obtener_envio(move2)
		elif not move.letter_create_id:
			return move.new_bank_id
		else:
			return move.letter_create_id.journal_id_type_bank_id.bank_id.id or move.new_bank_id
		return bank_id

class LetrasFacturas(models.Model):
	_name = 'letter.management.det'
	_description = 'Lineas Factura'

	letter_fact_id = fields.Many2one('letter.management', string="Related to template N°")
	move_id = fields.Many2one('account.move', string='Invoice', required=True, help='Factura seleccionada para procesar')
	generate_move_id = fields.Many2one('account.move', string='Generated invoice', readonly=True, help='Factura generada - No se usa para canje')
	document_type_id = fields.Many2one('l10n_latam.document.type', 'Doc. type')
	partner_id = fields.Many2one('res.partner', string='Partner')
	currency_id = fields.Many2one('res.currency', related='move_id.currency_id', string="Currency", store=True)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
	operation_methods = fields.Selection(OPERATION_METHOD_SELECTION, string='Operation Method', default='portfolio', required=True, readonly=True)

	document_type_code = fields.Char('Document code', related="document_type_id.code", readonly=True)
	document_number = fields.Char(string="Document number", related="move_id.l10n_latam_document_number")

	amount_due = fields.Monetary(string='Amount owed', related="move_id.amount_total")
	interest_on_arrears = fields.Monetary(string='Int. on arrears')
	compensatory_interest = fields.Monetary(string='Compensatory Int.')
	amount_payable = fields.Monetary(string='To pay')
	new_amount_to_pay = fields.Monetary(string='Total', compute='_compute_new_amount', readonly=True)
	paid_amount = fields.Monetary('Debt', readonly=True)

	delay_days = fields.Char(string='Delay Days')
	expiration_date = fields.Date(string='Due date', related="move_id.invoice_date_due", readonly=True)
	invoice_date = fields.Date(string='Emission Date', related="move_id.invoice_date", readonly=True)

	payment_term = fields.Selection([
		('counted', 'Counted'),
		('credit', 'Credit')], string='Payment term', related="move_id.sale_type")
	letter_state = fields.Selection([
		('portfolio', 'In portfolio'),
		('collection', 'In collection'),
		('warranty', 'In warranty'),
		('discount', 'In discount'),
		('protest', 'In protest'),
		], string='Letter State')

	@api.depends('interest_on_arrears', 'compensatory_interest', 'amount_payable')
	def _compute_new_amount(self):
		for amount in self:
			if amount.interest_on_arrears < 0:
				raise UserError(_('Enter an amount greater than 0 in Interest on Arrears'))
			if amount.compensatory_interest < 0:
				raise UserError(_('Enter an amount greater than 0 in Compensatory Interest'))
			amount.new_amount_to_pay = amount.interest_on_arrears + amount.compensatory_interest + amount.amount_payable

	@api.onchange('interest_on_arrears', 'compensatory_interest', 'amount_payable')
	def _onchange_new_amount(self):
		for new_amount in self:
			if new_amount.amount_payable == 0:
				new_amount.amount_payable = new_amount.paid_amount
			new_amount.new_amount_to_pay = new_amount.interest_on_arrears + new_amount.compensatory_interest + new_amount.amount_payable

	@api.onchange('partner_id', 'document_type_id', 'letter_state', 'move_id', 'document_number')
	def _write_partner(self):
		for rec in self:
			# move = []
			# poner no open en los 3 campos
			# rec.letter_fact_id._onchange_partner_or_document_type()
			domain = [('partner_id', '=', rec.partner_id.id), ('l10n_latam_document_type_id', '=', rec.document_type_id.id),
					  ('currency_id', '=', rec.letter_fact_id.currency_id.id),
					  ('payment_state', '=', 'not_paid'), ('state', '=', 'posted')]

			check_modules = True
			rec.letter_fact_id._check_letter_management_modules_are_installed(check_modules)

			# if rec.letter_fact_id.exchange_type in ['collection']:
			#     domain = [('move_type', 'in',['out_refund', 'out_invoice'])]
			# letter_payable_module = self.env['ir.module.module'].sudo().search(
			#     [('name', '=', 'qa_letter_management_payables'), ('state', '=', 'installed')], limit=1)
			# letter_receivable_module = self.env['ir.module.module'].sudo().search(
			#     [('name', '=', 'qa_letter_management_receivable'), ('state', '=', 'installed')], limit=1)
			if not rec.letter_fact_id.exchange_type:
				rec.unlink()

				message = _('Elige primero el Tipo de Canje')
				warning_mess = {'title': _('No hay tipo de canje!'), 'message': message}
				return {'warning': warning_mess}

				# raise UserError(_('Elige primero el tipo de canje'))

			if rec.letter_fact_id.exchange_type in ['payment']:
				# if len(letter_payable_module) == 1:
					if rec.operation_methods in ['portfolio']:
						domain += [('move_type', 'in', ['in_refund', 'in_invoice'])]
					else:
						raise UserError('Solo puede validar los procesos de canje')
				# else:
				#     raise UserError(_('Falta instalar Letras por pagar'))
			if rec.letter_fact_id.exchange_type in ['collection']:
				# if len(letter_receivable_module) == 1:
				domain += [('move_type', 'in', ['out_refund', 'out_invoice'])]
				# else:
				#     raise UserError(_('Falta instalar Letras por cobrar'))

			# if rec.letter_fact_id.operation_methods in ['portfolio']:
			if rec.letter_fact_id.operation_methods in ['portfolio']:
				rec.partner_id = rec.letter_fact_id.partner_id and rec.letter_fact_id.partner_id.id or False
				if rec.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08']:
					rec.document_type_id = False
					# rec.document_type_id = self.env.ref('solse_pe_edi.document_type01').id
					rec.letter_state = False
					rec.move_id = False
				if rec.letter_state:
					rec.letter_state = False
					rec.move_id = False

			if rec.move_id:
				# move.append('move_id.id')
				domain += [('move_id', '!=', rec.letter_fact_id.letter_det_ids.mapped('move_id.id'))]

			if not rec.move_id:
				rec.paid_amount = 0.0
				rec.amount_payable = 0.0
				rec.new_amount_to_pay = 0.0
			# if not rec.partner_id
			return {'domain': {'move_id': domain}}

	@api.onchange('amount_payable')
	def _onchange_move_id(self):
		for rec in self:
			if not rec.move_id:
				rec.amount_payable = 0.0
			else:
				if rec.amount_payable > rec.paid_amount:
					rec.amount_payable = rec.paid_amount

	@api.onchange('move_id')
	def _onchange_amount_payable(self):
		for rec in self:
			if rec.move_id:
				# if rec.paid_amount == 0.0:
				rec.paid_amount = rec.move_id.amount_residual
				rec.amount_payable = rec.paid_amount
