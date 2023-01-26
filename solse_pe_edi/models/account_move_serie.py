# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
import re
_logging = logging.getLogger(__name__)

 
class AccountMoveSerie(models.Model):
	_inherit = 'account.move'

	es_primera_en_secuencia = fields.Boolean("Es primera en secuencia")

	def _must_check_constrains_date_sequence(self):
		if self.l10n_latam_document_type_id.usar_prefijo_personalizado:
			return False
		return True

	def _is_manual_document_number(self):
		#return self.journal_id.type == 'purchase'
		return False

	def _get_last_sequence_domain(self, relaxed=False):
		self.ensure_one()
		if not self.date or not self.journal_id:
			return "WHERE FALSE", {}

		if self.usar_prefijo_personalizado and self.l10n_latam_document_type_id:
			where_string = " WHERE company_id = %(company_id)s AND name != '/'"
			param = {'company_id': self.company_id.id}
			where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
			param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id
			return where_string, param

		where_string = "WHERE journal_id = %(journal_id)s AND name != '/'"
		param = {'journal_id': self.journal_id.id}

		if not relaxed:
			domain = [('journal_id', '=', self.journal_id.id), ('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', '', False))]
			if self.journal_id.refund_sequence:
				refund_types = ('out_refund', 'in_refund')
				domain += [('move_type', 'in' if self.move_type in refund_types else 'not in', refund_types)]
			reference_move_name = self.search(domain + [('date', '<=', self.date)], order='date desc', limit=1).name
			if not reference_move_name:
				reference_move_name = self.search(domain, order='date asc', limit=1).name
			sequence_number_reset = self._deduce_sequence_number_reset(reference_move_name)
			if sequence_number_reset == 'year':
				where_string += " AND date_trunc('year', date::timestamp without time zone) = date_trunc('year', %(date)s) "
				param['date'] = self.date
				param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
			elif sequence_number_reset == 'month':
				where_string += " AND date_trunc('month', date::timestamp without time zone) = date_trunc('month', %(date)s) "
				param['date'] = self.date
			else:
				param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

			if param.get('anti_regex') and not self.journal_id.sequence_override_regex:
				where_string += " AND sequence_prefix !~ %(anti_regex)s "

		if self.journal_id.refund_sequence:
			if self.move_type in ('out_refund', 'in_refund'):
				where_string += " AND move_type IN ('out_refund', 'in_refund') "
			else:
				where_string += " AND move_type NOT IN ('out_refund', 'in_refund') "

		return where_string, param
	
	def _get_starting_sequence(self):
		if self.usar_prefijo_personalizado and self.l10n_latam_document_type_id:
			doc_mapping = {'01': 'FFI', '03': 'BOL', '07': 'CNE', '08': 'NDI'}
			middle_code = doc_mapping.get(self.l10n_latam_document_type_id.code, self.journal_id.code)
			
			numero = self.l10n_latam_document_type_id.correlativo_inicial
			correlativo = "00000000"
			if self.usar_prefijo_personalizado and self.l10n_latam_document_type_id.prefijo and numero:
				numero = numero - 1
				correlativo = ""
				middle_code = self.l10n_latam_document_type_id.prefijo
				l_numero = len(str(numero))
				cant_restante = 8 - l_numero
				
				for i in range(0, cant_restante):
					correlativo = correlativo+"0"
				correlativo = correlativo + str(numero)
			elif self.journal_id.code != 'INV':
				middle_code = middle_code[:1] + self.journal_id.code[:2]
			
			return "%s %s-%s" % (self.l10n_latam_document_type_id.doc_code_prefix, middle_code, correlativo)
		elif self.l10n_latam_document_type_id:
			doc_mapping = {'01': 'FFI', '03': 'BOL', '07': 'CNE', '08': 'NDI'}
			middle_code = doc_mapping.get(self.l10n_latam_document_type_id.code, self.journal_id.code)
			# TODO: maybe there is a better method for finding decent 2nd journal default invoice names
			if self.journal_id.code != 'INV':
				middle_code = middle_code[:1] + self.journal_id.code[:2]
			return "%s %s-00000000" % (self.l10n_latam_document_type_id.doc_code_prefix, middle_code)

		return super()._get_starting_sequence()

	def obtener_correlativo_inicial(self, prefijo, numero):
		numero = numero
		correlativo = ""
		middle_code = prefijo
		l_numero = len(str(numero))
		cant_restante = 8 - l_numero
		
		for i in range(0, cant_restante):
			correlativo = correlativo+"0"
		correlativo = correlativo + str(numero)

		correlativo = "%s %s%s" % (self.l10n_latam_document_type_id.doc_code_prefix, prefijo, correlativo)
		return correlativo

	def _set_next_sequence(self):
		self.ensure_one()

		if self.usar_prefijo_personalizado:
			secuencia = self.l10n_latam_document_type_id.prefijo
			inicio = 1
			if self.l10n_latam_document_type_id.secuencia_id:
				secuencia = self.l10n_latam_document_type_id.secuencia_id.prefix
				inicio = self.l10n_latam_document_type_id.secuencia_id.number_next
			last_sequence = self._get_last_sequence(secuencia)
			new = not last_sequence
			nombre = "/"
			if new:
				nombre = self.obtener_correlativo_inicial(secuencia, inicio)
				self.es_primera_en_secuencia = True
			else:
				self.es_primera_en_secuencia = False
			self[self._sequence_field] = nombre
			self._compute_split_sequence()
			return

		last_sequence = self._get_last_sequence()
		new = not last_sequence
		if new:
			last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()

		format, format_values = self._get_sequence_format_param(last_sequence)
		if new:
			if (self.is_cpe or self.usar_prefijo_personalizado) and self.l10n_latam_document_type_id:
				#format_values['seq'] = format_values['seq'] - 1
				format_values['seq'] = format_values['seq']
			else:
				format_values['seq'] = 0
			
			format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
			format_values['month'] = self[self._sequence_date_field].month
		format_values['seq'] = format_values['seq'] + 1

		# aca se asigna el correlativo
		self[self._sequence_field] = format.format(**format_values)
		self._compute_split_sequence()

	@api.depends(lambda self: [self._sequence_field])
	def _compute_split_sequence(self):
		for record in self:
			sequence = record[record._sequence_field] or ''
			if sequence and sequence not in ["//", "/"] and record.usar_prefijo_personalizado:
				datos = sequence.split("-")
				if len(datos) == 2:
					record.sequence_prefix = datos[0].split(" ")[0]
					record.sequence_number = datos[1]
					continue
			regex = re.sub(r"\?P<\w+>", "?:", record._sequence_fixed_regex.replace(r"?P<seq>", ""))  # make the seq the only matching group
			matching = re.match(regex, sequence)
			record.sequence_prefix = sequence[:matching.start(1)]
			record.sequence_number = int(matching.group(1) or 0)

	def _get_sequence(self):
		self.ensure_one()
		return self.l10n_latam_document_type_id.secuencia_id

	@api.depends('posted_before', 'state', 'journal_id', 'date')
	def _compute_name(self):
		res = super(AccountMoveSerie, self)._compute_name()
		for move in self:
			if move.name in ['/', '//', '/0'] and move.usar_prefijo_personalizado and move.state == 'posted':
				sequence = move._get_sequence()
				if not sequence:
					raise UserError('Defina una secuencia en su tipo de documento.')
				move.name = "%s %s" % (move.l10n_latam_document_type_id.doc_code_prefix, sequence.with_context(ir_sequence_date=move.date).next_by_id())
			elif move.name and move.es_primera_en_secuencia and move.usar_prefijo_personalizado and move.state == 'posted':
				sequence = move._get_sequence()
				if not sequence:
					raise UserError('Defina una secuencia en su tipo de documento.')
				move.es_primera_en_secuencia = False
				sequence.with_context(ir_sequence_date=move.date).next_by_id()

		self._compute_split_sequence()

	