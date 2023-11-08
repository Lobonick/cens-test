# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import timedelta
from odoo.tools import float_round

class LetterManagement(models.Model):
	_inherit = 'letter.management'

	############# FIELDS #############

	### MANY2ONE
	loans_type_id = fields.Many2one('account.account', string="Loans Account", copy=False)
	_writeoff_account_id = fields.Many2one('account.account', string="Difference Account", copy=False)
	analytic_account_id = fields.Many2one('account.analytic.account', string='Analytical Account', required=False)
	analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
	letters_serie_id = fields.Many2one(comodel_name='sunat.series', string="Serie for letters", ondelete="restrict")
	new_bank_id = fields.Many2one('res.bank', string='Send to Bank')
	journal_id_type_bank_id = fields.Many2one('account.journal', string='Bank', readonly=True,
											  states={'draft': [('readonly', False)]}, tracking=True,
											  domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
	move_expenses_id = fields.Many2one('account.move', string="Disbursement and Expenses Entry")
	move_claim_expenses_id = fields.Many2one('account.move', string="Claim Expenses Entry")

	### STRING
	unique_code = fields.Char(string='Unique Code')
	commentary = fields.Text(string='Commentary')
	reason_cancellation = fields.Text(string='Reason for Cancellation')

	### NUMERIC
	percentage_discount = fields.Float(string='% Discount')
	total_discount_all_letters = fields.Monetary(string='Amount Total Discount', compute='_check_discount', store=True)

	############## POLIMASTER ################
	total_discount_manual = fields.Boolean('Discount Manual')
	total_discount_real = fields.Monetary(string='Discount Real', store=True)
	claim = fields.Boolean('Claim')
	claim_journal_id = fields.Many2one('account.journal', string='Claim Journal')   
	claim_account_id = fields.Many2one('account.account', string="Claim Account")  

	### DATE
	disbursement_date = fields.Date('Disbursement Date', store=True)

	### SELECTION
	type_collection = fields.Selection([('free', 'Free collection'), ('warranty', 'Warranty')],
									   string='Shipping method', default='free')

	# operation_methods = fields.Selection(selection_add=[
	#     ('collection', 'Collection'),
	#     ('discount', 'Discount'),
	#     ('refinancing', 'Refinancing'),  # refinanciamiento
	#     ('renewal', 'Renewal'),  # renovacion
	#     ('protest', 'Protest'),  # protest
	#     ('return', 'Return'),  # protest
	# ])

	# exchange_type = fields.Selection(selection_add=[
	#     ('collection', ' Collection')
	# ])

	### BOOLEAN
	is_collection = fields.Boolean(string='Is Collection', default=False, compute='template_is_posted')
	is_discount = fields.Boolean(string='Is Discount', default=False, compute='template_is_posted')
	is_protest = fields.Boolean(string='Is Protest', default=False, compute='template_is_posted')
	is_return = fields.Boolean(string='Is Return', default=False, compute='template_is_posted')
	is_refinanced = fields.Boolean(string='Is Refinanced', default=False, compute='template_is_posted')
	is_renewal = fields.Boolean(string='Is Renewal', default=False, compute='template_is_posted')
	add_financial_expenses = fields.Boolean(string='Banking expenses')
	is_state_discount = fields.Boolean(string='State Discount', default=False, compute='_compute_same_state')
	is_expenses_account = fields.Boolean(string='Is expenses account', default=False, compute='_check_expenses_account')
	complete_disbursement = fields.Boolean(string='Complete disbursement', default=False)
	#### FUNCTIONS ### 

	### Si el desembolso es completo damos la opcion a crear un asiento por los
	### portes y comisiones para lo que necesitamos un campo para guardar el asiento.
	fees_comissions_id = fields.Many2one('account.move', string='Fees and Comissions')

	@api.model
	def default_get(self, fields):
		letter_state_list = []
		res = super(LetterManagement, self).default_get(fields)
		if 'letter_det_ids' in res:
			if 'operation_methods' in res:
				for inv in res['letter_det_ids']:
					print('Default Heredado')
					invoice_doc = self.env['account.move'].browse(inv[2]['move_id'])
					if invoice_doc:
						inv[2].update({
							'letter_state': invoice_doc.letter_state
							})
					else:
						raise UserError(_('The line document was not found'))
					if res['operation_methods']:
						if res['operation_methods'] in ['collection', 'discount', 'renewal', 'protest', 'return']:
							if invoice_doc.move_type in ['in_invoice']:
								raise UserError(_(
									'Los procesos de Cobranza, Descuento, Renovación, Refinanciamiento, Protesto y Devolucion no estan disponibles para Proveedores'))

						if res['operation_methods'] in ['collection', 'discount']:
							if inv[2]['document_type_code'] == 'LT':
								if inv[2]['letter_state'] != 'portfolio':
									raise UserError(
										_('Just select documents of type letters, with status in portfolio'))
								else:
									if res['operation_methods'] in ['discount']:
										res['add_financial_expenses'] = True
							else:
								raise UserError(_('Select letter type documents'))
						if res['operation_methods'] in ['refinancing']:
							# if inv[2]['document_type_code'] not in
							# if len(inv) > 1:
							#     if len(inv.mapped('document_type_id')) == 1:
							if inv[2]['document_type_code'] not in ['01', '03', '05', '15', '16', '19', '08',
																	'LT']:
								# if invoice_ids.mapped('document_type_id.code') not in ['LT', '01', '08']:
								raise UserError(_(
									'To refinance documents, select portfolio letters, invoices, debit notes, tickets'))
								# elif len(inv.mapped('document_type_id')) > 1:
								# if inv[2]['document_type_code'] not in ['01', '03', '05', '15', '16', '19', '08',
								#                                         'LT']:
								# raise UserError(_(
								#     'In the selection, if you choose letters, they have to be in Portfolio status'))

								# if len(list(inv.mapped('partner_id'))) > 1:
								#     raise UserError(
								#         _(
								#             'To refinance documents, select those that have the same customer or supplier'))
							# elif len(inv) == 1:
							#     if inv[2]['document_type_code'] not in ['01', '03', '05', '15', '16', '19', '08', 'LT']:
							#         raise UserError(
							#             _(
							#                 'To refinance documents, select portfolio letters, invoices, debit notes, tickets'))
							# if inv[2]['document_type_code'] in ['LT']:
							#     if inv[2]['letter_state'] not in ['portfolio', 'protest']:
							#         raise UserError(_(
							#             'In the selection, if you choose letters, they have to be in Portfolio status'))

						if res['operation_methods'] in ['renewal']:
							# El proceso de renovación no es individual
							# if len(res['letter_det_ids']) > 1:
							#     # if len(inv) > 1:
							#     raise UserError(_(
							#         'The renewal process is individual by letter.'))
							if len(res['letter_det_ids']) == 1:
								if inv[2]['document_type_code'] not in ['LT']:
									raise UserError(_('To renewal documents, select a letter'))
								# else:
								#     if inv[2]['letter_state'] not in ['portfolio']:
								#         raise UserError(_('Only letters in portfolio'))

						if res['operation_methods'] in ['protest', 'return']:
							# if res['operation_methods'] in ['protest', 'return']:
							if res['operation_methods'] in ['return']:
								if invoice_doc.letter_state not in ['collection', 'discount','warranty']:
									raise UserError(_(
										'Just select documents of type letters, with status in collection (Free or warranty) or discount'))

							if invoice_doc.document_type_code == 'LT':
								if invoice_doc.letter_state == res['operation_methods']:
									raise UserError(_('Can\'t %s letters in %s state') % (res['operation_methods'], invoice_doc.letter_state))
								# if invoice_doc.letter_state in ['discount']:
								#     res['add_financial_expenses'] = True
								letter_state_list.append(invoice_doc.letter_state)
								# print(letter_state_list)
								if len(set(letter_state_list)) == 1:
									if set(letter_state_list) in ['discount']:
										res['add_financial_expenses'] = True
								else:
									raise UserError(
										_('For this process, just select letters with the same letter status'))
							#else:
							#    raise UserError(_('For this process, just select letters with the same letter status'))
						# if (invoice_ids.mapped('document_type_code')).count('08') >= 1:
						#     res['generate_interest'] = True
						# res['include_interests_in_letter'] = True

		# if 'exchange_type' in res:
		# _logger.info(res['exchange_type'])
		# if res['exchange_type'] in ['collection']:
		#     res['move_type'] = 'out_invoice'
		# else:
		#     res['move_type'] = 'in_invoice'
		# _type = res['move_type']
		# res.update({
		#     'move_type': _type,
		# })
		return res

	# DEPENDS

	@api.depends('total_discount_all_letters', 'list_letters_ids.amount_discount')
	def _check_discount(self):
		self.total_discount_all_letters = 0
		for rec in self:
			discount = 0
			# _logger.info(rec.total_discount_all_letters)
			if rec.operation_methods in ['protest', 'return']:
				if rec.total_discount_all_letters != 0:
					rec.total_discount_all_letters = abs(rec.total_discount_all_letters) * -1
			if rec.operation_methods in ['discount']:
				discount = rec.currency_id.round(
					sum(rec.list_letters_ids.mapped('amount_discount')))
				rec.total_discount_all_letters = abs(discount) * -1
				# rec.total_amount_letras = rec.currency_id.round(sum(rec.list_letters_ids.mapped('letter_amount')))
				rec.total_amount_letras = rec.currency_id.round(sum(rec.list_letters_ids.mapped('amount_total')))

	@api.depends('state')
	def template_is_posted(self):
		res = super(LetterManagement, self).template_is_posted()
		for rec in self:
			# Se creó ésta validacion por si intentaban duplicar una plantilla posteada
			# if rec.state not in ['posted']:
			# rec.is_exchanged = False
			rec.is_collection = rec.is_discount = rec.is_refinanced = False
			rec.is_renewal = rec.is_protest = rec.is_return = False
			if rec.state in ['posted', 'cancel']:
				# if rec.operation_methods in ['portfolio']:
				#     rec.is_exchanged = True
				if rec.operation_methods in ['collection']:
					rec.is_collection = True
				if rec.operation_methods in ['discount']:
					rec.is_discount = True
				if rec.operation_methods in ['refinancing']:
					rec.is_refinanced = True
				if rec.operation_methods in ['renewal']:
					rec.is_renewal = True
				if rec.operation_methods in ['protest']:
					rec.is_protest = True
				if rec.operation_methods in ['return']:
					rec.is_return = True

	@api.depends('letter_det_ids.move_id.letter_state')
	def _compute_same_state(self):
		for rec in self:
			rec.is_state_discount = False
			if not rec.add_financial_expenses:
				rec.add_financial_expenses = False
			if len(set(rec.letter_det_ids.mapped('move_id.letter_state'))) == 1:
				for line in rec.letter_det_ids:
					if rec.operation_methods in ['protest', 'return']:
						if line.move_id.letter_state in ['discount']:
							rec.is_state_discount = True
					if rec.operation_methods in ['discount']:
						rec.is_state_discount = True
						rec.add_financial_expenses = True

	@api.depends('letter_det_ids.interest_on_arrears', 'letter_det_ids.compensatory_interest')
	def _compute_amount_debit_note(self):
		self.all_amount_interest = 0.0
		for rec in self:
			if rec.operation_methods in ['portfolio', 'renewal', 'refinancing']:
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

				# En polimaster no se agregan intereses al cliente por eso 
				# colocamos otro filtro para evitar esta función al renovar 
				###################### POLIMASTER ###########################
				# if rec.letters_is_created:
				if rec.letters_is_created and rec.operation_methods != 'renewal':
					rec.list_letters_ids._onchange_amount_letter_line()

	@api.depends('letter_det_ids.partner_id')
	def _compute_same_partner(self):
		for rec in self:
			rec.is_same_partner = False
			if rec.operation_methods in ['portfolio', 'renewal', 'refinancing']:
				if rec.partner_id:
					if len(rec.letter_det_ids.mapped('partner_id')) < 1:
						rec.is_same_partner = False
					if len(rec.letter_det_ids.mapped('partner_id')) == 1:
						rec.is_same_partner = True
			if rec.operation_methods in ['discount', 'collection', 'protest', 'return']:
				if len(rec.letter_det_ids.mapped('partner_id')) == 1:
					rec.is_same_partner = True
					rec.partner_id = rec.letter_det_ids.mapped('partner_id')[0]

	@api.depends('_writeoff_account_id')
	def _check_expenses_account(self):
		for rec in self:
			rec.is_expenses_account = False
			if rec._writeoff_account_id:
				if rec._writeoff_account_id.code[:2] in ['62', '63', '64', '65', '67', '68']:
					rec.is_expenses_account = True  # Cuando este campo se activa, la cuenta ni etiqueta analitica sera exigible

	### ONCHANGE

	@api.onchange('list_letters_ids.send_date', 'list_letters_ids.acceptance_date')
	def _writing_dates_of_letters_to_docs(self):
		for rec in self:
			if rec.operation_methods in ['collection', 'discount']:
				for dates in rec.letter_det_ids:
					# for dates in rec.list_letters_ids:
					if rec.list_letters_ids.send_date:
						dates.move_id.send_date = rec.list_letters_ids.send_date
					if rec.list_letters_ids.acceptance_date:
						dates.move_id.acceptance_date = rec.list_letters_ids.acceptance_date

	@api.onchange('unique_code')
	def _onchange_unique_code(self):  # Codigo unico masivo
		for rec in self:
			if rec.operation_methods in ['collection', 'discount']:
				if rec.unique_code:
					for line in rec.list_letters_ids:
						line.unique_code = rec.unique_code

	@api.onchange('add_financial_expenses')
	def _onchange_add_financial_expenses(self):
		for rec in self:
			if not rec.add_financial_expenses:
				rec.journal_id_type_bank_id = False
				rec.loans_type_id = False
				rec._writeoff_account_id = False
				rec.is_expenses_account = False
				rec.analytic_account_id = False
				rec.analytic_tag_ids = False
				if rec.total_discount_all_letters != 0:
					rec.total_discount_all_letters = 0.0

	# @api.onchange('exchange_type')
	# def _onchange_exchange_type(self):
	#     for rec in self:
	#         if rec.exchange_type:
	#             if rec.exchange_type not in ['collection']:
	#                 rec.letters_serie_id = False

	## GENERANDO DOCUMENTOS
	######### BOTONES #########
	def create_send(self):
		for rec in self:
			new_invoices = 0
			if rec.state == 'draft':
				rec.generate_letters()

	# def generate_letters(self):
	#     for rec in self:
	#         if rec.exchange_type in ['collection']:
	#             if rec.operation_methods in ['portfolio', 'refinancing']:
	#                 if not rec.letters_serie_id:
	#                     raise UserError(_('Choose a series for the letters'))
	#     return super(LetterManagement, self).generate_letters()

	# def generate_letters(self):
	#     print('funcion heredada y Generando letras')
	#     res = super(LetterManagement, self).generate_letters()
	#     for rec in self:
	#         date_temp = False
	#         self._check_products_company()
	#         self._check_bridge_journal()
	#         if rec.operation_methods in ['portfolio', 'refinancing']:
	#             if rec.exchange_type in ['collection']:
	#                 if not rec.letters_serie_id:
	#                     raise UserError(_('Choose a series for the letters'))
	#         if not rec.currency_id:
	#             raise UserError(_('Select a type of Currency'))
	#         if len(list(rec.letter_det_ids.mapped('move_id.id'))) < 1:
	#             raise UserError(_('There is no document to generate letters'))
	#         for amount in rec.letter_det_ids:
	#             if amount.amount_payable == 0:
	#                 if amount.move_id.amount_residual > 0.0:
	#                     raise UserError(_(
	#                         'To generate the letters, the documents must have a amount payable (can be partial payment)'))
	#             if amount.move_id.amount_residual <= 0.0:
	#                 raise UserError(_('To generate the letters, the documents must have a balance due'))
	#         # self._check_products_company()
	#         if rec.state in ['draft', 'in_process']:
	#             if rec.journal_id:
	#                 if rec.another_journal_id:  # Gestión de Letras >> Otro Diario
	#                     if rec.operation_methods in ['portfolio', 'refinancing']:
	#                         if rec.generate_interest:  # Si marca generar intereses y quiere generar las letras pero sin generar antes la nota de debito
	#                             # if not rec.debit_notes_in_docs:
	#                             if not rec.is_debit_generated:
	#                                 raise UserError(
	#                                     _('Generate and publish the debit note before generating the letters'))
	#                             else:
	#                                 for debit_note_generated in rec.list_debit_notes_ids:
	#                                     if debit_note_generated.state != 'posted':
	#                                         raise UserError(_('Publish the debit note first'))
	#                     # Borramos las letras creadas para poder recalcular
	#                     if rec.list_letters_ids:
	#                         rec.list_letters_ids.unlink()
	#                         rec.letters_is_created = False
	#                         rec.is_exchanged = False
	#                     rec._validate_documents_receivable()
	#                     new_letters = self.env['account.move']
	#                     if not rec.letters_is_created:
	#                         if rec.operation_methods:
	#                             n = 0
	#                             rec.is_letter = True
	#                             if rec.operation_methods in ['portfolio','refinancing']:
	#                                 if rec.letter_number <= 0 and rec.days_range <= 0:
	#                                     raise UserError(_(
	#                                         'The values entered in Letters to generate and Range of days must be greater than 0'))
	#                                 if rec.letter_number <= 0:
	#                                     raise UserError(
	#                                         _('The value entered in Letters to be generated must be greater than 0'))
	#                                 if rec.days_range <= 0:
	#                                     raise UserError(_('Values entered in the Day Range must be greater than 0'))
	#
	#                                 # Creamos las letras
	#                                 date_temp = rec.date
	#                                 amount_temp = 0
	#                                 amount_total = 0
	#                                 # days_expires = False
	#                                 for line in range(0, rec.letter_number):
	#                                     if line == rec.letter_number - 1:
	#                                         if rec.include_interests_in_letter:
	#                                             amount_total = rec.currency_id.round(
	#                                                 (rec.total_amount_fact + rec.all_amount_interest) - amount_temp)
	#                                         else:
	#                                             amount_total = rec.currency_id.round(rec.total_amount_fact - amount_temp)
	#                                     else:
	#                                         if rec.include_interests_in_letter:
	#                                             amount_total = rec.currency_id.round(
	#                                                 (rec.total_amount_fact + rec.all_amount_interest) / rec.letter_number)
	#                                         else:
	#                                             amount_total = rec.currency_id.round(
	#                                                 rec.total_amount_fact / rec.letter_number)
	#
	#                                         amount_temp += amount_total
	#                                     date_due = date_temp = date_temp + timedelta(days=rec.days_range)
	#
	#                                     invoice_lines = [(0, 0, {
	#                                         'product_id': rec.company_id.letter_portfolio.id,
	#                                         'name': rec.company_id.letter_portfolio.display_name,
	#                                         'account_id': rec.company_id.letter_portfolio.property_account_income_id.id,
	#                                         'price_unit': amount_total,
	#                                     })]
	#                                     letras = rec._prepare_invoice_vals(invoice_lines, amount_total)
	#
	#                                     if rec.exchange_type in ['collection']:
	#                                         serie = self.letters_serie_id and self.letters_serie_id.id or False
	#                                         letras['sunat_serie'] = serie
	#                                         letras['invoice_serie'] = False
	#                                         number_temp = new_letters._get_correlativo_temporal(serie,
	#                                                                                             letras['document_type_id'],
	#                                                                                             2)
	#                                         letras['sunat_number_temp'] = number_temp
	#                                     if rec.exchange_type in ['payment']:
	#                                         # serie = self.letters_serie_id.name or False
	#                                         # letras['invoice_serie'] = str(serie)
	#                                         letras['sunat_serie'] = False
	#                                         letras['sunat_number_temp'] = False
	#                                     letras['partner_id'] = self.partner_id and self.partner_id.id or False
	#                                     # letras['invoice_date'] = self.date
	#                                     letras['invoice_date_due'] = date_due
	#                                     days_expires = letras['invoice_date_due'] - letras['invoice_date']
	#                                     letras['how_days_expires'] = days_expires.days
	#                                     # letras['acc_number'] = self.acc_number
	#                                     letras['bank_acc_number_id'] = self.bank_acc_number_id.id
	#                                     letras['bank_id'] = self.bank_id and self.bank_id.id or False
	#                                     new_letters.create(letras)
	#
	#                             if rec.operation_methods in ['collection', 'protest', 'return']:
	#                                 for docs in rec.letter_det_ids:
	#                                     if rec.operation_methods in ['collection']:
	#                                         invoice_lines = [(0, 0, {
	#                                             'product_id': rec.company_id.letter_collection.id,
	#                                             'name': rec.company_id.letter_collection.display_name,
	#                                             'account_id': rec.company_id.letter_collection.property_account_income_id.id,
	#                                             'price_unit': docs.amount_payable
	#                                         })]
	#                                     if rec.operation_methods in ['protest', 'return']:
	#                                         invoice_lines = [(0, 0, {
	#                                             'product_id': rec.company_id.letter_portfolio.id,
	#                                             'name': rec.company_id.letter_portfolio.display_name,
	#                                             'account_id': rec.company_id.letter_portfolio.property_account_income_id.id,
	#                                             'price_unit': docs.amount_payable,
	#                                         })]
	#                                     letras = rec._prepare_invoice_vals(invoice_lines,
	#                                                                        docs.amount_payable)
	#
	#                                     letras[
	#                                         'partner_id'] = docs.move_id.partner_id and docs.move_id.partner_id.id or False
	#                                     # letras['invoice_date'] = docs.move_id.invoice_date
	#                                     letras['invoice_date_due'] = docs.move_id.invoice_date_due
	#                                     letras[
	#                                         'document_type_id'] = docs.move_id.document_type_id and docs.move_id.document_type_id.id or False
	#                                     letras[
	#                                         'sunat_serie'] = docs.move_id.sunat_serie and docs.move_id.sunat_serie.id or False
	#                                     letras['sunat_number_temp'] = new_letters._get_correlativo_temporal(
	#                                         letras['sunat_serie'], letras['document_type_id'], 2)
	#                                     letras['send_date'] = docs.move_id.send_date
	#                                     # letras['acc_number'] = docs.move_id.acc_number
	#                                     letras['bank_acc_number_id'] = docs.move_id.bank_acc_number_id.id
	#                                     letras['acceptance_date'] = docs.move_id.acceptance_date
	#                                     letras[
	#                                         'endorsement'] = docs.move_id.endorsement and docs.move_id.endorsement.id or False
	#                                     if rec.operation_methods in ['collection', 'return']:
	#                                         letras['new_bank_id'] = self.new_bank_id and self.new_bank_id.id or False
	#                                     letras['bank_id'] = docs.move_id.bank_id and docs.move_id.bank_id.id or False
	#                                     move_generate = new_letters.create(letras)
	#                                     docs.generate_move_id = move_generate and move_generate.id or False
	#                             if rec.operation_methods in ['renewal']:
	#                                 price_unit = 0
	#                                 price_temp = 0
	#                                 letter_created = 0
	#                                 if rec.debit_notes_in_docs:  # Caso 2
	#                                     # if not rec.include_interests_in_letter:
	#                                     #     raise UserError(_(
	#                                     #         'Debit note selected in Docs. receivable, check the box Include \n'
	#                                     #         'interest in the letter'))
	#                                     docs = rec.letter_det_ids.mapped('move_id.document_type_code').count('LT')
	#                                     if docs >= 1:
	#                                         # letter_created += 1
	#                                         if letter_created > docs:
	#                                             break
	#                                         if letter_created <= docs:
	#                                             for docs_receivable in rec.letter_det_ids:
	#                                                 if docs_receivable.move_id.document_type_id.code == 'LT':
	#                                                     rec.letter_number = int(docs)
	#                                                     # for line in range(0, rec.letter_number):
	#                                                     if letter_created == rec.letter_number - 1:
	#                                                         price_unit = rec.currency_id.round(
	#                                                             rec.total_amount_fact - price_temp)
	#                                                     else:
	#                                                         price_unit = rec.currency_id.round(
	#                                                             rec.total_amount_fact / rec.letter_number)
	#                                                         price_temp += price_unit
	#                                                     interest = 0
	#                                                     invoice_lines = [(0, 0, {
	#                                                         'product_id': rec.company_id.letter_portfolio.id,
	#                                                         'name': rec.company_id.letter_portfolio.display_name,
	#                                                         'account_id': rec.company_id.letter_portfolio.property_account_income_id.id,
	#                                                         'price_unit': price_unit,
	#                                                     })]
	#                                                     letras = rec._prepare_invoice_vals(invoice_lines,
	#                                                                                        price_unit)
	#                                                     letras[
	#                                                         'partner_id'] = self.partner_id and self.partner_id.id or False
	#                                                     letras['amount_letter'] = price_unit
	#                                                     letras[
	#                                                         'document_type_id'] = docs_receivable.move_id.document_type_id and docs_receivable.move_id.document_type_id.id or False
	#                                                     letras[
	#                                                         'sunat_serie'] = docs_receivable.move_id.sunat_serie and docs_receivable.move_id.sunat_serie.id or False
	#                                                     letras['sunat_number_temp'] = new_letters._get_correlativo_temporal(
	#                                                         letras['sunat_serie'], letras['document_type_id'], 2)
	#                                                     letras[
	#                                                         'bank_acc_number_id'] = docs_receivable.move_id.bank_acc_number_id.id
	#                                                     # letras['invoice_date'] = docs.move_id.invoice_date
	#                                                     letras[
	#                                                         'invoice_date_due'] = docs_receivable.move_id.invoice_date_due
	#                                                     letras['letter_amount'] = letras['amount_letter']
	#                                                     letras[
	#                                                         'endorsement'] = docs_receivable.move_id.endorsement and docs_receivable.move_id.endorsement.id or False
	#                                                     move_generate = new_letters.create(letras)
	#                                                     docs_receivable.generate_move_id = move_generate and move_generate.id or False
	#                                                     letter_created += 1
	#
	#                                 else:
	#                                     for move in rec.letter_det_ids:
	#                                         if rec.include_interests_in_letter:  # Caso 4
	#                                             if rec.is_debit_generated:
	#                                                 if rec.all_debit_generated_posted:  # Notas de debito generadas y posteadas
	#                                                     if sum(self.list_debit_notes_ids.mapped('letter_amount')) != sum(
	#                                                             self.letter_det_ids.mapped(
	#                                                                 'compensatory_interest') + self.letter_det_ids.mapped(
	#                                                                 'interest_on_arrears')):
	#                                                         raise UserError(_(
	#                                                             'Interest amounts in Docs. receivables other than the amount of the debit notes generated, \n"'
	#                                                             'delete and regenerate debit notes'))
	#                                                     for debit in rec.list_debit_notes_ids:
	#                                                         if len(list(rec.letter_det_ids.mapped('move_id.id'))) == len(
	#                                                                 list(rec.list_debit_notes_ids.mapped('id'))):
	#                                                             if move.move_id.sunat_number == debit.refund_invoice_sunat_number:
	#                                                                 price_unit = move.amount_payable + debit.amount_total
	#                                                         if len(list(rec.letter_det_ids.mapped('move_id.id'))) > len(
	#                                                                 list(rec.list_debit_notes_ids.mapped('id'))):
	#                                                             if move.move_id.sunat_number == debit.refund_invoice_sunat_number:
	#                                                                 price_unit = move.amount_payable + debit.amount_total
	#                                                             else:
	#                                                                 price_unit = move.amount_payable
	#
	#                                                 else:
	#                                                     raise UserError(_(
	#                                                         'Publish the generated debit notes'))
	#                                             else:
	#                                                 price_unit = move.new_amount_to_pay
	#                                         else:
	#                                             price_unit = move.amount_payable
	#
	#                                         interest = 0
	#                                         invoice_lines = [(0, 0, {
	#                                             'product_id': rec.company_id.letter_portfolio.id,
	#                                             'name': rec.company_id.letter_portfolio.display_name,
	#                                             'account_id': rec.company_id.letter_portfolio.property_account_income_id.id,
	#                                             'price_unit': price_unit,
	#                                         })]
	#                                         letras = rec._prepare_invoice_vals(invoice_lines, price_unit)
	#                                         letras['partner_id'] = self.partner_id and self.partner_id.id or False
	#                                         letras['amount_letter'] = price_unit
	#                                         letras['letter_amount'] = letras['amount_letter']
	#                                         letras[
	#                                             'document_type_id'] = move.move_id.document_type_id and move.move_id.document_type_id.id or False
	#                                         letras[
	#                                             'sunat_serie'] = move.move_id.sunat_serie and move.move_id.sunat_serie.id or False
	#                                         letras['sunat_number_temp'] = new_letters._get_correlativo_temporal(
	#                                             letras['sunat_serie'], letras['document_type_id'], 2)
	#                                         letras['invoice_date_due'] = move.move_id.invoice_date_due
	#                                         # letras['acc_number'] = move.move_id.acc_number
	#                                         letras['bank_acc_number_id'] = move.move_id.bank_acc_number_id.id
	#                                         letras['bank_id'] = move.move_id.bank_id and move.move_id.bank_id.id or False
	#                                         # letras['sunat_serie'] = move.move_id.sunat_serie.id
	#                                         letras[
	#                                             'endorsement'] = move.move_id.endorsement and move.move_id.endorsement.id or False
	#                                         move_generate = new_letters.create(letras)
	#                                         move.generate_move_id = move_generate and move_generate.id or False
	#
	#                                         # self.env['account.move'].create(letras)
	#                             if rec.operation_methods == 'discount':
	#                                 for docs in rec.letter_det_ids:
	#                                     discount = 0
	#                                     rec._validate_discount()
	#                                     if rec.percentage_discount > 0:
	#                                         amount_doc = rec.currency_id.round(docs.amount_payable)
	#                                         discount = rec.currency_id.round(
	#                                             amount_doc * (rec.percentage_discount * 0.01))
	#                                         amount = amount_doc - discount
	#                                     if rec.other_currency:
	#                                         # product_discount = rec.company_id.letter_discount_me
	#                                         invoice_lines = [(0, 0, {
	#                                             'product_id': rec.company_id.letter_discount_me.id,
	#                                             # 'product_id': rec.company_id.letter_discount.id,
	#                                             'name': rec.company_id.letter_discount_me.display_name,
	#                                             'account_id': rec.company_id.letter_discount_me.property_account_income_id.id,
	#                                             'price_unit': amount
	#                                         })]
	#                                     else:
	#                                         # product_discount = rec.company_id.letter_discount
	#                                         invoice_lines = [(0, 0, {
	#                                             'product_id': rec.company_id.letter_discount.id,
	#                                             # 'product_id': rec.company_id.letter_discount.id,
	#                                             'name': rec.company_id.letter_discount.display_name,
	#                                             'account_id': rec.company_id.letter_discount.property_account_income_id.id,
	#                                             'price_unit': amount
	#                                         })]
	#                                     letras = rec._prepare_invoice_vals(invoice_lines,
	#                                                                        docs.amount_payable)
	#                                     letras[
	#                                         'partner_id'] = docs.move_id.partner_id and docs.move_id.partner_id.id or False
	#                                     print(invoice_lines)
	#                                     # letras['acc_number'] = docs.move_id.acc_number
	#                                     letras['bank_acc_number_id'] = docs.move_id.bank_acc_number_id.id
	#                                     letras[
	#                                         'document_type_id'] = docs.move_id.document_type_id and docs.move_id.document_type_id.id or False
	#                                     letras[
	#                                         'sunat_serie'] = docs.move_id.sunat_serie and docs.move_id.sunat_serie.id or False
	#                                     letras['sunat_number_temp'] = new_letters._get_correlativo_temporal(
	#                                         letras['sunat_serie'], letras['document_type_id'], 2)
	#                                     letras['amount_letter'] = amount_doc
	#                                     letras['amount_discount'] = - discount
	#                                     letras['letter_amount'] = amount
	#                                     # letras['invoice_date'] = docs.move_id.invoice_date
	#                                     letras['invoice_date_due'] = docs.move_id.invoice_date_due
	#                                     letras['send_date'] = docs.move_id.send_date
	#                                     letras['acceptance_date'] = docs.move_id.acceptance_date
	#                                     letras[
	#                                         'endorsement'] = docs.move_id.endorsement and docs.move_id.endorsement.id or False
	#                                     letras['new_bank_id'] = self.new_bank_id and self.new_bank_id.id or False
	#                                     letras['bank_id'] = docs.move_id.bank_id and docs.move_id.bank_id.id or False
	#                                     move_generate = self.env['account.move'].create(letras)
	#                                     docs.generate_move_id = move_generate and move_generate.id or False
	#                                     rec.total_discount_all_letters = rec.currency_id.round(sum(
	#                                         (rec.list_letters_ids.mapped('amount_discount'))))
	#                             # if rec.operation_methods not in ['portfolio']:
	#                             if rec.operation_methods in ['renewal', 'refinancing', 'return']:
	#                             # if rec.operation_methods in ['renewal', 'refinancing', 'return']:
	#                                 letras['letter_state'] = 'portfolio'
	#                             else:
	#                                 letras['letter_state'] = rec.operation_methods
	#                         rec.letters_is_created = True  # Letra Creada
	#                         rec._validate_documents_receivable()
	#                         rec.state = 'in_process'
	#                     # rec.action_save()
	#                 # else:
	#                 #     raise UserError(_('The journal with which the letters will are generated is missing'))
	#             # else:
	#             #     raise UserError(_('Journal to Pay missing'))
	#         # else:
	#         #     raise UserError(_('To generate the letters, the template must be in Draft State or in Process'))

	def _generate_letters_in_template(self):
		res = super(LetterManagement, self)._generate_letters_in_template()
		for rec in self:
			if rec.exchange_type in ['collection']:
				if rec.operation_methods in ['portfolio', 'refinancing']:
					# operation_method = ['portfolio']
					rec._generate_letters_portfolio(rec.operation_methods)
				else:
					rec._generate_letters_receivables()

	def _validate_percentage_renewal(self):
		for rec in self:
			if rec.renewal_percentage <= 0:
				raise UserError(_('You need to put a value greater than 0 in the Renewal Percentage % field'))

	@api.onchange('disbursement_date')
	def _onchange_disbursement_date(self):
		for rec in self:
			for letter in rec.list_letters_ids:
				letter.amount_discount = rec._get_discount_by_percentage(rec, letter)
			rec.total_discount_all_letters = rec.currency_id.round(sum(rec.list_letters_ids.mapped('amount_discount')))

	def _get_discount_by_percentage(self, rec, letter):
		return ((((rec.percentage_discount / 100 + 1) ** ((letter.invoice_date_due - rec.disbursement_date).days / 360)) - 1) * letter.letter_amount)

	def _generate_letters_receivables(self):
		for rec in self:
			account_move = self.env['account.move']
			for docs in rec.letter_det_ids:
				# PRODUCTO DE LA LETRA
				if rec.operation_methods in ['collection']:
					product_letter = rec.company_id.letter_collection
				if rec.operation_methods in ['protest', 'return', 'renewal']:
					product_letter = rec.company_id.letter_portfolio
				if rec.operation_methods in ['discount']:
					product_letter = rec.company_id.letter_discount
					if rec.other_currency:
						product_letter = rec.company_id.letter_discount_me
				# PRODUCTO DE LA LETRA

				if rec.operation_methods in ['renewal']:
					# Error si el campo de Porcentaje de renovación tiene un valor menor de 0
					rec._validate_percentage_renewal()
					letter_in_docs = 0
					price_temp = 0
					price_unit = 0
					# for docs in rec.letter_det_ids:
					if rec.debit_notes_in_docs:
						docs_letter = rec.letter_det_ids.mapped('move_id.document_type_code').count('LT')
						if docs_letter >= 1:
							if docs.move_id.l10n_latam_document_type_id.code in ['LT']:
								rec.letter_number = int(docs_letter)
								############## POLIMASTER ################
								# Cambiamos la forma de calcular el nuevo monto de la letra renovada
								if letter_in_docs == rec.letter_number - 1:
									price_unit = rec.currency_id.round((rec.total_amount_fact - price_temp) * ((100 - rec.renewal_percentage) /100))
								else:
									price_unit = rec.currency_id.round((rec.total_amount_fact / rec.letter_number) * ((100 - rec.renewal_percentage) /100))
									price_temp += price_unit

					else:
						# for docs in rec.letter_det_ids:
						if rec.include_interests_in_letter:
							if rec.is_debit_generated:
								if not rec.all_debit_generated_posted:
									raise UserError(_('Publish the generated debit notes'))
								if rec.all_debit_generated_posted:
									if sum(self.list_debit_notes_ids.mapped('letter_amount')) != sum(
											self.letter_det_ids.mapped(
												'compensatory_interest') + self.letter_det_ids.mapped(
												'interest_on_arrears')):
										raise UserError(_(
											'Interest amounts in Docs. receivables other than the amount of the debit '
											'notes generated, \n" '
											'delete and regenerate debit notes'))
									for debit in rec.list_debit_notes_ids:
										############## POLIMASTER ################
										# Cambiamos la forma de calcular el nuevo monto de la letra renovada
										if len(list(
												rec.letter_det_ids.mapped('move_id.id'))) == len(
											list(rec.list_debit_notes_ids.mapped('id'))):
											if docs.move_id.sunat_number == debit.refund_invoice_sunat_number:
												price_unit = rec.currency_id.round((docs.amount_payable + debit.amount_total) * ((100 - rec.renewal_percentage) /100))
										if len(list(rec.letter_det_ids.mapped('move_id.id'))) > len(
												list(rec.list_debit_notes_ids.mapped('id'))):
											if docs.move_id.sunat_number == debit.refund_invoice_sunat_number:
												price_unit = rec.currency_id.round((docs.amount_payable + debit.amount_total) * ((100 - rec.renewal_percentage) /100))
											else:
												price_unit = rec.currency_id.round(docs.amount_payable * ((100 - rec.renewal_percentage) /100))
							else:
								price_unit = rec.currency_id.round(docs.new_amount_to_pay * ((100 - rec.renewal_percentage) /100))
						else:
							price_unit = rec.currency_id.round(docs.amount_payable * ((100 - rec.renewal_percentage) /100))

				if rec.operation_methods in ['discount']:
					discount = 0
					# Error si el campo de Descuento tiene un valor menor de 0
					rec._validate_discount()

					if rec.percentage_discount > 0:
						amount_doc = rec.currency_id.round(docs.amount_payable)
						############## POLIMASTER ################
						# Cambio de formula
						# discount = rec.currency_id.round(amount_doc * (rec.percentage_discount * 0.01))
						rec.disbursement_date = rec.exchange_date or fields.Date.context_today(self)
						discount = rec._get_discount_by_percentage(rec, docs.move_id)
						
						############## POLIMASTER ################
						# No decscontamos en el asiento el monto
						letter_amount = amount_doc #- discount

				if rec.operation_methods in ['collection', 'protest', 'return']:
					letter = rec._get_invoices_lines(product_letter, docs.amount_payable, docs.move_id, is_letter=True)
					letter['partner_id'] = docs.move_id.partner_id and docs.move_id.partner_id.id or False

				if rec.operation_methods in ['discount']:
					letter = rec._get_invoices_lines(product_letter, letter_amount, docs.move_id, is_letter=True)
					letter['partner_id'] = docs.move_id.partner_id and docs.move_id.partner_id.id or False

				if rec.operation_methods in ['renewal']:
					letter = rec._get_invoices_lines(product_letter, price_unit, docs.move_id, is_letter=True)
					letter['partner_id'] = rec.partner_id and rec.partner_id.id or False
					letter_in_docs += 1

				if rec.operation_methods in ['discount']:
					letter['amount_letter'] = amount_doc
					letter['amount_discount'] = - discount
					letter['letter_amount'] = letter_amount

				if rec.operation_methods in ['discount', 'collection', 'return']:
					letter['new_bank_id'] = self.new_bank_id and self.new_bank_id.id or False

				# if rec.operation_methods in ['collection', 'protest', 'return', 'renewal']:
				if rec.operation_methods in ['renewal']:
					letter['amount_letter'] = price_unit
					letter['letter_amount'] = letter['letter_amount']
					letter['amount_discount'] = -(docs.amount_payable - price_unit)
					letter['letter_state'] = docs.letter_state
					letter['new_bank_id'] = docs.move_id.new_bank_id

				if rec.operation_methods not in ['portfolio', 'refinancing']:
					letter['document_type_id'] = docs.move_id.l10n_latam_document_type_id and docs.move_id.l10n_latam_document_type_id.id or False
					#letter['sunat_serie'] = docs.move_id.sunat_serie and docs.move_id.sunat_serie.id or False
					#letter['sunat_number_temp'] = account_move._get_correlativo_temporal(letter['sunat_serie'], letter['document_type_id'], 2)

					letter['bank_acc_number_id'] = docs.move_id.bank_acc_number_id and docs.move_id.bank_acc_number_id.id or False
					letter['bank_id'] = docs.move_id.bank_id and docs.move_id.bank_id.id or False
					letter['invoice_date_due'] = docs.move_id.invoice_date_due
					letter['send_date'] = docs.move_id.send_date
					letter['acceptance_date'] = docs.move_id.acceptance_date
					letter['endorsement'] = docs.move_id.endorsement and docs.move_id.endorsement.id or False

				if rec.operation_methods in ['discount']:
					letter['invoice_date'] = docs.move_id.invoice_date
					letter['send_date'] = self.date
					letter['acceptance_date'] = fields.Date.context_today(self)

				if rec.operation_methods in ['renewal']:
					letter['invoice_date_due'] = docs.move_id.invoice_date_due + timedelta(days=30)
					letter['how_days_expires'] = (letter['invoice_date_due'] - letter['invoice_date']).days

				if docs.move_id.partner_id == docs.move_id.acceptor_id:
					letter['acceptor_id'] = rec.partner_id and rec.partner_id.id or False
				else:
					letter['acceptor_id'] = docs.move_id.acceptor_id and docs.move_id.acceptor_id.id or False
				letter_generated = account_move.create(letter)
					
				docs.generate_move_id = letter_generated and letter_generated.id or False

				if rec.operation_methods in ['discount']:
					rec.total_discount_all_letters = rec.currency_id.round(
						sum(rec.list_letters_ids.mapped('amount_discount')))
				

				# get_prepare_lines ya asigna el estado de la letra a generar

	# def btn_generate_debit_note(self):
	#     for rec in self:
	#         # self._check_products_company()
	#         # self._check_bridge_journal()
	#         # if not rec.generate_interest:
	#         #     raise UserError(_('Click on Generate Interests'))
	#         # if rec.state not in ['draft', 'in_process']:
	#         #     raise UserError(_('Only in Draft and In Process state'))
	#         # if not rec.debit_notes_serie_id.id:
	#         #     raise UserError(_('Choose a series of for the Debit Note'))
	#         # if not rec.journal_debit_note_id:
	#         #     raise UserError(_('Choose a debit note journal'))
	#         # if rec.operation_methods in ['portfolio', 'renewal', 'refinancing']:
	#         #     if rec.all_amount_interest <= 0:
	#         #         raise UserError(_('Enter values in the interests of the tab >> Docs. receivable <<'))
	#
	#         # Caso 3:
	#         if rec.state == 'in_process':
	#             if rec.letters_is_created:
	#                 if not rec.include_interests_in_letter:
	#                     if rec.debit_notes_serie_id.id:
	#                         rec.is_debit = True  # Caso 3
	#                         rec.generate_debit_notes()
	#                 else:
	#                     # if rec.letters_is_created:
	#                     raise UserError(_(
	#                         'The debit note cannot be created because the letters were generated with interest included'))
	#             else:
	#                 raise UserError(_('You have to generate the letters'))
	#         # Caso 4:
	#         if rec.state == 'draft':
	#             if not rec.letters_is_created:
	#                 # if not rec.letters_is_created:
	#                 # if rec.include_interests_in_letter:
	#                 if rec.debit_notes_serie_id.id:
	#                     rec.is_debit_generated = True
	#                     rec.generate_debit_notes()
	#                 else:
	#                     raise UserError(_('Select a series for debit notes'))
	#                 # else:
	#                 #     raise UserError(_(
	#                 #         'If you want to generate a debit note before the letters, you must check the box include interest in the letter'))
	#
	#         rec.state = 'in_process'rec.currency_id.round((docs.amount_payable + debit.amount_total) * ((100 - rec.renewal_percentage) /100))
	#     # return self.reload_page()

	def _validate_discount(self):
		for rec in self:
			if rec.percentage_discount <= 0:
				raise UserError(_('You need to put a value greater than 0 in the % Discount field'))

	def _exchange_process_after(self):
		if self.operation_methods == 'discount':
			self.disbursement_date = self.env.context.get('exchange_date')
			self._onchange_disbursement_date()
			for letter in self.list_letters_ids:
				letter.new_bank_id = self.journal_id_type_bank_id.bank_id
		return super()._exchange_process_after()

	def exchange_process1(self):
		# total = 0
		for rec in self:
			# self._check_products_company()
			# self._check_bridge_journal()
			# check_modules = True
			# rec._check_letter_management_modules_are_installed(check_modules)
			# rec._check_if_ribbon_is_activated()
			# letter_payable_module = self.env['ir.module.module'].search(
			#     [('name', '=', 'qa_letter_management_payables'), ('state', '=', 'installed')], limit=1)
			# letter_receivable_module = self.env['ir.module.module'].search(
			#     [('name', '=', 'qa_letter_management_receivable'), ('state', '=', 'installed')], limit=1)
			# for letters_docs in rec.list_letters_ids:
			#     if rec.exchange_type in ['payment']:
			#         if len(letter_payable_module) == 1:
			#             if rec.letters_is_created:
			#                 if not letters_docs.invoice_serie:
			#                     raise UserError(_('Add the Invoice serie to validate'))
			#                 if not letters_docs.invoice_number:
			#                     raise UserError(_('Add the Invoice Number to validate'))
			#         else:
			#             raise UserError(_('Please install the Letters payables module'))
			#     if rec.exchange_type in ['collection']:
			#         if not len(letter_receivable_module) == 1:
			#             raise UserError(_('Please install the Letters receivables module'))
			# if not rec.state == 'in_process':
			#     raise UserError(_('only validates when the template is in the >> in process << state'))
			# if not rec.letters_is_created:
			#     raise UserError(_('Generate the letters first'))
			# if not rec.another_journal_id:
			#     raise UserError(_('Choose a journal for the letters generate'))
			# if rec.is_exchanged:
			#     raise UserError(_('Selected documents cannot be exchanged if they have already been exchanged'))
			# if rec.is_renewal:
			#     raise UserError(_('You cannot renew letters again if they are already renewed'))
			# if rec.is_refinanced:
			#     raise UserError(_('You cannot refinance letters if they are already Refinanced'))
			# if rec.is_discount:
			#     raise UserError(_('Letters cannot be discounted again if they are already on Discount'))
			# if rec.is_collection:
			#     raise UserError(_('Letters cannot be collected again if they are already collected'))
			# if rec.is_protest:
			#     raise UserError(_('Letters cannot be protested again if they are already protested'))
			# if rec.is_return:
			#     raise UserError(_('Letters cannot be returned again if they are already returned'))
			# for amount in rec.letter_det_ids:
			# if amount.amount_payable == 0:
			#     if amount.move_id.amount_residual > 0.0:
			#         raise UserError(_(
			#             'The documents must have a amount payable (can be partial payment)'))
			# if amount.move_id.amount_residual <= 0.0:
			#     raise UserError(_('The documents must have a balance due'))
			# if rec.operation_methods in ['portfolio', 'refinancing']:
			#     if rec.is_debit_generated:
			#         if not rec.include_interests_in_letter:
			#             if rec.total_amount_fact != rec.total_amount_letras:
			#                 raise UserError(_(
			#                     'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge and Letters <<'))
			#         else:
			#             doc_plus_interest = rec.currency_id.round(
			#                 rec.total_amount_fact + rec.all_amount_interest)  # monto de los documentos mas los intereses
			#             if doc_plus_interest != rec.total_amount_letras:  #
			#                 raise UserError(_(
			#                     'You cannot validate this operation since there are differences in the amounts of the Amount of >> Docs. Charge + interest << and Letters'))
			#     elif rec.difference_amount != 0:
			#         raise UserError(_('You cannot validate, there is a difference in the amounts'))
			# if rec.operation_methods in ['collection', 'discount']:
			#     if rec.list_letters_ids:
			#         for letter in rec.list_letters_ids:
			#             if not letter.unique_code:
			#                 raise UserError(_('Enter the Unique Code'))
			# if rec.operation_methods in ['discount', 'protest', 'return']:
			#     if rec.operation_methods in ['protest', 'return']:
			#         if rec.total_discount_all_letters != 0:
			#             if not rec.analytic_account_id and not rec.analytic_tag_ids:
			#                 raise UserError(_('You need to assign an >> account or tag << analytic'))
			if rec.state == 'in_process':
				# new_payment_ids = []
				# docs_receivable = []
				# Metodo de Pago - General
				# payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
				# if not payment_method_id:
				#     payment_method_id = self.env['account.payment.method'].search([], limit=1)

				# docs_receivable = rec.letter_det_ids.move_id
				# if rec.list_debit_notes_ids:
				#     docs_receivable += rec.list_debit_notes_ids
				# docs_receivable.extend(rec.letter_det_ids)
				# docs_receivable.extend(rec.list_debit_notes_ids)

				### Iteracion por factura ###
				# for doc in docs_receivable:
				# for invoice in rec.letter_det_ids:
					# Creando el pago
					# payval = {
					#     'payment_type': rec.payment_type,
					#     'partner_type': rec.partner_type,
					#     'partner_id': invoice.move_id.partner_id and invoice.move_id.partner_id.id or False,
					#     'payment_method_id': payment_method_id and payment_method_id.id or False,
					#     'state': 'draft',
						# 'company_id'
						# 'date': rec.date.strftime("%Y-%m-%d") if rec.date else False,
						# 'currency_id': rec.currency_id and rec.currency_id.id or False,
						# 'other_currency': rec.other_currency,
						# 'amount': invoice.amount_payable,
						# 'journal_id': rec.journal_id and rec.journal_id.id or False,
						# }
					# if payval['other_currency']:
					#     payval['exchange_date'] = rec.exchange_date
					#     payval['user_exchange_rate'] = rec.user_exchange_rate
					#     payval['exchange_rate'] = rec.exchange_rate
					# payval['invoice_ids'] = [(6, 0, [invoice.move_id.id])]
					# payment_id = self.env['account.payment'].create(payval)
					# Agregando el pago en borrador
					# new_payment_ids.append(payment_id)

				# for debit in rec.list_debit_notes_ids:
					# Creando el pago
					# payval = {
					#     'payment_type': rec.payment_type,
						# 'partner_type': rec.partner_type,
						# 'partner_id': debit.partner_id and debit.partner_id.id or False,
						# 'payment_method_id': payment_method_id and payment_method_id.id or False,
						# 'state': 'draft',
						# 'company_id'
						# 'date': rec.date.strftime("%Y-%m-%d") if rec.date else False,
						# 'currency_id': rec.currency_id and rec.currency_id.id or False,
						# 'other_currency': rec.other_currency,
						# 'amount': debit.amount_residual,
						# 'journal_id': rec.journal_id and rec.journal_id.id or False,
						# }
					# if payval['other_currency']:
					#     payval['exchange_date'] = rec.exchange_date
					#     payval['user_exchange_rate'] = rec.user_exchange_rate
					#     payval['exchange_rate'] = rec.exchange_rate
					# payval['invoice_ids'] = [(6, 0, [debit.id])]
					# payment_id = self.env['account.payment'].create(payval)
					# Agregando el pago en borrador
					# new_payment_ids.append(payment_id)

				# Postea la letra generada
				if rec.operation_methods in ['portfolio', 'refinancing']:
					# if not rec.generate_interest:
					#     if rec.currency_id.round(rec.total_amount_fact) != rec.currency_id.round(
					#             rec.total_amount_letras):
					#         raise UserError(_(
					#             'Total amount of Docs receivable is different from the total amount of Letters generated\n'
					#             'Edit the amount of the letter so that there are no differences\n'
					#             'Otherwise, you will not be able to validate.'))
					if rec.list_letters_ids.mapped('invoice_date_due').count(False) >= 1:
						raise UserError(_('Acceptance date is missing'))
					# for days in rec.list_letters_ids:
						# if rec.exchange_type in ['collection']:
						#     if days.sunat_serie.id == False:
						#         raise UserError(_('Regenerate the letters, the series is missing'))
						# if rec.exchange_type in ['payment']:
						#     if days.invoice_serie == False:
						#         raise UserError(_('Regenerate the letters, the series is missing'))
						# if days.how_days_expires == False:
						#     raise UserError(_('Values are missing in the Due Days field'))
						# if rec.operation_methods in ['refinancing']:
							# if days.mapped('document_type_id.code') == ['08']:
							#     if days.sunat_serie and not rec.debit_notes_serie_id:
							#         raise UserError(_(
							#             'You have generated a debit note in the Letters tab, but there is no Series value selected in the template'))
							#     if days.sunat_serie != rec.debit_notes_serie_id:
							#         raise UserError(_(
							#             'You have generated a debit note in the Letters tab, but it is different from the Series selected in the template'))
							#     if days.invoice_line_ids.mapped('tax_ids') and not rec._tax_ids_debit:
							#         raise UserError(_(
							#             'You have generated a debit note in the Letters tab, but there is no Tax value selected in the template'))
							#     if days.invoice_line_ids.mapped('tax_ids') != rec._tax_ids_debit:
							#         raise UserError(_(
							#             'You have generated a debit note in the Letters tab, but it is different from the Tax selected in the template'))

					# dominio = [('state', 'like', 'draft'),
					#            ('letter_create_id', 'like', self.id),
					#            ('document_type_code', 'in', ['LT', '08'])]
					# invoices_to_post = rec.list_letters_ids.search(dominio, order="id asc")
					# invoices_to_post.post()  # postear letras generadas
					# rec.list_letters_ids.post()
					# if rec.operation_methods in ['portfolio']:
					#     rec.is_exchanged = True
					# else:
					#     for tab_letters in rec.list_letters_ids:
					#         if tab_letters.document_type_id.code in ['LT']:
					#             tab_letters.sunat_number = tab_letters.sunat_number + 'F'
							# if rec.letter_det_ids[0].move_id.letter_state not in ['portfolio']:
							# state_letter = rec.letter_det_ids[0].move_id.sunat_number
						# rec.is_refinanced = True
				# if rec.operation_methods in ['collection', 'discount', 'protest', 'return']:
				#     lett = sorted(rec.list_letters_ids)
				#     for docs in rec.letter_det_ids:  # letras seleccionadas
				#         for letters in lett:
							# if rec.operation_methods in ['collection', 'discount']:
								# if rec.list_letters_ids.mapped('send_date').count(False) >= 1:
								#     raise UserError(_('Shipping date is missing'))
								# if rec.list_letters_ids.mapped('acceptance_date').count(False) >= 1:
								#     raise UserError(_('Acceptance date is missing'))
								# docs.move_id.send_date = letters.send_date
								# docs.move_id.acceptance_date = letters.acceptance_date
								# if rec.operation_methods in ['collection', 'discount']:
								# if rec.list_letters_ids.mapped('unique_code').count(False) == 0:
									# if letters.unique_code:
									# if rec.operation_methods in ['collection']:
										# rec.is_collection = True
										# if rec.type_collection == 'free':
										#     docs.generate_move_id.sunat_number = docs.move_id.sunat_number + 'C'
										# elif rec.type_collection == 'warranty':
										#     docs.generate_move_id.sunat_number = docs.move_id.sunat_number + 'G'
											# docs.generate_move_id.post()

									# if rec.operation_methods == 'discount':
										# if rec.add_financial_expenses:
											# if not rec.journal_id_type_bank_id:
											#     raise UserError(_('Choose a Bank-type Journal'))
											# if not rec._writeoff_account_id:
											#     raise UserError(
											#         _('Choose an accounting account of type Expenses'))
										# docs.generate_move_id.sunat_number = docs.move_id.sunat_number + 'D'
										# rec.is_discount = True
									# docs.generate_move_id.post()
								# else:
								#     raise UserError(_('Unique Code is missing'))
							# if rec.operation_methods in ['protest', 'return']:
								# if rec.add_financial_expenses:
									# Si el campo gastos financieros = 0, tendra que llenarse la cuenta prestamos
									# if rec.total_discount_all_letters == 0:
									#     if not rec.loans_type_id:
									#         raise UserError(_('Choose a Loans Account'))
									# if rec.total_discount_all_letters != 0:
										# Sino, solo llena la cuenta gastos
										# if not rec._writeoff_account_id:
										#     raise UserError(
										#         _('Choose an accounting account of type Expenses'))
									# if not rec.journal_id_type_bank_id:
									#     raise UserError(_('Choose a Bank-type Journal'))

								# if rec.operation_methods in ['protest']:
								#     docs.generate_move_id.sunat_number = docs.move_id.sunat_number + 'P'
								#     docs.generate_move_id.post()
									# rec.is_protest = True
								# if rec.operation_methods in ['return']:
								#     docs.generate_move_id.sunat_number = docs.move_id.sunat_number + 'B'
								#     docs.generate_move_id.post()
									# rec.is_return = True

				# if rec.operation_methods in ['renewal']:
					# if rec.document_type_id:
					#     if rec.all_amount_interest <= 0:
					#         raise UserError(_('No puede validar, tiene que asignar valores en los campos interes de la pestaña de documentos por cobrar'))
					# for letter in rec.list_letters_ids:
						# if letter.mapped('document_type_id.code') == ['LT']:
							# if rec.operation_methods == 'renewal':
								# if letter.how_days_expires == 0:
								#     raise UserError(
								#         _('Values are missing in the Due Days field'))
						# if letter.mapped('document_type_id.code') == ['08']:
						#     if letter.sunat_serie and not rec.debit_notes_serie_id:
						#         raise UserError(_(
						#             'You have generated a debit note in the Letters tab, but there is no Series value selected in the template'))
						#     if letter.sunat_serie != rec.debit_notes_serie_id:
						#         raise UserError(_(
						#             'You have generated a debit note in the Letters tab, but it is different from the Series selected in the template'))
						#     if letter.invoice_line_ids.mapped('tax_ids') and not rec._tax_ids_debit:
						#         raise UserError(_(
						#             'You have generated a debit note in the Letters tab, but there is no Tax value selected in the template'))
						#     if letter.invoice_line_ids.mapped('tax_ids') != rec._tax_ids_debit:
						#         raise UserError(_(
						#             'You have generated a debit note in the Letters tab, but it is different from the Tax selected in the template'))

							# letter.post()
					# for docs in rec.letter_det_ids:
						# if docs.mapped('document_type_id.code') == ['LT']:
							# if rec.operation_methods == 'renewal':
								# rec.is_renewal = True
								# sunat_number_move = docs.move_id.sunat_number + 'R'
								# docs.generate_move_id.sunat_number = sunat_number_move

							# else:
							#     rec.is_refinanced = True
							#     sunat_number_move = docs.move_id.sunat_number + 'F'
							#     docs.generate_move_id.sunat_number = sunat_number_move
							# docs.generate_move_id.post()

				# Se postea un mensaje en el doc por cobrar diciendo que se genero letras en X plantilla
				# data = {}
				# process = {
				#     'portfolio': _('Exchange'),
				#     'collection': _('Free Collection'),
				#     'warranty': _('Warranty'),
				#     'discount': _('Discount'),
				#     'renewal': _('Renewal'),
				#     'refinancing': _('Refinancing'),
				#     'protest': _('Protest'),
				#     'return': _('Return')
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
				#     pay.move_line_ids.move_id.seat_generated_id = self and self.id or False
				#     pay.move_line_ids.move_id.gloss = False
				#     ruc = pay.partner_id.vat
				#     operation_type = pay.invoice_ids[0].operation_type_id and pay.invoice_ids[
				#         0].operation_type_id.id or False
					# if rec.exchange_type in ['collection']:
					#     serie = pay.invoice_ids[0].sunat_serie and pay.invoice_ids[0].sunat_serie.id or False
					#     number_fact = pay.invoice_ids[0].sunat_number
					# if rec.exchange_type in ['payment']:
					#     serie = pay.invoice_ids[0].invoice_serie or False
					#     number_fact = pay.invoice_ids[0].invoice_number
					# gloss_entry = 'Ingreso de ' + str(ruc) + '-' + str(operation_type) + '-' + str(serie) + '-' + str(
					#     number_fact)
					# pay.move_line_ids.move_id.gloss = gloss_entry
					# entry_receivable = pay.move_line_ids.move_id and pay.move_line_ids.move_id.id or False
					# self.seat_generated_by_payment_ids.append(entry_receivable)
				# Para el proceso de Descuento - Protesto - Devolucion
				# if rec.operation_methods in ['discount', 'protest', 'return']:
				#     if rec.add_financial_expenses:
						# self._generate_financial_expenses_entry()
				# Realizamos los procesos de cierre
				# rec.state = 'posted'
		# return True

	# def generate_debit_notes(self):
	#     for rec in self:
	#         debit_notes = []
	#         new_debit_notes = []
	#         self._check_products_company()
	#         self._check_bridge_journal()
	#         if rec.is_debit:  # Caso 3
	#             _interest = 0
	#             _interest_arrears = 0
	#             _interest_compensatory = 0
	#             _interest_arrears = sum(rec.letter_det_ids.mapped('interest_on_arrears'))
	#             _interest_compensatory = sum(rec.letter_det_ids.mapped('compensatory_interest'))
	#             _interest = _interest_arrears + _interest_compensatory
	#             invoice_lines = [(0, 0, {
	#                 'product_id': rec.company_id.letter_interest.id,
	#                 'name': rec.company_id.letter_interest.display_name,
	#                 'account_id': rec.company_id.letter_interest.property_account_income_id.id,
	#                 'tax_ids': rec._tax_ids_debit and rec._tax_ids_debit.ids or False,
	#                 'product_uom_id': rec.company_id.letter_interest.uom_id and rec.company_id.letter_interest.uom_id.id or False,
	#                 'price_unit': _interest
	#             })]
	#             # if rec.is_debit:
	#             debit_notes = rec._prepare_invoice_vals(invoice_lines, _interest)
	#             debit_notes['partner_id'] = rec.letter_det_ids[0].move_id.partner_id and rec.letter_det_ids[
	#                 0].move_id.partner_id.id or False
	#             debit_notes['journal_id'] = self.journal_debit_note_id and self.journal_debit_note_id.id or False,
	#             debit_notes['letter_amount'] = _interest
	#             # debit_notes['invoice_date'] = rec.date
	#             debit_notes['amount_letter'] = debit_notes['letter_amount']
	#             self.env['account.move'].create(debit_notes)
	#
	#         if rec.is_debit_generated:  # Caso 4
	#             amount_interest = 0
	#             for move in rec.letter_det_ids:
	#                 if move.interest_on_arrears > 0 or move.compensatory_interest > 0:
	#                     amount_interest = move.interest_on_arrears + move.compensatory_interest
	#                     invoice_lines = [(0, 0, {
	#                         'product_id': rec.company_id.letter_interest.id,
	#                         'name': rec.company_id.letter_interest.display_name,
	#                         'account_id': rec.company_id.letter_interest.property_account_income_id.id,
	#                         'tax_ids': rec._tax_ids_debit and rec._tax_ids_debit.ids or False,
	#                         'price_unit': amount_interest
	#                     })]
	#                     new_debit_notes = rec._prepare_invoice_vals(invoice_lines,
	#                                                                 amount_interest)
	#                     new_debit_notes['debit_create_id'] = self and self.id or False,
	#                     new_debit_notes['debit_note_type'] = '1'
	#                     # new_debit_notes['invoice_date'] = rec.date
	#                     new_debit_notes[
	#                         'refund_invoice_document_type_id'] = move.move_id.document_type_id and move.move_id.document_type_id.id or False,
	#                     new_debit_notes['refund_invoice_invoice_date'] = move.move_id.invoice_date
	#                     if rec.exchange_type == 'collection':
	#                         new_debit_notes['refund_invoice_sunat_serie'] = move.move_id.sunat_serie.name
	#                         new_debit_notes['refund_invoice_sunat_number'] = move.move_id.sunat_number
	#                     if rec.exchange_type == 'payment':
	#                         new_debit_notes['refund_invoice_sunat_serie'] = move.move_id.invoice_serie
	#                         new_debit_notes['refund_invoice_sunat_number'] = move.move_id.invoice_number
	#                     new_debit_notes['partner_id'] = move.move_id.partner_id.id
	#                     new_debit_notes[
	#                         'journal_id'] = self.journal_debit_note_id and self.journal_debit_note_id.id or False,
	#                     self.env['account.move'].create(new_debit_notes)

	def _create_claim_entry(self, amount):
		############## POLIMASTER ################
		# Esta funcion crea el asiento de reclamo si los intereses exceden el monto calculado
		# Obtenemos la fecha y el tipo de cambio del contexto
		exchange_date = self.env.context.get('exchange_date')
		exchange_rate = self.env.context.get('exchange_rate')
		lines = []
		currency = self.currency_id.id
		if self.env.company.currency_id != self.currency_id:
			debit_credit = amount * self.exchange_rate
		else:
			debit_credit = amount
		_writeoff_account_id = self.env.context.get('_writeoff_account_id') if self.env.context.get('_writeoff_account_id') else self._writeoff_account_id
		analytic_account_id = self.env.context.get('analytic_account_id') if self.env.context.get('analytic_account_id') else self.analytic_account_id
		analytic_tag_ids = self.env.context.get('analytic_tag_ids') if self.env.context.get('analytic_tag_ids') else self.analytic_tag_ids
		claim_account_id = self.env.context.get('claim_account_id') if self.env.context.get('claim_account_id') else self.claim_account_id
		lines.append((0, 0, {
			'account_id': claim_account_id.id,
			'amount_currency': abs(amount),
			'currency_id': currency,
			'debit': abs(debit_credit)
			}))
		lines.append((0, 0, {
			'account_id': _writeoff_account_id.id,
			'analytic_account_id': analytic_account_id and analytic_account_id.id or False,
			'analytic_tag_ids': analytic_tag_ids and analytic_tag_ids.ids or False,
			'amount_currency': -abs(amount),
			'currency_id': currency,
			'credit': abs(debit_credit)
			}))
		dict_entry = {
			'date': exchange_date if exchange_date else (self.date or fields.Date.today() or False),
			'journal_id': self.journal_id_type_bank_id and self.journal_id_type_bank_id.id or False,
			'move_type': 'entry',
			'currency_id': currency,
			'exchange_rate': exchange_rate,
			'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			#'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
			'line_ids': lines,
			}
		move_claim_expenses_id = self.env['account.move'].create(dict_entry)
		if move_claim_expenses_id:
			move_claim_expenses_id.account_analytic_destino()
			move_claim_expenses_id.post()

		self.move_claim_expenses_id = move_claim_expenses_id and move_claim_expenses_id.id or False
		for entry in move_claim_expenses_id:
			msg_body = _("This entry for claim expenses was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)

	def fees_comissions(self):
		return self.env['fees.comissions.wizard'].with_context({'active_model': 'letter.management', 'active_id': self.id, 'total_discount_all_letters': self.total_discount_all_letters}).get_fees_and_comissions()

	def _create_fees_and_comissions_entry(self):
		############## POLIMASTER ################
		# Esta funcion crea el asiento de portes y comisiones creado por separado en algunos bancos
		# Obtenemos la fecha y el tipo de cambio del contexto y los montos de los portes y comisiones
		# Ademas si hay reclamo en el wizard creamos el asiento de reclamaciones
		fees = self.env.context.get('bank_interests')
		comission = self.env.context.get('financial_expenses')
		amount = fees + comission
		if amount == 0:
			raise UserError(_('Fees and comissions can\'t be equals 0'))
		if self.env.context.get('claim'):
			amount = amount - self.total_discount_all_letters
			if amount:
				self._create_claim_entry(amount)
			else:
				raise UserError(_('Can\'t claim 0 amount'))
		amount = fees + comission
		exchange_date = self.env.context.get('exchange_date')
		exchange_rate = self.env.context.get('exchange_rate')
		analytic_account_id = self.env.context.get('analytic_account_id')
		analytic_tag_ids = self.env.context.get('analytic_tag_ids')
		lines = []
		currency = self.currency_id.id
		if self.env.company.currency_id != self.currency_id:
			credit_amount = amount * self.exchange_rate
			fees_debit = fees * self.exchange_rate
			comission_debit = comission * self.exchange_rate
		else:
			credit_amount = amount 
			fees_debit = fees
			comission_debit = comission
		lines.append((0, 0, {
			'account_id': self.journal_id_type_bank_id.payment_credit_account_id.id,
			'amount_currency': -amount,
			'currency_id': currency,
			'credit': credit_amount
			}))
		if fees:
			lines.append((0, 0, {
				'account_id': self.env.context.get('_writeoff_account_id').id,
				'analytic_account_id': analytic_account_id and analytic_account_id.id or False,
				'analytic_tag_ids': analytic_tag_ids and analytic_tag_ids.ids or False,
				'amount_currency': fees,
				'currency_id': currency,
				'debit': fees_debit
				}))
		if comission:
			lines.append((0, 0, {
				'account_id': self.env.context.get('_writeoff_account_id').id,
				'analytic_account_id': analytic_account_id and analytic_account_id.id or False,
				'analytic_tag_ids': analytic_tag_ids and analytic_tag_ids.ids or False,
				'amount_currency': comission,
				'currency_id': currency,
				'debit': comission_debit
				}))
		dict_entry = {
			'date': exchange_date if exchange_date else (self.date or fields.Date.today() or False),
			'journal_id': self.journal_id_type_bank_id and self.journal_id_type_bank_id.id or False,
			'move_type': 'entry',
			'currency_id': currency,
			'exchange_rate': exchange_rate,
			'ref': _('Disburse fees and comissions ') + str(self.name),
			#'gloss': _('Disburse fees and comissions ') + str(self.name),
			'line_ids': lines,
			}
		fees_comissions_id = self.env['account.move'].create(dict_entry)
		if fees_comissions_id:
			fees_comissions_id.account_analytic_destino()
			fees_comissions_id.post()

		self.fees_comissions_id = fees_comissions_id and fees_comissions_id.id or False
		for entry in fees_comissions_id:
			msg_body = _("This entry for fees and comissions was generated from template No.") \
						+ " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
			entry.message_post(body=msg_body)
			
	def delete_fees_comissions(self):
		for rec in self:
			if rec.fees_comissions_id:
				rec.fees_comissions_id.with_context(force_delete=True).unlink()
			if rec.move_claim_expenses_id:
				rec.move_claim_expenses_id.with_context(force_delete=True).unlink()

	def _generate_financial_expenses_entry(self):
		lines = []
		self._check_products_company()
		self._check_bridge_journal()
		# this function generates the financial expenses entry
		############## POLIMASTER ################
		# Obtenemos la fecha y el tipo de cambio del contexto
		exchange_date = self.env.context.get('exchange_date')
		exchange_rate = self.env.context.get('exchange_rate')
		for rec in self:
			if rec.add_financial_expenses:
				_discount = 0
				account_first_line = False
				account_third_line = False
				_amount_first_line = 0
				_amount_third_line = 0
				difference_discount = 0
				
				if rec.operation_methods in ['discount']:
					if rec.total_discount_all_letters == 0:
						raise UserError(_('An amount has not been assigned in the Financial expenses field'))
					if rec.total_discount_manual and rec.total_discount_real == rec.total_discount_all_letters:
						raise UserError(_('The amount in total discount manual should be different than real.'))
					else:
						if not self.complete_disbursement:
							if rec.claim:
								self._create_claim_entry(rec.total_discount_real - rec.total_discount_all_letters)
							#elif rec.total_discount_manual:
								#difference_discount = abs(rec.total_discount_real) #- abs(rec.total_discount_all_letters)

				# Para desembolsos completos dejar el descuento en 0
				if not self.complete_disbursement:
					if not rec.total_discount_manual:
						rec.total_discount_real =  abs(rec.total_discount_all_letters)
						_discount = abs(rec.currency_id.round(rec.total_discount_all_letters))  # gastos
					else:
						#if rec.claim:
						#    _discount = abs(rec.currency_id.round(rec.total_discount_real))  # gastos
						#else:
						_discount = abs(rec.currency_id.round(rec.total_discount_real)) #- abs(difference_discount)  # gastos
				if rec.operation_methods in ['discount']:
					account_first_line = rec.journal_id_type_bank_id.payment_debit_account_id.id  # diario banco >> cambiar nombre de campo a journal_type_bank_id >> cambiar de nombre a la variable a account_first_line
					# _amount_first_line = rec.currency_id.round(sum(rec.list_letters_ids.mapped('letter_amount')))
					_amount_first_line = rec.currency_id.round(rec.total_amount_letras - _discount)
					account_third_line = rec.company_id.bridge_journal.default_account_id.id
					# _amount_third_line = rec.currency_id.round(sum(rec.letter_det_ids.mapped('amount_payable')))
					_amount_third_line = rec.currency_id.round(rec.total_amount_fact)

				if rec.operation_methods in ['protest', 'return']:
					account_first_line = rec.loans_type_id.id  # cuenta prestamos
					_amount_first_line = self.currency_id.round(
						sum(self.letter_det_ids.mapped('amount_payable')))  # sumatoria de los docs por cobrar
					# _amount_first_line = rec.currency_id.round(rec.total_amount_fact)  # sumatoria de los docs por cobrar
					account_third_line = rec.journal_id_type_bank_id.default_account_id.id  # diario banco
					_amount_third_line = rec.currency_id.round(
						_discount + _amount_first_line)  # monto diario banco
				if rec.other_currency:
					currency = rec.currency_id.id
					exchange = rec.exchange_rate
					amount_currency_first = _amount_first_line
					# _debit_first = rec.currency_id.round(amount_currency_first * exchange)
					# Conversion de moneda extranjera a moneda local
					_debit_first = rec.currency_id.with_context(custom_rate_from=rec.exchange_rate or False,
																custom_other_rate=rec.other_currency)._convert(
																amount_currency_first, rec.company_id.currency_id, rec.company_id,
																rec.exchange_date or fields.Date.today())
					amount_currency_third = - _amount_third_line
					# credit_third = rec.currency_id.round(abs(amount_currency_third) * exchange)
					credit_third = sum(rec.list_letters_ids.mapped('amount_total'))
					credit_third = rec.currency_id.with_context(custom_rate_from=rec.exchange_rate or False,
																custom_other_rate=rec.other_currency)._convert(
																credit_third, rec.company_id.currency_id, rec.company_id,
																rec.exchange_date or fields.Date.today())
					amount_currency_second = _discount
					# Para cuadrar el asiento y no tener diferencias de cambio de un centavo
					# pero si hay una diferencia entoneces cuadramos la diferencia
					if difference_discount:
						_debit_second = rec.currency_id.round(amount_currency_second * exchange)
					else:
						_debit_second = credit_third - _debit_first #rec.currency_id.round(amount_currency_second * exchange)
				else:
					currency = self.env.company.currency_id.id
					amount_currency_first = False
					_debit_first = _amount_first_line
					amount_currency_second = False
					_debit_second = _discount
					amount_currency_third = False
					credit_third = _amount_third_line

				line_name = _('Disbursement ') + self.env['res.currency'].search([('id', '=', currency)]).symbol + str(amount_currency_first) + ' - ' + (self.partner_id.name if self.partner_id else '') + ' - ' + str(exchange_date if exchange_date else (self.date or fields.Date.today() or False))

				lines.append((0, 0, {
					'partner_id': rec.journal_id_type_bank_id.bank_partner_id.id,
					'name': line_name,
					'account_id': account_first_line,
					'amount_currency': amount_currency_first,
					'currency_id': currency,
					'debit': _debit_first
					}))
				if rec.total_discount_all_letters != 0 and not rec.complete_disbursement:
					# se agrega la linea de gastos
					lines.append((0, 0, {
						'partner_id': rec.journal_id_type_bank_id.bank_partner_id.id,
						'name': line_name,
						'account_id': rec._writeoff_account_id.id,
						'analytic_account_id': rec.analytic_account_id and rec.analytic_account_id.id or False,
						'analytic_tag_ids': rec.analytic_tag_ids and rec.analytic_tag_ids.ids or False,
						'amount_currency': amount_currency_second,
						'currency_id': currency,
						'debit': _debit_second
						}))
				# Si hay una diferencia entre el monto cobrado por intereses y el monto manual
				# se agrega una linea con la diferencia a la cuenta de gasto siempre y cuando
				# el cobro del banco sea mayor al cobro calculado por la formula
				
				_debit_third = 0
				#if difference_discount > 0 and not rec.claim:
				#    _debit_third = credit_third - _debit_first - _debit_second
				#    lines.append((0,0,{
				#        'partner_id': rec.journal_id_type_bank_id.bank_partner_id.id,
				#        'name': _('Expenses difference charged in bank.'),
				#        'account_id': rec._writeoff_account_id.id,
				#        'amount_currency': abs(difference_discount),
				#        'currency_id': currency,
				#        'credit': 0,
				#        'debit': _debit_third,
				#        'analytic_account_id': rec.analytic_account_id and rec.analytic_account_id.id or False,
				#    }))

				# Si hay una diferencia entre las letras (por la division del monto total en dolares)
				#  y el total del desembolso se agrega un linea mas
				if not rec.complete_disbursement: 
					difference = _debit_first + _debit_second + _debit_third - credit_third
				else:
					difference = _debit_second + _debit_third
				if difference and float_round(abs(difference), 2) >= 0.01:
					lines.append((0,0,{
						'partner_id': rec.journal_id_type_bank_id.bank_partner_id.id,
						'name': _('Rounding amount on dividing letters'),
						'account_id': self.env.company.income_rounding_currency_exchange_account_id.id if difference > 0 else self.env.company.expense_rounding_currency_exchange_account_id.id,
						'credit': abs(difference) if difference > 0 else 0,
						'debit': abs(difference) if difference < 0 else 0,
						'analytic_account_id': self.env.company.rounding_analitic_account_id.id if difference < 0 else False,
					}))
				lines.append((0, 0, {
					'partner_id': rec.journal_id_type_bank_id.bank_partner_id.id,
					'name': line_name,
					'account_id': account_third_line,
					'amount_currency': amount_currency_third,
					'currency_id': currency,
					'credit': credit_third
					}))
				dict_entry = {
					'date': exchange_date if exchange_date else (self.date or fields.Date.today() or False),
					'journal_id': self.journal_id_type_bank_id and self.journal_id_type_bank_id.id or False,
					'move_type': 'entry',
					'currency_id': currency,
					'exchange_date': exchange_date,
					'exchange_rate': exchange_rate,
					'ref': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
					#'gloss': _('Letter ') + (self.operation_methods + ' ') + str(self.name),
					'line_ids': lines,
					}
				financial_expenses_entry = self.env['account.move'].create(dict_entry)
				# for line in financial_expenses_entry.line_ids:
				#     print(line.debit, line.credit, line.amount_currency)
				if financial_expenses_entry:
					# destination._compute_has_destiny()
					financial_expenses_entry.account_analytic_destino()
					financial_expenses_entry.post()

				self.move_expenses_id = financial_expenses_entry and financial_expenses_entry.id or False
				# Se postea un mensaje en el asiento de gastos financieros generado
				for entry in financial_expenses_entry:
					msg_body = _("This entry for financial expenses was generated from template No.") \
							   + " <a href=# data-oe-model=letter.management>%s</a>" % (self.id)
					# self.id, self.id, data['operacion'])
					entry.message_post(body=msg_body)

	def _validate_documents_receivable(self):
		for rec in self:
			# if rec.operation_methods in ['portfolio']:
			#     if len(list(rec.letter_det_ids.mapped('partner_id'))) > 1:
			#         raise UserError(_('For this operation, select those that have the same partner'))
			#     if len(list(rec.letter_det_ids.mapped('move_id.id'))) >= 1:
			#         for line in rec.letter_det_ids:
			#             if line.move_id.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08']:
			#                 raise UserError(_('To exchange documents, select invoices, debit notes, tickets'))
			# if len(list(rec.letter_det_ids.mapped('partner_id'))) == 1:
			#     rec.partner_id = rec.letter_det_ids[0].partner_id.id

			if rec.operation_methods in ['portfolio', 'refinancing', 'renewal']:
				if len(list(rec.letter_det_ids.mapped('partner_id'))) > 1:
					raise UserError(_('For this operation, select those that have the same partner'))

			# if rec.operation_methods in ['portfolio']:
			#     # if len(list(rec.letter_det_ids.mapped('move_id.id'))) >= 1:
			#     for line in rec.letter_det_ids:
			#         if line.move_id.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08']:
			#             raise UserError(_('To exchange documents, select invoices, debit notes, tickets'))

			if rec.operation_methods in ['refinancing']:
				# if len(list(rec.letter_det_ids.mapped('move_id.id'))) > 1:
				for line in rec.letter_det_ids:
					if line.move_id.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08', 'LT']:
						raise UserError(
							_('To refinance documents, select portfolio letters, invoices, debit notes, tickets'))

					if line.move_id.document_type_id.code in ['LT']:
						if line.move_id.letter_state not in ['portfolio', 'protest']:
							raise UserError(_(
								'In the selection, if you choose letters, they have to be in Portfolio or Protest status'))
			#
			#     # if len(list(rec.letter_det_ids.mapped('move_id.id'))) == 1:
			#     #     for line in rec.letter_det_ids:
			#     #         if line.move_id.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08', 'LT']:
			#     # if rec.letter_det_ids.mapped('document_type_id.code') not in ['LT', '01', '08']:
			#     # raise UserError(
			#     #     _('To refinance documents, select portfolio letters, invoices, debit notes, tickets'))
			#
			if rec.operation_methods in ['collection', 'discount']:
				if len(list(rec.letter_det_ids.mapped('document_type_id.code'))) > 1:
					raise UserError(_(
						'Only letter type documents, Delete those documents that are different from the type Letters'))
				else:
					if rec.letter_det_ids.document_type_id.code not in ['LT']:
						raise UserError(_('Only letter type documents'))
					else:
						for letter in rec.letter_det_ids:
							if letter.move_id.letter_state not in ['portfolio', 'protest']:
								raise UserError(
									_('Just select documents of type letters, with status in portfolio or protest'))
			if rec.operation_methods in ['renewal']:
				if len(list(rec.letter_det_ids.mapped('move_id.id'))) > 1:
					raise UserError(_('To renewal documents, select a letter in portfolio'))
				if len(list(rec.letter_det_ids.mapped('move_id'))) == 1:
					for line in rec.letter_det_ids:
						if line.move_id.document_type_id.code not in ['LT']:
							# if (rec.letter_det_ids.mapped('move_id.document_type_code')).count('LT') < 1:
							raise UserError(_('To renewal documents, select a letter in portfolio'))
						else:
							if line.move_id.letter_state not in ['portfolio']:
								raise UserError(_('Only letters in portfolio'))

				for doc in rec.letter_det_ids:
					if doc.document_type_id.code in ['LT']:
						if doc.letter_state not in ['portfolio', 'protest']:
							raise UserError(_(
								'In the selection, if you choose letters, they have to be in Portfolio status'))

			if rec.operation_methods in ['protest']:
				# if len(list(rec.letter_det_ids.mapped('move_id.id'))) >= 1:
				for letter in rec.letter_det_ids:
					if letter.move_id.document_type_id.code not in ['LT']:
						raise UserError(_('You only need to choose a Letter type document'))

			if rec.operation_methods in ['return']:
				for letter in rec.letter_det_ids:
					if letter.move_id.document_type_id.code not in ['LT']:
						raise UserError(_('You only need to choose a Letter type document'))
					if letter.move_id.letter_state not in ['collection', 'discount']:
						raise UserError(_(
							'Just select documents of type letters, with status in collection (Free or warramty) or discount'))
			if len(list(rec.letter_det_ids.mapped('partner_id'))) == 1:
				rec.partner_id = rec.letter_det_ids[0].partner_id.id

	def _check_products_company(self):
		for rec in self:
			if rec.company_id:
				action = self.env.ref('base_setup.action_general_configuration')
				msg = _(
					'Cannot find a product for the generation of documents, You should configure it. Press the button to go to your company settings.')
				if rec.operation_methods in ['portfolio']:
					if not rec.company_id.letter_portfolio:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))
				if rec.operation_methods in ['discount']:
					if not rec.company_id.letter_discount_me or not rec.company_id.letter_discount:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))
				if rec.operation_methods in ['collection']:
					if not rec.company_id.letter_collection:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))
				if rec.generate_interest:
					if not rec.company_id.letter_interest:
						raise RedirectWarning(msg, action.id, _('Go to my company settings'))

	def _check_if_ribbon_is_activated(self):
		for rec in self:
			if rec.is_renewal:
				raise UserError(_('You cannot renew letters again if they are already renewed'))
			if rec.is_refinanced:
				raise UserError(_('You cannot refinance letters if they are already Refinanced'))
			if rec.is_discount:
				raise UserError(_('Letters cannot be discounted again if they are already on Discount'))
			if rec.is_collection:
				raise UserError(_('Letters cannot be collected again if they are already collected'))
			if rec.is_protest:
				raise UserError(_('Letters cannot be protested again if they are already protested'))
			if rec.is_return:
				raise UserError(_('Letters cannot be returned again if they are already returned'))

	def _check_before_to_processing_the_payment(self):
		res = super(LetterManagement, self)._check_before_to_processing_the_payment()
		for rec in self:
			if rec.exchange_type in ['collection']:
				############## POLIMASTER ################
				# Quitamos la validación de código único :)
				# if rec.operation_methods in ['collection', 'discount']:
				#     if rec.list_letters_ids:
				#         for letter in rec.list_letters_ids:
				#             if not letter.unique_code:
				#                 raise UserError(_('Enter the Unique Code'))
				if rec.operation_methods in ['discount', 'protest', 'return']:
					if rec.operation_methods in ['protest', 'return']:
						if rec.total_discount_all_letters != 0:
							if not rec.analytic_account_id and not rec.analytic_tag_ids:
								raise UserError(_('You need to assign an >> account or tag << analytic'))

	def check_values_to_post_docs(self):
		res = super(LetterManagement, self).check_values_to_post_docs()
		for rec in self:
			# if rec.state in ['in_process']:
			if rec.exchange_type in ['collection']:
				# for doc in rec.list_letters_ids:
				#     if not doc.sunat_serie:
				#         raise UserError(_('Regenerate the letters, the series is missing'))
				if rec.operation_methods in ['portfolio', 'refinancing', 'renewal']:
					for doc in rec.list_letters_ids:
						if doc.document_type_id.code not in ['08']:
							if not doc.how_days_expires or doc.how_days_expires == 0:
								raise UserError(_('Values are missing in the Due Days field'))
						if not doc.invoice_date_due:
							raise UserError(_('Date due is missing'))
						# if rec.operation_methods in ['refinancing']:
						if doc.document_type_id.code in ['08']:
							"""if doc.sunat_serie and not rec.debit_notes_serie_id:
								raise UserError(_(
									'You have generated a debit note in the Letters tab, but there is no Series value selected in the template'))
							if doc.sunat_serie != rec.debit_notes_serie_id:
								raise UserError(_(
									'You have generated a debit note in the Letters tab, but it is different from the Series selected in the template'))
							"""
							if doc.invoice_line_ids.mapped('tax_ids') and not rec._tax_ids_debit:
								raise UserError(_(
									'You have generated a debit note in the Letters tab, but there is no Tax value selected in the template'))
							if doc.invoice_line_ids.mapped('tax_ids') != rec._tax_ids_debit:
								raise UserError(_(
									'You have generated a debit note in the Letters tab, but it is different from the Tax selected in the template'))

				if rec.operation_methods in ['collection', 'discount', 'protest', 'return']:
					for docs in rec.letter_det_ids:
						for letter in rec.list_letters_ids:
							if rec.operation_methods in ['collection', 'discount']:
								if not letter.send_date:
									raise UserError(_('Shipping date is missing'))
								if not letter.acceptance_date:
									raise UserError(_('Acceptance date is missing'))
								############## POLIMASTER ################
								# Comentamos estas líneas por que no se tienen los números únicos hasta que el banco los entrega
								# Ademas los números son "únicos" por letra
								# if not rec.unique_code or not letter.unique_code:
								#     raise UserError(_('Unique Code is missing'))
								# if letter.unique_code:
								#     if rec.operation_methods in ['collection']:
								docs.move_id.send_date = letter.send_date
								docs.move_id.acceptance_date = letter.acceptance_date

							if rec.operation_methods in ['discount', 'protest', 'return']:
								if rec.add_financial_expenses:
									if not rec.journal_id_type_bank_id:
										raise UserError(_('Choose a Bank-type Journal'))
									if rec.operation_methods in ['discount']:
										if not rec._writeoff_account_id and not rec.complete_disbursement:
											raise UserError(
												_('Choose an accounting account of type Expenses'))
									if rec.operation_methods in ['protest', 'return']:
										if rec.total_discount_all_letters == 0:
											if not rec.loans_type_id:
												raise UserError(_('Choose a Loans Account'))
										else:
											if not rec._writeoff_account_id:
												raise UserError(
													_('Choose an accounting account of type Expenses'))

				rec.posting_docs_in_portfolio()

	def posting_docs_in_portfolio(self):
		res = super(LetterManagement, self).posting_docs_in_portfolio()
		for rec in self:
			domain = [('state', 'like', 'draft'),
					  ('letter_create_id', 'like', self.id),
					  ('document_type_code', 'in', ['LT', '08'])]
			invoices_to_post = rec.list_letters_ids.search(domain, order='id asc')
			letter = ''
			if rec.operation_methods not in ['portfolio']:
				if rec.operation_methods in ['refinancing']:
					rec.is_refinanced = True
					letter = 'F'
				if rec.operation_methods in ['collection']:
					rec.is_collection = True
					letter = 'C' if rec.type_collection in ['free'] else 'G'
				if rec.operation_methods in ['discount']:
					rec.is_discount = True
					letter = 'D'
				if rec.operation_methods in ['protest']:
					rec.is_protest = True
					letter = 'P'
				#if rec.operation_methods in ['return']:
				#    rec.is_return = True
				#    letter = 'B'
				# if rec.operation_methods in ['renewal']:
				#     rec.is_renewal = True
				#     letter = 'R'

				if rec.operation_methods in ['refinancing', 'renewal']:
					for inv in invoices_to_post:
						# if rec.operation_methods in ['refinancing']:
						#     inv.sunat_number += letter if inv.document_type_id.code in ['LT'] else ''
						inv.post()

				if rec.operation_methods in ['refinancing', 'collection', 'discount', 'protest', 'return', 'renewal']:
					for doc in rec.letter_det_ids:
						if rec.operation_methods in ['refinancing', 'collection', 'discount', 'protest', 'return']:
							for inv in invoices_to_post:
								# if doc.move_id.templates_cancelled_ids:
								#     doc.generate_move_id.sunat_number = str(int(doc.move_id.sunat_number[:9])+len(doc.move_id.templates_cancelled_ids)) + doc.move_id.sunat_number[9:] + letter
								# else:
								doc.generate_move_id.sunat_number = doc.move_id.sunat_number + letter
						if rec.operation_methods in ['renewal']:
							sunat_number = ''.join([s for s in doc.move_id.sunat_number if s.isdigit()])
							ending_letters = ''.join([s for s in doc.move_id.sunat_number if not s.isdigit()])
							doc.generate_move_id.sunat_number = sunat_number[:-2] + str(int(sunat_number[-2:])+1).zfill(2) +  ending_letters
							doc.generate_move_id.origin_id = doc.move_id.origin_id if doc.move_id.origin_id else doc.move_id
							doc.generate_move_id.line_ids.filtered(lambda l: l.debit > 0).account_id = doc.generate_move_id.origin_id.line_ids.filtered(lambda l: l.debit > 0).account_id
						if doc.generate_move_id.state != 'posted':
							doc.generate_move_id._post()

	def _get_process(self):
		process = super(LetterManagement, self)._get_process()
		for rec in self:
			if rec.exchange_type in ['collection']:
				process = {
					'portfolio': _('Exchange'),
					'collection': _('Collection'),
					'discount': _('Discount'),
					'renewal': _('Renewal'),
					'refinancing': _('Refinancing'),
					'protest': _('Protest'),
					'return': _('Return')
					}
			return process

	def assigning_letter_in_doc_posted(self, value_letter):
		for rec in self:
			if value_letter:
				for let in rec.list_letters_ids:
					if rec.operation_methods in ['refinancing']:
						if let.document_type_id.code in ['lT']:
							let.sunat_number = let.sunat_number + value_letter

	def paying_generated_payments(self, new_payment_ids):
		res = super(LetterManagement, self).paying_generated_payments(new_payment_ids)
		for rec in self:
			if rec.operation_methods in ['discount', 'protest', 'return']:
				if rec.add_financial_expenses:
					rec._generate_financial_expenses_entry()

	# def _get_serie(self):
	#     serie = super(LetterManagement, self)._get_serie()
	#     for rec in self:
	#         if rec.exchange_type in ['collection']:
	#             serie = rec.letters_serie_id.id
	#     return serie

	def btn_cancel_template(self):
		res = super().btn_cancel_template()
		for rec in self:
			if rec.operation_methods == 'discount':
				rec.move_expenses_id.button_draft()
				rec.move_expenses_id.with_context(force_delete=True).unlink()
				if rec.move_claim_expenses_id:
					rec.move_claim_expenses_id.button_draft()
					rec.move_claim_expenses_id.with_context(force_delete=True).unlink()
				rec.fees_comissions_id.button_draft()
				rec.fees_comissions_id.with_context(force_delete=True).unlink()
		return res

class LetrasFacturas(models.Model):
	_inherit = 'letter.management.det'
	_description = 'Lineas Factura'

	letter_state = fields.Selection([
		('portfolio', 'In portfolio'),
		('collection', 'In collection'),
		('warranty', 'In warranty'),
		('discount', 'In discount'),
		('protest', 'In protest'),
		], string='Letter State')

	# por el momento: se sobreescribe el codigo
	@api.onchange('partner_id', 'document_type_id', 'letter_state', 'move_id', 'document_number')
	def _write_partner(self):
		for rec in self:
			domain = [('partner_id', '=', rec.partner_id.id), ('document_type_id', '=', rec.document_type_id.id),
					  ('currency_id', '=', rec.letter_fact_id.currency_id.id),
					  ('payment_state', '=', 'not_paid'), ('state', '=', 'posted')]

			check_modules = True
			rec.letter_fact_id._check_letter_management_modules_are_installed(check_modules)

			if not rec.letter_fact_id.exchange_type:
				rec.unlink()

				message = _('Elige primero el Tipo de Canje')
				warning_mess = {'title': _('No hay tipo de canje!'), 'message': message}
				return {'warning': warning_mess}

			if rec.letter_fact_id.exchange_type in ['payment']:
				# if len(letter_payable_module) == 1:
				if rec.letter_fact_id.operation_methods in ['portfolio']:
					domain += [('move_type', 'in', ['in_refund', 'in_invoice'])]
				else:
					raise UserError('Solo puede validar los procesos de canje')
				# else:
				#     raise UserError(_('Falta instalar Letras por pagar'))
			if rec.letter_fact_id.exchange_type in ['collection']:
				# if len(letter_receivable_module) == 1:
				domain += [('move_type', 'in', ['out_refund', 'out_invoice'])]

			if rec.letter_fact_id.operation_methods in ['portfolio', 'renewal', 'refinancing']:
				rec.partner_id = rec.letter_fact_id.partner_id and rec.letter_fact_id.partner_id.id or False
			if rec.letter_fact_id.operation_methods in ['portfolio']:
				if rec.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08']:
					rec.document_type_id = False
					# rec.document_type_id = self.env.ref('qa_standard_locations_account.document_type_01').id
					rec.letter_state = False
					rec.move_id = False
				if rec.letter_state:
					rec.letter_state = False
					rec.move_id = False
			if rec.letter_fact_id.operation_methods in ['renewal']:
				if rec.document_type_id.code not in ['LT']:
					# rec.document_type_id = False
					rec.document_type_id = self.env.ref('qa_letter_management.document_type_lt1').id
					rec.letter_state = 'portfolio'
					rec.move_id = False
				if rec.document_type_id.code in ['LT']:
					if rec.letter_state not in ['portfolio']:
						if rec.letter_state:
							rec.letter_state = 'portfolio'
							rec.move_id = False
					# agregar un if para validar que si esta en estado portfolio, agregue el dominio del estado portfolio para mejorar el filtro
					domain += [('letter_state', '=', rec.letter_state)]
			if rec.letter_fact_id.operation_methods in ['refinancing']:
				if rec.document_type_id.code not in ['01', '03', '05', '15', '16', '19', '08', 'LT']:
					rec.document_type_id = False
					rec.letter_state = False
				if rec.document_type_id.code in ['LT']:
					if rec.letter_state not in ['protest', 'portfolio']:
						if rec.letter_state:
							rec.letter_state = 'portfolio'
							rec.move_id = False
					domain += [('letter_state', '=', rec.letter_state)]
			if rec.letter_fact_id.operation_methods in ['collection', 'discount']:
				if rec.document_type_id.code not in ['LT']:
					rec.document_type_id = self.env.ref('qa_letter_management.document_type_lt1').id
					rec.letter_state = False
				if rec.document_type_id.code in ['LT']:
					if rec.letter_state not in ['protest', 'portfolio']:
						rec.letter_state = 'portfolio'
						rec.move_id = False
					domain += [('letter_state', '=', rec.letter_state)]
			if rec.letter_fact_id.operation_methods in ['return', 'protest']:
				if rec.document_type_id.code not in ['LT']:
					rec.document_type_id = self.env.ref('qa_letter_management.document_type_lt1').id
					if rec.letter_fact_id.operation_methods in ['return']:
						rec.letter_state = 'collection'
					if rec.letter_fact_id.operation_methods in ['protest']:
						rec.letter_state = 'portfolio'
				if rec.document_type_id.code in ['LT']:
					if rec.letter_fact_id.operation_methods in ['return']:
						if rec.letter_state not in ['collection', 'discount']:
							rec.letter_state = 'collection'
					if rec.letter_fact_id.operation_methods in ['protest']:
						if not rec.letter_state:
							rec.letter_state = 'portfolio'
					if rec.letter_fact_id.letter_det_ids[0].letter_state:
						if rec.letter_state != rec.letter_fact_id.letter_det_ids[0].letter_state:
							# rec.letter_state = False
							rec.letter_state = rec.letter_fact_id.letter_det_ids[0].letter_state
					domain += [('letter_state', '=', rec.letter_state)]
			if rec.move_id:
				# move.append('move_id.id')
				domain += [('move_id', '!=', rec.letter_fact_id.letter_det_ids.mapped('move_id.id'))]
			# if rec.document_number:
			#    rec.move_id =
			# if rec.move_id:
			# if not rec.document_type_id.code:
			#     rec.move_id = False
			if not rec.move_id:
				rec.paid_amount = 0.0
				rec.amount_payable = 0.0
				rec.new_amount_to_pay = 0.0
			# if not rec.partner_id
			return {'domain': {'move_id': domain}}
