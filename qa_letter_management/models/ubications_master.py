from odoo import _, api, fields, models
from odoo.exceptions import UserError

STATE_DOC_SELECTION = [('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancelled')]
LETTER_STATE_SELECTION = [('portfolio', 'In portfolio'), ('collection', 'In collection'),
						  ('warranty', 'In warranty'), ('discount', 'In discount'), ('protest', 'In protest')]


class MasterUbications(models.Model):
	_name = 'letter.masterlocations'
	_description = 'Maestro de ubicaciones'

	name = fields.Char(string='Location status')
	require_attach_document = fields.Boolean(string='Require attach document', default=False)


class AccountUbicationsLetter(models.Model):
	_name = 'letter.locations'
	_description = 'Lineas de seguimiento de letras'

	invoice_user_id = fields.Many2one('res.users', copy=False, string='Salesperson', default=lambda self: self.env.user)
	state_tracing = fields.Many2one(comodel_name='letter.masterlocations', string='Status tracing', ondelete="restrict")
	doc_letters_id = fields.Many2one('account.move', string='Docs letter')
	document_type_id = fields.Many2one('l10n_latam.document.type', 'Document type')

	locations_line_ids = fields.One2many('letter.locations.line', 'letter_location_id', string='Invoices')

	date_tracing = fields.Date(string='Date Tracing', required=True, copy=False,
							   default=lambda s: fields.Date.context_today(s))

	commentary = fields.Text(string='Commentary')

	# Envio y aceptacion
	send_date = fields.Date(string='Shipping date')
	acceptance_date = fields.Date(string='Acceptance Date')

	move_type = fields.Selection(selection=[
		('entry', 'Journal Entry'),
		('out_invoice', 'Customer Invoice'),
		('out_refund', 'Customer Credit Note'),
		('in_invoice', 'Vendor Bill'),
		('in_refund', 'Vendor Credit Note'),
		('out_receipt', 'Sales Receipt'),
		('in_receipt', 'Purchase Receipt')], string="Type")

	require_attach_document = fields.Boolean(string='Require attach document',
											 related='state_tracing.require_attach_document')
	tracing_created = fields.Boolean(string='Tracing created', default=False)

	attachment_id = fields.Many2many('ir.attachment', string="Attachment Documents", required=True, ondelete='cascade')

	@api.model
	def default_get(self, fields):
		res = super(AccountUbicationsLetter, self).default_get(fields)
		inv_ids = self._context.get('active_ids')
		vals = []
		invoice_ids = self.env['account.move'].browse(inv_ids)
		if invoice_ids:
			# if invoice_ids.mapped('document_type_id.code') != ['LT']:
			#     raise UserError(_('Only select documents of type Letters >> with status: Draft or Posted <<'))
			for inv in invoice_ids:
				vals.append((0, 0, {
					'move_id': inv and inv.id or False,
					'invoice_date': inv.invoice_date or False,
					'send_date': inv.send_date or False,
					'acceptance_date': inv.acceptance_date or False,
					'letter_state': inv.letter_state or False,
					'state_doc': inv.state or False
					}))
				res.update({
					'locations_line_ids': vals,
					'document_type_id': self.env.ref('qa_letter_management.document_type_lt1').id,
					'move_type': invoice_ids.mapped('move_type')[0]
					})
		# if res['move_type']
		res.update({
			'document_type_id': self.env.ref('qa_letter_management.document_type_lt1').id,
			'move_type': 'out_invoice',
			})
		return res

	@api.constrains('commentary', 'attachment_id')
	def _constrains_tracing(self):
		for rec in self:
			# if not rec.commentary:
			#     raise UserError(_('Write a commentary'))
			if rec.require_attach_document:
				if not rec.attachment_id:
					raise UserError(_('Attach a document for follow-up'))

	def add_tracing(self):
		for rec in self:
			self.ensure_one()
			_tracing_ids = []
			if len(list(rec.locations_line_ids.mapped('move_id.id'))) < 1:
				raise UserError(_('There are no documents to comment'))
			if rec.tracing_created:
				raise UserError(_('The comment is already created'))
			if not rec.state_tracing:
				raise UserError(_('Select a tracking status'))
			s_date = fields.Date.from_string(rec.send_date)
			a_date = fields.Date.from_string(rec.acceptance_date)
			if s_date != False or a_date != False:
				rec.add_send_and_acceptance_date()
			# if s_date > a_date:
			#     raise UserError(_('The acceptance date cannot be less than the shipping date'))
			for line in rec.locations_line_ids:
				if line.move_id.move_type != rec.move_type:
					raise UserError(_('Customer letters only'))

				# a_date = rec.acceptance_date.strftime('%Y-%m-%d')
				# if line.move_id.send_date and line.move_id.acceptance_date:
			if rec.state_tracing:
				_tracing_ids.append((0, 0, {
					'state_tracing': rec.state_tracing.id,
					'invoice_user_id': rec.invoice_user_id.id,
					'commentary': rec.commentary or '',
					'require_attach_document': rec.require_attach_document,
					'attachment_id': rec.attachment_id and rec.attachment_id.ids or False,
					'tracing_created': True,
					}))
				rec.locations_line_ids.move_id.write({
					'tracing_ids': _tracing_ids})

	def add_send_and_acceptance_date(self):
		for rec in self:
			s_date = False
			a_date = False
			for line in rec.locations_line_ids:
				s_date = fields.Date.from_string(rec.send_date)
				a_date = fields.Date.from_string(rec.acceptance_date)
				# a_date = rec.acceptance_date.strftime('%Y-%m-%d')
				if rec.send_date and rec.acceptance_date:
					if s_date > a_date:
						raise UserError(_('The acceptance date cannot be less than the shipping date'))
				if rec.send_date:
					line.send_date = rec.send_date
				if rec.acceptance_date:
					line.acceptance_date = rec.acceptance_date


class GetLetters(models.Model):
	_name = 'letter.locations.line'
	_description = 'letter locations line'
	letter_location_id = fields.Many2one('letter.locations', string='Location - commentary')

	move_id = fields.Many2one('account.move', string='Invoice')

	invoice_date = fields.Date(string='Emission Date', related='move_id.invoice_date', readonly=True)
	send_date = fields.Date(string='Send Date', related='move_id.send_date', readonly=False)
	acceptance_date = fields.Date(string='Acceptance Date', related='move_id.acceptance_date', readonly=False)

	letter_state = fields.Selection(LETTER_STATE_SELECTION, string='Letter State', related='move_id.letter_state')
	state_doc = fields.Selection(STATE_DOC_SELECTION, related='move_id.state', string='State')

	@api.onchange('send_date', 'acceptance_date')
	def _onchange_date_send_acceptance(self):
		for rec in self:
			# for line in rec.locations_line_ids:
			if rec.send_date:
				rec.move_id.send_date = rec.send_date
			if rec.acceptance_date:
				rec.move_id.acceptance_date = rec.acceptance_date