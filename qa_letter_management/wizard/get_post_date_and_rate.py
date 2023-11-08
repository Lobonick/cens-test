# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.tools import float_round
import logging
_logger = logging.getLogger(__name__)

class DateRateWizard(models.TransientModel):
	_name = "date.rate.wizard"
	_description = "Date and rate Wizard"

	# def _get_exchange_rate(self, amount, currency, company, date):
	#     active_id = self.env.context.get('active_id')
	#     active_model = self.env.context.get('active_model')
	#     letter_management = self.env[active_model].search([('id','=',active_id)])
	#     return letter_management.currency_id._convert(amount, currency, company, date, False)

	def _get_rates(self):
		_logger.info("**************************************** _get_rates")
		_logger.info(self.env.context)
		active_id = self.env.context.get('active_id')
		active_model = self.env.context.get('active_model')
		letter_management = self.env[active_model].search([('id','=',active_id)])
		# rate = letter_management.currency_id._convert(1, letter_management.company_id.currency_id, letter_management.company_id, self.reconcile_date or datetime.now(), False)
		domain = [('currency_id.id', '=', letter_management.currency_id.id),
					('name', '=', fields.Date.to_string(self.exchange_date)),
					('company_id.id', '=', letter_management.company_id.id)]
		currency = self.env['res.currency.rate'].search(domain, limit=1)
		if letter_management.other_currency:
			if currency:
				return currency.rate_pe
			else:
				self.exchange_date = False
				return 0

	exchange_date = fields.Date(string='Date', default=fields.Date.context_today)
	user_exchange_rate = fields.Boolean(string="Exchange Rate User")
	exchange_rate = fields.Float(string="Exchange rate", digits='Exchange rate', store=True, readonly=False, default=_get_rates)
	bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', compute='_get_protest_journal')
	bank_interests = fields.Float(string='Bank Interests', default=0)
	financial_expenses = fields.Float(string='Financial Expenses', default=0)
	_writeoff_account_id = fields.Many2one('account.account', string="Interests and Expenses Account", copy=False)
	is_destiny_account = fields.Boolean('Account has destiny', compute='_account_has_destiny')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Analytical Account')
	analytic_tag_ids = fields.Many2many('account.analytic.plan', string='Analytic Plan')
	
	@api.depends('exchange_date')
	def _get_protest_journal(self):
		_logger.info("**************************************** _get_protest_journal")
		_logger.info(self.env.context)
		if self.env.context.get('protest'):
			active_id = self.env.context.get('active_id')
			active_model = self.env.context.get('active_model')
			letter_management = self.env[active_model].search([('id','=',active_id)])
			# if letter_management.letter_det_ids[0].move_id.letter_create_id:
			#     if letter_management.letter_det_ids[0].move_id.origin_id.letter_create_id.journal_id_type_bank_id:
			#         self.bank_journal_id = letter_management.letter_det_ids[0].move_id.origin_id.letter_create_id.journal_id_type_bank_id
			# else:
			account_id = letter_management.letter_det_ids[0].move_id.invoice_line_ids.account_id
			self.bank_journal_id = self.env['account.journal'].search([('responsibility_account_id','=', account_id.id)], limit=1)
		else:
			self.bank_journal_id = self.bank_journal_id

	@api.depends('_writeoff_account_id')
	def _account_has_destiny(self):
		self.is_destiny_account = self._writeoff_account_id.is_expense_account()

	@api.onchange('exchange_date')
	def onchange_reconcile_date(self):
		self.exchange_rate = self._get_rates()

	def get_post_date_and_rate(self):
		_logger.info("**************************************** get_post_date_and_rate")
		_logger.info(self.env.context)
		active_id = self.env.context.get('active_id')
		if not active_id:
			return ''

		return {
			'name': _('Date and rate Wizard'),
			'res_model': 'date.rate.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('qa_letter_management.view_date_rate_wizard_form').id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def enviar_registro(self):
		_logger.info("enviar registroooooooooooooooo")

	def send_expenses(self):
		_logger.info("**************************************** send_expenses")
		_logger.info(self._context)

		active_id = self._context.get('active_id')
		active_model = self._context.get('active_model')
		letter_management = self.env[active_model].search([('id','=',active_id)])
		letter_management.with_context(
			exchange_date=self.exchange_date,
			user_exchange_rate=self.user_exchange_rate,
			exchange_rate=self.exchange_rate,
			bank_journal_id=self.bank_journal_id,
			bank_interests=self.bank_interests,
			financial_expenses=self.financial_expenses,
			#_writeoff_account_id=self._writeoff_account_id,
			analytic_account_id=self.analytic_account_id,
			analytic_tag_ids=self.analytic_tag_ids,
			)._exchange_process_after()

	def send_expenses_n2(self):
		_logger.info("**************************************** send_expenses_n2")
		"""_logger.info(self._context)

		active_id = self._context.get('active_id')
		active_model = self._context.get('active_model')
		letter_management = self.env[active_model].search([('id','=',active_id)])
		letter_management.with_context(
			exchange_date=self.exchange_date,
			user_exchange_rate=self.user_exchange_rate,
			exchange_rate=self.exchange_rate,
			bank_journal_id=self.bank_journal_id,
			bank_interests=self.bank_interests,
			financial_expenses=self.financial_expenses,
			#_writeoff_account_id=self._writeoff_account_id,
			analytic_account_id=self.analytic_account_id,
			analytic_tag_ids=self.analytic_tag_ids,
		)._exchange_process_after()"""