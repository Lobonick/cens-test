odoo.define('cens_crm.popup_message', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');

    var _t = core._t;

    function openPopupMessage() {
        var dialog = new Dialog(null, {
            title: _t('Popup Message'),
            size: 'medium',
            buttons: [
                {
                    text: _t('ACEPTAR'),
                    classes: 'btn-primary',
                    close: true,
                },
            ],
            $content: $('<div>', {
                html: '<img src="/web/image/109230-73c85c92/TelcoGo%20-%20Icono%20-%20Low.png?access_token=db39d2cf-10bb-423f-8f2d-ec93f866322a" alt="Image"/>' +
                '<p>ESTE ES EL PINCHE MENSAJE.</p>',
                class: 'popup-message-content',
            }),
        });
        dialog.open();
    }

    return {
        openPopupMessage: openPopupMessage,
    };
});