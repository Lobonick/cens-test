from odoo import models, fields, api, _

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	invoice_status = fields.Selection(selection_add=[('redeemed', 'Redeemed'), ('waiting', 'Waiting for letter')], ondelete={'redeemed': 'set null', 'waiting': 'set null'})

	@api.depends('state', 'order_line.invoice_status')
	def _compute_invoice_status(self):
		res = super()._compute_invoice_status()
		unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done'])
		confirmed_orders = self - unconfirmed_orders
		for rec in confirmed_orders:
			if any(invoice_id.payment_state in ['redeemed', 'in_redemption'] for invoice_id in rec.invoice_ids):
				rec.invoice_status = 'redeemed'
			for invoice_id in rec.invoice_ids:
				move_id = self.env['letter.management'].search([('state','=','in_process')]).letter_det_ids.filtered(lambda l: l.move_id == invoice_id).move_id
				if move_id:
					rec.invoice_status = 'waiting'
		return res