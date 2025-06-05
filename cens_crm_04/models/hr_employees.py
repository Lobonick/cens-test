from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    cens_user_passw = fields.Char(
        string='Password',
        help='Password de Usuario CENS para acceder al módulo CRM'
    )

    cens_user_check = fields.Boolean(
        string='Activador Usuario',
        help='Check que lo activa como Usuario CENS.',
        store=True
    )

    @api.model
    def validate_employee_password(self, employee_id, password):
        """Valida el password del empleado"""
        employee = self.browse(employee_id)
        if employee and employee.cens_user_passw == password:
            return True
        return False