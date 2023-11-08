from odoo import models, api  # , fields, _


# from odoo.exceptions import UserError,RedirectWarning

class AccountMove(models.Model):
	_inherit = 'account.move'

	# advanced_payment_to_apply_id = fields.Many2one('account.move', string='Advanced Payment to Apply')

	@api.onchange('l10n_latam_document_type_id')
	def _onchange_document_type_id(self):
		#super(AccountMove, self)._onchange_document_type_id()
		if self.l10n_latam_document_type_id.code == 'LT' and self.is_purchase_document:
			self.acceptor_id = self.env.company.partner_id

	# def action_post(self):
	#     # Si se dan todas estas condiciones es un anticipo de proveedor que
	#     # entonces debe crear un asiento para poder aplicar a las facturas
	#     for rec in self:
	#         if rec.document_type_id.code == 'LT' and not rec.have_letters_generated_id and rec.is_purchase_document():
	#             rec._create_advanced_payment_to_apply()
	#     return super(AccountMove, self).action_post()

	# def _create_advanced_payment_to_apply(self):
	#     advanced_payment_account_id = self.env['account.update'].search([('anticipo_provider','=', True),('currency_id','=', self.currency_id.id),('transaction_type','=','is_purchase_document')]).account_id.id
	#     if not advanced_payment_account_id:
	#         action = self.env.ref('qa_standard_locations_account.account_update_action')
	#         msg = _('The account for advanced payments is not configured in homologation for provider. Please add an advanced payment account for %s') %self.currency_id.name
	#         raise RedirectWarning(msg, action.id, _('Go to Homologation'))
	#     reversed_move = self._reverse_move_vals({}, False)
	#     for line in reversed_move['line_ids']:
	#         account_id = self.env['account.account'].search([('id','=',line[2]['account_id'])])
	#         if not account_id.user_type_id.type not in ('receivable', 'payable'):
	#             line[2]['account_id'] = advanced_payment_account_id
	#     reversed_move.update({'move_type': 'entry', 'type_purchase': False, 'refund_invoice_sunat_serie': '', 'refund_invoice_sunat_number': '', })
	#     self.advanced_payment_to_apply_id = self.env['account.move'].create(reversed_move)
	#     self.advanced_payment_to_apply_id.post()

	# def button_draft(self):
	#     res = super(AccountMove, self).button_draft()
	#     reverted_advanced_payment = self.env['account.move'].search([('state', 'in', ['posted']),
	#                                                     ('move_type', '=', 'entry'),
	#                                                     ('reversed_entry_id', '=', self.advanced_payment_to_apply_id.id)], limit=1)
	#     if self.advanced_payment_to_apply_id and reverted_advanced_payment or self.advanced_payment_to_apply_id.state == 'cancel':
	#         if self.advanced_payment_to_apply_id:
	#             self.advanced_payment_to_apply_id.button_draft()
	#             self.advanced_payment_to_apply_id.with_context(force_delete=True).unlink()
	#     else:
	#         if self.advanced_payment_to_apply_id:
	#             raise UserError(_('You must revert the advanced payment to apply first.'))
	#         # if self.advanced_payment_to_apply_id:
	#         #     self.advanced_payment_to_apply_id.button_draft()
	#         #     self.advanced_payment_to_apply_id.with_context(force_delete=True).unlink()
	#     return res
