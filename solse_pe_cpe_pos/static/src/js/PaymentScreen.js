var ejecutando = false;
odoo.define('solse_pe_cpe_pos.PaymentScreen', function(require) {
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const rpc = require('web.rpc');
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const { isConnectionError } = require('point_of_sale.utils');
	const _t = core._t;
	const QWeb = core.qweb;
	const { onMounted } = owl;

	const PaymentScreenCPE = PaymentScreen =>
		class extends PaymentScreen {
			setup() {
				super.setup();

				onMounted(() => {
					this.inicioPago();
					this.mostrarTiposDocumentos(this.currentOrder)
				});
				
			}

			async validate_journal_invoice() {
				var self = this;
				var order = this.env.pos.get_order();
				var client = order.get_partner();
				

				if(!client){
					if(order.es_cpe() && this.env.pos.config.cliente_varios) {
						order.set_partner(this.env.pos.db.get_partner_by_id(this.env.pos.config.cliente_varios[0]));
					}
					client = order.get_partner();
				}

				if(!client){
					if(order.es_cpe()) {

					}
					self.showPopup('ErrorTracebackPopup',{
								  'title': _t('Error en cliente'),
								  'body':  _t('El cliente es necesario'
									),
							});
					res = true;
				}

				var doc_type = order.get_doc_type();
				var doc_number = order.get_doc_number();
				let val_diario = order.check_pe_journal(doc_type, doc_number);
				if(!val_diario[0]){
					self.showPopup('ErrorTracebackPopup',{
						  'title': _t('Error en el diario'),
						  'body':  val_diario[1],
					});
					return true;
				}
				var res = false;
				var is_validate = this.env.pos.validate_pe_doc(doc_type, doc_number);
				var cpe_type = order.get_cpe_type();
				var err_lines = false;

				/*let lineas = order.orderlines.models;
				for(let indice in lineas) {
					let registro = lineas[indice]
					if(registro.price == 0) */

				let lineas = order.orderlines.models;
				for(let indice in lineas) {
					let registro = lineas[indice]
					if(registro.price == 0) {
						self.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'El monto de las lineas no puede ser 0 para un comprobante electronico',
						});
						res = true;
					}
					if(registro.quantity == 0) {
						self.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'La cantidad no puede ser 0 para un comprobante electronico',
						});
						res = true;
					}
					/*if(!registro.quantity == 0) {
						this.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'La cantidad no puede ser 0 para un comprobante electronico',
						});
						ejecutando = false;
						return false
					}*/
				}


				/*var error_um = false;
				error_um = order.orderlines.each(_.bind( function(item) {
					if ((item.get_quantity() <= 0 || item.get_unit_price() <= 0) && !error_um) {
						return true;    
					}
					
				}, this));

				if (error_um){
					self.showPopup('ErrorTracebackPopup',{
								  'title': _t('Error en lineas de Pedido'),
								  'body':  _t('Debe establecer una unidad de medida para el producto'
									),
							});
					res = true;
				}*/
				
				
				if (self.env.pos.company.sunat_amount< order.get_total_with_tax() && !doc_type && !doc_number){
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('An anonymous order cannot be invoiced'),
								'body': _t('Debe seleccionar un cliente con RUC ó DNI válido antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}

				if ( ['1', '6'].indexOf(doc_type)!=-1 && !is_validate){
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								title: _t('Please select the Customer'),
								body: _t('Debe seleccionar un cliente con RUC ó DNI válido antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				/*if ( ['01', '03'].indexOf(cpe_type)==-1){
				   self.showPopup('ErrorTracebackPopup','No se puede emitir ese tipo de bono. Configura bien tu diario');
					res = true;
				}*/
				if (cpe_type=='01' && doc_type!='6') {
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('Please select the Customer'),
								'body': _t('Debe seleccionar un cliente con RUC antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				if (cpe_type=='03' && doc_type=='6') {
					const { confirmed } = await self.showPopup('ConfirmPopup',{
								'title': _t('Please select the Customer'),
								'body': _t('Debe seleccionar un cliente con DNI antes de poder facturar su pedido.'),
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				if (cpe_type=='03' && doc_type != '1' && self.env.pos.company.sunat_amount <  order.get_total_with_tax()) {
					self.showPopup('ErrorTracebackPopup',{
						  'title': 'Aviso',
						  'body':  'Para montos iguales o mayores a '+self.env.pos.company.sunat_amount+' Son obligatorios el Tipo de Doc. y Numero',
					});
					/*if (confirmed) {
						self.showScreen('ClientListScreen');
					}*/
					res = true;
				}
				order.pe_invoice_date = moment(new Date().getTime()).format('YYYY-MM-DD HH:mm:ss');
				return res;
				
			}
			mostrarTiposDocumentos(newOrder){
				var self = this;
				var sale_journals = this.render_sale_journals();
				//$('.payment-buttons').html('');
				$('.js_invoice').css({'display': 'none'});
				sale_journals.appendTo($('.payment-buttons'));
				$('.js_sale_journal').click(function () {
					self.click_sale_journals($(this).data('id'));
				});
				if(newOrder.l10n_latam_document_type_id) {
					newOrder.set_to_invoice(true);
					$('.js_sale_journal').removeClass('highlight');
					$('div[data-id="' + newOrder.l10n_latam_document_type_id + '"]').addClass('highlight');
				}
			}
			render_sale_journals() {
				var self = this;
				var order = this.env.pos.get_order();
				var sale_journals = $(QWeb.render('SaleInvoiceJournal', { widget: this.env }));
				return sale_journals;
			}
			click_sale_journals(doc_type_sale_id) {
				var order = this.env.pos.get_order();
				//$('.js_invoice').click();
				order.set_to_invoice(true);
				this.render();

				if (order.get_doc_type_sale() != doc_type_sale_id) {
					order.set_doc_type_sale(doc_type_sale_id);
					$('.js_sale_journal').removeClass('highlight');
					$('div[data-id="' + doc_type_sale_id + '"]').addClass('highlight');
				} else {
					order.set_doc_type_sale(false);
					$('.js_sale_journal').removeClass('highlight');
				}
			}
			async _isOrderValid(isForceValidate) {
				var order = this.env.pos.get_order();
				var tipo_doc_venta = order.get_cpe_type()
				let monto_orden = order.get_total_with_tax()

				let lineas = order.orderlines.models;
				for(let indice in lineas) {
					let registro = lineas[indice]
					if(registro.price == 0) {
						this.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'El monto de las lineas no puede ser 0 para un comprobante electronico',
						});
						ejecutando = false;
						return false
					}
					if(registro.quantity == 0) {
						this.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'La cantidad no puede ser 0 para un comprobante electronico',
						});
						ejecutando = false;
						return false
					}
					/*if(!registro.quantity == 0) {
						this.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'La cantidad no puede ser 0 para un comprobante electronico',
						});
						ejecutando = false;
						return false
					}*/
				}
				//return false;

				if(!tipo_doc_venta){
					if(monto_orden >= 0) {
						if(this.env.pos.config.doc_venta_defecto) {
							this.click_sale_journals(this.env.pos.config.doc_venta_defecto[0]);
						} else {
							this.showPopup('ErrorPopup', {
								title: 'Aviso',
								body: 'Defina un tipo de documento para el comprobante',
							});
							ejecutando = false;
							return false;
						}
					} else {
						this.showPopup('ErrorPopup', {
							title: 'Aviso',
							body: 'Defina un tipo de documento para el comprobante',
						});
						ejecutando = false;
						return false
						/*console.log("nota de credito")
						console.log(this)
						console.log(order)*/
					}
				}
				

				var client = order.get_partner();
				if(!client){
					if(order.es_cpe() && this.env.pos.config.cliente_varios) {
						order.set_partner(this.env.pos.db.get_partner_by_id(this.env.pos.config.cliente_varios[0]));
					}
				}
				
				var res = super._isOrderValid(isForceValidate);
				if (!res) {
					return res;
				}
				if(order.es_cpe()) {
					if (await this.validate_journal_invoice()) {
						return false;
					}
				}
				return res;
			}
			async validateOrder(isForceValidate) {
				if(ejecutando) {
					return;
				}
				ejecutando = true;
				if(this.env.pos.config.cash_rounding) {
					if(!this.env.pos.get_order().check_paymentlines_rounding()) {
						this.showPopup('ErrorPopup', {
							title: this.env._t('Rounding error in payment lines'),
							body: this.env._t("The amount of your payment lines must be rounded to validate the transaction."),
						});
						return;
					}
				}
				if (await this._isOrderValid(isForceValidate)) {
					// remove pending payments before finalizing the validation
					for (let line of this.paymentLines) {
						if (!line.is_done()) this.currentOrder.remove_paymentline(line);
					}
					await this._finalizeValidation();
				}
				ejecutando = false;
			}
			validar_plazo_pago() {
				let condicion = $('.div_cuotas_credito').css('display')
				if(condicion != 'block') {
					return true
				} else {
					if($('.plazo_pago').val() == "0") {
						this.showPopup('ErrorPopup', {
							title: "Aviso",
							body: "Seleccione un plazo de pago",
						});
						ejecutando = false;
						return false;
					} else {
						var order = this.env.pos.get_order();
						order.set_invoice_payment_term($('.plazo_pago').val());
						return true;
					}
				}
			}
			validarSerieOffline() {
				let serie = "";
				//serie = "F002-545454";
				return serie;
			}
			async _finalizeValidation() {
				let rpt_validar_plazo = await this.validar_plazo_pago();
				if(!rpt_validar_plazo) {
					return;
				}
				if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
					this.env.proxy.printer.open_cashbox();
				}

				this.currentOrder.initialize_validation_date();
				this.currentOrder.finalized = true;

				let syncOrderResult, hasError;

				try {
					// 1. Save order to server.
					syncOrderResult = await this.env.pos.push_single_order(this.currentOrder);

					// 2. Invoice.
					if (this.currentOrder.is_to_invoice()) {
						if (syncOrderResult.length) {
							/*await this.env.legacyActionManager.do_action('account.account_invoices', {
								additional_context: {
									active_ids: [syncOrderResult[0].account_move],
								},
							});*/
							let data = await rpc.query({
								model: 'pos.order',
								method: 'generar_enviar_xml_cpe',
								args: [{"pos_order_id": [syncOrderResult[0].id]}],
							})
							if(data.length > 0) {
								this.currentOrder.number = data[0]['serie']
								//this.currentOrder.set_number(data[0]['serie'])
								if('serie_referencia' in data[0]) {
									this.currentOrder.number_ref = data[0]['serie_referencia'];
								}
							} else {
								await this.showPopup('ErrorPopup', {
									title: 'Aviso.',
									body: 'No se pudo recuperar la serie, porfavor reimprima el comprobante',
								});
							}
						} else {
							throw { code: 401, message: 'Backend Invoice', data: { order: this.currentOrder } };
						}
					}

					// 3. Post process.
					if (syncOrderResult.length && this.currentOrder.wait_for_push_order()) {
						const postPushResult = await this._postPushOrderResolve(
							this.currentOrder,
							syncOrderResult.map((res) => res.id)
						);
						if (!postPushResult) {
							this.showPopup('ErrorPopup', {
								title: this.env._t('Error: no internet connection.'),
								body: this.env._t('Some, if not all, post-processing after syncing order failed.'),
							});
						}
					}
				} catch (error) {
					hasError = true;

					if (error.code == 700)
						this.error = true;

					if ('code' in error) {
						// We started putting `code` in the rejected object for invoicing error.
						// We can continue with that convention such that when the error has `code`,
						// then it is an error when invoicing. Besides, _handlePushOrderError was
						// introduce to handle invoicing error logic.
						await this._handlePushOrderError(error);
					} else {
						// We don't block for connection error. But we rethrow for any other errors.
						if (isConnectionError(error)) {
							this.showPopup('OfflineErrorPopup', {
								title: this.env._t('Connection Error'),
								body: this.env._t('Order is not synced. Check your internet connection'),
							});
							let correlativo = this.validarSerieOffline()
							if(correlativo) {
								this.currentOrder.number = correlativo;
								this.env.pos.push_single_order(this.currentOrder);
							} else {
								this.showPopup('OfflineErrorPopup', {
									title: this.env._t('Connection Error'),
									body: "No se pudo obtener la serie, esta sera generada automáticamente una vez el pedido se sincronice. Vuelva a imprimir la factura una vez el pedido este sincronizado.",
								});
							}
						} else {
							throw error;
						}
					}
				} finally {
					// Always show the next screen regardless of error since pos has to
					// continue working even offline.
					this.showScreen(this.nextScreen);
					// Remove the order from the local storage so that when we refresh the page, the order
					// won't be there
					this.env.pos.db.remove_unpaid_order(this.currentOrder);

					// Ask the user to sync the remaining unsynced orders.
					if (!hasError && syncOrderResult && this.env.pos.db.get_orders().length) {
						const { confirmed } = await this.showPopup('ConfirmPopup', {
							title: this.env._t('Remaining unsynced orders'),
							body: this.env._t(
								'There are unsynced orders. Do you want to sync these orders?'
							),
						});
						if (confirmed) {
							// NOTE: Not yet sure if this should be awaited or not.
							// If awaited, some operations like changing screen
							// might not work.
							this.env.pos.push_orders();
						}
					}
				}
			}
			async _finalizeValidationAnterior() {
				let rpt_validar_plazo = await this.validar_plazo_pago();
				if(!rpt_validar_plazo) {
					return;
				}
				if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
					this.env.pos.proxy.printer.open_cashbox();
				}

				this.currentOrder.initialize_validation_date();
				
				var order = this.env.pos.get_order();
				let syncedOrderBackendIds = [];
				var self = this;
				var ejecutar = true;
				try {
					let tipo_doc_venta = self.currentOrder.get_cpe_type()
					let validar_tipo_doc = tipo_doc_venta != false && tipo_doc_venta != '00'  ? true : false;
					//if (self.currentOrder.is_to_invoice() && validar_tipo_doc) {
					if (self.currentOrder.is_to_invoice()) {
						ejecutar = false;
						syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
							self.currentOrder
						);
						let data = await rpc.query({
							model: 'pos.order',
							method: 'generar_enviar_xml_cpe',
							args: [{"pos_order_id": syncedOrderBackendIds}],
						})
						if(data.length > 0) {
							order.set_number(data[0]['serie'])
							if('serie_referencia' in data[0]) {
								order.number_ref = data[0]['serie_referencia'];
							}
						} else {
							await this.showPopup('ErrorPopup', {
								title: 'Aviso.',
								body: 'No se pudo recuperar la serie, porfavor reimprima el comprobante',
							});
						}

						self.currentOrder.finalized = true;
						self.showScreen(self.nextScreen);




						if (syncOrderResult.length) {
							await this.env.legacyActionManager.do_action('account.account_invoices', {
								additional_context: {
									active_ids: [syncOrderResult[0].account_move],
								},
							});

							let data = await rpc.query({
								model: 'pos.order',
								method: 'generar_enviar_xml_cpe',
								args: [{"pos_order_id": syncedOrderBackendIds}],
							})
							if(data.length > 0) {
								order.set_number(data[0]['serie'])
								if('serie_referencia' in data[0]) {
									order.number_ref = data[0]['serie_referencia'];
								}
							} else {
								await this.showPopup('ErrorPopup', {
									title: 'Aviso.',
									body: 'No se pudo recuperar la serie, porfavor reimprima el comprobante',
								});
							}

							self.currentOrder.finalized = true;
							self.showScreen(self.nextScreen);

						} else {
							throw { code: 401, message: 'Backend Invoice', data: { order: this.currentOrder } };
						}


					} else {
						self.currentOrder.finalized = true;
						syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
					}
				} catch (error) {
					self.currentOrder.finalized = true;
					if (error.code == 700)
						this.error = true;
					if (error instanceof Error) {
						throw error;
					} else {
						await this._handlePushOrderError(error);
					}
				}
				if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
					const result = await this._postPushOrderResolve(
						this.currentOrder,
						syncedOrderBackendIds
					);
					if (!result) {
						await this.showPopup('ErrorPopup', {
							title: 'Error: no internet connection.',
							body: error,
						});
					}
				}
				if (ejecutar == true) {
					this.showScreen(this.nextScreen);
				}
				

				// If we succeeded in syncing the current order, and
				// there are still other orders that are left unsynced,
				// we ask the user if he is willing to wait and sync them.
				if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
					const { confirmed } = await this.showPopup('ConfirmPopup', {
						title: this.env._t('Remaining unsynced orders'),
						body: this.env._t(
							'There are unsynced orders. Do you want to sync these orders?'
						),
					});
					if (confirmed) {
						// NOTE: Not yet sure if this should be awaited or not.
						// If awaited, some operations like changing screen
						// might not work.
						this.env.pos.push_orders();
					}
				}
			}


			addNewPaymentLine({ detail: paymentMethod }) {
				for(let indice in this.paymentLines) {
					let registro = this.paymentLines[indice];
					if(registro.payment_method.type == 'pay_later') {
						return;
					}
				}
				var order = this.env.pos.get_order();
				
				let estado = false;
				// original function: click_paymentmethods
				if (this.currentOrder.electronic_payment_in_progress()) {
					this.showPopup('ErrorPopup', {
						title: this.env._t('Error'),
						body: this.env._t('There is already an electronic payment in progress.'),
					});
					estado = false;
				} else {
					this.currentOrder.add_paymentline(paymentMethod);
					NumberBuffer.reset();
					this.payment_interface = paymentMethod.payment_terminal;
					if (this.payment_interface) {
						this.currentOrder.selected_paymentline.set_payment_status('pending');
					}
					estado = true;
				}
				setTimeout(function(){
					if(paymentMethod.type == 'pay_later') {
						$('.div_cuotas_credito').css('display', 'block')
						//order.set_invoice_payment_term(doc_type_sale_id);
					} else {
						$('.div_cuotas_credito').css('display', 'none')
					}
				}, 500)
				
				this.validar_monto_pago()
				return estado;
			}

			inicioPago() {
				ejecutando = false;
				$('.div_cuotas_credito').css('display', 'none')
				for(let indice in this.paymentLines) {
					let registro = this.paymentLines[indice];
					if(registro.payment_method.type == 'pay_later') {
						$('.div_cuotas_credito').css('display', 'block')
					}
				}
			}

			_updateSelectedPaymentline() {
				var res = super._updateSelectedPaymentline();
				this.validar_monto_pago()
				return res;
	        }

	        deletePaymentLine(event) {
	        	var res = super.deletePaymentLine(event);
				this.validar_monto_pago()
				return res;
	        }

	        validar_monto_pago() {
	        	if(this.currentOrder.get_due() > 0) {
					$('.payment-numpad').css('display', 'block');
				} else if(this.tiene_pago_con_banco()){
					$('.payment-numpad').css('display', 'none');
				} else {
					$('.payment-numpad').css('display', 'block');
				}
	        }
	        tiene_pago_con_banco() {
	        	for(let indice in this.paymentLines) {
					let registro = this.paymentLines[indice];
					if(registro.payment_method.type == 'bank') {
						return true;
					}
				}
	        	return false;
	        }
		};

	Registries.Component.extend(PaymentScreen, PaymentScreenCPE);

	return PaymentScreen;
});
