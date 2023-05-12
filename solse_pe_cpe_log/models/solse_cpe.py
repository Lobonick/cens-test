# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class SolseCPE(models.Model):
	_inherit = 'solse.cpe'

	no_enviar_rnoaceptados = fields.Boolean("No reintentar envió")
	cant_intentos = fields.Integer("Cant. Intentos", default=0, help="Cantidad de reintentos de envio a sunat")

	def obtener_dominio_pendientes(self):
		dominio = [('type', 'in', ['sync']), ('no_enviar_rnoaceptados', '=', False), ('estado_sunat', 'not in', ['05', '11', '13'])]
		dominio.append(('cant_intentos', '<', 6))

		#send_date
		return dominio

	def procesar_cpes_reenviar(self, cpe_count=None):
		pendientes = self.env['solse.cpe'].search(self.obtener_dominio_pendientes())
		pendientes_procesar = pendientes[0:cpe_count] if cpe_count else pendientes
		for cpe in pendientes_procesar:
			factura = cpe.invoice_ids[0]
			es_sync = factura.l10n_latam_document_type_id.is_synchronous
			cant_int = 7
			if es_sync:
				cpe.action_cancel()
				cpe.action_draft()
				cpe.action_generate()
				cpe.action_send()
				cant_int = cpe.cant_intentos + 1
				
			cpe.write({"cant_intentos": cant_int})

		cant_pendientes = len(pendientes) - len(pendientes_procesar)
		if cant_pendientes > 0:
			self.env.ref('solse_pe_cpe_log.ir_cron_procesar_cpe')._trigger()


	def obtener_dominio_consultar_estado(self):
		dominio = [('type', 'in', ['sync']), ('no_enviar_rnoaceptados', '=', False), ('error_code', 'in', ['2109', '1033'])]
		return dominio

	def procesar_cpes_consultar_estado(self, cpe_count=None):
		pendientes = self.env['solse.cpe'].search(self.obtener_dominio_consultar_estado())

		dominio = [('type', 'in', ['sync']), ('no_enviar_rnoaceptados', '=', False), ("response", "=ilike", "%ha sido aceptada%"), ("estado_sunat", "in", ["07","09"])]
		pendientes_n2 = self.env['solse.cpe'].search(dominio)

		if pendientes:
			pendientes_procesar = pendientes[0:cpe_count] if cpe_count else pendientes
			for cpe in pendientes_procesar:
				cpe.action_document_status()

		if pendientes_n2:
			pendientes_procesar_n2 = pendientes_n2[0:cpe_count] if cpe_count else pendientes_n2
			for cpe in pendientes_procesar_n2:
				cpe.action_document_status()

		dominio_n3 = [('type', 'in', ['sync']), ('no_enviar_rnoaceptados', '=', False), ("datas_response", "!=", False), ("estado_sunat", "in", ["01"])]
		pendientes_n3 = self.env['solse.cpe'].search(dominio_n3)

		if pendientes_n3:
			pendientes_procesar_n3 = pendientes_n3[0:cpe_count] if cpe_count else pendientes_n3
			for cpe in pendientes_procesar_n3:
				cpe.action_document_status()
		