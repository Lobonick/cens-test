# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountDebitNote(models.TransientModel):
	_inherit = "account.debit.note"

	pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Codigo SUNAT")
	l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Documento', domain=[('code', '=', '08')])

	@api.model
	def _get_pe_debit_note_type(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

	def _prepare_default_values(self, move):
		res = super()._prepare_default_values(move)
		journal_id = move.journal_id.id or res.get('journal_id')
		journal = self.env['account.journal'].browse(journal_id)
		l10n_latam_document_type_id = move.l10n_latam_document_type_id.nota_debito.id or res.get('l10n_latam_document_type_id')
		res.update({
			'journal_id': journal.id,
			'l10n_latam_document_type_id': l10n_latam_document_type_id,
			'origin_doc_code': self.pe_debit_note_code,
			'pe_debit_note_code': self.pe_debit_note_code,
			'pe_invoice_code': move.l10n_latam_document_type_id.nota_debito.code,
		})
		return res
