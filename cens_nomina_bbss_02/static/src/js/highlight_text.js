odoo.define('cens_contratos_plantilla.HighlightTextWidget', function (require) {
    'use strict';

    var basic_fields = require('web.basic_fields');
    var field_registry = require('web.field_registry');
    var core = require('web.core');

    var HighlightText = basic_fields.FieldText.extend({
        _renderReadonly: function () {
            var highlight_word = 'EMPRESA';  // La palabra a resaltar
            var regex = new RegExp(`(${highlight_word})`, 'gi');
            var highlighted_content = (this.value || '').replace(regex, '<span style="color: red;">$1</span>');
            this.$el.html(highlighted_content);
        }
    });

    field_registry.add('highlight_text', HighlightText);

    return {
        HighlightText: HighlightText
    };
});