# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.


import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round, float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form


class AccountAccount(models.Model):
	_inherit = "account.account"

	sub_cuenta_ingresos = fields.Selection([("otros", "Otros ingresos"), 
		("financieros", "Ingresos Financieros")], default="otros", string="Sub cuenta ingresos")

	sub_cuenta_gastos = fields.Selection([("otros", "Otros gastos"), 
		("operativos", "Gastos Operativos"), ("financieros", "Gastos Financieros")], default="otros", string="Sub cuenta ingresos")

	sub_cuenta_por_cobrar = fields.Selection([("comerciales", "Comerciales"), 
		("otros", "Otros")], default="comerciales", string="Sub cuenta por cobrar")

	sub_cuenta_activo_fijo = fields.Selection([("inmuebles", "INMUEBLES, MAQ. Y EQUIPO"), 
		("intangibles", "INTANGIBLES")], default="inmuebles", string="Sub cuenta Activo fijo")

	sub_cuenta_por_pagar = fields.Selection([("remuneraciones", "Remuneraciones por pagar"), 
		("comerciales", "Cuentas por pagar Comerciales-Terceros"), ("otras", "Otras cuentas por Pagar")], default="remuneraciones",
		string="Sub cuenta Por Pagar")

	