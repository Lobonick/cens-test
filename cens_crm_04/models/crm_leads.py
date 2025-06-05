from odoo import models, fields, api
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    cens_empleado_activo_id = fields.Many2one(
        'hr.employee',
        string='Empleado Activo',
        help='Empleado que está utilizando el CRM'
    )
    
    @api.model
    def check_employee_authentication(self):
        """Verifica si hay un empleado autenticado en la sesión"""
        # Verificar en la sesión del usuario si hay un empleado autenticado
        return self.env.context.get('cens_empleado_autenticado', False)