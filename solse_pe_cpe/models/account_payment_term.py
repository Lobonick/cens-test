# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

class AccontPaymentTerm(models.Model):
	_inherit = "account.payment.term"

	tipo_transaccion = fields.Selection([('contado', 'Contado'), ('credito', 'Credito')], string='Tipo de Transacción', default='credito', required=True)