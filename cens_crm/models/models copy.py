from odoo import api, fields, models
from datetime import datetime
from gtts import gTTS
from playsound import playsound

#import pyttsx3
# from datetime import timedelta

class crm_lead_Custom(models.Model):
    _inherit = 'crm.lead'
    # engine = pyttsx3.init()

    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    x_cens_gasto_controlmain = fields.Char(string='Control General:', readonly=False)
    # x_cens_hora = fields.Datetime(string='Hora:', readonly=True)
    x_cens_solicitudes_gasto = fields.Many2many(
        comodel_name='hr.expense', 
        relation='x_crm_lead_hr_expense_rel', 
        column1='crm_lead_id', 
        column2='hr_expense_id', 
        string='Solicitudes Gasto:',
        default=lambda self: self._default_x_cens_solicitudes_gasto() )
 

    def play_sound(self):
        # Lógica adicional antes de reproducir el sonido si es necesario

        # Devolver la vista con el elemento de audio visible para reproducir el sonido
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'demo.model',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'current',
            'flags': {'action_buttons': True},
        }
    
    # ------------------------------
    # SOLICITA GASTO
    # ------------------------------
    def solicita_gasto(self):
        w_correlativo = ""

        return True
    
    # -------------------------------
    # PERMITE REPRODUCIR UN TEXTO
    # -------------------------------
    def reproducir_texto(texto):
        # engine.say(texto)
        # engine.runAndWait()
        pass

    # -------------------------------
    # ACCION PRUEBA
    # -------------------------------
    def export_to_spreadsheet(self):
        w_dato = "LLEGÓ..."
        # Definir el texto que quieres convertir a audio
        w_texto = "Hola QUIQUE, esto es un ejemplo de gTTS."

        # Crear el objeto gTTS con el texto y el idioma deseado (por defecto es 'en' para inglés)
        tts = gTTS(text=w_texto, lang='es')

        # Guardar el audio en un archivo temporal
        archivo_temporal = "temp_audio.mp3"
        tts.save(archivo_temporal)

        # Reproducir el archivo de audio en tiempo real
        playsound(archivo_temporal)

        # Eliminar el archivo temporal
        import os
        os.remove(archivo_temporal)

        # reproducir_texto("Hola QUIQUE, este es un ejemplo de texto que será reproducido.")
        pass

    # ------------------------------
    # CARGA SOLICITUDES DE GASTO
    # ------------------------------
    def _default_x_cens_solicitudes_gasto(self):
        # for record in self:
        #    record.x_cens_id_oportunidad = self.env.context.get('active_id')
        active_solicitudes = self.env['hr.expense'].search([('x_cens_oportunidad_id', '=', self.env.context.get('active_id'))], limit=1)
        if active_solicitudes:
            return [(6, 0, active_solicitudes.x_cens_solicitudes_gasto.ids)]
        return False




#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        for record in self:
#            record.x_hora = record.date_from

#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Calcula el código correlativo
#        w_correlativo = ""
#        for record in self:
#            w_correlativo = ("000000"+str(record.id))[-6:]  
#            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo

#    def genera_codigo_correlativo(self):
#        w_correlativo = ""
#        for record in self:
#            w_correlativo = ("000000"+str(record.id))[-6:]  
#            record.x_cens_codiden = "AU-" + str(record.date_from.year) + "-" + w_correlativo
#        return True


#    @api.onchange('date_from')
#    def _onchange_date_from(self):
#        # Obtiene la hora
#        for record in self:
#            record.x_hora = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')

