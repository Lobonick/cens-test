# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import models
from odoo.tools import date_utils
import logging
_logging = logging.getLogger(__name__)


class AccountCashFlowReport(models.AbstractModel):
	_name = 'report.account_cash_flow_report.cash_flow_report_template'
	
	@api.model
	def _get_report_values(self, docids, data=None):
		if data.get('form'):
			start_date = data['form'].get('start_date')
			end_date = data['form'].get('end_date')
			company_id = data['form'].get('company_id')
			cash_flow_lines = self._get_cash_flow_lines(start_date, end_date, company_id)
			return {
				'doc_ids': docids,
				'doc_model': 'account.move',
				'docs': self.env['account.move'].browse(docids),
				'cash_flow_lines': cash_flow_lines,
				'start_date': start_date,
				'end_date': end_date,
				'company_id': company_id,
			}
	
	#def _get_cash_flow_lines(self, start_date, end_date, company_id):
	@api.model
	def _get_cash_flow_lines(self, start_date, end_date, company_id):
		# Obtener todas las categorías de flujo de efectivo
		cash_flow_categories = self.env['account.cash.flow.category'].search([])
		cash_flow_lines = []
		# Iterar sobre todas las categorías de flujo de efectivo
		for category in cash_flow_categories:
			# Obtener las cuentas asociadas a la categoría
			account_ids = category.account_ids.filtered(lambda r: r.company_id.id == company_id).ids
			if account_ids:
				# Obtener los movimientos de cuentas de la categoría dentro del rango de fechas
				moves = self.env['account.move.line'].search([
					('account_id', 'in', account_ids),
					('date', '>=', start_date),
					('date', '<=', end_date),
					('move_id.state', '=', 'posted'),
					('move_id.l10n_latam_document_type_id', 'not in', self.env.ref('l10n_latam_invoice_document.document_type_20').ids)  # Filtrar facturas de importación
				])
				if moves:
					# Sumar el total de la cuenta
					total = sum(moves.mapped('balance'))
					# Crear una línea de flujo de efectivo
					cash_flow_lines.append({
						'name': category.name,
						'code': category.code,
						'type': category.type,
						'total': total,
					})
		return cash_flow_lines


class AccountMove(models.Model):
	_inherit = 'account.move'
	
	cash_flow_category_id = fields.Many2one('account.cash.flow.category', string='Cash Flow Category')
	
class AccountCashFlowCategory(models.Model):
	_name = 'account.cash.flow.category'
	_description = 'Cash Flow Category'
	
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	type = fields.Selection([('inflow', 'Inflow'), ('outflow', 'Outflow')], string='Type', required=True)

class AccountCashFlow(models.Model):
	_name = 'account.cash.flow'
	_description = 'Cash Flow'
	_rec_name = 'date'
	_order = 'date, id'
	
	name = fields.Char('Name', readonly=True)
	date = fields.Date('Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft': [('readonly', False)]})
	category_id = fields.Many2one('account.cash.flow.category', string='Category', required=True, readonly=True, states={'draft': [('readonly', False)]})
	move_ids = fields.Many2many('account.move', string='Journal Entries', domain=[('state', '=', 'posted')], readonly=True, states={'draft': [('readonly', False)]})
	state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='Status', default='draft', readonly=True, copy=False, track_visibility='onchange')
	
	def action_post(self):
		self.write({'state': 'posted'})
		self._create_account_moves()
	
	@api.model
	def _create_account_moves(self, date_start, date_stop, company_id):
		# Obtener las líneas de flujo de efectivo para el rango de fechas y compañía especificados
		cash_flow_lines = self._get_cash_flow_lines(date_start, date_stop, company_id)
		# Crear un asiento contable para cada línea de flujo de efectivo
		move_ids = []
		for line in cash_flow_lines:
			# Obtener la cuenta de contrapartida según el tipo de categoría de flujo de efectivo
			if line['type'] == 'ingreso':
				counterpart_account = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_cash_flow_statement.ingress_account_id')
			elif line['type'] == 'egreso':
				counterpart_account = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_cash_flow_statement.expense_account_id')
			else:
				counterpart_account = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_cash_flow_statement.transfer_account_id')
			# Crear el asiento contable con la información de la línea de flujo de efectivo
			move = self.env['account.move'].create({
				'journal_id': self.env['ir.config_parameter'].sudo().get_param('l10n_pe_cash_flow_statement.journal_id'),
				'company_id': company_id,
				'date': date_stop,
				'ref': line['name'],
			})
			debit_vals = {
				'name': line['name'],
				'account_id': line['category'].cash_flow_account_id.id,
				'debit': line['total'],
				'credit': 0.0,
				'move_id': move.id,
				'partner_id': False,
			}
			credit_vals = {
				'name': line['name'],
				'account_id': counterpart_account,
				'debit': 0.0,
				'credit': line['total'],
				'move_id': move.id,
				'partner_id': False,
			}
			# Crear las líneas de asiento contable
			self.env['account.move.line'].create(debit_vals)
			self.env['account.move.line'].create(credit_vals)
			# Agregar el ID del asiento contable a la lista de IDs
			move_ids.append(move.id)
		return move_ids

