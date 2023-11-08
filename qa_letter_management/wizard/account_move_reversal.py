from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
	"""Credit Notes"""
	_inherit = "account.move.reversal"

	@api.model
	def default_get(self, fields):
		res = super(AccountMoveReversal, self).default_get(fields)
		move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
			'active_model') == 'account.move' else self.env['account.move']
		if move_ids.seat_generated_id:
			for letter in move_ids.seat_generated_id.list_letters_ids:
				if letter.have_letters_generated_id and letter.amount_residual != 0:
					raise UserError(_('One of the letters on the template ') + str(move_ids.seat_generated_id.id) + _(
						', has generated letters.\n') + _('To reverse the payment entry you need:\n'
														  'Create internal credit notes for each letter posted. When the amount owed\n'
														  'for these letters is 0, you can make the reversal of the payment entry.\n') +
									_(
										'But if these Published letters have letters generated in another template, revert your payment entry first.'))
				if not letter.have_letters_generated_id and letter.amount_residual > 0:
					raise UserError(
						_('The letter template No. ') + str(move_ids.seat_generated_id.id) + _(
							', has generated letters.\n') + _('To reverse the payment entry you need:\n'
															  'Create internal credit notes for each letter posted. When the amount owed\n'
															  'for these letters is 0, you can make the reversal of the payment entry.\n'))
		res['refund_method'] = (len(move_ids) > 1 or move_ids.move_type == 'entry') and 'cancel' or 'refund'
		res['residual'] = len(move_ids) == 1 and move_ids.amount_residual or 0
		res['currency_id'] = len(move_ids.currency_id) == 1 and move_ids.currency_id.id or False
		res['move_type'] = len(move_ids) == 1 and move_ids.move_type or False
		res['move_ids'] = [(6, 0, move_ids.ids)] if move_ids else False
		return res
