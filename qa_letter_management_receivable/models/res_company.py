from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    letter_collection = fields.Many2one('product.product', string='Letter in collection')
    letter_discount = fields.Many2one('product.product', string='Letter in discount MN')
    # letter_interest = fields.Many2one('product.product', string='Letter interest')
    letter_discount_me = fields.Many2one('product.product', string='Letter in discount ME')