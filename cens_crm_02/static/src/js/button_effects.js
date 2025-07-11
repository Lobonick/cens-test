odoo.define('cens_crm_02.button_effects', function (require) {
    "use strict";
    
    var core = require('web.core');
    var session = require('web.session');
    var rpc = require('web.rpc');
    
    console.log("=== CENS CRM 02: Iniciando carga de efectos personalizados ===");
    
    // Función para enviar logs al servidor Odoo
    function logToOdoo(message, level) {
        level = level || 'info';
        rpc.query({
            model: 'ir.logging',
            method: 'create',
            args: [{
                'name': 'cens_crm_02.button_effects',
                'level': level,
                'message': message,
                'path': 'static/src/js/button_effects.js',
                'func': 'button_effects',
                'line': '1'
            }]
        }).then(function() {
            console.log("Log enviado a Odoo: " + message);
        }).catch(function(error) {
            console.log("Error enviando log a Odoo:", error);
        });
    }
    
    // Esperamos a que Odoo esté completamente cargado
    $(document).ready(function() {
        console.log("=== CENS CRM 02: DOM Ready - Verificando registry ===");
        logToOdoo("Iniciando registro de efectos personalizados");
        
        // Verificamos si el registry existe
        if (core.effect_registry) {
            console.log("✅ CENS CRM 02: Effect registry encontrado - Registrando efectos...");
            logToOdoo("Effect registry encontrado correctamente");
            
            try {
                // Registrar efecto roll_in
                core.effect_registry.add('roll_in', function(element, options) {
                    console.log("🎭 CENS CRM 02: Ejecutando efecto roll_in", options);
                    logToOdoo("Efecto roll_in ejecutado correctamente");
                    var $element = $(element);
                    
                    // Aplicar la animación CSS
                    $element.addClass('o_roll_in_effect');
                    console.log("🎨 CENS CRM 02: roll_in - Clase CSS aplicada");
                
                // Mensaje de efecto si existe
                if (options && options.message) {
                    var $message = $('<div class="o_effect_message">' + options.message + '</div>');
                    $('body').append($message);
                    
                    // Mostrar la imagen si existe
                    if (options.img_url) {
                        var $img = $('<img src="' + options.img_url + '" style="width: 64px; height: 64px;">');
                        $message.prepend($img);
                    }
                    
                    // Configurar fadeout
                    var fadeoutSpeed = options.fadeout || 'medium';
                    var fadeoutTime = fadeoutSpeed === 'fast' ? 1000 : 
                                     fadeoutSpeed === 'medium' ? 2000 : 
                                     fadeoutSpeed === 'slow' ? 4000 : 2000;
                    
                    setTimeout(function() {
                        $message.fadeOut(500, function() {
                            $message.remove();
                        });
                    }, fadeoutTime);
                }
                
                // Remover clase de animación después de la animación
                setTimeout(function() {
                    $element.removeClass('o_roll_in_effect');
                }, 1000);
                
                return $element;
            });
            
                // Registrar otros efectos
                core.effect_registry.add('slide', function(element, options) {
                    console.log("🎭 CENS CRM 02: Ejecutando efecto slide", options);
                    logToOdoo("Efecto slide ejecutado correctamente");
                    var $element = $(element);
                    $element.addClass('o_slide_effect');
                    
                    if (options && options.message) {
                        // Similar lógica para mensaje
                        core.bus.trigger('notification', {
                            type: 'info',
                            title: options.message,
                            sticky: false
                        });
                    }
                    
                    setTimeout(function() {
                        $element.removeClass('o_slide_effect');
                    }, 1000);
                    
                    return $element;
                });
                
                core.effect_registry.add('explode', function(element, options) {
                    console.log("🎭 CENS CRM 02: Ejecutando efecto explode", options);
                    logToOdoo("Efecto explode ejecutado correctamente");
                    var $element = $(element);
                    $element.addClass('o_explode_effect');
                    
                    if (options && options.message) {
                        core.bus.trigger('notification', {
                            type: 'info',
                            title: options.message,
                            sticky: false
                        });
                    }
                    
                    setTimeout(function() {
                        $element.removeClass('o_explode_effect');
                    }, 1000);
                    
                    return $element;
                });
                
                console.log("✅ CENS CRM 02: Todos los efectos registrados correctamente");
                console.log("📋 CENS CRM 02: Efectos disponibles:", Object.keys(core.effect_registry.map));
                logToOdoo("Efectos personalizados registrados: " + Object.keys(core.effect_registry.map).join(', '));
                
            } catch (error) {
                console.error("❌ CENS CRM 02: Error registrando efectos:", error);
                logToOdoo("Error registrando efectos: " + error.message, 'error');
            }
        } else {
            console.error("❌ CENS CRM 02: Effect registry NO encontrado");
            logToOdoo("Error: Effect registry no encontrado", 'error');
        }
    });
    
    console.log("=== CENS CRM 02: Archivo button_effects.js cargado completamente ===");
    logToOdoo("Archivo button_effects.js cargado completamente");
});