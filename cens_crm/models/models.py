from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
import base64
from io import BytesIO
from odoo.exceptions import UserError

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
    cens_marcador_extorno = fields.Binary(string="Imagen Extorno", related='company_id.x_studio_marcador_extorno')
    cens_fecha_actual = fields.Datetime(string='Fecha Actual:', readonly=True, existing_field=True)
    cens_conta_visita = fields.Integer(string='Visitas:', readonly=True, default=0, existing_field=True)
    cens_campo_control = fields.Char("CONTROL:")
     
    # ------------------------------
    # SOLICITA GASTO
    # ------------------------------
    def solicita_gasto(self):
        w_correlativo = ""
        return True
    
    # ------------------------------------
    # GENERAR EXTORNO - Duplica registro
    # ------------------------------------
    def action_generar_extorno(self):
        w_Pase_Ok = False
        for record in self:
            if (record.partner_id):
                w_Pase_Ok = True
            else:
                w_Pase_Ok = False
                record.x_studio_observaciones = "ATENCIÓN: Debe seleccionar un CLIENTE."
        if w_Pase_Ok:
            for lead in self:
                new_lead = lead.copy()
                new_lead.x_studio_fecha_de_oportunidad = datetime.now()
                new_lead.x_studio_monto_de_operacion_entero = new_lead.x_studio_monto_de_operacion_entero * -1
                new_lead.name = f"Extorno de {lead.name}"
                # Copiar los registros relacionados de x_studio_proyectos_vinculados
                for related_record in lead.x_studio_proyectos_vinculados:
                    self.env['x_crm_lead_line_b50b7'].create({
                        'x_crm_lead_id': new_lead.id,
                        'x_name': related_record.x_name,
                        'x_studio_imagen_proyecto': related_record.x_studio_imagen_proyecto,
                        'x_studio_many2one_field_p3hXb': related_record.x_studio_many2one_field_p3hXb.id,
                        'x_studio_referencia_telco': related_record.x_studio_referencia_telco,
                        'x_studio_responsable': related_record.x_studio_responsable,
                        'x_studio_sequence': related_record.x_studio_sequence,
                    })
            return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': new_lead.id,
            'target': 'current',
            }    
    
    # ----------------------------------------------------
    # GENERAR EXTORNO DESDE NUEVO - Crea nuevo registro
    # ----------------------------------------------------
    def action_generar_extorno_nuevo(self):
        new_lead = self.create({
            'x_studio_monto_de_operacion_entero': -1,
            'x_studio_moneda_monto': "soles",
            'name': "Nuevo Extorno...",
            'x_studio_margen_utilidad': 0.01,
            'x_studio_entrega_propuesta': datetime.now(),
            'x_studio_fecha_proyectada_de_cierre': datetime.now(),      # Crea un nuevo registro de crm.lead
            'date_deadline': datetime.now(),
            'contact_name': "NONE",
            'function': "NONE",
            'mobile': "000-000-000"
        })
        return True

    # @api.model
    # def create(self, vals):
    #    if 'cens_user_id' not in vals:
    #        vals['cens_user_id'] = self.env.user.id

    #    for record in self:
    #        current_datetime = datetime.now()
    #        record.cens_fecha_actual = current_datetime
    #        record.cens_campo_control = "ENTRÓ LA WADA"

    #    return super(crm_lead_Custom, self).create(vals)


    # -------------------------------------------------------------------------------------------------------
    # ACCION - EXPORTAR REPORTE HACIA HOJA DE CALCULO EN EXCEL (Usa librería: xlsxwriter, base64, BytesIO)
    # -------------------------------------------------------------------------------------------------------
    def export_to_spreadsheet(self):
        w_path = "user/cens_crm/report/"
        w_ruta = "/home/odoo/src/user/cens_crm/models/report/"
        w_file = "CENS-CRM-LEADS.xlsx"
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
            cell_format_cent.set_text_wrap()
            # ------
            cell_format_left = workbook.add_format()
            cell_format_left.set_align('vcenter')
            # ------
            cell_format_porc = workbook.add_format()
            cell_format_porc = workbook.add_format({'num_format': '0%'})
            cell_format_porc.set_align('center')
            cell_format_porc.set_align('vcenter')
            # ------
            cell_format_xcen = workbook.add_format()
            cell_format_xcen = workbook.add_format({'num_format': '0.00%'})
            cell_format_xcen.set_align('center')
            cell_format_xcen.set_align('vcenter')
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
            # ------                                (ColIni,ColFin,Ancho) --- AJUSTA EL ANCHO DE LAS COLUMNAS
            worksheet.set_column(0, 0, 9)       #-- Ord
            worksheet.set_column(1, 1, 13)      #-- Código 
            worksheet.set_column(2, 2, 12)      #-- F.Registro
            worksheet.set_column(3, 3, 12)      #-- F.Estimada de Cierre
            worksheet.set_column(4, 4, 12)      #-- F.Cierre
            worksheet.set_column(5, 5, 19)      #-- GDN
            worksheet.set_column(6, 6, 12)      #-- UDN
            worksheet.set_column(7, 7, 16)      #-- SUN
            worksheet.set_column(8, 8, 35)      #-- Cliente
            worksheet.set_column(9, 9, 5)       #-- Moneda
            worksheet.set_column(10, 10, 12)      #-- Importe SOLES
            worksheet.set_column(11, 11, 12)    #-- Importe DOLARES
            worksheet.set_column(12, 12, 9)     #-- Tipo de Cambio
            worksheet.set_column(13, 13, 12)    #-- Importe AJUSTADO
            worksheet.set_column(14, 14, 10)    #-- Margen Utilidad %
            worksheet.set_column(15, 15, 12)    #-- Utilidad Esperada
            worksheet.set_column(16, 16, 40)    #-- Descripción de la Oportunidad
            worksheet.set_column(17, 17, 10)    #-- Código TELCO oportunidad
            worksheet.set_column(18, 18, 40)    #-- Proyecto Asignado
            worksheet.set_column(19, 19, 12)    #-- Probabilidad
            worksheet.set_column(20, 20, 12)    #-- Estado Oportunidad
            worksheet.set_column(21, 21, 12)    #-- Fecha Último Estado
            worksheet.set_column(22, 22, 12)    #-- Fecha de GANADA
            worksheet.set_column(23, 23, 50)    #-- Motivo de la Pérdida
            # ------
            worksheet.set_row(6, 27)        # (Fila,Altura)
            worksheet.set_zoom(85)          # %-Zoom
            # -------------------------------------------------------------------------------------
            # CABECERA DEL REPORTE
            # -------------------------------------------------------------------------------------
            worksheet.insert_image('A1', 'src/user/cens_crm/static/description/logo-tiny_96.png')
            worksheet.write('B2', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
            worksheet.write('B3', 'Área de Sistemas - CENS-PERÚ')
            cell_format_cabe.set_font_name('Arial Black')
            cell_format_cabe.set_font_size(11)
            worksheet.write('H4', 'OPORTUNIDADES DE NEGOCIO - CENS', cell_format_cabe)
            # ------
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
            worksheet.merge_range('J6:O6', 'Merged Cells', merge_format)
            worksheet.write('J6', 'IMPORTES SOBRE LA PROPUESTA NEGOCIADA', cell_format_tuti)
            # -------------------------------------------------------------------------------------
            # BARRA DE TITULOS
            # -------------------------------------------------------------------------------------
            cell_format_tuti.set_font_name('Arial')
            cell_format_tuti.set_font_color('black')
            cell_format_tuti.set_font_size(8)
            cell_format_tuti.set_text_wrap()                 # FORMATO TÍTULO - COLUMNAS IMPORTES
            cell_format_tuti.set_bg_color('#92CDDC')
            cell_format_tuti.set_align('center')
            cell_format_tuti.set_align('vcenter')
            #-----
            cell_format_titu.set_font_name('Arial')
            cell_format_titu.set_font_color('white')
            cell_format_titu.set_font_size(8)
            cell_format_titu.set_text_wrap()                 # FORMATO TÍTULO - TODA LA BARRA
            cell_format_titu.set_bg_color('#31869B')
            cell_format_titu.set_align('center')
            cell_format_titu.set_align('vcenter')
            #-----
            #worksheet.set_row(7, 7)
            #worksheet.set_column('A:M', 7)
            worksheet.write('A7', 'ORD', cell_format_titu)                          #-- 00
            worksheet.write('B7', 'CÓDIGO', cell_format_titu)                       #-- 01
            worksheet.write('C7', 'FECHA REGISTRO', cell_format_titu)               #-- 02
            worksheet.write('D7', 'CIERRE ESTIMADO', cell_format_titu)     #-- 03
            worksheet.write('E7', 'CIERRE OPORTUNIDAD', cell_format_titu)     #-- 04
            worksheet.write('F7', 'GDN REPONSABLE', cell_format_titu)               #-- 05
            worksheet.write('G7', 'UNIDAD DE NEGOCIO', cell_format_titu)            #-- 06
            worksheet.write('H7', 'SUB.UNIDAD DE NEGOCIO', cell_format_titu)        #-- 07
            worksheet.write('I7', 'C L I E N T E', cell_format_titu)                #-- 08
            worksheet.write('J7', 'MONE', cell_format_titu)                         #-- 09
            worksheet.write('K7', 'IMPORTE SOLES(PEN)', cell_format_titu)           #-- 10
            worksheet.write('L7', 'IMPORTE DÓLARES(USD)', cell_format_titu)         #-- 11
            worksheet.write('M7', 'TIPO CAMBIO', cell_format_titu)                  #-- 12
            worksheet.write('N7', 'AJUSTADO SOLES', cell_format_titu)               #-- 13
            worksheet.write('O7', 'MARGEN UTILIDAD', cell_format_titu)              #-- 14
            worksheet.write('P7', 'UTILIDAD ESPERADA', cell_format_titu)            #-- 15
            worksheet.write('Q7', 'DESCRIPCIÓN DE LA OPORTUNIDAD', cell_format_titu)#-- 16
            worksheet.write('R7', 'CÓDIGO TELCO-GO', cell_format_titu)              #-- 17
            worksheet.write('S7', 'PROYECTO ASIGNADO', cell_format_titu)            #-- 18
            worksheet.write('T7', 'PROBABILIDAD %', cell_format_titu)               #-- 19
            worksheet.write('U7', 'ESTADO OPORTUNIDAD', cell_format_titu)           #-- 20
            worksheet.write('V7', 'FECHA ÚLTIMO ESTADO', cell_format_titu)          #-- 21
            worksheet.write('W7', 'FECHA DE GANADA', cell_format_titu)              #-- 22
            worksheet.write('X7', 'MOTIVO DE LA PÉRDIDA', cell_format_titu)         #-- 23
            worksheet.freeze_panes(7, 0)
            # -------------------------------------------------------------------------------------
            # CUERPO PRINCIPAL DEL REPORTE
            # -------------------------------------------------------------------------------------
            w_leads = self.search(self._context.get('active_domain', []))  # Obtener registros según el dominio activo en la vista
            w_dato = ""
            w_fila = 7
            w_acum_gana = 0
            w_acum_abie = 0
            w_acum_anul = 0
            w_acum_perd = 0
            w_acum_exto = 0
            for w_lead in w_leads:
                worksheet.write(w_fila, 0, w_fila-6, cell_format_cent)   
                worksheet.write(w_fila, 1, w_lead.x_studio_nro_agrupamiento, cell_format_cent)
                worksheet.write(w_fila, 2, w_lead.x_studio_fecha_de_oportunidad, cell_format_fech)
                worksheet.write(w_fila, 3, w_lead.x_studio_fecha_proyectada_de_cierre, cell_format_fech)
                worksheet.write(w_fila, 4, w_lead.date_deadline, cell_format_fech)
                worksheet.write(w_fila, 5, w_lead.x_studio_gdn_responsable, cell_format_left)
                w_dato = w_lead.x_studio_many2one_field_t33Z2.x_udn_abrv
                worksheet.write(w_fila, 6, w_dato, cell_format_left)
                w_dato = w_lead.x_studio_many2one_field_RmaJp.x_sun_abrv
                worksheet.write(w_fila, 7, w_dato, cell_format_left)
                w_dato = w_lead.partner_id.name
                worksheet.write(w_fila, 8, w_dato, cell_format_left)
                
                worksheet.write(w_fila, 9, w_lead.x_studio_moneda_simbolo, cell_format_cent)
                if (w_lead.x_studio_moneda_simbolo=="S/."):
                    worksheet.write(w_fila, 10, w_lead.x_studio_monto_de_operacion_entero, cell_format_nume)
                else:
                    worksheet.write(w_fila, 11, w_lead.x_studio_monto_de_operacion_entero, cell_format_nume)
                    worksheet.write(w_fila, 12, w_lead.x_studio_tasa_cambiaria_dolares, cell_format_tcam)
                worksheet.write(w_fila, 13, w_lead.x_studio_monto_ajustado_reporte, cell_format_nume)
                worksheet.write(w_fila, 14, w_lead.x_studio_margen_utilidad, cell_format_xcen)
                w_utilidad_esperada = w_lead.x_studio_monto_ajustado_reporte * w_lead.x_studio_margen_utilidad
                worksheet.write(w_fila, 15, w_utilidad_esperada, cell_format_nume) 
                worksheet.write(w_fila, 16, w_lead.x_studio_proyecto, cell_format_left)
                #-----
                if (w_lead.x_studio_estado_oportunidad == "Ganada"):
                    lines  = w_lead.x_studio_proyectos_vinculados
                    w_acum_codig = ""
                    w_cont_regis = 0
                    w_cant_regis = len(lines)                               #-- EXTRAE LOS CÓDIGOS PROYECTO
                    for line in lines:
                        w_cont_regis += 1
                        if (line.x_studio_referencia_telco):
                            w_acum_codig += line.x_studio_referencia_telco.strip() 
                            if not (w_cont_regis==w_cant_regis):
                                w_acum_codig += "\n"
                    worksheet.write(w_fila, 17, w_acum_codig, cell_format_cent)
                else:
                    worksheet.write(w_fila, 17, " ", cell_format_cent)
                #-----
                if w_lead.x_studio_proyectos_asignados_rpt:
                    worksheet.write(w_fila, 18, w_lead.x_studio_proyectos_asignados_rpt, cell_format_left)
                    w_cant = len(w_lead.x_studio_proyectos_vinculados)
                    if (w_cant > 1):                                        #-- INSERTA COMENTARIO EN CELDA
                        if w_lead.x_studio_proyectos_asignados_rpt2:
                            w_titu = 'PROYECTOS ASIGNADOS:'+'\n'+'---------------------------------------'+'\n'
                            worksheet.write_comment(w_fila, 17, w_titu + w_lead.x_studio_proyectos_asignados_rpt2, {
                                                    'author': 'CENS-PERÚ',
                                                    'width': 400,  # pixels
                                                    'color': '#f5e69b',
                                                    'font_name': 'Arial'
                                        })
                else:
                    worksheet.write(w_fila, 18, " ")

                #-----                                          DETERMINA Y PINTA - ESTADO OPORTUNIDAD
                worksheet.write(w_fila, 19, w_lead.x_studio_porcentaje_de_probabilidad, cell_format_porc)
                if (w_lead.x_studio_monto_de_operacion_entero>=0):
                    if (w_lead.x_studio_estado_oportunidad == "Ganada"):
                        worksheet.write(w_fila, 20, w_lead.x_studio_estado_oportunidad, cell_format_verd)
                        w_acum_gana += w_lead.x_studio_monto_ajustado_reporte
                    elif (w_lead.x_studio_estado_oportunidad == "Abierto"):
                        worksheet.write(w_fila, 20, w_lead.x_studio_estado_oportunidad, cell_format_amba)
                        w_acum_abie += w_lead.x_studio_monto_ajustado_reporte
                    elif (w_lead.x_studio_estado_oportunidad == "Anulada"):
                        worksheet.write(w_fila, 20, w_lead.x_studio_estado_oportunidad, cell_format_rojo)
                        worksheet.write(w_fila, 23, w_lead.x_studio_sustento_anulado_perdido, cell_format_perd)
                        w_acum_anul += w_lead.x_studio_monto_ajustado_reporte
                    elif (w_lead.x_studio_estado_oportunidad == "Perdida"):
                        worksheet.write(w_fila, 20, w_lead.x_studio_estado_oportunidad, cell_format_rojo)
                        worksheet.write(w_fila, 23, w_lead.x_studio_sustento_anulado_perdido, cell_format_perd)
                        w_acum_perd += w_lead.x_studio_monto_ajustado_reporte
                    else:
                        worksheet.write(w_fila, 20, w_lead.x_studio_estado_oportunidad, cell_format_cent)
                else:
                    worksheet.write(w_fila, 20, "EXTORNO", cell_format_cent)
                    w_acum_exto += w_lead.x_studio_monto_ajustado_reporte

                worksheet.write(w_fila, 21, w_lead.x_studio_fecha_hora_ultimo_estado, cell_format_fech)
                worksheet.write(w_fila, 22, w_lead.x_fecha_win_texto, cell_format_fech)
                w_fila += 1

            # ---------------------------------------------------------
            # GENERA GRÁFICO COMPARATIVO
            # ---------------------------------------------------------
            worksheet2 = workbook.add_worksheet("COMPARATIVO")
            worksheet2.activate()
            datos1 = ["Ganadas", "Abiertas", "Anuladas", "Perdidas", "Extornadas"]
            datos2 = [w_acum_gana, w_acum_abie, w_acum_anul, w_acum_perd, w_acum_exto]
            worksheet2.write_column('A1', datos1, cell_format_left)
            worksheet2.write_column('B1', datos2, cell_format_nume)
            worksheet2.write_column('A7', "Acumulado", cell_format_left)
            
            grafico1 = workbook.add_chart({'type': 'bar', 
                                           'name': 'COMPARATIVO DE OPORTUNIDADES',
                                           'data_labels': {'value': True,                   # Etiquetas de datos
                                                           'value': '=COMPARATIVO!$B$1:$B$5',
                                                           'position': 'outside_end',   # Posición de las etiquetas de datos
                                                           'font': {'size': 10,  # Tamaño de la fuente de las etiquetas
                                                                    'color': 'black'}
                                                          }
                                           })

            grafico1.add_series({"name": "=COMPARATIVO!$A$7",
                                 "categories": "=COMPARATIVO!$A$1:$A$5",
                                 "values": "=COMPARATIVO!$B$1:$B$5",
                                 'fill':   {'color': '#FF9900'},
                                })
            grafico1.set_title({"name": "COMPARATIVO OPORTUNIDADES DE NEGOCIO (ON)"+"\n"+"(Según Estatus y Periodo)"})
            grafico1.set_x_axis({"name": "ESTADOS OPORTUNIDADES"})
            grafico1.set_y_axis({"name": "ACUMULADO (S/.)"})
            grafico1.set_size({'width': 840, 'height': 480})
            
            grafico1.set_table()       # Mostrar la tabla de datos
            grafico1.set_legend({'position': 'none'})  # Desactivar la leyenda
            grafico1.set_x_axis({'num_format': '0"K"'})    # Formatear los valores del eje Y de forma abreviada
            grafico1.set_x_axis({'position_axis': 'on_tick'})  # Establecer los ejes en vertical primario
            grafico1.set_y_axis({'position_axis': 'value'})
            grafico1.set_style(13)
            grafico1.set_plotarea({'fill':   {'color': '#DBEEF4'}})


            worksheet2.insert_chart('A1', grafico1)  # Insert the chart into the worksheet.

            worksheet.activate()
            workbook.close()

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Obtener los datos binarios del archivo 
        # -------------------------------------------------------------------------------------
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Crear un registro temporal para almacenar el archivo 
        # -------------------------------------------------------------------------------------
        attachment = self.env['ir.attachment'].create({
            'name': 'CENS-CRM-LEADS.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': 'CENS-CRM-LEADS.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # -------------------------------------------------------------------------------------
        # DOWNLOAD - Devolver una acción para descargar el archivo 
        # -------------------------------------------------------------------------------------
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # -------------------------------------
    # MÉTODO - INICIALIZA VARIABLES
    # -------------------------------------
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
    
    # @api.model
    # def create(self, vals):
    #    if 'cens_user_id' not in vals:
    #        vals['cens_user_id'] = self.env.user.id

    #    for record in self:
    #        current_datetime = datetime.now()
    #        record.cens_fecha_actual = current_datetime
    #        record.cens_campo_control = "ENTRÓ LA WADA"

    #    return super(crm_lead_Custom, self).create(vals)


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


            # Copiar los registros relacionados de x_studio_proyectos_vinculados
            #for related_record in lead.x_studio_proyectos_vinculados:
                #self.env['x_crm_lead_line_b50b7'].create({
                #    'x_crm_lead_id': new_lead.id,
                #    'x_project_id': related_record.x_project_id.id,
                #    'x_state': related_record.x_state,
                #    'x_cliente': related_record.x_cliente,
                #    'x_contrato': related_record.x_contrato,
                #    'x_fecha_inicio': related_record.x_fecha_inicio,
                #    'x_fecha_fin': related_record.x_fecha_fin,
                #    'x_monto': related_record.x_monto,
                #    'x_observaciones': related_record.x_observaciones,
                #})
