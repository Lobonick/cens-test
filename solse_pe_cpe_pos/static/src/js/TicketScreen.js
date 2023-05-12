odoo.define('solse_pe_cpe_pos.TicketScreen', function(require) {
	'use strict';

	const TicketScreen = require('point_of_sale.TicketScreen');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const rpc = require('web.rpc');
	const _t = core._t;
	const QWeb = core.qweb;

	const TicketScreenCPE = TicketScreen =>
		class extends TicketScreen {
			async _onDoRefund() {
	            const order = this.getSelectedSyncedOrder();

	            if (this._doesOrderHaveSoleItem(order)) {
	                if (!this._prepareAutoRefundOnOrder(order)) {
	                    // Don't proceed on refund if preparation returned false.
	                    return;
	                }
	            }

	            if (!order) {
	                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
	                return;
	            }

				let doc_n_credito = order.get_doc_type_sale()
				let doc_venta = this.env.pos.get_doc_type_sale_id(doc_n_credito);
				if(!doc_venta) {
					this.showPopup('ErrorPopup', {
						title: 'Aviso',
						body:'No se encontro el tipo de documento',
					});
					return this.render();
				}
				let nota_credito = doc_venta.nota_credito
				if(!nota_credito) {
					this.showPopup('ErrorPopup', {
						title: 'Aviso',
						body:'Establezca un tipo de comprobante para la nota de crédito',
					});
					return this.render();
				}

	            const partner = order.get_partner();

	            const allToRefundDetails = this._getRefundableDetails(partner);
	            if (allToRefundDetails.length == 0) {
	                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
	                return;
	            }

	            // The order that will contain the refund orderlines.
	            // Use the destinationOrder from props if the order to refund has the same
	            // partner as the destinationOrder.
	            const destinationOrder =
	                this.props.destinationOrder && partner === this.props.destinationOrder.get_partner()
	                    ? this.props.destinationOrder
	                    : this._getEmptyOrder(partner);

	            // Add orderline for each toRefundDetail to the destinationOrder.
	            for (const refundDetail of allToRefundDetails) {
	                const product = this.env.pos.db.get_product_by_id(refundDetail.orderline.productId);
	                const options = this._prepareRefundOrderlineOptions(refundDetail);
	                await destinationOrder.add_product(product, options);
	                refundDetail.destinationOrderUid = destinationOrder.uid;
	            }

	            // Set the partner to the destinationOrder.
	            if (partner && !destinationOrder.get_partner()) {
	                destinationOrder.set_partner(partner);
	                destinationOrder.updatePricelist(partner);
	            }

	            if (this.env.pos.get_order().cid !== destinationOrder.cid) {
	                this.env.pos.set_order(destinationOrder);
	            }
	            destinationOrder.set_doc_type_sale(nota_credito[0]);
	            this._onCloseScreen();
	        }

		}

	Registries.Component.extend(TicketScreen, TicketScreenCPE);

	return TicketScreen;
})