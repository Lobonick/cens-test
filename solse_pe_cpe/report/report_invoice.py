# -*- coding: utf-8 -*-
from odoo import api,models

class GuideReport(models.AbstractModel):
	_name = "report.solse_guias_facturabien.guide_mov_template"

	@api.model
	def get_report_values(self,docids,data=None):

		records = self.env[objectname].browse(docids)
		return {
			"doc_ids":docids,
			"docs":records,
			"data":data,
		}