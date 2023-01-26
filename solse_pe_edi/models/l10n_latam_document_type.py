# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)


class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'

	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	is_cpe = fields.Boolean('Es un CPE', help="Es un comprobante electronico")
	sub_type = fields.Selection([('sale', 'Ventas'), ('purchase', 'Compras')], string="Sub tipo")
	is_synchronous = fields.Boolean("Es sincrono", default=True)
	is_synchronous_anull = fields.Boolean("Anulación sincrona", default=True)
	nota_credito = fields.Many2one('l10n_latam.document.type', string='Nota credito', domain=[('code', '=', '07')])
	nota_debito = fields.Many2one('l10n_latam.document.type', string='Nota debito', domain=[('code', '=', '08')])
	usar_prefijo_personalizado = fields.Boolean('Personalizar prefijo')
	prefijo = fields.Char('Prefijo', copy=False)
	correlativo_inicial = fields.Integer('Correlativo inicial', default=1, help="Correlativo usado para el primer comprobante emitidio con este tipo de documento")
	secuencia_id = fields.Many2one("ir.sequence", string="Secuencia", copy=False)
	sequence_number_next = fields.Integer(string='Número siguiente',
		help='El siguiente número de secuencia se utilizará para el proximo comprobante.',
		compute='_compute_seq_number_next',
		inverse='_inverse_seq_number_next')

	@api.depends('secuencia_id.use_date_range', 'secuencia_id.number_next_actual')
	def _compute_seq_number_next(self):
		for reg in self:
			if reg.secuencia_id:
				sequence = reg.secuencia_id._get_current_sequence()
				reg.sequence_number_next = sequence.number_next_actual
			else:
				reg.sequence_number_next = 1

	def _inverse_seq_number_next(self):
		'''Invierta 'sequence_number_next' para editar el siguiente número de la secuencia actual.
		'''
		for reg in self:
			if reg.secuencia_id and reg.sequence_number_next:
				sequence = reg.secuencia_id._get_current_sequence()
				sequence.sudo().number_next = reg.sequence_number_next

	@api.model
	def create(self, vals):
		if not vals.get('secuencia_id') and vals.get('usar_prefijo_personalizado') and vals.get('prefijo'):
			vals.update({'secuencia_id': self.sudo()._create_sequence(vals).id})

		rpt = super(L10nLatamDocumentType, self).create(vals)
		return rpt

	def crear_secuencia(self):
		if not self.prefijo:
			raise UserError("No tiene un prefijo establecido")
		if self.usar_prefijo_personalizado and not self.secuencia_id and self.prefijo:
			datos_prefijo = {'prefijo': self.prefijo}
			ultimo_numero = self.obtener_ultimo_numero()
			if ultimo_numero:
				datos_prefijo['sequence_number_next'] = ultimo_numero + 1
			seq = self._create_sequence(datos_prefijo)
			self.secuencia_id = seq

	def obtener_ultimo_numero(self):
		facturas = self.env['account.move'].search([('state', '!=', 'draft'), ('l10n_latam_document_type_id', '=', self.id), ('l10n_latam_document_number', '!=', False)], order="sequence_number desc", limit=1)
		if facturas:
			if not facturas[0].l10n_latam_document_number:
				return 0
			serie = facturas[0].l10n_latam_document_number
			numero = serie.split("-")[1]
			return int(numero) if numero else 0
		return 0

	def reasignar_ultimo_numero(self):
		facturas = self.env['account.move'].search([('state', '!=', 'draft'), ('l10n_latam_document_type_id', '=', self.id), ('l10n_latam_document_number', '!=', False)], order="sequence_number desc", limit=1)
		if not facturas:
			self.sequence_number_next = 1
			return

		if not facturas[0].l10n_latam_document_number:
			self.sequence_number_next = 1
			return

		serie = facturas[0].l10n_latam_document_number
		numero = serie.split("-")[1]
		self.sequence_number_next = int(numero) + 1
			

	@api.model
	def _get_sequence_prefix(self, code):
		prefix = code.upper()
		return prefix + '-'

	@api.model
	def _create_sequence(self, vals):
		""" Create new no_gap entry sequence for every new Journal"""
		prefix = self._get_sequence_prefix(vals['prefijo'])
		seq_name = vals['prefijo']
		seq = {
			'name': '%s Secuencia' % seq_name,
			'implementation': 'no_gap',
			'prefix': prefix,
			'padding': 8,
			'number_increment': 1,
			'use_date_range': False,
		}
		if 'company_id' in vals:
			seq['company_id'] = vals['company_id']
		seq = self.env['ir.sequence'].create(seq)
		seq_date_range = seq._get_current_sequence()
		seq_date_range.number_next = vals.get('sequence_number_next', 1)
		return seq

