from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EmployeeAuthWizard(models.TransientModel):
    _name = 'cens_crm_04.employee.auth.wizard'
    _description = 'Wizard de Autenticación de Empleados'
    
    company_id = fields.Many2one(
        'res.company', 
        string='Compañía', 
        default=lambda self: self.env.company.id
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Seleccionar Empleado',
        required=True,
        help='Seleccione el empleado que va a usar el CRM'
    )
    employee_foto = fields.Binary(string="foto", related='employee_id.avatar_128')
    password = fields.Char(
        string='Password',
        required=True,
        help='Ingrese el password del empleado'
    )
    
    def action_authenticate(self):
        """Autentica al empleado y redirige al CRM"""
        # Validar password
        if not self.env['hr.employee'].validate_employee_password(
            self.employee_id.id, self.password
        ):
            raise ValidationError('Password incorrecto para el empleado seleccionado.')
        
        # Redirigir a la vista tree de CRM leads
        return {
            'type': 'ir.actions.act_window',
            'name': 'Oportunidades',
            'res_model': 'crm.lead',
            'view_mode': 'tree',
            'target': 'current',
            'context': {
                'cens_empleado_autenticado': True,
                'cens_empleado_activo_id': self.employee_id.id,
                'default_cens_empleado_activo_id': self.employee_id.id,
            }
        }
    
    def action_reset_employee(self):
        """Limpia la selección de empleado para elegir otro"""
        self.write({
            'employee_id': False,
            'password': ''
        })
        return 
    
        #{
        #    'type': 'ir.actions.do_nothing'
        #}
    
    def action_cancel(self):
        """Cancela la autenticación"""
        return {'type': 'ir.actions.act_window_close'}