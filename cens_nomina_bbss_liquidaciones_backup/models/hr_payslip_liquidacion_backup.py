import base64
import json
import logging
from datetime import date, datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Modelo de origen que queremos poder respaldar/restaurar. Se referencia por
# nombre (string) a propósito: este módulo NO depende de
# cens_nomina_bbss_liquidaciones para poder sobrevivir a su desinstalación.
SOURCE_MODEL = 'hr.payslip.liquidacion'

# Campos técnicos/de mensajería que no aportan valor como "dato de negocio"
# y que no queremos respaldar ni restaurar.
EXCLUDE_FIELDS = {
    'id', 'display_name', '__last_update',
    'create_uid', 'create_date', 'write_uid', 'write_date',
    'message_ids', 'message_follower_ids', 'message_partner_ids',
    'message_main_attachment_id', 'website_message_ids',
    'activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id',
    'activity_date_deadline', 'activity_summary',
    'activity_exception_decoration', 'activity_exception_icon',
    'my_activity_date_deadline',
}


class HrPayslipLiquidacionBackup(models.Model):
    _name = 'hr.payslip.liquidacion.backup'
    _description = 'Respaldo de Liquidación de Beneficios Sociales (BBSS)'
    _order = 'backup_date desc, id desc'

    name = fields.Char(string='Código Liquidación', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', readonly=True, index=True)
    source_res_id = fields.Integer(string='ID Origen', readonly=True, index=True,
                                    help='ID que tenía el registro en hr.payslip.liquidacion al momento del respaldo.')
    backup_date = fields.Datetime(string='Fecha Respaldo', readonly=True, default=fields.Datetime.now)
    field_count = fields.Integer(string='Núm. Campos Respaldados', readonly=True)
    data_json = fields.Text(string='Datos Respaldados (JSON)', readonly=True)
    state = fields.Selection([
        ('backup', 'Respaldado'),
        ('restored', 'Restaurado'),
    ], string='Estado', default='backup', readonly=True)
    restored_res_id = fields.Integer(string='ID Restaurado', readonly=True,
                                      help='ID del nuevo registro creado en hr.payslip.liquidacion al restaurar.')
    restored_date = fields.Datetime(string='Fecha Restauración', readonly=True)

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _get_source_model(self):
        """Devuelve el modelo de origen si el módulo que lo define está
        instalado actualmente, o None si no existe en el registro."""
        try:
            return self.env[SOURCE_MODEL].sudo()
        except KeyError:
            return None

    @api.model
    def _get_backup_field_names(self, Source):
        """Campos propios (no relacionados) y almacenados del modelo de
        origen. Se excluyen los 'related' porque su valor depende de otro
        registro (empleado, contrato, boleta...) que sigue existiendo, y se
        recalculará solo; así el respaldo no se vuelve obsoleto cuando el
        usuario agregue campos nuevos al modelo de origen."""
        return [
            fname for fname, field in Source._fields.items()
            if field.store and not field.related and fname not in EXCLUDE_FIELDS
        ]

    def _to_jsonable(self, value):
        if isinstance(value, models.BaseModel):
            if len(value) <= 1:
                return value.id if value else False
            return value.ids
        if isinstance(value, datetime):
            return fields.Datetime.to_string(value)
        if isinstance(value, date):
            return fields.Date.to_string(value)
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                return base64.b64encode(value).decode('ascii')
        return value

    # ------------------------------------------------------------------
    # BOTÓN / ACCIÓN: Ejecutar Respaldo Ahora
    # ------------------------------------------------------------------
    @api.model
    def action_run_backup_all(self):
        """Respalda TODOS los registros actuales de hr.payslip.liquidacion.
        Se puede ejecutar varias veces: si el registro origen ya tiene un
        respaldo (mismo ID origen), se actualiza en lugar de duplicarlo."""
        Source = self._get_source_model()
        if Source is None:
            raise UserError(_(
                "El modelo de origen '%s' no está instalado actualmente.\n"
                "No hay datos que respaldar."
            ) % SOURCE_MODEL)

        field_names = self._get_backup_field_names(Source)
        created = 0
        updated = 0

        for record in Source.search([]):
            data = {}
            for fname in field_names:
                try:
                    data[fname] = self._to_jsonable(record[fname])
                except Exception:
                    _logger.warning(
                        "No se pudo respaldar el campo '%s' del registro %s (%s)",
                        fname, record.id, SOURCE_MODEL
                    )

            vals = {
                'name': record.name or False,
                'employee_id': record.employee_id.id if record.employee_id else False,
                'source_res_id': record.id,
                'backup_date': fields.Datetime.now(),
                'data_json': json.dumps(data, ensure_ascii=False),
                'field_count': len(data),
                'state': 'backup',
            }

            existing = self.search([('source_res_id', '=', record.id)], limit=1)
            if existing:
                existing.write(vals)
                updated += 1
            else:
                self.create(vals)
                created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Respaldo BBSS completado'),
                'message': _('%s registro(s) nuevos, %s actualizados.') % (created, updated),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': _('Respaldos - Liquidación BBSS'),
                    'res_model': 'hr.payslip.liquidacion.backup',
                    'view_mode': 'tree,form',
                    'target': 'current',
                },
            },
        }

    # ------------------------------------------------------------------
    # BOTÓN / ACCIÓN: Restaurar Seleccionados
    # ------------------------------------------------------------------
    def action_run_restore(self):
        """Recrea en hr.payslip.liquidacion los registros seleccionados de
        este respaldo. Solo se escriben campos propios (no 'related' ni
        'compute') que existan en el modelo de destino en este momento; los
        campos calculados se recalculan solos a partir de sus dependencias."""
        if not self:
            raise UserError(_("Seleccione al menos un registro de respaldo para restaurar."))

        Target = self._get_source_model()
        if Target is None:
            raise UserError(_(
                "El modelo destino '%s' no está instalado actualmente.\n"
                "Instale/actualice primero el módulo de Liquidaciones BBSS "
                "(cens_nomina_bbss_liquidaciones) antes de restaurar."
            ) % SOURCE_MODEL)

        restored = 0
        skipped = 0

        for backup in self:
            if backup.state == 'restored':
                skipped += 1
                continue
            try:
                data = json.loads(backup.data_json or '{}')
            except ValueError:
                _logger.warning("JSON inválido en el respaldo %s, se omite.", backup.id)
                skipped += 1
                continue

            vals = {}
            for fname, fvalue in data.items():
                field = Target._fields.get(fname)
                if field is None or field.related or field.compute:
                    continue
                vals[fname] = fvalue

            if not vals:
                skipped += 1
                continue

            new_record = Target.create(vals)
            backup.write({
                'state': 'restored',
                'restored_res_id': new_record.id,
                'restored_date': fields.Datetime.now(),
            })
            restored += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Restauración BBSS completada'),
                'message': _('%s registro(s) restaurados, %s omitidos.') % (restored, skipped),
                'type': 'success' if restored else 'warning',
                'sticky': False,
            },
        }
