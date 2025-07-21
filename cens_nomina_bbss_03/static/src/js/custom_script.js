odoo.define('your_module.custom_script', function (require) {
    "use strict";
    
    var FormController = require('web.FormController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    
    FormController.include({
        _saveRecord: function () {
            var self = this;
            var confirmMessage = "Are you sure you want to save?"; // Aquí mensaje de confirmación
            
            Dialog.confirm(this, confirmMessage, {
                confirm_callback: function () {
                    self._super.apply(self, arguments);
                },
                cancel_callback: function () {
                    // # Realizar acciones cuando el usuario cancela la acción de guardar.
                    //  ...
                },
            });
        },
    });
});