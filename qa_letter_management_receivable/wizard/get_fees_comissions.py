# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class FeesComissionsWizard(models.TransientModel):
    _name = "fees.comissions.wizard"
    _description = "Fees and Comission Wizard"

    def _get_rates(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        letter_management = self.env[active_model].search([('id','=',active_id)])
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
    # bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', compute='_get_protest_journal')
    bank_interests = fields.Float(string='Bank Interests', default=0)
    financial_expenses = fields.Float(string='Financial Expenses', default=0)
    _writeoff_account_id = fields.Many2one('account.account', string="Disbursment expense account", copy=False)
    is_destiny_account = fields.Boolean('Account has destiny', compute='_account_has_destiny')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytical Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    # total_discount_manual = fields.Boolean('Discount Manual')
    # total_discount_real = fields.Float(string='Discount Real')
    claim = fields.Boolean('Claim')
    claim_journal_id = fields.Many2one('account.journal', string='Claim Journal')   
    claim_account_id = fields.Many2one('account.account', string="Claim Account")  


    # @api.depends('exchange_date')
    # def _get_protest_journal(self):
    #     if self.env.context.get('protest'):
    #         active_id = self.env.context.get('active_id')
    #         active_model = self.env.context.get('active_model')
    #         letter_management = self.env[active_model].search([('id','=',active_id)])
    #         if letter_management.letter_det_ids[0].move_id.letter_create_id.journal_id_type_bank_id:
    #             self.bank_journal_id = letter_management.letter_det_ids[0].move_id.letter_create_id.journal_id_type_bank_id
    #     else:
    #         self.bank_journal_id = self.bank_journal_id

    @api.depends('_writeoff_account_id')
    def _account_has_destiny(self):
        self.is_destiny_account = self._writeoff_account_id.is_expense_account()

    @api.onchange('exchange_date')
    def onchange_reconcile_date(self):
        self.exchange_rate = self._get_rates()

    def get_fees_and_comissions(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Fees and Comission Wizard'),
            'res_model': 'fees.comissions.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('qa_letter_management_receivable.view_fees_comissions_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def send_expenses(self):
        
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        letter_management = self.env[active_model].search([('id','=',active_id)])
        letter_management.with_context(
            exchange_date=self.exchange_date,
            user_exchange_rate=self.user_exchange_rate,
            exchange_rate=self.exchange_rate,
            # bank_journal_id=self.bank_journal_id,
            bank_interests=self.bank_interests,
            financial_expenses=self.financial_expenses,
            _writeoff_account_id=self._writeoff_account_id,
            analytic_account_id=self.analytic_account_id,
            analytic_tag_ids=self.analytic_tag_ids,
            # total_discount_manual=self.total_discount_manual,
            # total_discount_real=self.total_discount_real,
            claim=self.claim,
            claim_journal_id=self.claim_journal_id,   
            claim_account_id=self.claim_account_id,
            )._create_fees_and_comissions_entry()