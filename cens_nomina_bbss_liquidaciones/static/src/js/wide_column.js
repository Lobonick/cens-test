odoo.define('cens_nomina_5ta_cat.wide_column', function (require) {
    'use strict';
    
    var ListRenderer = require('web.ListRenderer');
    
    ListRenderer.include({
        _renderView: function () {
            var def = this._super.apply(this, arguments);
            
            def.then(() => {
                // Ancho de columna
                var $nameColumn = this.$('.o_field_widget[name="renta_detail_ids"] th[data-name="name"], .o_field_widget[name="renta_detail_ids"] td[name="name"]');
                if ($nameColumn.length) {
                    $nameColumn.css({
                        'min-width': '600px',
                        'width': '600px',
                        'max-width': '600px'
                    });
                }

                // Colores de fondo
                this.$('.o_data_row').each((index, row) => {
                    var $row = $(row);
                    var name = $row.find('td[name="name"]').text().trim();
                    
                    if (name === 'REMUNERACIÓN PROYECTADA') {
                        $row.find('td').css('background-color', '#fcf3cf'); // Amarillo claro
                    } else if (['RENTA ANUAL PROYECTADA', 'IMPUESTO ANUAL', 'IMPUESTO A PAGAR', 'RETENCIÓN MENSUAL'].includes(name)) {
                        $row.find('td').css('background-color', '#fadbd8'); // Rojo claro
                    }
                });
            });
            
            return def;
        },
    });
});

/**
odoo.define('cens_nomina_5ta_cat.wide_column', function (require) {
    'use strict';
    
    var ListRenderer = require('web.ListRenderer');
    var core = require('web.core');
    
    ListRenderer.include({
        **
         * @override
         *
        _renderView: function () {
            var def = this._super.apply(this, arguments);
            
            def.then(() => {
                var $nameColumn = this.$('th[data-name="name"], td[name="name"]');
                if ($nameColumn.length) {
                    $nameColumn.css({
                        'min-width': '600px',
                        'width': '600px',
                        'max-width': '600px'
                    });
                }
            });
            
            return def;
        },
    });
});

*/