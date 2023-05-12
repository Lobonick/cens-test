odoo.define('solse_pe_cpe_pos.PartnerListScreen', function(require) {
    'use strict';

    const PartnerListScreen = require('point_of_sale.PartnerListScreen');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');
    const core = require('web.core');
    const _t = core._t;
    const QWeb = core.qweb;

    const PartnerListScreenCPE = PartnerListScreen =>
        class extends PartnerListScreen {
        	constructor() {
            	super(...arguments);
            	this.departamento = null;
			    this.provincia = null;
			    this.distrito = null;
            }
            
		    editClient(){
		        super.editClient();    
		    }
        };

    Registries.Component.extend(PartnerListScreen, PartnerListScreenCPE);

    return PartnerListScreen;
});
