from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import datetime
import base64
import xlrd
import xlsxwriter
from io import BytesIO

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def export_to_xlsx(self):
        # Crear archivo Excel en memoria
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        # -------------------------------------------------------------------------------------
        # CONFIGURACIÓN GENERAL DE LA WORKSHEET
        # -------------------------------------------------------------------------------------
        workbook.set_properties({
                'title':    'NOMINA-CENS - Hoja de Trabajo',
                'subject':  'Extracto a la fecha',
                'author':   'ODOO-CENS',
                'manager':  'Gestión Humana',
                'company':  'CENS PERÚ',
                'category': 'LOTE - EXCEL',
                'keywords': 'nómina, lote, worksheet',
                'created':  datetime.now(),
                'comments': 'Creado por: Área de Sistemas - CENS-PERÚ'})
        worksheet = workbook.add_worksheet('Nóminas')
        cell_format = workbook.add_format()
        cell_format_empr = workbook.add_format({'bold': True})
        cell_format_cabe = workbook.add_format()
        cell_format_tuti = workbook.add_format()
        cell_format_tut2 = workbook.add_format()
        cell_format_titu = workbook.add_format()
        # ------
        cell_format_nume = workbook.add_format()
        cell_format_nume.set_num_format('#,##0')
        cell_format_nume.set_align('center')
        cell_format_nume.set_align('vcenter')
        # ------
        cell_format_impo = workbook.add_format()
        cell_format_impo.set_num_format('#,##0.00')
        cell_format_impo.set_align('vcenter')
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
        # -------------------------------------------------------------------------------------
        # AJUSTA ANCHO DE COLUMNAS   (ColIni,ColFin,Ancho)
        # -------------------------------------------------------------------------------------
        worksheet.set_column(0, 0, 9)       #-- Ord
        worksheet.set_column(1, 1, 14)      #-- Boleta 
        worksheet.set_column(2, 2, 33)      #-- Npombre del Empleado
        worksheet.set_column(3, 3, 13)      #-- DNI
        worksheet.set_column(4, 4, 11)      #-- LOTE
        worksheet.set_column(5, 5, 13)      #-- FECHA INICIAL
        worksheet.set_column(6, 6, 13)      #-- FECHA GINAL
        worksheet.set_column(7, 7, 8)       #-- MONEDA
        worksheet.set_column(8, 8, 11)      #-- 
        worksheet.set_column(9, 9, 10)      #--
        worksheet.set_column(10, 10, 10)    #-- 
        worksheet.set_column(11, 11, 10)    #-- 
        worksheet.set_column(12, 12, 10)    #-- 
        worksheet.set_column(13, 13, 10)    #-- 
        worksheet.set_column(14, 14, 10)    #-- 
        worksheet.set_column(15, 15, 10)    #-- 
        worksheet.set_column(16, 16, 10)    #-- 
        worksheet.set_column(17, 17, 10)    #-- 
        worksheet.set_column(18, 18, 10)    #-- 
        worksheet.set_column(19, 19, 10)    #-- 
        worksheet.set_column(20, 20, 10)    #-- 
        worksheet.set_column(21, 21, 10)    #-- 
        worksheet.set_column(22, 22, 10)    #-- 
        worksheet.set_column(23, 23, 10)    #--
        worksheet.set_column(24, 24, 10)    #--
        worksheet.set_column(25, 25, 10)    #--
        worksheet.set_column(26, 26, 10)    #--
        worksheet.set_column(27, 27, 10)    #--
        worksheet.set_column(28, 28, 10)    #--
        worksheet.set_column(29, 29, 10)    #--
        worksheet.set_column(30, 30, 10)    #--
        worksheet.set_column(31, 31, 10)    #-- 
        worksheet.set_column(32, 32, 10)    #--
        worksheet.set_column(33, 33, 10)    #--
        # ------
        worksheet.set_row(6, 27)        # (Fila,Altura)
        worksheet.set_zoom(85)          # %-Zoom
        # -------------------------------------------------------------------------------------
        # CABECERA DEL REPORTE
        # -------------------------------------------------------------------------------------
        worksheet.insert_image('A1', 'src/user/cens_crm/static/description/logo-tiny_96.png')
        worksheet.write('B2', 'CARRIER ENTERPRISE NETWORK SOLUTIONS SAC', cell_format_empr)
        worksheet.write('B3', 'Gestión Humana - Nóminas - CENS-PERÚ')
        cell_format_cabe.set_font_name('Arial Black')
        cell_format_cabe.set_font_size(11)
        worksheet.write('H4', 'PLANILLA DE SUELDOS - EMPLEADOS CENS - DATA WORKSHEET', cell_format_cabe)
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
        worksheet.merge_range('J6:V6', 'Merged Cells', merge_format)
        worksheet.write('J6', 'PARÁMETROS MENSUALES PARA EL CÁLCULO DE INGRESOS', cell_format_tut2)

        worksheet.merge_range('W6:AA6', 'Merged Cells', merge_format)
        worksheet.write('W6', 'ACUERDOS CONTRACTUALES', cell_format_tuti)

        worksheet.merge_range('AC6:AH6', 'Merged Cells', merge_format)
        worksheet.write('AC6', 'E  G  R  E  S  O  S', cell_format_tuti)
        # -------------------------------------------------------------------------------------
        # BARRA DE TITULOS
        # -------------------------------------------------------------------------------------
        cell_format_tuti.set_font_name('Arial')
        cell_format_tuti.set_font_color('black')
        cell_format_tuti.set_font_size(8)
        cell_format_tuti.set_text_wrap()                 # FORMATO TÍTULO - COLUMNAS IMPORTES #B7DEE8
        cell_format_tuti.set_bg_color('#92CDDC')
        cell_format_tuti.set_align('center')
        cell_format_tuti.set_align('vcenter')
        #-----
        cell_format_tut2.set_font_name('Arial')
        cell_format_tut2.set_font_color('black')
        cell_format_tut2.set_font_size(8)
        cell_format_tut2.set_text_wrap()                 # FORMATO TÍTULO 2 - COLUMNAS IMPORTES #B7DEE8
        cell_format_tut2.set_bg_color('#B7DEE8')
        cell_format_tut2.set_align('center')
        cell_format_tut2.set_align('vcenter')
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
        worksheet.write('B7', 'BOLETA', cell_format_titu)                       #-- 01
        worksheet.write('C7', 'NOMBRE DEL EMPLEADO', cell_format_titu)          #-- 02
        worksheet.write('D7', 'D.N.I.', cell_format_titu)                       #-- 03
        worksheet.write('E7', 'LOTE', cell_format_titu)                         #-- 04
        worksheet.write('F7', 'FECHA INICIAL', cell_format_titu)                #-- 05
        worksheet.write('G7', 'FECHA FINAL', cell_format_titu)                  #-- 06
        worksheet.write('H7', 'MONEDA', cell_format_titu)                       #-- 07
        worksheet.write('I7', 'DIAS COMPUTADOS', cell_format_titu)              #-- 08
        worksheet.write('J7', 'LICENCIA FALLECIMTO', cell_format_titu)          #-- 09
        worksheet.write('K7', 'LICENCIA MATR-PATR', cell_format_titu)           #-- 10
        worksheet.write('L7', 'VACACIONES', cell_format_titu)                   #-- 11
        worksheet.write('M7', 'CON GOCE', cell_format_titu)                     #-- 12
        worksheet.write('N7', 'DESCANSO MÉDICO', cell_format_titu)              #-- 13
        worksheet.write('O7', 'TIPO FERIADOS', cell_format_titu)                #-- 14
        worksheet.write('P7', 'DIAS FERIADOS', cell_format_titu)                #-- 15
        worksheet.write('Q7', 'IMPORTE FERIADOS', cell_format_titu)             #-- 16
        worksheet.write('R7', 'BONIFIC. EXTRAORD.', cell_format_titu)           #-- 17
        worksheet.write('S7', 'IMPORTE H.EXTRAS', cell_format_titu)             #-- 18
        worksheet.write('T7', 'REEMBOLSO', cell_format_titu)                    #-- 19
        worksheet.write('U7', 'REEMBOLSO MOVILIDAD', cell_format_titu)          #-- 20
        worksheet.write('V7', 'REEMBOLSO COMBUSTIB', cell_format_titu)          #-- 21
        worksheet.write('W7', 'MOVILIDAD', cell_format_titu)                    #-- 22
        worksheet.write('X7', 'VALE ALIMENTOS', cell_format_titu)               #-- 23
        worksheet.write('Y7', 'CONDICS. LABORALES', cell_format_titu)           #-- 24
        worksheet.write('Z7', 'BONIFIC. EDUCACIÓN', cell_format_titu)           #-- 25
        worksheet.write('AA7', 'UTILIDAD. VOLUNTARS', cell_format_titu)         #-- 26
        worksheet.write('AB7', 'ADELANTO GRATIFICAC.', cell_format_titu)        #-- 27
        worksheet.write('AC7', 'DIAS INASISTENCIA', cell_format_titu)         #-- 28
        worksheet.write('AD7', 'DIAS SIN GOCE', cell_format_titu)               #-- 29
        worksheet.write('AE7', 'ADELANTO SUELDO', cell_format_titu)             #-- 30
        worksheet.write('AF7', 'MINUTOS TARDANZA', cell_format_titu)             #-- 31
        worksheet.write('AG7', 'RETENCIÓN JUDICIAL', cell_format_titu)          #-- 32
        worksheet.write('AH7', 'DSCTO. PRÉSTAMOS', cell_format_titu)            #-- 33
        worksheet.write('AI7', 'MO', cell_format_titu)         #-- 34
        worksheet.write('AJ7', 'MO', cell_format_titu)         #-- 35
        worksheet.write('AK7', 'MO', cell_format_titu)         #-- 36
        worksheet.write('AL7', 'MO', cell_format_titu)         #-- 37
        worksheet.write('AM7', 'MO', cell_format_titu)         #-- 38
        worksheet.write('AN7', 'MO', cell_format_titu)         #-- 39
        worksheet.freeze_panes(7, 4)


        # Definir campos a exportar
        fields_to_export = [
            'id', 'number', 'name', 'date_from', 'date_to',
            'employee_id', 'contract_id', 'struct_id', 'state'
        ]

        # Escribir encabezados
        for col, field in enumerate(fields_to_export):
            worksheet.write(7, col, field)

        # Escribir datos
        for row, record in enumerate(self, start=9):
            for col, field in enumerate(fields_to_export):
                value = record[field]
                if field in ['employee_id', 'contract_id', 'struct_id']:
                    value = value.name if value else ''
                worksheet.write(row, col, str(value))

        workbook.close()
        
        # Crear adjunto
        xlsx_data = output.getvalue()
        attachment = self.env['ir.attachment'].create({
            'name': 'nominas_export.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
        })

        # Retornar acción para descargar
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def import_from_xlsx(self):
        # Mostrar wizard de importación
        return {
            'name': _('Importar Nóminas'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.import.wizard',
            'view_mode': 'form',
            'target': 'new',
        }
