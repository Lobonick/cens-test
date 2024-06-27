from odoo import api, fields, models
#from jinja2 import Environment, select_autoescape
#from odoo.models import ir_model, ir_model_fields
from datetime import datetime
import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)

class CustomPlantilla(models.Model):
    _name = 'hr.contract.plantilla_documento'
    _description = 'Plantilla Contratos'

    name = fields.Char("Nombre")
    user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)
    state = fields.Selection([("draft", "Borrador"), ("posted", "Confirmado"), ("annul", "Anulado")], default="draft")
    cens_marcador_cabecera = fields.Binary(string="Imagen", related='company_id.x_studio_plantilla_contrato')
    cens_img_sello_anulado = fields.Binary(string="Imagen", related='company_id.x_studio_sello_anulado')
    cens_separador_06 = fields.Binary(string="Imagen", related='company_id.x_studio_separador_06')
    cens_regimen_laboral = fields.Selection([("locac", "Locación de Servicios"), ("gener", "Régimen General"), ("inter", "Régimen Intermitente")], default="locac")
    cens_campo_seleccionado= fields.Many2one('hr.contract.plantilla_camposinsert', string='Campo Seleccionado')
    cens_campo_insertag = fields.Char("Campo a Insertar", readonly=True, store=True, compute='_compute_cens_campo_insertag')
    cens_campo_insertag_2 = fields.Char("Texto insertar")
    cens_campo_descripcion = fields.Char("Descripción del Campo", related='cens_campo_seleccionado.cens_campo_descripcion', store=True, readonly=True)
    cens_campo_control     = fields.Text("CONTROL:")
    cens_contenido_titulo    = fields.Char("Título contrato")
    cens_contenido_generales = fields.Text("Cabecera contrato")
    cens_clausula_01_titulo  = fields.Char("Cláusula 01 - Título")
    cens_clausula_01_parrafo = fields.Text("Cláusula 01 - Párrafo")
    cens_clausula_02_titulo  = fields.Char("Cláusula 02 - Título")
    cens_clausula_02_parrafo = fields.Text("Cláusula 02 - Párrafo")
    cens_clausula_03_titulo  = fields.Char("Cláusula 03 - Título")
    cens_clausula_03_parrafo = fields.Text("Cláusula 03 - Párrafo")
    cens_clausula_04_titulo  = fields.Char("Cláusula 04 - Título")
    cens_clausula_04_parrafo = fields.Text("Cláusula 04 - Párrafo")
    cens_clausula_05_titulo  = fields.Char("Cláusula 05 - Título")
    cens_clausula_05_parrafo = fields.Text("Cláusula 05 - Párrafo")
    cens_clausula_06_titulo  = fields.Char("Cláusula 06 - Título")
    cens_clausula_06_parrafo = fields.Text("Cláusula 06 - Párrafo")
    cens_clausula_07_titulo  = fields.Char("Cláusula 07 - Título")
    cens_clausula_07_parrafo = fields.Text("Cláusula 07 - Párrafo")
    cens_clausula_08_titulo  = fields.Char("Cláusula 08 - Título")
    cens_clausula_08_parrafo = fields.Text("Cláusula 08 - Párrafo")
    cens_clausula_09_titulo  = fields.Char("Cláusula 09 - Título")
    cens_clausula_09_parrafo = fields.Text("Cláusula 09 - Párrafo")
    cens_clausula_10_titulo  = fields.Char("Cláusula 10 - Título")
    cens_clausula_10_parrafo = fields.Text("Cláusula 10 - Párrafo")
    cens_clausula_11_titulo  = fields.Char("Cláusula 11 - Título")
    cens_clausula_11_parrafo = fields.Text("Cláusula 11 - Párrafo")
    cens_clausula_12_titulo  = fields.Char("Cláusula 12 - Título")
    cens_clausula_12_parrafo = fields.Text("Cláusula 12 - Párrafo")
    cens_clausula_13_titulo  = fields.Char("Cláusula 13 - Título")
    cens_clausula_13_parrafo = fields.Text("Cláusula 13 - Párrafo")

    def confirmar_plantilla(self):
        self.state = 'posted'
    
    def regresa_borrador(self):
        self.state = 'draft'
    
    def anula_plantilla(self):
        self.state = 'annul'

    @api.model
    def insert_text(self, record_id, campo_seleccionado, texto_a_insertar):
        record = self.browse(record_id)
        if not record:
            raise UserError("Record not found")
        
        if not hasattr(record, campo_seleccionado):
            raise UserError("Invalid field selected")
        
        campo_actual = getattr(record, campo_seleccionado, "")
        nuevo_texto = campo_actual + texto_a_insertar
        setattr(record, campo_seleccionado, nuevo_texto)
        record.write({campo_seleccionado: nuevo_texto})

        return True


    # @api.model
    # def action_button_insertar(self):
    #    campo_seleccionado = self.cens_campo_seleccionado
    #    texto_a_insertar = self.cens_campo_insertag_2
    #    if campo_seleccionado and texto_a_insertar:
    #        campo_actual = getattr(self, campo_seleccionado, "")
    #        nuevo_texto = campo_actual + texto_a_insertar
    #        setattr(self, campo_seleccionado, nuevo_texto)
    #    return True

    # def action_button_insertar2(self):
    #    # Lógica para insertar el contenido en el lugar del cursor
    #    self.cens_campo_control = "MAY-DAY"
    #    #self.cens_campo_insertag
    #    return 
    
    #    {
    #        'type': 'ir.actions.client',
    #        'tag': 'insert_content',
    #        'params': {
    #            'field_names': ['cens_contenido_generales'],
    #            'insert_value': self.cens_campo_insertag,
    #        }
    #    }             

    def action_button_limpia(self):
        #
        #
        pass

    @api.depends('cens_campo_seleccionado')
    def _compute_cens_campo_insertag(self):
        for record in self:
            if record.cens_campo_seleccionado:
                record.cens_campo_insertag = '<' + record.cens_campo_seleccionado.name + '>'
            else:
                record.cens_campo_insertag = "QUIQUE LO MÁXIMO"
        pass

    @api.model
    def create(self, vals):
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
        if 'company_id' not in vals:
            vals['company_id'] = self.env.company.id
        return super(CustomPlantilla, self).create(vals)

    # --------------------------------
    # BOTÓN: CONFIRMAR PLANTILLA 
    # --------------------------------
    # @api.model
    # def confirmar_plantilla(self):
    #    for record in self:
    #        record.state = 'posted'


class CustomInsertag(models.Model):
    _name = 'hr.contract.plantilla_insertag'
    _description = 'Etiquetas Inserción'

    name = fields.Char("Nombre")
    user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)
    state = fields.Selection([("draft", "Borrador"), ("posted", "Confirmado"), ("annul", "Anulado")], default="draft")
    cens_marcador_cabecera = fields.Binary(string="Imagen", related='company_id.x_studio_plantilla_contrato_insertag')
    cens_img_insertag = fields.Binary(string="Imagen", related='company_id.x_studio_imagen_insertag')
    cens_separador_06 = fields.Binary(string="Imagen", related='company_id.x_studio_separador_06')
    cens_campo_descripcion = fields.Char("Descripción del Campo")
    cens_campo_insertag    = fields.Char("Etiqueta a insertar")
    cens_campo_tecnico     = fields.Char("Nombre técnico")

    def confirmar_insertag(self):
        self.state = 'posted'
    
    def borrador_insertag(self):
        self.state = 'draft'
    
    def anula_insertag(self):
        self.state = 'annul'

    @api.model
    def create(self, vals):
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
        if 'company_id' not in vals:
            vals['company_id'] = self.env.company.id
        return super(CustomInsertag, self).create(vals)
    

class CustomCamposinsert(models.Model):
    _name = 'hr.contract.plantilla_camposinsert'
    _description = 'Campos para Inserción'

    name = fields.Char("Nombre")
    user_id = fields.Many2one('res.users', string='Usuario activo', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True, default=lambda self: self.env.company.id)
    state = fields.Selection([("draft", "Borrador"), ("posted", "Confirmado"), ("annul", "Anulado")], default="draft")
    cens_marcador_cabecera = fields.Binary(string="Imagen", related='company_id.x_studio_plantilla_contrato_campos')
    cens_img_insertag = fields.Binary(string="Imagen", related='company_id.x_studio_imagen_insertag')
    cens_img_decora   = fields.Binary(string="Imagen", related='company_id.x_studio_decora_codigo_02')
    cens_separador_06 = fields.Binary(string="Imagen", related='company_id.x_studio_separador_06')
    cens_campo_modelo = fields.Selection([("employee", "Ficha Personal"), ("contract", "Contrato Laboral"), ("project", "Proyectos")], string="Modelo Origen", default="project")
    cens_campo_filename = fields.Char("Nombre Técnico del modelo (tabla)", readonly=True) # default="\\server\hr.contract", 
    cens_campo_descripcion = fields.Char("Descripción del Campo")
    cens_campo_tipo    = fields.Selection([("char", "Caracter"), ("text", "Texto"), ("integer", "Entero"), ("float", "Decimal"), ("datetime", "Fecha"), ("selection", "Selección")], string="Tipo de Dato", default="text")
    cens_campo_tecnico     = fields.Char("Nombre técnico")

    def confirmar_camposinsert(self):
        self.state = 'posted'
    
    def borrador_camposinsert(self):
        self.state = 'draft'
    
    def anula_camposinsert(self):
        self.state = 'annul'

    @api.onchange('cens_campo_modelo')
    def _onchange_cens_campo_modelo(self):
        if self.cens_campo_modelo == 'employee':
            self.cens_campo_filename = '\\server\hr.employee'
        elif self.cens_campo_modelo == 'contract':
            self.cens_campo_filename = '\\server\hr.contract'
        elif self.cens_campo_modelo == 'project':
            self.cens_campo_filename = '\\server\project.project'
        
    #else:
    #self.cens_campo_filename = '\\'

    @api.model
    def create(self, vals):
        if 'user_id' not in vals:
            vals['user_id'] = self.env.user.id
        if 'company_id' not in vals:
            vals['company_id'] = self.env.company.id
        
        return super(CustomCamposinsert, self).create(vals)




        # ----------------------------------------------------------------
        # cens_campo_contrato    = fields.Many2one('hr.contract', string='Campo del contrato', domain=lambda self: self._get_contract_fields())
        # ----------------------------------------------------------------
        # @api.model
        # def _get_contract_fields(self):
        #    allowed_fields = [
        #            'x_studio_tipo_de_planilla', #
        #            'x_studio_movilidad_mensual',#
        #            'x_studio_alimentacion',     #
        #            'x_studio_condiciones_laborales_1',  #
        #            'x_studio_bonificacion_x_educacion', #
        #            'x_studio_utilidades_voluntarias',   #
        #        ]            
        #    contract_fields = self.env['hr.contract']._fields
        #    field_names = [(field, field) for field in contract_fields if field in allowed_fields]
        #    return field_names
        #
        # -----------------------------------------------------------------
        # excluded_fields = [
        #        'x_custom_field1',   Campo específico
        #        'x_custom_field2',   Campo específico
        #        'x_field_prefix_*',  Todos los campos que comiencen con 'x_field_prefix_'
        #        'x_*_suffix',        Todos los campos que terminen con '_suffix'
        #    ]   
        # contract_fields = self.env['hr.contract']._fields
        # field_names = [(field, field) for field in contract_fields if field not in excluded_fields]
        # return field_names
        # ----------------------------------------------------------------
        # field_names = [(field, field) for field in contract_fields if any(re.match(pattern, field) for pattern in allowed_fields)]

