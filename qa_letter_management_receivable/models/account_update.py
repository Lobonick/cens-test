from odoo import fields, models


class AccountUpdate(models.Model):
    _inherit = 'account.update'

    letter_state = fields.Selection(selection_add=[
        ('collection', 'Letter in collection'),
        ('warranty', 'Letter in warranty'),
        ('discount', 'Letter in discount'),
        ('protest', 'Letter in protest')])