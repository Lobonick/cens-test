from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = 'account.move'

	unique_code = fields.Char(string='Unique Code')
	amount_discount = fields.Monetary(string='Discount')
	new_bank_id = fields.Many2one('res.bank', string='Send to Bank')
	renewal_ids = fields.One2many('account.move', 'origin_id', string='Renewals')
	origin_id = fields.Many2one('account.move', string='Origin')
	payment_state = fields.Selection(selection_add=[('responsibility', 'Responsibility')], ondelete={'responsibility': 'set null'})
	third_party = fields.Boolean('Is third party letter?', compute='_is_third_party', store=True)

	@api.depends('acceptor_id','partner_id')
	def _is_third_party(self):
		for rec in self:
			if rec.partner_id != rec.acceptor_id:
				rec.third_party = True

	@api.onchange('letter_amount')
	def _onchange_amount_letter_line(self):
		for rec in self:
			if rec.letter_create_id.operation_methods in ['portfolio', 'refinancing']:
				if rec.letter_amount != rec.amount_total:
					rec._inverse_first_amount()
					if not rec.exchange_rate:
						# if rec.line_ids[1].debit == 0 and rec.line_ids[1].credit:
						#     rec.line_ids[1].debit = rec.letter_amount
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
			if rec.debit_create_id.operation_methods in ['renewal', 'refinancing']:
				if not rec.debit_create_id._tax_ids_debit:
					# if rec.debit_create_id.is_debit_generated:
					rec.amount_total = rec.letter_amount
					rec.line_ids[1].debit = rec.letter_amount
				# else:
				#     rec.letter_
				# else:
				#     if rec.debit_create_id._tax_ids_debit
			# if rec.letter_create_id.operation_methods not in ['discount']:
			rec.with_context(check_move_validity=False)._onchange_currency()

	@api.onchange('amount_discount')
	def _compute_discount(self):
		res = super()._compute_discount()
		for rec in self:
			if rec.letter_create_id.operation_methods in ['discount']:
				rec.letter_amount = 0.0
				if rec.invoice_line_ids:
					rec.invoice_line_ids[0].price_unit = 0.0
				if rec.amount_discount != 0:
					discount = abs(rec.amount_discount)
					rec.amount_discount = -discount
					# rec.amount_discount = rec.currency_id.round(-discount)
					# rec.letter_amount = rec.currency_id.round(rec.amount_letter - discount)
				else:
					rec.amount_discount = 0
				############## POLIMASTER ################
				# No descontar
				# rec.letter_amount = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
				rec.letter_amount = rec.currency_id.round(rec.amount_letter)
				rec._inverse_first_amount()
			rec.with_context(check_move_validity=False)._onchange_currency()

		return res

	@api.depends('invoice_line_ids.price_unit')
	def _compute_first_amount(self):
		for rec in self:
			# rec.letter_amount = 0.0
			if rec.invoice_line_ids:
				if rec.letter_create_id.operation_methods in ['discount']:
					############## POLIMASTER ################
					# No descontar
					# disc = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
					disc = rec.currency_id.round(rec.amount_letter)
					rec.invoice_line_ids[0].price_unit = disc
				# else:
				precio_unit = rec.invoice_line_ids[0].price_unit
				rec.letter_amount = rec.currency_id.round(precio_unit)

	def _inverse_first_amount(self):
		for rec in self:
			# print(rec.invoice_line_ids)
			# if rec.invoice_line_ids:
			if rec.document_type_code in ['LT']:
				if rec.invoice_line_ids:
					# if rec.move_type in ['out_invoice']:
					rec.amount_residual = 0
					if rec.letter_create_id.operation_methods in ['discount']:
						############## POLIMASTER ################
						# No descontar
						# precio_unit = rec.currency_id.round(rec.amount_letter - abs(rec.amount_discount))
						precio_unit = rec.currency_id.round(rec.amount_letter)
						# rec.invoice_line_ids[0].price_unit = precio_unit
					else:
						precio_unit = rec.currency_id.round(rec.letter_amount)

					rec.invoice_line_ids[0].price_unit = precio_unit
					rec.with_context(check_move_validity=False)._onchange_currency()
			# else:
			#     rec.asign_products_to_letter()
	
	# Para dejar de mostrar el pago de la letra y solo el de la responsabilidad en las eltras en descuento
	def _get_reconciled_invoices_partials(self):
		res = super()._get_reconciled_invoices_partials()
		lines_to_remove = []
		for line in res:
			# Este if solo sirve para las letras de saldos iniciales que no tienen letter_create_id
			# if self.letter_create_id:
			#     if len(res) > 1 and self.letter_state == 'discount' and line[2].account_id  == self.letter_create_id.journal_id_type_bank_id.responsibility_account_id:
			#         lines_to_remove.append(line)
			# else:
			if len(res) > 1 and self.letter_state == 'discount' and line[2].account_id  == self.line_ids.filtered(lambda l: l.credit > 0).account_id:
				lines_to_remove.append(line)
		for line in lines_to_remove:
			res.remove(line)
		return res
	
	# Para borrar la conciliacion tambien de la letra y no solo la responsabilidad
	def js_remove_outstanding_partial(self, partial_id):
		partial = self.env['account.partial.reconcile'].browse(partial_id)
		credit_move = self.env['account.move'].browse(partial.credit_move_id.move_id.id)
		debit_move = self.env['account.move'].browse(partial.debit_move_id.move_id.id)
		if credit_move.document_type_code == 'LT' and credit_move.letter_state == 'discount':
			raise UserError(_('Can\'t unreconcile this payment because it\'s a letter discount payment. Please try to cancel the payment move first.'))
		res = super().js_remove_outstanding_partial(partial_id)
		# if debit_move.document_type_code == 'LT' and debit_move.letter_state == 'discount':
		#     (debit_move.line_ids.matched_debit_ids + debit_move.line_ids.matched_credit_ids).unlink()
		return res

	# def js_assign_outstanding_line(self, line_id):
	#     res = super().js_assign_outstanding_line(line_id)
	#     if self.document_type_code == 'LT' and self.letter_state == 'discount' and self._context.get():
	#         line = self.env['account.move.line'].browse(line_id)
	#         lines = line.payment_id.move_id.line_ids.filtered(lambda l: l.account_id == self.invoice_line_ids.account_id)
	#         lines += self.invoice_line_ids
	#         lines.reconcile()
	#     return res

	def action_register_payment(self):
		res = super().action_register_payment()
		last_journal = self.env['account.journal']
		for move in self:
			if move.document_type_code == 'LT' and move.letter_state == 'discount' and move.move_type != 'in_invoice' and move.payment_state != 'responsibility':
				# Este if solo sirve para las letras de saldos iniciales que no tienen letter_create_id
				if not move.letter_create_id or move.origin_id:
					current_journal = self.env['account.journal'].search([('responsibility_account_id','=', move.line_ids.filtered(lambda l: l.credit > 0).account_id.id)]).id
				else:
					current_journal = move.letter_create_id.journal_id_type_bank_id.id
					if last_journal and last_journal != current_journal:
						raise UserError(_('Can\'t pay letters from diferent banks at once.'))
				last_journal = current_journal
				res['context']['default_journal_id'] = last_journal
				res['context']['is_letter'] = True
		return res

	############## POLIMASTER ################
	# Funcion para cambiar el estado del pago solo cuando la responsabilidad se paga por separado
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
			new_pmt_state = move.payment_state
			if move.document_type_code == 'LT' and move.letter_state == 'discount':
				if not move.line_ids.filtered(lambda l: l.credit > 0).reconciled and move.amount_residual == 0:
					new_pmt_state = 'responsibility'
			move.payment_state = new_pmt_state
		return res