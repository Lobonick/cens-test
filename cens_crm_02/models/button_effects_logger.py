# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class ButtonEffectsLogger(models.TransientModel):
    _name = 'cens.crm.button.effects.logger'
    _description = 'Logger para efectos de botones personalizados'

    @api.model
    def log_effects_loaded(self):
        """Método para registrar cuando se cargan los efectos"""
        _logger.info("=== CENS CRM 02: Efectos de botones personalizados cargados ===")
        _logger.info("Archivo JavaScript: button_effects.js - CARGADO")
        _logger.info("Archivo SCSS: effects.scss - CARGADO")
        _logger.info("Efectos disponibles: roll_in, slide, explode, fold")
        return True

    @api.model
    def log_effect_execution(self, effect_name, options=None):
        """Método para registrar cuando se ejecuta un efecto"""
        _logger.info(f"🎭 CENS CRM 02: Efecto '{effect_name}' ejecutado")
        if options:
            _logger.info(f"Opciones del efecto: {options}")
        return True