# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api
import base64
#from base64 import b64decode, b64encode
from odoo.exceptions import UserError, Warning
from xml.dom import minidom
import logging
import unicodedata
_logging = logging.getLogger(__name__)

class ImportarFacturasCompra(models.Model):
	_name = "scpe.pe.purchase.import"
	_inherit = ['mail.thread.cc', 'mail.activity.mixin']
	_description = "Importar compras desde xml"

	name = fields.Char('Nombre')
	company_id = fields.Many2one('res.company', string='Empresa', required=True, readonly=False, default=lambda self: self.env.company)
	diario = fields.Many2one('account.journal', string="Diario", domain=[("type", "=", "purchase")])
	cuenta_lineas_factura = fields.Many2one("account.account", string="Cuenta para gastos")
	producto_id = fields.Many2one("product.product", string="Producto")
	attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'scpe.pe.purchase.import')], string='Archivos')
	factura_ids = fields.One2many("account.move", "xml_import_id", string="Facturas")
	invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced', readonly=True)

	@api.depends('factura_ids')
	def _get_invoiced(self):
		for reg in self:
			reg.invoice_count = len(reg.factura_ids)

	def action_view_invoice(self):
		invoices = self.mapped('factura_ids')
		action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
		if len(invoices) > 1:
			action['domain'] = [('id', 'in', invoices.ids)]
		elif len(invoices) == 1:
			form_view = [(self.env.ref('account.view_move_form').id, 'form')]
			if 'views' in action:
				action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
			else:
				action['views'] = form_view
			action['res_id'] = invoices.id
		else:
			action = {'type': 'ir.actions.act_window_close'}

		context = {
			'default_move_type': 'in_invoice',
		}
		action['context'] = context
		return action

	def leer_archivos(self):
		for archivo in self.attachment_ids:
			tipo = archivo.mimetype
			if tipo:
				tipo = tipo.split("/")[1]
			else:
				continue

			if tipo not in ["xml"]:
				continue
			decoded_data = base64.b64decode(archivo.datas)
			dom = minidom.parseString(decoded_data)
			es_linea_valida = self.obtener_compra_json_de_xml(dom, archivo.datas, archivo.name)

	def obtener_pdf_para_xml(self, nombre_pdf):
		for archivo in self.attachment_ids:
			if archivo.name == nombre_pdf:
				return archivo.datas

		return False


	def obtener_compra_json_de_xml(self, xml_datos, archivo_binario, nombre_binario):
		if not xml_datos.getElementsByTagName("cac:Signature"):
			raise UserError("No se pudo encontrar la serie para el documento %s, revise que sea un xml valido y no un CDR" % nombre_binario)
		data_serie = xml_datos.getElementsByTagName("cac:Signature")[0].getElementsByTagName("cbc:ID")[0]
		serie_correlativo = data_serie.firstChild.data
		opciones_correlativo = xml_datos.getElementsByTagName("cbc:ID")
		for opcion in opciones_correlativo:
			serie_correlativo = opcion.firstChild.data
			if len(serie_correlativo.split("-")) > 1:
				break
		
		data_fecha = xml_datos.getElementsByTagName("cbc:IssueDate")[0]
		fecha_factura = data_fecha.firstChild.data

		data_fecha_vencimiento = xml_datos.getElementsByTagName("cbc:DueDate")
		fecha_vencimiento = False
		if data_fecha_vencimiento:
			fecha_vencimiento = data_fecha_vencimiento[0].firstChild.data
		else:
			data_fecha_vencimientos = xml_datos.getElementsByTagName("cbc:PaymentDueDate")
			for data_fecha_vencimiento in data_fecha_vencimientos:
				fecha_vencimiento = data_fecha_vencimiento.firstChild.data

		data_tipo_doc = xml_datos.getElementsByTagName("cbc:InvoiceTypeCode")[0]
		tipo_doc = data_tipo_doc.firstChild.data

		#data_monto_letras = xml_datos.getElementsByTagName("cbc:Note")[0]
		#monto_letras = data_monto_letras.firstChild.data

		data_moneda = xml_datos.getElementsByTagName("cbc:DocumentCurrencyCode")[0]
		moneda = data_moneda.firstChild.data

		# quien emite la factura
		"""nodo_proveedor = xml_datos.getElementsByTagName("cac:SignatoryParty")[0]
		ruc_proveedor = nodo_proveedor.getElementsByTagName("cbc:ID")[0].firstChild.data
		nombre_proveedor = nodo_proveedor.getElementsByTagName("cbc:Name")[0].firstChild.data"""

		nodo_proveedor = xml_datos.getElementsByTagName("cac:AccountingSupplierParty")[0]
		ruc_proveedor = nodo_proveedor.getElementsByTagName("cbc:ID")[0].firstChild.data
		nombre_proveedor = nodo_proveedor.getElementsByTagName("cbc:RegistrationName")[0].firstChild.data

		nodo_cliente = xml_datos.getElementsByTagName("cac:AccountingCustomerParty")[0]
		data_ruc = nodo_cliente.getElementsByTagName("cbc:ID")[0]
		cliente_tipo_doc = data_ruc.getAttribute("schemeID")
		data_cliente = nodo_cliente.getElementsByTagName("cbc:RegistrationName")[0]
		nombre_cliente = data_cliente.firstChild.data
		ruc_cliente = data_ruc.firstChild.data

		#if self.company_id.vat != ruc_cliente:
		#	raise Warning("La factura "+serie_correlativo+" no corresponde a la empresa en curso, esta factura pertenece a la empresa "+nombre_cliente)

		nodo_termino_pago = xml_datos.getElementsByTagName("cac:PaymentTerms")[0]
		data_termino_pago_id = nodo_termino_pago.getElementsByTagName("cbc:ID")[0]
		data_termino_pago_nombre = nodo_termino_pago.getElementsByTagName("cbc:PaymentMeansID")[0]
		termino_pago_id = data_termino_pago_id.firstChild.data
		termino_pago_nombre = data_termino_pago_nombre.firstChild.data

		moneda_id = self.env["res.currency"].search([("name", "=", moneda)], limit=1)

		tipo_documento = self.env["l10n_latam.document.type"].search([("code", "=", "01"), ("sub_type", "=", "purchase")], limit=1)
		entidad = self.obtener_entidad(cliente_tipo_doc, ruc_proveedor)

		factura_existe = self.env["account.move"].search([("move_type", "=", "in_invoice"), ("ref", "=", serie_correlativo), ("partner_id", "=", entidad.id)])
		if factura_existe:
			raise Warning("La factura "+serie_correlativo+" ya existe regitrada con el proveedor: "+entidad.display_name)

		
		nombre_pdf = nombre_binario.replace(".xml", ".pdf")
		pdf_binary = self.obtener_pdf_para_xml(nombre_pdf)
		datos_json = {
			"partner_id": entidad.id,
			'company_id': self.company_id.id,
			"invoice_date": fecha_factura,
			"move_type": "in_invoice",
			"journal_id": self.diario.id,
			"xml_import_id": self.id,
			"currency_id": moneda_id.id,
			"l10n_latam_document_type_id": tipo_documento.id,
			"ref": serie_correlativo,
			"data_xml": archivo_binario,
			"datas_fname": nombre_binario,
			"data_pdf": pdf_binary,
			"datas_fname_pdf": nombre_pdf,
			#"termino_pago_id": termino_pago_id,
			#"termino_pago_nombre": termino_pago_nombre,
		}
		if fecha_vencimiento:
			datos_json["invoice_date_due"] = fecha_vencimiento

		array_lineas = []
		lineas = xml_datos.getElementsByTagName("cac:InvoiceLine")
		for linea in lineas:
			data_cantidad = linea.getElementsByTagName("cbc:InvoicedQuantity")[0]
			tipo_unidad = data_cantidad.getAttribute("unitCode")
			cantidad = data_cantidad.firstChild.data
			data_precio = linea.getElementsByTagName("cac:Price")[0].getElementsByTagName("cbc:PriceAmount")[0]
			moneda = data_precio.getAttribute("currencyID")
			precio = data_precio.firstChild.data

			data_precio_ref = linea.getElementsByTagName("cac:PricingReference")[0]
			precio_ref = data_precio_ref.getElementsByTagName("cbc:PriceAmount")[0].firstChild.data

			data_producto = linea.getElementsByTagName("cac:Item")[0]
			data_item_producto = data_producto.getElementsByTagName("cbc:ID")
			id_producto = False
			if data_item_producto and data_item_producto[0].firstChild:
				id_producto = data_item_producto[0].firstChild.data
				
			nombre_producto = data_producto.getElementsByTagName("cbc:Description")[0].firstChild.data

			reg_producto = self.obtener_producto(id_producto, nombre_producto)
			invoice_line_vals = {
				"product_id": reg_producto.id,
				"name": nombre_producto,
				"quantity": cantidad,
				"account_id": self.cuenta_lineas_factura.id,
				"price_unit": precio,
				"tax_ids": self.obtener_impuestos_compra(linea.getElementsByTagName("cac:TaxSubtotal"), precio_ref),
			}
			array_lineas.append((0, 0, invoice_line_vals))

		datos_json["invoice_line_ids"] = array_lineas
		factura = self.env['account.move'].create(datos_json)
		return True

	def obtener_entidad(self, tipo_documento, nro_ruc):
		datos_entidad = self.env['res.partner'].consulta_datos_completo(tipo_documento, nro_ruc)
		if datos_entidad['error']:
			raise Warning(datos_entidad['message'])
		elif 'registro' in datos_entidad and datos_entidad['registro']:
			return datos_entidad['registro']
		elif 'data' in datos_entidad and datos_entidad['data']:
			return self.crear_entidad(datos_entidad['data'], nro_ruc)
		else:
			raise Warning("No se pudo establecer el proveedor")

	def crear_entidad(self, datos_json, nro_ruc):
		"""entidad = self.env['res.partner'].create({
		})
		"""
		datos = datos_json["data"]
		json_entidad = {
			"commercial_name": datos["razonSocial"],
			"legal_name": datos["razonSocial"],
			"name": datos["razonSocial"],
			"street": datos["direccion"],
			"company_type": "company",
			"state": datos['estado'],
			"condition": datos['condicion'],
			"is_validate": True,
		}
		if json_entidad.get('buen_contribuyente', False):
			json_entidad["buen_contribuyente"] = datos.get('buen_contribuyente')
			json_entidad["a_partir_del"] = datos.get('a_partir_del')
			json_entidad["resolucion"] = datos.get('resolucion')


		ditrict_obj = self.env['l10n_pe.res.city.district']
		district = False
		if datos.get('ubigeo'):
			ubigeo = datos.get('ubigeo')
			district = ditrict_obj.search([('code', '=', ubigeo)], limit=1)
		elif datos.get('distrito') and datos.get('provincia'):
			distrito = unicodedata.normalize('NFKD', datos.get('distrito')).encode('ASCII', 'ignore').strip().upper().decode()
			district = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id', '!=', False)])
			if len(district) < 1:
				raise Warning('No se pudo ubicar el codigo de distrito'+distrito)
			elif len(district) > 1:
				district = ditrict_obj.search([('name_simple', '=ilike', distrito), ('city_id.name_simple', '=ilike', datos.get('provincia'))])
			if len(district) > 1:
				raise Warning('No se pudo establecer el codigo de distrito, mas de una opcion encontrada')
			elif len(district) < 1:
				raise Warning('No se pudo ubicar el codigo de distrito, se perdio en la validacion '+distrito+' '+datos.get('provincia')+' '+datos.get('departamento')) 
			
		if district:
			json_entidad["l10n_pe_district"] = district.id
			json_entidad["city_id"] = district.city_id.id
			json_entidad["state_id"] = district.city_id.state_id.id
			json_entidad["zip"] = district.code
			json_entidad["country_id"] = district.city_id.state_id.country_id.id

		json_entidad["doc_number"] = nro_ruc
		json_entidad["vat"] = nro_ruc
		entidad = self.env["res.partner"].create(json_entidad)
		return entidad

	def obtener_producto(self, id_producto, nombre_producto):
		obj_producto = self.env["product.product"]
		producto = obj_producto.search([("barcode", "=", id_producto)], limit=1)
		if producto:
			return producto

		producto = obj_producto.search([("default_code", "=", id_producto)], limit=1)
		if producto:
			return producto

		nombre = nombre_producto.replace("<![CDATA[", "")
		nombre = nombre.replace("]]", "")
		producto = obj_producto.search([("name", "=", nombre)], limit=1)

		if producto:
			return producto

		producto = self.producto_id
		return producto

	def obtener_impuestos_compra(self, data_impuestos, precio_ref):
		array_ids = []
		for data_impuesto in data_impuestos:
			impuesto_type_code = data_impuesto.getElementsByTagName("cbc:TaxTypeCode")[0].firstChild.data
			impuesto_code = data_impuesto.getElementsByTagName("cac:TaxScheme")[0].getElementsByTagName("cbc:ID")[0].firstChild.data
			impuesto = self.env["account.tax"].search([("type_tax_use", "=", "purchase"), ("l10n_pe_edi_tax_code", "=", impuesto_code), ("price_include", "=", False)], limit=1)
			if not impuesto:
				impuesto = self.env["account.tax"].search([("type_tax_use", "=", "purchase"), ("l10n_pe_edi_tax_code", "=", impuesto_code)], limit=1)
			if not impuesto:
				raise UserError('No se encontro registrado un impuesto para el codigo %s de tipo %s' % (impuesto_code, impuesto_type_code))
			array_ids.append(impuesto.id)

		return [(6, 0,array_ids)]




	