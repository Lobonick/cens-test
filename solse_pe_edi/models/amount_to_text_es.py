# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: moylop260 (moylop260@vauxoo.com)
#    Launchpad Project Manager for Publication: Nhomar Hernandez - nhomar@vauxoo.com
############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# http://bazaar.launchpad.net/~openerp-mexico-maintainer/openerp-mexico-localization/7.0/view/head:/l10n_mx_invoice_amount_to_text/amount_to_text_es_MX.py
class Amount2Text:
	"""
	Transforma de una cantidad numerica a cantidad en letra
	ej. 200 -> doscientos
	"""

	def __init__(self):
		self._n1 = (
			"un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
			"nueve", "diez", "once", "doce", "trece", "catorce", "quince",
			"dieciseis", "diecisiete", "dieciocho", "diecinueve", "veinte")

		self._n11 = ("un", "dos", "tres", "cuatro",
					 "cinco", "seis", "siete", "ocho", "nueve")

		self._n2 = (
			"dieci", "veinti", "treinta", "cuarenta", "cincuenta", "sesenta",
			"setenta", "ochenta", "noventa")

		self._n3 = ("ciento", "dosc", "tresc", "cuatroc", "quin", "seisc",
					"setec", "ochoc", "novec")

	def amount_to_text_cheque(self, nNumero, intermedio="soles", sufijo="M. N.", show_fraction=False):
		"""
		@params nNumero : Amount for convert to text
		@params intermedio : Name Divisa
		@sufijo : Sufix of the currency
		"""
		nNumero = round(nNumero, 2)
		strCantEntera = self.amount_to_text(nNumero)
		intCantDecimal = self.extraeDecimales(nNumero)
		if intCantDecimal <= 9:
			strCantDecimal = "0%d" % (intCantDecimal)
		else:
			strCantDecimal = "%d" % (intCantDecimal)
		strCantDecimal += "/100"
		if show_fraction:
			intermedio="%s y" % intermedio
			return strCantEntera+' '+intermedio+' '+strCantDecimal+' '+sufijo
		else:
			sufijo=intermedio
			return strCantEntera+' y '+strCantDecimal+' '+sufijo

	def extraeDecimales(self, nNumero, max_digits=2):
		"""
		@params nNumero : Number complete whit decimals
		@params max_digits : Maximum number of decimals to take
		"""
		strDecimales = str(round(nNumero % 1, 2)).replace('0.', '')
		strDecimales += "0"*max_digits
		strDecimales = strDecimales[0:max_digits]
		return int(strDecimales)

	def amount_to_text(self, nNumero, lFemenino=False):
		"""
		NOTE: Only numbers integer, omittes the DECIMALS
		amount_to_text(nNumero, lFemenino) --> cLiteral
			Converts the number to string literal of characters
			example:  201   --> "Two thousand one"
					  1111  --> "One thousand one hundred eleven"

		@params nNumero : Number to conert
		@params lFemenino : 'true' if the literal is female
		"""
		# Nos aseguramos del tipo de <nNumero>
		# se podria adaptar para usar otros tipos (pe: float)
		nNumero = int(nNumero)
		if nNumero < 0:
			cRes = "menos "+self._amount_to_text(-nNumero, lFemenino)
		elif nNumero == 0:
			cRes = "cero"
		else:
			cRes = self._amount_to_text(nNumero, lFemenino)

		# Excepciones a considerar
		if not lFemenino and nNumero != 1 and nNumero % 10 == 1 and nNumero % 100 != 11:
			cRes += "o"
		# cRes = cRes.upper()
		# cRes = cRes.capitalize()
		return cRes

	# Funcion auxiliar recursiva
	def _amount_to_text(self, n, lFemenino=0):
		"""
		@params nNumero : Number to conert
		@params lFemenino : '0' if the literal isn't female
		"""

		# Localizar los billones
		prim, resto = divmod(n, 10**12)
		if prim != 0:
			if prim == 1:
				cRes = "un billon"
			else:
				cRes = self._amount_to_text(
					prim, 0)+" billones"  # Billones es masculino

			if resto != 0:
				cRes += " "+self._amount_to_text(resto, lFemenino)

		else:
		# Localizar millones
			prim, resto = divmod(n, 10**6)
			if prim != 0:
				if prim == 1:
					cRes = "un millon"
				else:
					cRes = self._amount_to_text(
						prim, 0)+" millones"  # Millones es masculino

				if resto != 0:
					cRes += " " + self._amount_to_text(resto, lFemenino)

			else:
			# Localizar los miles
				prim, resto = divmod(n, 10**3)
				if prim != 0:
					if prim == 1:
						cRes = "mil"
					else:
						cRes = self._amount_to_text(prim, lFemenino)+" mil"

					if resto != 0:
						cRes += " " + self._amount_to_text(resto, lFemenino)

				else:
				# Localizar los cientos
					prim, resto = divmod(n, 100)
					if prim != 0:
						if prim == 1:
							if resto == 0:
								cRes = "cien"
							else:
								cRes = "ciento"
						else:
							cRes = self._n3[prim-1]
							if lFemenino:
								cRes += "ientas"
							else:
								cRes += "ientos"

						if resto != 0:
							cRes += " "+self._amount_to_text(resto, lFemenino)

					else:
					# Localizar las decenas
						if lFemenino and n == 1:
							cRes = "una"
						elif n <= 20:
							cRes = self._n1[n-1]
						else:
							prim, resto = divmod(n, 10)
							cRes = self._n2[prim-1]
							if resto != 0:
								if prim == 2:
									cRes += self._n11[resto-1]
								else:
									cRes += " y "+self._n1[resto-1]

								if lFemenino and resto == 1:
									cRes += "a"
		return cRes


def amount_to_text(amount, currency="", sufijo="", show_fraction=False):
	"""
	@params amount : Amount for convert to text
	@params lang  : Language to used for the text converted
	@params currency : Name of currency used in amount
	"""
	# return amount_to_text(amount, lang, currency)
	amount_text = Amount2Text().amount_to_text_cheque(
		abs(amount), currency, sufijo)
	amount_text = amount_text and amount_text.upper() or ''
	return amount_text


