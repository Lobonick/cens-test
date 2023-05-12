# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PosInvoiceReport(models.AbstractModel):
	_inherit = 'report.point_of_sale.report_invoice'
	_description = "Informe POS"

	@api.model
	def render_html(self, docids, data=None):
		res = super(PosInvoiceReport, self).render_html(docids=docids, data=data)
		return res