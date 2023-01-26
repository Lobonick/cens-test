# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
_logging = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
	_inherit = "account.move.reversal"

	pe_credit_note_code = fields.Selection(selection="_get_pe_crebit_note_type", string="Codigo SUNAT")
	l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Documento', domain=[('code', '=', '07')])
	fecha_nota_credito_proveedor = fields.Date("Fecha emisión del Proveedor")
	payment_reference = fields.Char("Nota de crédito del proveedor")

	@api.model
	def _get_pe_crebit_note_type(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

	@api.model
	def _get_pe_debit_note_type(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

	def reverse_moves(self):
		res = super(AccountMoveReversal, self).reverse_moves()
		if self.env.context.get("is_pe_debit_note", False):
			invoice_domain = res['domain']
			if invoice_domain:
				del invoice_domain[0]
				res['domain'] = invoice_domain
		return res

	def _prepare_default_reversal(self, move):
		reverse_date = self.date if self.date_mode == 'custom' else move.date
		l10n_latam_document_type_id = move.l10n_latam_document_type_id.nota_credito
		reverse_date = self.date if self.date_mode == 'custom' else move.date
		datos_retorno = {
			'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason)
				   if self.reason
				   else _('Reversal of: %s', move.name),
			'date': reverse_date,
			'invoice_date_due': reverse_date,
			'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
			'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
			'l10n_latam_document_type_id': l10n_latam_document_type_id.id,
			'pe_credit_note_code': self.pe_credit_note_code or move.pe_credit_note_code,
			'invoice_payment_term_id': None,
			'invoice_user_id': move.invoice_user_id.id,
			'auto_post': 'at_date' if reverse_date > fields.Date.context_today(self) else 'no',
			'move_type': 'in_refund',
		}

		if move.move_type == 'in_invoice':
			datos_retorno['fecha_nota_credito_proveedor'] = self.fecha_nota_credito_proveedor
			datos_retorno['payment_reference'] = self.payment_reference

		return datos_retorno