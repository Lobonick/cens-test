from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import base64
from io import BytesIO

#
# clase: import xlsxwriter
#
# REQUISITO:  pip install xlsxwriter
#
# APLICACIÓN
#
# Abrir / crear libro 
#   workbook = xlsxwriter.Workbook('/ruta/del/archivo/reporte.xlsx')
# Agregar una nueva hoja al libro
#    worksheet = workbook.add_worksheet('Mi Hoja')
# Escribir datos en la hoja
#    worksheet.write('A1', 'Valor 1')
#    worksheet.write('B1', 'Valor 2')
# Cerrar el libro
#    workbook.close()

class crm_lead_Custom(models.Model):
    _inherit = 'crm.lead'
    file_data = fields.Binary("File")
    file_name = fields.Char("File Name")
    # ---------------------------
    # AGREGA CAMPOS AL MODELO
    # ---------------------------
    cens_user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    cens_fecha_actual = fields.Datetime(string='Fecha Actual:', readonly=True, existing_field=True)
    cens_conta_visita = fields.Integer(string='Visitas:', readonly=True, default=0, existing_field=True)
    cens_solicitudes_gasto = fields.Many2many(
        comodel_name='hr.expense', 
        relation='x_crm_lead_hr_expense_rel', 
        column1='crm_lead_id', 
        column2='hr_expense_id', 
        string='Solicitudes Gasto:',
        default=lambda self: self._default_cens_solicitudes_gasto(),
        existing_field=True )
    cens_campo_control = fields.Char("CONTROL:")
     
    # ------------------------------
    # SOLICITA GASTO
    # ------------------------------
    def solicita_gasto(self):
        w_correlativo = ""
        return True
    
    # -------------------------------
    # ACCION PRUEBA
    # -------------------------------
    def export_to_spreadsheet(self):
        w_path = "user/cens_crm/report/"
        w_ruta = "/home/odoo/src/user/cens_crm/models/report/"
        w_file = "reporte.xlsx"
        w_erro = ""

        # Crear un buffer en memoria para almacenar el archivo
        output = BytesIO()
        
        try:
            # ANTERIOR: workbook = xlsxwriter.Workbook(w_file)
            # Crear el workbook y worksheet
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        except:
            w_erro = "ERROR ARCHIVO: " + w_ruta + w_file  
        else:
            # -------------------------------------------------------------------------------------
            # CONFIGURACIÓN GENERAL DE LA WORKSHEET
            # -------------------------------------------------------------------------------------
            workbook.set_properties({
                'title':    'REPORTE - Oportunidades de Negocio',
                'subject':  'Extracto a la fecha',
                'author':   'ODOO-CENS',
                'manager':  'Área de Gestión Comercial',
                'company':  'CENS PERÚ',
                'category': 'CRM - LEADS',
                'keywords': 'Oportunidades, Negocio, crm',
                'created':  datetime.now(),
                'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})
            worksheet = workbook.add_worksheet("DATA-CENS")
            cell_format = workbook.add_format()
            cell_format_empr = workbook.add_format({'bold': True})
            cell_format_cabe = workbook.add_format()
            cell_format_tuti = workbook.add_format()
            cell_format_titu = workbook.add_format()
            # ------
            cell_format_nume = workbook.add_format()
            cell_format_nume.set_num_format('#,##0')
            cell_format_nume.set_align('vcenter')
            # ------
            cell_format_tcam = workbook.add_format()
            cell_format_tcam.set_num_format('##0.000')
            cell_format_tcam.set_align('vcenter')
            # ------
            cell_format_cent = workbook.add_format()
            cell_format_cent.set_align('center')
            cell_format_cent.set_align('vcenter')
            # ------
            cell_format_left = workbook.add_format()
            cell_format_left.set_align('vcenter')
            # ------
            cell_format_porc = workbook.add_format()
            cell_format_porc = workbook.add_format({'num_format': '0%'})
            cell_format_porc.set_align('center')
            cell_format_porc.set_align('vcenter')
            # ------
            cell_format_fech = workbook.add_format()
            cell_format_fech.set_num_format('dd/mm/yyyy')
            cell_format_fech.set_align('center')
            cell_format_fech.set_align('vcenter')
            # ------
            cell_format_verd = workbook.add_format()
            cell_format_verd.set_font_color('white')
            cell_format_verd.set_bg_color('#30C381')    ##--- Semáforo en VERDE
            cell_format_verd.set_align('center')
            cell_format_verd.set_align('vcenter')
            # ------
            cell_format_rojo = workbook.add_format()
            cell_format_rojo.set_font_color('white')
            cell_format_rojo.set_bg_color('#ff0026')    ##--- Semáforo en ROJO
            cell_format_rojo.set_align('center')
            cell_format_rojo.set_align('vcenter')
            # ------
            cell_format_amba = workbook.add_format()
            cell_format_amba.set_font_color('black')
            cell_format_amba.set_bg_color('#ffa600')    ##--- Semáforo en AMBAR
            cell_format_amba.set_align('center')
            cell_format_amba.set_align('vcenter')
            # ------
            cell_format_perd = workbook.add_format()
            cell_format_perd.set_font_color('red')        ##--- Motivo de la Pérdida
            cell_format_perd.set_align('vcenter')
            cell_format_perd.set_text_wrap()
            # ------
            worksheet.write(5, 0, datetime.now(), cell_format_fech)
            worksheet.set_column(0, 0, 9)
            worksheet.set_column(1, 1, 13)  # (ColIni,ColFin,Ancho) --- AJUSTA EL ANCHO DE LAS COLUMNAS
            worksheet.set_column(2, 3, 12)
            worksheet.set_column(4, 4, 19)
            worksheet.set_column(5, 5, 12)
            worksheet.set_column(6, 6, 16)
            worksheet.set_column(7, 7, 35)
            worksheet.set_column(8, 8, 5)
            worksheet.set_column(9, 10, 12)
            worksheet.set_column(11, 11, 9)
            worksheet.set_column(12, 12, 12)
            worksheet.set_column(13, 13, 9)
            worksheet.set_column(14, 15, 40)
            worksheet.set_column(16, 19, 12)
            worksheet.set_column(20, 20, 50)
            worksheet.set_row(6, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A1', 'src/user/cens_crm/static/description/logo-tiny_96.png')
            worksheet.write('B2', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B3', 'Área de Sistemas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)
            worksheet.write('H4', 'OPORTUNIDADES DE NEGOCIO - CENS', cell_format_cabe)
            worksheet.write('A5', 'FECHA:')
            worksheet.write('B5', datetime.now(), cell_format_fech)
            #-----
            worksheet.write('A6', 'USUARIO:')
            w_usuario_actual = self.env.context.get("uid")
            usuario_actual = self.env['res.users'].browse(w_usuario_actual)
            w_usuario_names = usuario_actual.name
            worksheet.write('B6', w_usuario_names)
            #-----
            merge_format = workbook.add_format({'align': 'center'})
            worksheet.merge_range('J6:M6', 'Merged Cells', merge_format)
            worksheet.write('J6', 'IMPORTES DE PROPUESTAS NEGOCIADAS', cell_format_tuti)
            # -------------------------------------------------------------------------------------
            # BARRA DE TITULOS
            # -------------------------------------------------------------------------------------
            cell_format_tuti.set_font_name('Arial')
            cell_format_tuti.set_font_color('black')
            cell_format_tuti.set_font_size(8)
            cell_format_tuti.set_text_wrap()                 # FORMATO DE CELDA
            cell_format_tuti.set_bg_color('#92CDDC')
            cell_format_tuti.set_align('center')
            cell_format_tuti.set_align('vcenter')
            #-----
            cell_format_titu.set_font_name('Arial')
            cell_format_titu.set_font_color('white')
            cell_format_titu.set_font_size(8)
            cell_format_titu.set_text_wrap()                 # FORMATO DE CELDA
            cell_format_titu.set_bg_color('#31869B')
            cell_format_titu.set_align('center')
            cell_format_titu.set_align('vcenter')
            #-----
            #worksheet.set_row(7, 7)
            #worksheet.set_column('A:M', 7)
            worksheet.write('A7', 'ORD', cell_format_titu)
            worksheet.write('B7', 'CÓDIGO', cell_format_titu)
            worksheet.write('C7', 'FECHA REGISTRO', cell_format_titu)
            worksheet.write('D7', 'FECHA CIERRE', cell_format_titu)
            worksheet.write('E7', 'GDN REPONSABLE', cell_format_titu)
            worksheet.write('F7', 'UNIDAD DE NEGOCIO', cell_format_titu)
            worksheet.write('G7', 'SUB.UNIDAD DE NEGOCIO', cell_format_titu)
            worksheet.write('H7', 'C L I E N T E', cell_format_titu)
            worksheet.write('I7', 'MONE', cell_format_titu)
            worksheet.write('J7', 'IMPORTE SOLES(PEN)', cell_format_titu)
            worksheet.write('K7', 'IMPORTE DÓLARES(USD)', cell_format_titu)
            worksheet.write('L7', 'TIPO CAMBIO', cell_format_titu)
            worksheet.write('M7', 'AJUSTADO SOLES', cell_format_titu)
            worksheet.write('N7', 'MARGEN UTILIDAD', cell_format_titu)
            worksheet.write('O7', 'DESCRIPCIÓN DE LA OPORTUNIDAD', cell_format_titu)
            worksheet.write('P7', 'PROYECTO ASIGNADO', cell_format_titu)
            worksheet.write('Q7', 'PROBABILIDAD', cell_format_titu)
            worksheet.write('R7', 'ESTADO OPORTUNIDAD', cell_format_titu)
            worksheet.write('S7', 'FECHA ÚLTIMO ESTADO', cell_format_titu)
            worksheet.write('T7', 'FECHA DE GANADA', cell_format_titu)
            worksheet.write('U7', 'MOTIVO DE LA PÉRDIDA', cell_format_titu)
            worksheet.freeze_panes(7, 0)
            # -------------------------------------------------------------------------------------
            # CUERPO DEL REPORTE
            # -------------------------------------------------------------------------------------
            w_leads = self.search(self._context.get('active_domain', []))  # Obtener registros según el dominio activo en la vista
            w_dato = ""
            w_fila = 7
            for w_lead in w_leads:
                worksheet.write(w_fila, 0, w_fila-6, cell_format_cent)        # Escribir datos de los registros
                worksheet.write(w_fila, 1, w_lead.x_studio_nro_agrupamiento, cell_format_cent)
                worksheet.write(w_fila, 2, w_lead.x_studio_fecha_de_oportunidad, cell_format_fech)
                worksheet.write(w_fila, 3, w_lead.date_deadline, cell_format_fech)
                worksheet.write(w_fila, 4, w_lead.x_studio_gdn_responsable, cell_format_left)
                w_dato = w_lead.x_studio_many2one_field_t33Z2.x_udn_abrv
                worksheet.write(w_fila, 5, w_dato, cell_format_left)
                w_dato = w_lead.x_studio_many2one_field_RmaJp.x_sun_abrv
                worksheet.write(w_fila, 6, w_dato, cell_format_left)
                w_dato = w_lead.partner_id.name
                worksheet.write(w_fila, 7, w_dato, cell_format_left)
                
                worksheet.write(w_fila, 8, w_lead.x_studio_moneda_simbolo, cell_format_cent)
                if (w_lead.x_studio_moneda_simbolo=="S/."):
                    worksheet.write(w_fila, 9, w_lead.x_studio_monto_de_operacion_entero, cell_format_nume)
                else:
                    worksheet.write(w_fila, 10, w_lead.x_studio_monto_de_operacion_entero, cell_format_nume)
                    worksheet.write(w_fila, 11, w_lead.x_studio_tasa_cambiaria_dolares, cell_format_tcam)
                worksheet.write(w_fila, 12, w_lead.x_studio_monto_ajustado_reporte, cell_format_nume)

                worksheet.write(w_fila, 13, w_lead.x_studio_margen_utilidad, cell_format_porc)
                worksheet.write(w_fila, 14, w_lead.x_studio_proyecto, cell_format_left)
                if w_lead.x_studio_proyectos_asignados_rpt:
                    worksheet.write(w_fila, 15, w_lead.x_studio_proyectos_asignados_rpt, cell_format_left)
                else:
                    worksheet.write(w_fila, 15, " ")
                worksheet.write(w_fila, 16, w_lead.x_studio_porcentaje_de_probabilidad, cell_format_porc)
                if (w_lead.x_studio_estado_oportunidad == "Ganada"):
                    worksheet.write(w_fila, 17, w_lead.x_studio_estado_oportunidad, cell_format_verd)
                elif (w_lead.x_studio_estado_oportunidad == "Abierto"):
                    worksheet.write(w_fila, 17, w_lead.x_studio_estado_oportunidad, cell_format_amba)
                elif (w_lead.x_studio_estado_oportunidad == "Anulada"):
                    worksheet.write(w_fila, 17, w_lead.x_studio_estado_oportunidad, cell_format_rojo)
                    worksheet.write(w_fila, 20, w_lead.x_studio_sustento_anulado_perdido, cell_format_perd)
                elif (w_lead.x_studio_estado_oportunidad == "Perdida"):
                    worksheet.write(w_fila, 17, w_lead.x_studio_estado_oportunidad, cell_format_rojo)
                    worksheet.write(w_fila, 20, w_lead.x_studio_sustento_anulado_perdido, cell_format_perd)
                else:
                    worksheet.write(w_fila, 17, w_lead.x_studio_estado_oportunidad, cell_format_cent)

                worksheet.write(w_fila, 18, w_lead.x_studio_fecha_hora_ultimo_estado, cell_format_fech)
                worksheet.write(w_fila, 19, w_lead.x_fecha_win_texto, cell_format_fech)
                w_fila += 1

            workbook.close()
        
        # Obtener los datos binarios del archivo
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()
        
        # Crear un registro temporal para almacenar el archivo
        attachment = self.env['ir.attachment'].create({
            'name': 'reporte.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'reporte.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Devolver una acción para descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # ------------------------------
    # CARGA SOLICITUDES DE GASTO
    # ------------------------------
    def _default_cens_solicitudes_gasto(self):
        # for record in self:
        #    record.x_cens_id_oportunidad = self.env.context.get('active_id')
        active_solicitudes = self.env['hr.expense'].search([('x_cens_oportunidad_id', '=', self.env.context.get('active_id'))], limit=1)
        if active_solicitudes:
            return [(6, 0, active_solicitudes.cens_solicitudes_gasto.ids)]
        return False

    def inicializa_variables(self):
        for record in self:
            current_datetime = datetime.now()
            record.x_studio_nro_agrupamiento = ("ON-"+("000000"+str(record.id-92))[-6:]) if record.x_studio_nro_agrupamiento in ('*','ON-') else record.x_studio_nro_agrupamiento
            record.name = "CÓDIGO: " + record.x_studio_nro_agrupamiento
            record.x_studio_usuario_actual = self.env.context.get("uid")
            record.cens_conta_visita += 1
            record.cens_fecha_actual = current_datetime

    # def create(self, vals):
    #    record = super(crm_lead_Custom, self).create(vals)
    #    record.inicializa_variables()
    #    return record
    
    @api.model
    def create(self, vals):
        if 'cens_user_id' not in vals:
            vals['cens_user_id'] = self.env.user.id

        for record in self:
            current_datetime = datetime.now()
            record.cens_fecha_actual = current_datetime
            record.cens_campo_control = "ENTRÓ LA WADA"

        return super(crm_lead_Custom, self).create(vals)

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

