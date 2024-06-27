


def action_button_insertar(self, vals):
        textarea = self.env['ir.ui.view'].render_template(
            "<textarea>{{ textarea_value }}</textarea>",
            {'textarea_value': self.cens_campo_descripcion}
        )
        insert_value = self.cens_campo_insertag
        start_pos = textarea.find(self.cens_campo_descripcion)
        end_pos = start_pos + len(self.cens_campo_descripcion)
        new_text = textarea[:start_pos] + insert_value + textarea[end_pos:]
        self.cens_campo_descripcion = new_text
        #
        #
        pass

@api.model
def insert_text(self):
        textarea = self.env['ir.ui.view'].render_template(
            "<textarea>{{ textarea_value }}</textarea>",
            {'textarea_value': self.cens_campo_descripcion}
        )
        insert_value = self.cens_campo_insertag
        start_pos = textarea.find(self.cens_campo_descripcion)
        end_pos = start_pos + len(self.cens_campo_descripcion)
        new_text = textarea[:start_pos] + insert_value + textarea[end_pos:]
        self.cens_campo_descripcion = new_text

@api.model
def action_button_insertar(self, vals):
        env = Environment(autoescape=select_autoescape(['html', 'xml']))
        template = env.from_string("<textarea>{{ textarea_value }}</textarea>")
        textarea = template.render({'textarea_value': self.cens_campo_descripcion})
        insert_value = self.cens_campo_insertag
        start_pos = textarea.find(self.cens_campo_descripcion)
        end_pos = start_pos + len(self.cens_campo_descripcion)
        new_text = textarea[:start_pos] + insert_value + textarea[end_pos:]
        self.cens_campo_descripcion = new_text

def action_button_insertar(self):
        for record in self:
            textarea = record.cens_contenido_generales
            insert_value = record.cens_campo_insertag
            start_pos = textarea.find(record.cens_contenido_generales)
            end_pos = start_pos + len(record.cens_contenido_generales)
            new_text = textarea[:start_pos] + insert_value + textarea[end_pos:]
            record.cens_campo_descripcion = new_text
            record.cens_campo_control = "StartPos="+str(type(start_pos))+"\n"+"EndPos="+str(type(end_pos))+"\n"+"InsertValue="+str(type(insert_value))+"\n"+"Desc="+str(type(record.cens_contenido_generales))+"\n"+"new_text="+str(type(new_text))
       