# -*- coding: utf-8 -*-

from odoo import api, models


class LetterManagement(models.Model):
    _inherit = 'letter.management'

    @api.onchange('unique_code_supplier')
    def _onchange_unique_code_supplier(self):  # Codigo unico masivo solo para proveedores
        # Se creó este campo unique_code_supplier porque si se pasaba unique_code a la libreria base,
        # se limpiaba la informacion que contenia de registros anteriores
        for rec in self:
            if rec.exchange_type in ['payment']:
                if rec.operation_methods in ['portfolio']:
                    # if rec.unique_code_supplier:
                    for line in rec.list_letters_ids:
                        if not line.unique_code_supplier:
                            line.unique_code_supplier = rec.unique_code_supplier