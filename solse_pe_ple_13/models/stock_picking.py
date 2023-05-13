# -*- coding: utf-8 -*-
# Copyright (c) 2019-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	"""l10n_table_12_operation_type_id = fields.Many2one('l10n_pe_edi.table.12', string='Tipo de Operación', compute='_compute_l10n_table_12_operation_type_id')
	
	def _compute_l10n_table_12_operation_type_id(self):
		for record in self:
			move_id = record.get_account_move_id()  
			if (record.sale_id) and move_id: #or record.pos_session_id # TODO colocar en tiempo real POS , al instalar el modulo 13
				l10n_table_12_operation_type_id = self.env['l10n_pe_edi.table.12'].search([('code', '=', '01')])
			elif record.purchase_id and move_id:
				l10n_table_12_operation_type_id = self.env['l10n_pe_edi.table.12'].search([('code', '=', '02')])
			elif record.location_dest_id.usage == 'internal': # Entrada
				l10n_table_12_operation_type_id = self.env['l10n_pe_edi.table.12'].search([('code', '=', '21')])
			else: # Salida
				l10n_table_12_operation_type_id = self.env['l10n_pe_edi.table.12'].search([('code', '=', '11')])
			_logger.info('l10n_table_12_operation_type_id: %s' % l10n_table_12_operation_type_id)
			record.l10n_table_12_operation_type_id = l10n_table_12_operation_type_id"""
			
	def get_account_move_id(self):    
		account_move_id = False
		if self.sale_id and self.sale_id.invoice_ids.filtered(lambda i: i.state == 'posted'):
			account_move_id = self.sale_id.invoice_ids[0]
		elif self.purchase_id and self.purchase_id.invoice_ids.filtered(lambda i: i.state == 'posted'):
			account_move_id = self.purchase_id.invoice_ids[0]
		return account_move_id

	def get_partner_name(self):
		if self.partner_id:
			partner_name = self.partner_id.name
		else:
			partner_name = ''
		return partner_name
	
	def get_document_type_code(self):
		if self.pe_type_operation in ['01','02','03','04','05','06']:
			document_type_code = False
			account_move_id = self.get_account_move_id()
			if account_move_id:
				if account_move_id.l10n_latam_document_type_id:
					document_type_code = account_move_id.l10n_latam_document_type_id.code or '00'
				else:
					document_type_code = '00'
		else:
			document_type_code = '00'
		return document_type_code

	def get_account_move_serie(self):
		if self.pe_type_operation in ['01','02','03','04','05','06']:
			account_move_serie = False
			account_move_id = self.get_account_move_id()
			if account_move_id:
				if self.sale_id:
					account_move_serie = account_move_id.solse_pe_serie
				if self.purchase_id:
					account_move_serie = account_move_id.solse_pe_serie
		else:
			account_move_serie = '0'
		return account_move_serie

	def get_account_move_number(self):
		if self.pe_type_operation in ['01','02','03','04','05','06']:
			account_move_number = False
			account_move_id = self.get_account_move_id()
			if account_move_id:
				if self.sale_id:
					account_move_number = account_move_id.solse_pe_numero

				if self.purchase_id:
					account_move_number = account_move_id.solse_pe_numero
		else:
			account_move_number = '0'
		return account_move_number
