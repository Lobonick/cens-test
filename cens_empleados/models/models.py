from odoo import models, fields

class HrEmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    x_cens_char = fields.Char(string='Nuevo campo creado desde módulo.')
    x_cens_text = fields.Text(string='Nuevo campo creado desde módulo.')
    x_cens_integer = fields.Integer(string='Nuevo campo creado desde módulo.')
    x_cens_float = fields.Float(string='Nuevo campo creado desde módulo.')
    x_cens_fecha = fields.Date(string='Nuevo campo creado desde módulo.')
    x_cens_fecha_hora = fields.Datetime(string='Nuevo campo creado desde módulo.')
    x_cens_boolean = fields.Boolean(string='Nuevo campo creado desde módulo.')
    x_cens_seleccion = fields.Selection([
        ('1', 'Opción 1'),
        ('2', 'Opción 2'),
        ('3', 'Opción 3')
    ], string='Campo de selección')

    
