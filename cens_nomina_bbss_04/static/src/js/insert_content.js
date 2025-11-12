odoo.define('cens_contratos_plantilla.insert_content', function (require) {
    'use strict';

    var core = require('web.core');
    var FormController = require('web.FormController');

    var _t = core._t;

    FormController.include({
        _onButtonClicked: function (event) {
            var self = this;
            var def = this._super.apply(this, arguments);
            if (event.data.action.tag === 'insert_content') {
                var fieldNames = event.data.action.params.field_names;
                var insertValue = event.data.action.params.insert_value;
                if (fieldNames && fieldNames.length && insertValue) {
                    var $targetField = null;
                    var $activeElement = $(document.activeElement);
                    for (var i = 0; i < fieldNames.length; i++) {
                        $targetField = this.renderer.$('.o_field_widget[name="' + fieldNames[i] + '"]');
                        if ($activeElement.parents('.o_field_widget').is($targetField)) {
                            break;
                        }
                    }
                    if ($targetField && $targetField.length) {
                        var targetField = $targetField[0];
                        var startPos = targetField.selectionStart;
                        var endPos = targetField.selectionEnd;
                        var currentValue = targetField.value;
                        var newValue = currentValue.substring(0, startPos) + insertValue + currentValue.substring(endPos);
                        targetField.value = newValue;
                        targetField.setSelectionRange(startPos + insertValue.length, startPos + insertValue.length);
                    } else {
                        this.do_warn(_t('Field Not Found'), _t('The target field was not found in the form.'));
                    }
                }
            }
            return def;
        },
    });

});