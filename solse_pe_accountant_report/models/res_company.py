# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from datetime import timedelta

from odoo import models
from odoo.tools import date_utils
import logging
_logging = logging.getLogger(__name__)


class ResCompany(models.Model):
	_inherit = "res.company"

	def compute_fiscalyear_dates(self, current_date):
		self.ensure_one()

		fiscalyear = self.env["solse.pe.cierre"].search(
			[
				("company_id", "=", self.id),
				("fecha_inicio", "<=", current_date),
				("fecha_fin", ">=", current_date),
			],
			limit=1,
		)
		if fiscalyear:
			return {
				"date_from": fiscalyear.fecha_inicio,
				"date_to": fiscalyear.fecha_fin,
				"record": fiscalyear,
			}

		date_from, date_to = date_utils.get_fiscal_year(
			current_date,
			day=self.fiscalyear_last_day,
			month=int(self.fiscalyear_last_month),
		)

		fiscalyear_from = self.env["account.fiscal.year"].search(
			[
				("company_id", "=", self.id),
				("date_from", "<=", date_from),
				("date_to", ">=", date_from),
			],
			limit=1,
		)
		if fiscalyear_from:
			date_from = fiscalyear_from.date_to + timedelta(days=1)

		fiscalyear_to = self.env["account.fiscal.year"].search(
			[
				("company_id", "=", self.id),
				("date_from", "<=", date_to),
				("date_to", ">=", date_to),
			],
			limit=1,
		)
		if fiscalyear_to:
			date_to = fiscalyear_to.date_from - timedelta(days=1)

		return {
			"date_from": date_from,
			"date_to": date_to,
		}
