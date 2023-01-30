# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class FacturasElectronicas(models.Model):
	_name = "sdev.facturas"
	_description = "Facturas (proceso importar)"

	name = fields.Char('Numero')
	id_externo_cpe = fields.Char('Id externo cpe')

	datas = fields.Binary("Datos XML")
	datas_fname = fields.Char("Nombre de archivo XML")
	datas_sign = fields.Binary("Datos firmado XML")
	datas_sign_fname = fields.Char("Nombre de archivo firmado XML")
	datas_zip = fields.Binary("Datos Zip XML")
	datas_zip_fname = fields.Char("Nombre de archivo zip XML")
	datas_response = fields.Binary("Datos de respuesta XML")
	datas_response_fname = fields.Char("Nombre de archivo de respuesta XML")
	response = fields.Char("Respuesta")
	response_code = fields.Char("Código de respuesta")
	note = fields.Text("Nota")
	error_code = fields.Char(string="Código de error")
	digest = fields.Char("Codigo")
	signature = fields.Text("Firma")
	invoice_ids = fields.One2many("account.move", 'pe_cpe_id', string="Facturas")
	ticket = fields.Char("Ticket")