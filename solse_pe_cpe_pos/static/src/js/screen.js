odoo.define('solse_pe_cpe_pos.pos_screens', function(require) {
  "use strict";

var { PosGlobalState, Order } = require('point_of_sale.models');
var PosDB = require('point_of_sale.DB');
var core    = require('web.core');
var rpc = require('web.rpc');
var concurrency = require('web.concurrency');
const Registries = require('point_of_sale.Registries');
var QWeb = core.qweb;
var PosDBSuper = PosDB;
var Mutex = concurrency.Mutex;
var _t      = core._t;
var json_ordens = {}



	const PosModelCPE = (PosGlobalState) => class PosModelCPE extends PosGlobalState {

		async _processData(loadedData) {
			await super._processData(...arguments);
			let identifications = loadedData['l10n_latam.identification.type'];
			this.doc_code_by_id = {}
			var self = this;
			_.each(identifications, function(doc) {
				self.doc_code_by_id[doc.id] = doc.l10n_pe_vat_code
			})
			this.doc_types = identifications

			let plazos_pago = loadedData['account.payment.term'];
			this.invoice_payment_term_ids = plazos_pago;

			let documentos_venta = loadedData['l10n_latam.document.type'];
			this.l10n_latam_document_type_ids = documentos_venta;
			
			this._loadCpeData()
		}

		_loadCpeData() {
			//this.add_doc_type_sale(this.l10n_latam_document_type_ids);
			//this.add_invoice_payment_term(this.invoice_payment_term_ids);
		}

		add_doc_type_sale(doc_types) {
			if (!doc_types instanceof Array) {
				doc_types = [doc_types];
			}
			for (var i = 0, len = doc_types.length; i < len; i++) {
				this.doc_type_sale_by_id[doc_types[i].id] = doc_types[i];
			}
		}

		get_doc_type_sale_id(journal_id) {
			///if(!this.doc_type_sale_by_id) {
				let doc_types = this.l10n_latam_document_type_ids
				if (!doc_types instanceof Array) {
					doc_types = [doc_types];
				}
				for (var i = 0, len = doc_types.length; i < len; i++) {
					this.doc_type_sale_by_id[doc_types[i].id] = doc_types[i];
				}
			//}
			return this.doc_type_sale_by_id[journal_id];
		}

		add_invoice_payment_term(plazos_pago) {
			if (!plazos_pago instanceof Array) {
				plazos_pago = [plazos_pago];
			}
			for (var i = 0, len = plazos_pago.length; i < len; i++) {
				this.invoice_payment_term_by_id[plazos_pago[i].id] = plazos_pago[i];
			}
		}

		get_invoice_payment_term(item_id) {
			//if(!this.invoice_payment_term_by_id) {
				let plazos_pago = this.invoice_payment_term_ids
				//this.add_invoice_payment_term(this.invoice_payment_term_ids)
				if (!plazos_pago instanceof Array) {
					plazos_pago = [plazos_pago];
				}
				for (var i = 0, len = plazos_pago.length; i < len; i++) {
					this.invoice_payment_term_by_id[plazos_pago[i].id] = plazos_pago[i];
				}
			//}
			return this.invoice_payment_term_by_id[item_id];
		}

		constructor(obj, options) {
			super(...arguments);
			this.doc_types = []
			this.invoice_payment_term_ids = []
			this.l10n_latam_document_type_ids = []
			this.doc_type_sale_by_id = {};
			this.invoice_payment_term_by_id = {};
			this.partner_states = [
						{'code': 'ACTIVO', 'name':'ACTIVO'},
						{'code': 'BAJA DE OFICIO', 'name':'BAJA DE OFICIO'},
						{'code': 'BAJA PROVISIONAL', 'name':'BAJA PROVISIONAL'},
						{'code': 'SUSPENSION TEMPORAL', 'name':'SUSPENSION TEMPORAL'},
						{'code': 'INHABILITADO-VENT.UN', 'name':'INHABILITADO-VENT.UN'},
						{'code': 'BAJA MULT.INSCR. Y O', 'name':'BAJA MULT.INSCR. Y O'},
						{'code': 'PENDIENTE DE INI. DE', 'name':'PENDIENTE DE INI. DE'},
						{'code': 'OTROS OBLIGADOS', 'name':'OTROS OBLIGADOS'},
						{'code': 'NUM. INTERNO IDENTIF', 'name':'NUM. INTERNO IDENTIF'},
						{'code': 'ANUL.PROVI.-ACTO ILI', 'name':'ANUL.PROVI.-ACTO ILI'},
						{'code': 'ANULACION - ACTO ILI', 'name':'ANULACION - ACTO ILI'},
						{'code': 'BAJA PROV. POR OFICI', 'name':'BAJA PROV. POR OFICI'},
						{'code': 'ANULACION - ERROR SU', 'name':'ANULACION - ERROR SU'},
						];
			this.partner_conditions = [
						{'code': 'HABIDO', 'name':'HABIDO'},
						{'code': 'NO HALLADO', 'name':'NO HALLADO'},
						{'code': 'NO HABIDO', 'name':'NO HABIDO'},
						{'code': 'PENDIENTE', 'name':'PENDIENTE'},
						{'code': 'NO HALLADO SE MUDO D', 'name':'NO HALLADO SE MUDO D'},
						{'code': 'NO HALLADO NO EXISTE', 'name':'NO HALLADO NO EXISTE'},
						{'code': 'NO HALLADO FALLECIO', 'name':'NO HALLADO FALLECIO'},
						{'code': 'NO HALLADO OTROS MOT', 'name':'NO HALLADO OTROS MOT'},
						{'code': 'NO APLICABLE', 'name':'NO APLICABLE'},
						{'code': 'NO HALLADO NRO.PUERT', 'name':'NO HALLADO NRO.PUERT'},
						{'code': 'NO HALLADO CERRADO', 'name':'NO HALLADO CERRADO'},
						{'code': 'POR VERIFICAR', 'name':'POR VERIFICAR'},
						{'code': 'NO HALLADO DESTINATA', 'name':'NO HALLADO DESTINATA'},
						{'code': 'NO HALLADO RECHAZADO', 'name':'NO HALLADO RECHAZADO'},
						{'code': '-', 'name':'NO HABIDO'},
						];
		}

		validate_pe_doc(doc_type, doc_number) {
			if (!doc_type || !doc_number){
				return false;
			}
			if (doc_number.length==8 && doc_type=='1') {
				return true;
			}
			else if (doc_number.length==11 && doc_type=='6')
			{
				var vat= doc_number;
				var factor = '5432765432';
				var sum = 0;
				var dig_check = false;
				if (vat.length != 11){
					return false;
				}
				try{
					parseInt(vat)
				}
				catch(err){
					return false; 
				}
				
				for (var i = 0; i < factor.length; i++) {
					sum += parseInt(factor[i]) * parseInt(vat[i]);
				 } 

				var subtraction = 11 - (sum % 11);
				if (subtraction == 10){
					dig_check = 0;
				}
				else if (subtraction == 11){
					dig_check = 1;
				}
				else{
					dig_check = subtraction;
				}
				
				if (parseInt(vat[10]) != dig_check){
					return false;
				}
				return true;
			}
			else if (doc_number.length>=3 &&  ['0', '4', '7', 'A'].indexOf(doc_type)!=-1) {
				return true;
			}
			else if (doc_type.length>=2) {
				return true;
			}
			else {
				return false;
			}
		}

	}

	Registries.Model.extend(PosGlobalState, PosModelCPE);

	const CPEOrder = (Order) => class CPEOrder extends Order {
		check_pe_journal() {
			var client = this.get_partner();
			var doc_type=client ? client.doc_type : false;
			var l10n_latam_document_type_id = this.get_doc_type_sale();

			var journal_type = this.get_cpe_type();
			if(!journal_type){
				return [false, 'Seleccione un diario valido'];
			}
			if(journal_type == '01' && doc_type != '6') {
				return [false, 'El tipo de documento del cliente no es valido para facturas'];
			} else if(journal_type == '03' && doc_type == '6') {
				return [false, 'El tipo de documento del cliente no es valido para boletas'];
			}
			return  [true, 'OK'];
		}

		get_cpe_type() {
			var tipo_doc_venta = this.get_doc_type_sale();
			if (!tipo_doc_venta){
				return false;
			}
			var doc_type_sale = this.pos.get_doc_type_sale_id(tipo_doc_venta);
			return doc_type_sale ? doc_type_sale.code : false;
		}

		es_cpe() {
			let tipo_doc_venta = this.get_cpe_type()
			if(tipo_doc_venta) {
				return true;
			}
			return false;
		}

		es_un_cpe() {
			var tipo_doc_venta = this.get_doc_type_sale();
			if (!tipo_doc_venta){
				return false;
			}
			var doc_type_sale = this.pos.get_doc_type_sale_id(tipo_doc_venta);
			return doc_type_sale ? doc_type_sale.is_cpe : false;
		}

		get_cpe_qr(){
			var res=[]
			res.push(this.pos.company.vat || '');
			res.push(this.get_cpe_type() || ' ');
			res.push(this.get_number() || ' ');
			res.push(this.get_total_tax() || 0.0);
			res.push(this.get_total_with_tax() || 0.0);
			res.push(moment(new Date().getTime()).format('YYYY-MM-DD'));
			res.push(this.get_doc_type() || '-');
			res.push(this.get_doc_number() || '-');
			var qr_string=res.join('|');
			return qr_string;
		}

		set_doc_type_sale(l10n_latam_document_type_id) {
			this.assert_editable();
			this.l10n_latam_document_type_id = l10n_latam_document_type_id;
		}

		get_doc_type_sale() {
			return this.l10n_latam_document_type_id;
		}

		set_invoice_payment_term(invoice_payment_term_id) {
			this.assert_editable();
			this.invoice_payment_term_id = invoice_payment_term_id;
		}

		get_invoice_payment_term() {
			return this.invoice_payment_term_id;
		}

		get_payment_term() {
			var plazos_pago = this.get_invoice_payment_term();
			if (!plazos_pago){
				return false;
			}
			var nombre_plazo_pago = this.pos.get_invoice_payment_term(plazos_pago);
			return nombre_plazo_pago ? nombre_plazo_pago.name : false;
		}

		init_from_JSON(json) {
			const res = super.init_from_JSON(...arguments);

			var self = this;
			self.number = json.number || false;
			self.number_ref = json.number_ref || false;
			self.l10n_latam_document_type_id = json.l10n_latam_document_type_id || self.l10n_latam_document_type_id || 0;
			self.invoice_payment_term_id = json.invoice_payment_term_id || self.invoice_payment_term_id || 0;
			self.invoice_sequence_number = json.invoice_sequence_number || 0;
			self.date_invoice = json.date_invoice || false;
			self.pe_invoice_date = json.pe_invoice_date || false;
			json_ordens[json.name] = {
				'serie': self.number,
			}
			if(self.number_ref) {
				json_ordens[json.name]['serie_ref'] = self.number_ref
			}
		}

		export_as_JSON() {
			const res = super.export_as_JSON(...arguments);
			res['l10n_latam_document_type_id'] = this.l10n_latam_document_type_id;
			res['invoice_payment_term_id'] = this.invoice_payment_term_id;
			res['number'] = this.number;
			res['number_ref'] = this.number_ref;
			res['date_invoice'] = moment(new Date().getTime()).format('YYYY/MM/DD');
			res['pe_invoice_date']= this.pe_invoice_date;
			res['branch_id'] = "";
			res['branch_nombre']= "";
			res['branch_direccion']= "";
			res['branch_telefono']= "";
			return res;
		}

		getOrderReceiptEnv() {
			// Formerly get_receipt_render_env defined in ScreenWidget.
			return {
				order: this,
				receipt: this.export_for_printing(),
				orderlines: this.get_orderlines(),
				paymentlines: this.get_paymentlines(),
			};
		}

		export_for_printing(){
			const res = super.export_for_printing(...arguments);
			var self = this;
			var qr_string = self.get_cpe_qr();
			var qrcodesingle = new QRCode(false, {width : 128, height : 128, correctLevel : QRCode.CorrectLevel.Q});
			qrcodesingle.makeCode(qr_string);
			let qrdibujo = qrcodesingle.getDrawing();
			res['sunat_qr_code'] = qrdibujo._canvas_base64;
			//var company = this.pos.company;
			res['branch_id'] = "";
			res['branch_nombre']= "";
			res['branch_direccion']= "";
			res['branch_telefono']= "";

			let company = this.pos.company;
			res["company"]["street"] = company.street
			return res;
		}

		set_number(number) {
			this.assert_editable();
			this.number = number;
			//this.trigger('change',this);
		}

		get_number() {
			let serie = ""
			if(this.number) {
				serie = this.number
			} else if(this.name in json_ordens) {
				serie = json_ordens[this.name]['serie']
			}
			return serie;
		}

		get_number_ref() {
			let serie = ""
			if(this.number_ref) {
				serie = this.number_ref
			} else if(this.name in json_ordens && 'serie_ref' in json_ordens[this.name]) {
				serie = json_ordens[this.name]['serie_ref']
			}
			return serie;
		}

		get_doc_type() {
			var client = this.get_partner();
			if(!client) {
				return false
			}
			var doc_type = client ? client.doc_type : "";
			if(client.parent_id) {
				doc_type = client.cod_doc_rel
			}
			return doc_type;
		}

		get_doc_number() {
			var client = this.get_partner();
			var doc_number = client ? client.doc_number : "";
			if(!client) {
				return "";
			}
			if(client.parent_id) {
				doc_number = client.numero_temp || ""
			}
			return doc_number;
		}

		get_amount_text() {
			let monto = Math.abs(this.get_total_with_tax())
			return numeroALetras(monto, {
											  plural: this.pos.currency.plural_name,
											  singular: this.pos.currency.singular_name,
											  centPlural: this.pos.currency.show_fraction ? this.pos.currency.sfraction_name: "",
											  centSingular: this.pos.currency.show_fraction ? this.pos.currency.sfraction_name: ""
											})
		}
	}
	Registries.Model.extend(Order, CPEOrder);


});

/*
	# Datos del cliente
	doc_type
	doc_number

*/