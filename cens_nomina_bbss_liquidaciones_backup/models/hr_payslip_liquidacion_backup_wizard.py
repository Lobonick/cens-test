from odoo import fields, models


class HrPayslipLiquidacionBackupWizard(models.TransientModel):
    _name = 'hr.payslip.liquidacion.backup.wizard'
    _description = 'Asistente para ejecutar el respaldo de Liquidación BBSS'

    info = fields.Char(
        default='Se tomará una "foto" de TODOS los registros actuales de '
                'hr.payslip.liquidacion y se guardará (o actualizará) como '
                'respaldo. Puede ejecutar esta acción las veces que quiera.',
        readonly=True,
    )

    def action_confirm(self):
        return self.env['hr.payslip.liquidacion.backup'].action_run_backup_all()
