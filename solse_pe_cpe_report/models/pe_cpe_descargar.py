# -*- coding: utf-8 -*-
# Copyright (c) 2019-2022 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

class SolsePeCpeDescargar(models.Model):
	_name = 'solse.pe.cpe.descargar'
	_description = 'Descargar cpe'

	name = fields.Char('Nombre')
	datas_zip_fname = fields.Char("Nombre de archivo zip",  readonly=True)
	datas_zip = fields.Binary("Datos Zip", readonly=True)