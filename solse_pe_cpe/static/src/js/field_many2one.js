/** @odoo-module */
import { formView } from "@web/views/form/form_view";
import { FormLabel } from "@web/views/form/form_label";
import { Field } from "@web/views/fields/field";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { Many2XAutocomplete, useOpenMany2XRecord } from "@web/views/fields/relational_utils";
const { useState, Component } = owl;
const components = formView.Renderer.components;
import { ForecastedButtons } from "@stock/stock_forecasted/forecasted_buttons";
import { patch } from '@web/core/utils/patch';
var rpc = require('web.rpc');

const { onWillStart } = owl;
/*
patch(Field.prototype, 'edit_field.Field',{
	setup() {
		this._super.apply();
		console.log("ediiiiiiiiiiiiiiiiiiiiiiiiii")
		console.log(this)
		if(this.props.id == 'journal_id') {
			$('#journal_id_1').off('change');
			$('#journal_id_1').on('change', function(){
				alert("cambio")
			})
		}
	},


});
*/

patch(Many2OneField.prototype, 'edit_field.Many2OneField',{
	setup() {
		this._super.apply();
	},

    get Many2XAutocompleteProps() {
        if(this.this.props.name == 'journal_id' && this.this.env.config.viewType == 'form') {
            //$('.o_form_button_save').click()
            console.log("casi pero no")
        }
        return {
            value: this.displayName,
            id: this.props.id,
            placeholder: this.props.placeholder,
            resModel: this.relation,
            autoSelect: true,
            fieldString: this.props.string,
            activeActions: this.state.activeActions,
            update: this.update,
            quickCreate: this.quickCreate,
            context: this.context,
            getDomain: this.getDomain.bind(this),
            nameCreateField: this.props.nameCreateField,
            setInputFloats: this.setFloating,
            autocomplete_container: this.autocompleteContainerRef,
            kanbanViewId: this.props.kanbanViewId,
        };
    },

    async search(barcode) {
        const results = await this.orm.call(this.relation, "name_search", [], {
            name: barcode,
            args: this.getDomain(),
            operator: "ilike",
            limit: 2, // If one result we set directly and if more than one we use normal flow so no need to search more
            context: this.context,
        });
        return results.map((result) => {
            const [id, displayName] = result;
            console.log("antes de retornar cambio")
            return {
                id,
                name: displayName,
            };
        });
    }
	/*get displayName() {
		
		if(this.this.props.name == 'journal_id' && this.this.env.config.viewType == 'form') {
			alert("siiiiii")
			console.log("displayName")
			console.log(this)
			$('.o_form_button_save').click()
		} else {
			console.log("nooooooooooooooooooo")
			console.log(this)
			console.log(this.this)
			console.log(this.this.props.id)
			console.log(this.this.props.name)
		}
        return this.props.value ? this.props.value[1].split("\n")[0] : "";
    }*/


});