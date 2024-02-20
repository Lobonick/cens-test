from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta

class CustomModel(models.Model):
    _inherit = 'helpdesk.ticket'

    cens_fecha_actual = fields.Datetime(string='Fecha Actual:')
    cens_fecha_texto  = fields.Char(string='Tiempo Transcurrido:', readonly=False)
    cens_ticket_imagen2 = fields.Binary(string='', related='company_id.x_studio_tickets_cerrado')

    @api.onchange('assign_date', 'cens_fecha_actual')
    def get_time_elapsed(self):
        for record in self:
            current_datetime = datetime.now()
            record.cens_fecha_actual = current_datetime
            if (record.assign_date and record.cens_fecha_actual):
                delta = relativedelta(record.cens_fecha_actual, record.assign_date)
                months = delta.months
                days = delta.days
                hours = delta.hours
                minutes = delta.minutes
                elapsed_time = ""
                if (months > 0):
                    elapsed_time += f"{months} meses, "
                if (days > 0):
                    elapsed_time += f"{days} días, "
                if (hours > 0):
                    elapsed_time += f"{hours} horas, "
                if (minutes > 0):
                    elapsed_time += f"{minutes} minutos"
                return elapsed_time

    def update_fecha_actual(self):
        for record in self:
            current_datetime = datetime.now()
            record.cens_fecha_actual = current_datetime

    def create(self, vals):
        record = super(CustomModel, self).create(vals)
        record.update_fecha_actual()
        return record
    
    def read(self, fields=None, load='_classic_read'):
        # self.get_time_elapsed()
        self.update_fecha_actual()
        for record in self:
            record.cens_fecha_texto = self.get_time_elapsed()
        return super(CustomModel, self).read(fields=fields, load=load)

    # --------------------------------
    # BOTÓN: Refresca Fecha 
    # --------------------------------
    def action_button_refresh_fecha(self):
        self.update_fecha_actual()
        for record in self:
            record.cens_fecha_texto = self.get_time_elapsed()
        pass

    # --------------------------------
    # BOTÓN: Cierra Ticket Atención 
    # --------------------------------
    def cerrar_ticket_atencion(self):
        self.update_fecha_actual()
        for record in self:
            record.cens_fecha_texto = self.get_time_elapsed()
            record.stage_id = 5
            record.kanban_state = 'blocked'
        pass
