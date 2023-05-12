odoo.define('solse_pe_cpe_pos.InvoiceButton', function(require) {
	'use strict';

	const InvoiceButton = require('point_of_sale.InvoiceButton');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const _t = core._t;
	const QWeb = core.qweb;

    //const SaleOrderFetcher = require('point_of_sale.SaleOrderFetcher');

	const InvoiceButtonCPE = InvoiceButton =>
		class extends InvoiceButton {

			async _invoiceOrder() {
	            const order = this.props.order;
	            if (!order) return;

	            const orderId = order.backendId;

	            // Part 0. If already invoiced, print the invoice.
	            if (this.isAlreadyInvoiced) {
	                await this._downloadInvoice(orderId);
	                return;
	            }

	            // Part 1: Handle missing partner.
	            // Write to pos.order the selected partner.
	            if (!order.get_partner()) {
	                const { confirmed: confirmedPopup } = await this.showPopup('ConfirmPopup', {
	                    title: this.env._t('Need customer to invoice'),
	                    body: this.env._t('Do you want to open the customer list to select customer?'),
	                });
	                if (!confirmedPopup) return;

	                const { confirmed: confirmedTempScreen, payload: newPartner } = await this.showTempScreen(
	                    'PartnerListScreen'
	                );
	                if (!confirmedTempScreen) return;

	                await this.rpc({
	                    model: 'pos.order',
	                    method: 'write',
	                    args: [[orderId], { partner_id: newPartner.id }],
	                    kwargs: { context: this.env.session.user_context },
	                });
	            }

	            // Part 2: Invoice the order.
	            await this.rpc(
	                {
	                    model: 'pos.order',
	                    method: 'action_pos_order_invoice',
	                    args: [orderId],
	                    kwargs: { context: this.env.session.user_context },
	                },
	                {
	                    timeout: 30000,
	                    shadow: true,
	                }
	            );

	            // Part 3: Download invoice.
	            await this._downloadInvoice(orderId);
	            this.trigger('order-invoiced', orderId);
	        }
		};

	Registries.Component.extend(InvoiceButton, InvoiceButtonCPE);
	return InvoiceButton;
});