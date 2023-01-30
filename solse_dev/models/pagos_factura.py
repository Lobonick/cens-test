# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PagoFactura(models.Model):
	_name = "sdev.facturas.pago"
	_description = "Pagos factura (proceso importar)"

	name = fields.Char("Nombre")
	journal_id = fields.Many2one('account.journal', readonly=False, domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
	amount = fields.Monetary("Monto")
	payment_date = fields.Date(string="Fecha pago", required=True, default=fields.Date.context_today)
	payment_method_id = fields.Many2one('account.payment.method', string='Método de pago')
	currency_id = fields.Many2one('res.currency', string='Moneda')
	factura_ids = fields.One2many('account.move', 'pago_id', "Factura")
	partner_id = fields.Many2one('res.partner', string="Cliente/Proveedor")
	payment_type = fields.Selection([
		('outbound', 'Enviar dinero'),
		('inbound', 'Recibir dinero'),
	], string='Tipo de pago')
	partner_type = fields.Selection([
		('customer', 'Cliente'),
		('supplier', 'Proveedor'),
	], string="Tipo de socio")
	communication = fields.Char(string="Memo")
