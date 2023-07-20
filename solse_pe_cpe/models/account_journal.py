# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)


class AccountJournal(models.Model):
	_inherit = 'account.journal'

	tipo_doc_permitidos = fields.Many2many("l10n_latam.document.type", "diario_id", "tipo_doc_id", "diario_tipo_id", string="Documentos Permitidos")
	mostrar_impuestos_en_cero = fields.Boolean("Mostrar impuestos en cero", default=True)
	
