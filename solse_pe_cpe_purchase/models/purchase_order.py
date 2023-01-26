# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round
from datetime import datetime
from functools import partial
from itertools import groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from . import constantes
import logging

_logging = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	def _prepare_invoice(self):
		self.ensure_one()
		res = super(PurchaseOrder, self)._prepare_invoice()

		move_type = 'in_invoice'
		company_id = (self.company_id or self.env.company).id
		domain = [('company_id', '=', company_id), ('type', 'in', ['purchase'])]

		journal = None
		currency_id = self.currency_id.id or self._context.get('default_currency_id')
		if currency_id and currency_id != self.company_id.currency_id.id:
			currency_domain = domain + [('currency_id', '=', currency_id)]
			journal = self.env['account.journal'].search(currency_domain, limit=1)

		if not journal:
			journal = self.env['account.journal'].search(domain, limit=1)
			
		if not journal:
			raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

		partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
		partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
		#journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
		tipo_documento = self.env['l10n_latam.document.type']
		tipo_doc_id = tipo_documento.search([('code', '=', '01'), ('sub_type', '=', 'purchase')], limit=1)
		if not tipo_doc_id:
			raise UserError('No se encontro un tipo de documento para facturas de compra')
		
		reg = self
		tipo_transaccion = 'contado'
		if reg.payment_term_id:
			tipo_transaccion = reg.payment_term_id.tipo_transaccion or 'contado'

		invoice_vals = {
			'ref': self.partner_ref or '',
			'move_type': move_type,
			'purchase_id': self.id,
			'journal_id': journal.id,
			'l10n_latam_document_type_id': tipo_doc_id.id,
			'narration': self.notes,
			'currency_id': self.currency_id.id,
			'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
			'partner_id': partner_invoice.id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
			'payment_reference': self.partner_ref or '',
			'partner_bank_id': self.partner_id.bank_ids[:1].id,
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'tipo_transaccion': tipo_transaccion,
		}
		res.update(invoice_vals)
		return res

	def action_create_invoice(self):
		"""Create the invoice associated to the PO.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

		# 1) Prepare invoice vals and clean-up the section lines
		invoice_vals_list = []
		for order in self:
			if order.invoice_status != 'to invoice':
				continue

			order = order.with_company(order.company_id)
			pending_section = None
			# Invoice values.
			invoice_vals = order._prepare_invoice()
			# Invoice line values (keep only necessary sections).
			for line in order.order_line:
				if line.display_type == 'line_section':
					pending_section = line
					continue
				if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
					if pending_section:
						invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
						pending_section = None
					invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
			invoice_vals_list.append(invoice_vals)

		if not invoice_vals_list:
			raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

		# 2) group by (company_id, partner_id, currency_id) for batch creation
		new_invoice_vals_list = []
		for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
			origins = set()
			payment_refs = set()
			refs = set()
			ref_invoice_vals = None
			for invoice_vals in invoices:
				if not ref_invoice_vals:
					ref_invoice_vals = invoice_vals
				else:
					ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
				origins.add(invoice_vals['invoice_origin'])
				payment_refs.add(invoice_vals['payment_reference'])
				refs.add(invoice_vals['ref'])
			ref_invoice_vals.update({
				'ref': ', '.join(refs)[:2000],
				'invoice_origin': ', '.join(origins),
				'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
			})
			new_invoice_vals_list.append(ref_invoice_vals)
		invoice_vals_list = new_invoice_vals_list

		# 3) Create invoices.
		moves = self.env['account.move']
		AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
		for vals in invoice_vals_list:
			moves |= AccountMove.with_company(vals['company_id']).create(vals)

		# 4) Some moves might actually be refunds: convert them if the total amount is negative
		# We do this after the moves have been created since we need taxes, etc. to know if the total
		# is actually negative or not
		moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

		return self.action_view_invoice(moves)

class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	nro_oc = fields.Char("Nro OC", related="order_id.name", store=True)
	ref_proveedor_n2 = fields.Char("Nro. Factura Proveedor", related="invoice_lines.move_id.ref", store=True)
	fecha_pedido = fields.Datetime("Fecha Pedido", related="order_id.date_order", store=True)
	proveedor = fields.Many2one('res.partner', related='order_id.partner_id', store=True)
	uom_po_id = fields.Many2one('uom.uom', related="product_id.uom_po_id")