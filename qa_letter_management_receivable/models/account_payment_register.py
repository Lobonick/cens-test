from odoo import models, api, fields, _

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # only_responsibility = fields.Boolean(string='Only responsability')
    # is_discount_letter = fields.Boolean(string='Is discount letter?')

    def _create_payments(self):
        res = super(AccountPaymentRegister, self.with_context(skip_account_move_synchronization=True))._create_payments()
        # Si el check es falso cancelar las dos lineas
        # de lo contrario solo cancelar la responsabilidad
        for payment in res:
            move_id = payment.reconciled_invoice_ids
            if len(move_id) > 1:
                return res
            if move_id.document_type_code == 'LT':
                if move_id.payment_state != 'paid':
                    if len(move_id) == 1 and move_id.letter_state and move_id.letter_state == 'discount':
                        line_id = payment.line_ids.filtered(lambda l: l.account_id.user_type_id.type not in ('receivable','payable'))
                        # Este if solo sirve para las letras de saldos iniciales que no tienen letter_create_id
                        # if move_id.letter_create_id:
                        #     line_id.account_id = move_id.line_ids.filtered(lambda l: l.account_id != move_id.letter_create_id.journal_id_type_bank_id.responsibility_account_id).account_id
                        # else:
                        line_id.account_id = move_id.line_ids.filtered(lambda l: l.debit > 0).account_id
                        # move_id.payment_state = 'paid'
                        aux = payment.destination_account_id
                        payment.payment_type = 'inbound'
                        payment.partner_type = 'customer'
                        payment.destination_account_id = aux
                        line_id += move_id.line_ids.filtered(lambda l: l.account_id == line_id.account_id) #move_id.letter_create_id.move_expenses_id.line_ids.filtered(lambda l: l.account_id == line_id.account_id)
                        line_id.reconcile()
                    if move_id.document_type_code == 'LT':
                        aux = payment.destination_account_id
                        payment.partner_id = move_id.acceptor_id
                        payment.move_id.line_ids.partner_id = move_id.acceptor_id
                        payment.destination_account_id = aux
                else:
                    payment.ref += _(' Only responsibility')
        return res
    
    @api.model
    def default_get(self, fields_list):
        moves = self.env['account.move'].browse(self._context.get('active_ids', []))
        line_ids = self.env['account.move.line']
        for move in moves:
            if move.document_type_code == 'LT' and move.letter_state == 'discount':
                # # Este if solo sirve para las letras de saldos iniciales que no tienen letter_create_id
                # if move.letter_create_id:
                #     # Si es una renovacion y no tiene el campo journal_id_type_bank_id
                #     # buscamos la letra origen y de ahi sacamos el campo
                #     responsibility_account_id = move.letter_create_id.journal_id_type_bank_id.responsibility_account_id or move.origin_id.letter_create_id.journal_id_type_bank_id.responsibility_account_id
                #     line_ids += move.line_ids.filtered(lambda l: l.account_id == responsibility_account_id)   
                # else:
                line_ids += move.line_ids.filtered(lambda l: l.credit > 0) 
            else:
                line_ids += move.line_ids.filtered(lambda l: l.account_id.account_type in ['asset_receivable', 'liability_payable'])
        if any(move.document_type_code == 'LT' and move.letter_state == 'discount' for move in moves):
            res = super(AccountPaymentRegister, self.with_context(active_model='account.move.line', active_ids=line_ids.ids)).default_get(fields_list)
        else:
            res = super().default_get(fields_list)
        return res

    # @api.model
    # def _get_line_batch_key(self, line):
    #     res = super()._get_line_batch_key(line)
    #     if line.move_id.document_type_code == 'LT' and line.move_id.letter_state == 'discount':
    #         res['partner_type'] = 'customer'
    #         res['payment_type'] = 'inbound'
    #     return res

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _seek_for_lines(self):
        res = super()._seek_for_lines()
        self.ensure_one()
        liquidity_lines = self.env['account.move.line']
        for line in self.move_id.line_ids:
            if line.account_id in (self.journal_id.responsibility_account_id) and not line.move_id.payment_id:
                liquidity_lines += line
        res_new = list(res)
        res_new[0] += liquidity_lines
        for l in res_new[1]:
            if l in res_new[0]:
                res_new[1] -= l
        res_new = tuple(res_new)
        return res_new