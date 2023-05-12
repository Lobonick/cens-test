odoo.define('solse_pe_cpe_pos.pos_screens', function(require) {
  "use strict";

var models = require('point_of_sale.models');
var PosDB = require('point_of_sale.DB');
var core    = require('web.core');
var rpc = require('web.rpc');
var concurrency = require('web.concurrency');
var QWeb = core.qweb;
var PosModelSuper = models.PosModel;
var PosDBSuper = PosDB;
var OrderSuper = models.Order;
var Mutex = concurrency.Mutex;
var _t      = core._t;
var json_ordens = {}


	models.load_models(
		[{
			model: 'account.payment.term',
			fields: [],
			domain: function (self) { return []; },
			loaded: function (self, plazos_pago) {
				self.invoice_payment_term_ids = plazos_pago;
				self.db.add_invoice_payment_term(plazos_pago);
			},
		}]
	);

	models.load_models(
		[{
			model: 'l10n_latam.document.type',
			fields: [],
			domain: function (self) { return [['id', 'in', self.config.documento_venta_ids]]; },
			loaded: function (self, documentos_venta) {
				self.l10n_latam_document_type_ids = documentos_venta;
				self.db.add_doc_type_sale(documentos_venta);
			},
		}]
	);

});