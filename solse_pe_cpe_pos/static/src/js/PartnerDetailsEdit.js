odoo.define('solse_pe_cpe_pos.PartnerDetailsEdit', function(require) {
	'use strict';

	const PartnerDetailsEdit = require('point_of_sale.PartnerDetailsEdit');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
	const core = require('web.core');
	const _t = core._t;
	const rpc = require('web.rpc');
	const QWeb = core.qweb;
	const { onMounted } = owl;

	const PartnerDetailsEditCPE = PartnerDetailsEdit =>
		class extends PartnerDetailsEdit {
			setup() {
				super.setup();

				onMounted(() => {
					this.iniciarDatos_pe_cpe_pos();
				});
			}
			constructor() {
				super(...arguments);
				//this.intFields = ['country_id', 'state_id', 'property_product_pricelist'];
				this.departamento = null;
				this.provincia = null;
				this.distrito = null;
				this.intFields = ['country_id', 'parent_id', 'state_id', 'city_id', 'l10n_pe_district', 'zip', 'property_product_pricelist'];
				const partner = this.props.partner;
				this.changes = {
					'parent_id': partner.parent_id && partner.parent_id[0],
					'country_id': partner.country_id && partner.country_id[0],
					'state_id': partner.state_id && partner.state_id[0],
					'city_id': partner.city_id && partner.city_id[0],
					'l10n_pe_district': partner.l10n_pe_district && partner.l10n_pe_district[0],
					'l10n_latam_identification_type_id': partner.l10n_latam_identification_type_id && partner.l10n_latam_identification_type_id[0],
				};
			}
			iniciarDatos_pe_cpe_pos(){
				var self = this;
				let datos_c = self.env.pos.partners;
				let partner = this.props.partner;
				console.log("datos de contacto")
				console.log(partner)
				self.departamento = partner.state_id || [];
				self.provincia = partner.city_id || [];
				self.distrito = partner.l10n_pe_district || [];
				self.l10n_latam_identification_type_id = partner.l10n_latam_identification_type_id || [];


				if(self.l10n_latam_identification_type_id) {
					console.log(self.l10n_latam_identification_type_id[0])
					self.changes['l10n_latam_identification_type_id'] = self.l10n_latam_identification_type_id && self.l10n_latam_identification_type_id[0];
				}
				if(partner.country_id) {
					console.log(partner.country_id[0])
					self.changes['country_id'] = partner.country_id && partner.country_id[0];
				}
				if(partner.state_id) {
					console.log(partner.state_id[0])
					self.changes['state_id'] = partner.state_id && partner.state_id[0];
				}
				if(partner.city_id) {
					console.log(partner.city_id[0])
					self.changes['city_id'] = partner.city_id && partner.city_id[0];
				}
				if(partner.l10n_pe_district) {
					console.log(partner.l10n_pe_district[0])
					self.changes['l10n_pe_district'] = partner.l10n_pe_district && partner.l10n_pe_district[0];
				}
				
				//---
				var contents = $('.partner-details');
				if (contents.find("[name='doc_type']").val()==6){
					contents.find('.partner-state').show();
					contents.find('.partner-condition').show();
				}
				else {
					contents.find('.partner-state').hide();
					contents.find('.partner-condition').hide();
				}
				contents.find('.doc_number').on('change',function(event){
						var doc_type = contents.find("[name='l10n_latam_identification_type_id']").val();
						doc_type = self.env.pos.doc_code_by_id[doc_type];
						var doc_number = this.value;
						self.changes['doc_number'] = doc_number;
						self.changes['vat'] = doc_number;
					});
				contents.find("[name='l10n_latam_identification_type_id']").on('change',function(event){
					var doc_type = self.env.pos.doc_code_by_id[this.value];
					var doc_number = contents.find(".doc_number").val();
					if (doc_type=="6"){
						contents.find('.partner-state').show();
						contents.find('.partner-condition').show();
					}
					else{
						contents.find('.partner-state').hide();
						contents.find('.partner-condition').hide();
					}
					self.changes['doc_number'] = doc_number;
					self.changes['vat'] = doc_number;
					self.changes['l10n_latam_identification_type_id'] = this.value;
				});
				//---
				$('.client-address-country').off('change', '');
				$('.client-address-country').on('change', self._changeCountry.bind(self));
				$('#type').off('change', '');
				$('#type').on('change', self._changeType.bind(self));

				$('.client-address-states').off('change', '');
				$('.client-address-states').on('change', self._changeDepartamento.bind(self));
				$('#city_id').off('change', '');
				$('#city_id').on('change', self._onChangeProvincia.bind(self));
				self._changeCountry();
			}
			_changeType() {
				if($("#type").val() == 'contact') {
					$('.contact').show()
					$('.invoice').hide()
				} else {
					$('.contact').hide()
					$('.invoice').show()
				}
			}
			_changeCountry() {
				var self = this;
				if (!$(".client-address-country").val()) {
					return;
				}
				let div = $(".client-address-country")[0];
				if(div.options[div.selectedIndex].text == 'Perú'){
				  $('.div_provincia').show();
				  $('.div_distrito').show();
				  self._changeDepartamento();
				  self._onChangeProvincia();
				} else {
				  $('.div_provincia').hide();
				  $('.div_distrito').hide();
				}
				rpc.query({
					model: 'res.country',
					method: 'get_pos_sale_departamentos',
					args: [{"id": $(".client-address-country").val()}],
				}).then(function (data) {
					// placeholder phone_code
					//$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

					// populate states and display
					var selectStates = $("select[name='state_id']");
					// dont reload state at first loading (done in qweb)
					if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
						if (data.length) {
							selectStates.html('');
							_.each(data, function (x) {
							  let seleccion = x[0] == self.departamento[0] ? ' selected="1" ' : '';
								var opt = $('<option '+seleccion+'>').text(x[1])
									.attr('value', x[0])
									.attr('data-code', x[2]);
								selectStates.append(opt);
							});
							selectStates.parent('div').show();
						} else {
							selectStates.val('').parent('div').hide();
						}
						selectStates.data('init', 0);
					} else {
						selectStates.data('init', 0);
					}
					self._changeDepartamento();
					// manage fields order / visibility
					if (data.fields) {
						if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
							$(".div_zip").before($(".div_city"));
						} else {
							$(".div_zip").after($(".div_city"));
						}
						var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
						_.each(all_fields, function (field) {
							$(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
						});
					}
				});
			}
			_changeDepartamento() {
				var self = this;
				if (!$(".client-address-states").val()) {
					return;
				}
				rpc.query({
					model: 'res.country.state',
					method: 'get_pos_sale_privincias',
					args: [{"id": $(".client-address-states").val()}],
				}).then(function (data) {
				  var selectStates = $("select[name='city_id']");
				  if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
					  if (data.length) {
						  selectStates.html('');
						  var contador = 0;
						  _.each(data, function (x) {
							  let seleccion = x[0] == self.provincia[0] ? ' selected="1" ' : '';
							  if(x[0] == self.provincia[0] || (!self.provincia[0] && contador == 0)) {
								self.changes['city_id'] = x[0];
							  }
							  contador = contador + 1;
							  var opt = $('<option '+seleccion+' >').text(x[1]).attr('value', x[0]).attr('data-code', x[2]);
							  selectStates.append(opt);
						  });
							selectStates.parent('div').show();
							self._changeProvincia();
					  } else {
						  selectStates.val('').parent('div').hide();
					  }
					  selectStates.data('init', 0);
				  } else {
					  selectStates.data('init', 0);
				  }
				  
				});
			}
			_onChangeDepartamento(ev) {
				if (!$('.checkout_autoformat').length) {
					return;
				}
				this._changeDepartamento();
				this._onChangeProvincia();
			}
			_changeProvincia() {
				var self = this;
				if (!$("#city_id").val()) {
				  return;
				}
				let div = $("#city_id")[0];
				$("#city").val(div.options[div.selectedIndex].text);
					rpc.query({
					model: 'res.city',
					method: 'get_pos_sale_distritos',
					args: [{"id": $("#city_id").val()}],
				}).then(function (data) {
				  var selectStates = $("select[name='l10n_pe_district']");
				  if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
					  if (data.length) {
						  selectStates.html('');
						  var contador_distritos = 0;
						  _.each(data, function (x) {
							let seleccion = x[0] == self.distrito[0] ? ' selected="1" ' : '';
							if(x[0] == self.distrito[0] || (!self.distrito[0] && contador_distritos == 0)) {
								self.changes['l10n_pe_district'] = x[0];
								self.changes['zip'] = x[2];
								$("input[name='zip']").val(x[2])
							  }
							  contador_distritos = contador_distritos + 1;

							  var opt = $('<option '+seleccion+'>').text(x[1])
								  .attr('value', x[0])
								  .attr('data-code', x[2]);
							  selectStates.append(opt);
						  });
						  selectStates.parent('div').show();
					  } else {
						  selectStates.val('').parent('div').hide();
					  }
					  selectStates.data('init', 0);
					} else {
						selectStates.data('init', 0);
					}
				});
			}
			_onChangeProvincia(ev) {
				/*if (!this.$('.checkout_autoformat').length) {
					return;
				}*/
				this._changeProvincia();
			}
		};

	Registries.Component.extend(PartnerDetailsEdit, PartnerDetailsEditCPE);

	return PartnerDetailsEdit;
});
