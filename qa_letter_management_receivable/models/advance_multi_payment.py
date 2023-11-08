from odoo import fields, models

class AccountMove(models.Model):
	_inherit = "account.move"

	def _get_account_for_payment(self):
		#res = super()._get_account_for_payment()
		res = self.line_ids.filtered(lambda l: l.debit > 0).account_id.id
		if self.is_invoice(include_receipts=True):
			if self.document_type_code == 'LT' and self.letter_state == 'discount':
				res = self.line_ids.filtered(lambda l: l.debit > 0).account_id.id
			else:
				res = self.line_ids.filtered(lambda l: l.debit > 0).account_id.id
		return res

""""
class AdvanceMultiPayment(models.Model):
	_inherit = 'advance.multi.payment'

	def _create_payment(self, rec, payment, payment_method_id):
		res = super()._create_payment(rec, payment, payment_method_id)                            
		# Si la letra esta en descuento entonces tambien cancelamos la cuenta de responsabilidad
		am = payment.move_id
		payment_id = self.env['account.payment']
		if am.document_type_code == 'LT' and am.letter_state == 'discount':
			pay_val = {
				'payment_type': 'outbound',
				'date': fields.Date.from_string(rec.date) if rec.date else False,
				'partner_type': 'supplier',
				'partner_id': payment.partner_id and payment.partner_id.id or False,
				'journal_id': rec.company_id.bridge_journal.id or False,
				'payment_method_id': payment_method_id.id or False,
				'currency_id': rec.currency_id and rec.currency_id.id or False,
				'amount': payment.paid_amount,
				'destination_account_id': am.line_ids.filtered(lambda l: l.credit > 0).account_id.id,
				'multipayment_id': rec.id,
				'ref': payment.move_id.name or False,
				# Nuevo
				'vv_type': rec.type,
			}
			if rec.other_currency:
				pay_val.update({
					'other_currency': rec.other_currency,
					'exchange_date': rec.exchange_date,
					'user_exchange_rate': rec.user_exchange_rate,
					'exchange_rate': rec.exchange_rate,
				})
			payment_id = self.env['account.payment'].create(pay_val)  # Se crea el pago en borrador
			payment_id.move_id.gloss = f'Multipagos {rec.id}'  # Adicion de Glosa de Multipagos
		if payment_id:
			res += payment_id
		return res

	def _get_credit_debit_payments(self, rec):
		# OVERRIDE
		# Evitamos que el asiento de reclacificación tenga el monto de los pagos de las responsabilidades
		responsibility_ids = self.env['account.journal'].search([('type','=','bank')]).mapped('responsibility_account_id.id')
		# Agregamos las cuentas de descuento que existen en homologación para evitar los pagos de letras en descuento
		responsibility_ids += self.env['account.update'].search([('letter_state', '=', 'discount')]).mapped('account_id.id')
		payment_credit = rec.individuals_payments_ids.filtered(lambda p: p.destination_account_id.id not in responsibility_ids).mapped('invoice_line_ids.credit')
		payment_debit = rec.individuals_payments_ids.filtered(lambda p: p.destination_account_id.id not in responsibility_ids).mapped('invoice_line_ids.debit')
		return payment_credit, payment_debit

	def _get_mapped_payments(self, rec):
		# OVERRIDE
		# Evitamos el monto de las letras en descuento
		payments_to_map = self.env['advance.multi.move.line']
		for payment in rec.payment_ids:
			if payment.move_id.document_type_code != 'LT' or payment.move_id.document_type_code == 'LT' and payment.move_id.letter_state != 'discount':
				payments_to_map += payment
		return payments_to_map.mapped('paid_amount')

"""