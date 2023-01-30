# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SolseDev(models.Model):
	_name = "sdev.borrar"
	_description = "Borrar datos"

	name = fields.Char('Borrar')

	@api.model
	def borrar_facturas(self):
		self.env['account.payment'].search([]).action_draft()
		self.env['account.payment'].search([]).unlink()
		self.env['account.move'].search([('move_type', '!=', 'entry')]).write({'state': 'draft', 'name': '/'})
		self.env['account.partial.reconcile'].search([]).unlink()
		self.env['account.analytic.line'].search([]).unlink()
		#self.env['account.move.line'].search([]).unlink()
		self.env['account.move'].search([]).with_context(force_delete=True).unlink()
		self.env['solse.cpe'].search([]).write({'state': 'draft'})
		self.env['solse.cpe'].search([]).unlink()
		self.env['stock.move'].search([]).write({'state': 'draft'})
		self.env['stock.move'].search([]).unlink()
		self.env['stock.picking'].search([]).write({'state': 'draft'})
		self.env['stock.picking'].search([]).unlink()
		self.env['sale.order'].search([]).write({'state': 'draft'})
		self.env['sale.order'].search([]).unlink()
		self.env['purchase.order'].search([]).write({'state': 'cancel'})
		self.env['purchase.order'].search([]).unlink()
		self.env['crm.lead'].search([]).unlink()
		#self.env['account.journal'].search([]).write({'sequence_number_next': 1})

			
