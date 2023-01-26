# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from pdf417gen.encoding import to_bytes, encode_high, encode_rows
from pdf417gen.util import chunks
from pdf417gen.compaction import compact_bytes
from pdf417gen import render_image
import tempfile
#from base64 import encodestring
import base64
from odoo.exceptions import UserError
import re
from io import StringIO, BytesIO
from importlib import reload
import sys
try:
	import qrcode
	qr_mod = True
except:
	qr_mod = False

def encodestring(datos):
	respuesta = datos
	if sys.version_info >= (3, 9):
		respuesta = base64.encode(datos)
	else:
		respuesta = base64.encodestring(datos)

	return respuesta



class Picking(models.Model):
	_inherit = "stock.picking"

	pe_voided_id = fields.Many2one("solse.cpe.eguide", "Guía cancelada", copy=False)
	pe_guide_id = fields.Many2one("solse.cpe.eguide", "Guía electrónica", copy=False)
	pe_guide_number = fields.Char("Número de guía", default="/", copy=False)
	pe_is_realeted = fields.Boolean("Esta relacionada", copy=False)
	pe_related_number = fields.Char("Número relacionado", copy=False)
	pe_related_code = fields.Selection(selection="_get_pe_related_code", string="Código de número relacionado", copy=False)
	supplier_id = fields.Many2one(comodel_name="res.partner", string="Proveedor", copy=False)
	pe_transfer_code = fields.Selection(selection="_get_pe_transfer_code", string="Código de transferencia", default="01", copy=False)
	pe_gross_weight = fields.Float("Peso bruto", digits='Product Unit of Measure', copy=False)
	pe_unit_quantity = fields.Integer("Cantidad Bultos", copy=False)
	pe_transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Modo de transporte", copy=False)
	pe_carrier_id = fields.Many2one(comodel_name="res.partner", string="Transportista", copy=False)
	pe_is_eguide = fields.Boolean("Es Guía Electrónica", copy=False)
	pe_is_programmed = fields.Boolean("Transferencia programada", copy=False)
	pe_date_issue = fields.Date('Fecha de emisión', copy=False)
	pe_fleet_ids = fields.One2many(comodel_name="pe.stock.fleet", inverse_name="picking_id", string="Flota Privada", copy=False)
	placa = fields.Char("Placa", compute="_compute_placa")

	pe_digest = fields.Char("Digest", related="pe_guide_id.digest")
	sunat_qr_code = fields.Binary('QR Code (cpe)', compute='_compute_get_qr_code')
	pe_signature = fields.Text("Firma", related="pe_guide_id.signature")
	pe_response = fields.Char("Respuesta", related="pe_guide_id.response")
	pe_note = fields.Text("Sunat nota", related="pe_guide_id.note")
	pe_error_code = fields.Selection("_get_pe_error_code", string="Codigo de error", related="pe_guide_id.error_code", readonly=True)
	sunat_pdf417_code = fields.Binary("Pdf 417 Code", compute="_get_pdf417_code")
	pe_guide_state = fields.Selection([
		('draft', 'Draft'),
		('generate', 'Generated'),
		('send', 'Send'),
		('verify', 'Waiting'),
		('done', 'Done'),
		('cancel', 'Cancelled'),
	], string='Estado de Guía', related="pe_guide_id.state")

	pe_invoice_ids = fields.Many2many(comodel_name="account.move", string="Pickings", compute ="_compute_pe_invoice_ids", readonly=True)
	pe_invoice_name = fields.Char("Número interno", compute ="_compute_pe_invoice_ids")
	pe_type_operation = fields.Selection("_get_pe_type_operation", "Tipo de operación", help="Tipo de operación efectuada", copy=False)
	pe_number = fields.Char("Numero de Guia")

	almacen_origen = fields.Many2one('stock.warehouse', 'Almacén Origen', compute="_compute_almacen", store=True)
	almacen_destino = fields.Many2one('stock.warehouse', 'Almacén Destino', compute="_compute_almacen", store=True)

	@api.depends('location_id', 'location_dest_id')
	def _compute_almacen(self):
		for reg in self:
			almacen_origen = False
			almacen_destino = False
			if reg.location_id:
				almacen_origen = self.env['stock.warehouse'].search([('lot_stock_id', '=', reg.location_id.id)], limit=1)

			if reg.location_dest_id:
				almacen_destino = self.env['stock.warehouse'].search([('lot_stock_id', '=', reg.location_dest_id.id)], limit=1)

			reg.almacen_origen = almacen_origen.id if almacen_origen else False
			reg.almacen_destino = almacen_destino.id if almacen_destino else False

	@api.depends('pe_fleet_ids', 'pe_fleet_ids.fleet_id', 'pe_fleet_ids.fleet_id.license_plate')
	def _compute_placa(self):
		for reg in self:
			placa = ""
			if reg.pe_fleet_ids:
				registro = reg.pe_fleet_ids[0]
				if registro.fleet_id:
					placa = registro.fleet_id.license_plate
			reg.placa = placa
	
	@api.model
	def _get_pe_type_operation(self):
		return self.env['pe.datas'].get_selection("PE.TABLA12")    
	
	@api.model
	def _compute_pe_invoice_ids(self):
		pe_invoice_ids = False
		pe_invoice_name=[]
		for stock_id in self:
			stock_id.sale_id
			pe_invoice_ids = stock_id.sale_id.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
			if pe_invoice_ids:
				pe_invoice_name = pe_invoice_ids.mapped('l10n_latam_document_number')
			stock_id.pe_invoice_ids=pe_invoice_ids and pe_invoice_ids.ids or []
			stock_id.pe_invoice_name = ", ".join(pe_invoice_name) or False

	def _get_address_details(self, partner):
		self.ensure_one()
		address = ''
		if partner.l10n_pe_district:
			address = "%s" % (partner.l10n_pe_district.name)
		if partner.city:
			address += ", %s" % (partner.city)
		if partner.state_id.name:
			address += ", %s" % (partner.state_id.name)
		if partner.zip:
			address += "( %s)" % (partner.zip)
		if partner.country_id.name:
			address += ", %s" % (partner.country_id.name)
		reload(sys)
		html_text = str(tools.plaintext2html(address, container_tag=True))
		data = html_text.split('p>')
		if data:
			return data[1][:-2]
		return False
		
	def _get_street(self, partner):
		self.ensure_one()
		address = ''
		if partner.street:
			address = "%s" % (partner.street)
		if partner.street2:
			address += ", %s" % (partner.street2)
		reload(sys)
		html_text = str(tools.plaintext2html(address, container_tag=True))
		data = html_text.split('p>')
		if data:
			return data[1][:-2]
		return False

	@api.model
	def action_cancel_eguide(self):
		for picking_id in self:
			if picking_id.pe_guide_id and picking_id.pe_guide_id.state not in ["draft", "generate", "cancel"]:
				voided_id = self.env['solse.cpe.eguide'].get_eguide_async('low', picking_id)
				picking_id.pe_voided_id = voided_id.id

	@api.model
	def _get_pdf417_code(self):
		for picking_id in self:
			res = []
			if picking_id.pe_guide_number and picking_id.pe_is_eguide:
				res.append(picking_id.company_id.partner_id.doc_number)
				res.append('09')
				res.append(picking_id.pe_guide_number.split("-")[0] or '')
				res.append(picking_id.pe_guide_number.split("-")[1] or '')
				# res.append(str(picking_id.amount_tax))
				# res.append(str(picking_id.amount_total))
				res.append(str(picking_id.pe_date_issue))
				res.append(picking_id.partner_id.doc_type or "-")
				res.append(picking_id.partner_id.doc_number or "-")
				res.append(picking_id.pe_digest or "")
				res.append(picking_id.pe_signature or "")
				res.append("")
				pdf417_string = '|'.join(res)
				data_bytes = compact_bytes(to_bytes(pdf417_string, 'utf-8'))
				code_words = encode_high(data_bytes, 10, 5)
				rows = list(chunks(code_words, 10))
				codes = list(encode_rows(rows, 10, 5))

				image = render_image(codes, scale=2, ratio=2, padding=7)
				tmpf = BytesIO()
				image.save(tmpf, 'png')
				# tmpf.seek(0)
				picking_id.sunat_pdf417_code = encodestring(tmpf.getvalue())
			else:
				picking_id.sunat_pdf417_code = False

	@api.depends('name', 'pe_is_eguide', 'date_done', 'scheduled_date', 'partner_id.doc_number', 'partner_id.doc_type', 'company_id.partner_id.doc_number')
	def _compute_get_qr_code(self):
		for guia in self:
			fecha_guia = guia.date_done or guia.scheduled_date
			if not all((guia.name != '/', guia.pe_is_eguide, qr_mod)):
				guia.sunat_qr_code = ''
			elif len(guia.pe_guide_number.split('-')) > 1 and fecha_guia:
				res = [
				 guia.company_id.partner_id.doc_number or '-',
				 '09',
				 guia.pe_guide_number.split('-')[0] or '',
				 guia.pe_guide_number.split('-')[1] or '',
				 str('0'),
				 fields.Date.to_string(fecha_guia), guia.partner_id.doc_type or '-',
				 guia.partner_id.doc_number or '-', '']

				qr_string = '|'.join(res)
				qr = qrcode.QRCode(version=1, error_correction=(qrcode.constants.ERROR_CORRECT_Q))
				qr.add_data(qr_string)
				qr.make(fit=True)
				image = qr.make_image()
				tmpf = BytesIO()
				image.save(tmpf, 'png')
				guia.sunat_qr_code = encodestring(tmpf.getvalue())
			else:
				guia.sunat_qr_code = ''

	@api.model
	def _get_pe_error_code(self):
		return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

	@api.model
	def do_new_transfer(self):
		res = super(Picking, self).do_new_transfer()
		self.pe_gross_weight = sum(
			[line.product_id.weight for line in self.pack_operation_ids])
		self.pe_unit_quantity = sum(
			[line.qty_done or line.product_qty for line in self.pack_operation_ids])
		return res

	@api.model
	def _get_pe_transport_mode(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

	@api.model
	def _get_pe_related_code(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG21")

	@api.model
	def _get_pe_transfer_code(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG20")

	@api.model
	def validate_eguide(self):
		if not self.partner_id:
			raise UserError(_("Customer is required"))
		
		if self.picking_type_id.code != 'internal':
			if self.partner_id.id == self.company_id.partner_id.id:
				raise UserError("Destinatario no debe ser igual al remitente")
		if not self.partner_id.parent_id.doc_type and not self.partner_id.doc_type:
			raise UserError(_("Customer type document is required"))
		if not self.partner_id.parent_id.doc_number and not self.partner_id.doc_number:
			raise UserError(_("Customer number document is required"))
		if not self.partner_id.street:
			raise UserError(_("Customer street is required for %s") %
							(self.partner_id.name or ""))
		if not self.partner_id.l10n_pe_district:
			raise UserError(_("Customer district is required for %s") %
							(self.partner_id.name or ""))

		if not self.pe_carrier_id.doc_type and self.pe_transport_mode == "01":
			raise UserError(_("Carrier type document is required for %s") % (
				self.pe_carrier_id.name or ""))
		if not self.pe_carrier_id.doc_number and self.pe_transport_mode == "01":
			raise UserError(_("Carrier number document is required for %s") % (
				self.pe_carrier_id.name or ""))
		if not self.picking_type_id.warehouse_id.partner_id or not self.picking_type_id.warehouse_id.partner_id.street:
			raise UserError(_("It is necessary to enter the warehouse address for %s") % (
				self.picking_type_id.warehouse_id.partner_id.name or ""))
		if self.picking_type_id.warehouse_id.partner_id and not self.picking_type_id.warehouse_id.partner_id.l10n_pe_district:
			raise UserError(_("It is necessary to enter the warehouse district for %s") % (
				self.picking_type_id.warehouse_id.partner_id.name or ""))
		if self.pe_transport_mode == "02" and len(self.pe_fleet_ids) > 0:
			for line in self.pe_fleet_ids:
				if not line.driver_id.doc_type:
					raise UserError(_("Carrier type document is required for %s") % (
						line.driver_id.name or ""))
				if not line.driver_id.doc_number:
					raise UserError(_("Carrier number document is required for %s") % (
						line.driver_id.name or ""))
		elif self.pe_transport_mode == "02" and len(self.pe_fleet_ids) == 0:
			raise UserError(_("It is necessary to add a vehicle and driver"))

	def action_generate_eguide(self):
		for stock in self:
			if stock.pe_is_eguide:
				self.validate_eguide()
				self.pe_date_issue = fields.Date.context_today(self)
				if stock.pe_guide_number == '/':
					if stock.picking_type_id.warehouse_id.eguide_sequence_id:
						stock.pe_guide_number = stock.picking_type_id.warehouse_id.eguide_sequence_id.next_by_id()
					else:
						stock.pe_guide_number = self.env['ir.sequence'].next_by_code('pe.eguide.sync')
				if not re.match(r'^(T){1}[A-Z0-9]{3}\-\d+$', stock.pe_guide_number):
					raise UserError("El numero de la guia ingresada no cumple con el estandar.\n"
									"Verificar la secuencia del Diario por jemplo T001- o TG01-. \n"
									"Para cambiar ir a Configuracion/Gestion de Almacenes/Almacenes")
				if not self.pe_guide_id:
					pe_guide_id = self.env['solse.cpe.eguide'].create_from_stock(
						stock)
					stock.pe_guide_id = pe_guide_id.id
				else:
					pe_guide_id = stock.pe_guide_id
				if stock.company_id.pe_is_sync:
					pe_guide_id.generate_eguide()
					pe_guide_id.action_send()
					pe_guide_id.action_done()
				else:
					pe_guide_id.generate_eguide()
				self.pe_number = stock.pe_guide_number


class PeStockFleet(models.Model):
	_name = "pe.stock.fleet"
	_description = 'Stock Fleet'

	name = fields.Char("Placa", required=True)
	fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehículo")
	picking_id = fields.Many2one(comodel_name="stock.picking", string="Guía")
	driver_id = fields.Many2one(comodel_name="res.partner", string="Conductor", required=True)
	is_main = fields.Boolean("Principal")

	@api.onchange("fleet_id")
	def onchange_fleet_id(self):
		if self.fleet_id:
			self.name = self.fleet_id.license_plate
			self.driver_id = self.fleet_id.driver_id.id


class Warehouse(models.Model):
	_inherit = "stock.warehouse"

	eguide_sequence_id = fields.Many2one('ir.sequence', string='Secuencia de guía electrónica', )
