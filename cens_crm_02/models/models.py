from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools.mail import email_split
from datetime import datetime
import requests
import base64
import logging
from io import BytesIO

_logger = logging.getLogger(__name__)

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    cens_preventa_1 = fields.Many2one('res.users', string='PreVenta Asignado:', default=lambda self: self.env.user.id)
    cens_control_01 = fields.Integer(string='Control 01:', readonly=True, default=0, existing_field=True)
    cens_control_02 = fields.Char("Control 02:")
    cens_usuario_activo_id = fields.Integer(
        string='Usuario Activo', 
        default=0,
        compute='_compute_usuario_activo_id',
        store=False  # No almacenar en la BD
    )
    #cens_img_aprueba_00 = fields.Binary(string="Estado Aprobación", related='company_id.x_studio_crm_aprueba_00', store='False')
    #cens_img_aprueba_01 = fields.Binary(string="Estado Aprobación", related='company_id.x_studio_crm_aprueba_01', store='False')
    #cens_img_aprueba_02 = fields.Binary(string="Estado Aprobación", related='company_id.x_studio_crm_aprueba_02', store='False')
    
    # ------------------------------
    # ACTUALIZA USUARIO ACTIVO
    # ------------------------------
    def _compute_usuario_activo_id(self):
        for record in self:
            record.cens_usuario_activo_id = self.env.user.id
            record.x_studio_usuario_activo_id = self.env.user.id

    # ==================================================================================================================
    # INICIO: CONTACTOS FINANCIEROS - ADMIN
    # ==================================================================================================================

    @api.depends('x_studio_contactos_financieros')
    def _compute_contador_contactos(self):
        """Calcular el número de contactos financieros registrados"""
        for record in self:
            record.x_studio_contador_contactos = len(record.x_studio_contactos_financieros)

    # ----------------------------------------------
    # CARGAR CONTACTOS FINANCIEROS AUTOMÁTICAMENTE
    # ----------------------------------------------
    @api.onchange('partner_id')
    def _onchange_partner_id_load_financial_contacts(self):
        """
        Cargar automáticamente los contactos financieros cuando se selecciona un cliente
        """
        if self.partner_id:
            try:
                self._cargar_contactos_financieros()
            except Exception as e:
                _logger.warning('Error en onchange partner_id: %s', str(e))
                # No mostrar error al usuario, solo registrar en logs
    
    def _cargar_contactos_financieros(self):
        """
        Método principal para cargar contactos financieros desde la empresa cliente
        """
        # Prevenir ejecución durante instalación o upgrades
        if self.env.context.get('install_mode') or self.env.context.get('module') == 'base':
            return
            
        if not self.partner_id:
            # Si no hay cliente seleccionado, limpiar contactos financieros
            self.x_studio_contactos_financieros = [(5, 0, 0)]
            return
        
        try:
            # Buscar contactos relacionados a la empresa cliente
            contactos_empresa = self._buscar_contactos_empresa()
            
            if contactos_empresa:
                # Preparar lista de contactos para cargar
                contactos_financieros_vals = []
                
                for contacto in contactos_empresa:
                    contacto_vals = self._preparar_vals_contacto_financiero(contacto)
                    contactos_financieros_vals.append((0, 0, contacto_vals))
                
                # Actualizar la lista de contactos financieros
                # Primero limpiar los existentes, luego agregar los nuevos
                self.x_studio_contactos_financieros = [(5, 0, 0)] + contactos_financieros_vals
                
                # Log para seguimiento
                _logger.info(
                    'Cargados %s contactos financieros para la oportunidad %s (Cliente: %s)',
                    len(contactos_empresa), self.name or 'Nueva', self.partner_id.name
                )
            else:
                # Si no hay contactos, limpiar la lista
                self.x_studio_contactos_financieros = [(5, 0, 0)]
                _logger.info(
                    'No se encontraron contactos para la empresa %s en la oportunidad %s',
                    self.partner_id.name, self.name or 'Nueva'
                )
        except Exception as e:
            _logger.error('Error al cargar contactos financieros: %s', str(e))
            # En caso de error, no interrumpir el flujo normal
    
    def _buscar_contactos_empresa(self):
        """
        Buscar todos los contactos relacionados a la empresa cliente
        """
        if not self.partner_id:
            return self.env['res.partner']
        
        # Criterios de búsqueda para contactos de la empresa
        domain = [
            '|',
            ('parent_id', '=', self.partner_id.id),  # Contactos hijos de la empresa
            ('id', '=', self.partner_id.id),         # La empresa misma
        ]
        
        # Filtros adicionales para contactos válidos
        domain += [
            ('is_company', '=', False),  # Solo personas, no empresas
            ('email', '!=', False),      # Que tengan email
            ('active', '=', True),       # Que estén activos
        ]
        
        # Buscar contactos
        #contactos = self.env['res.partner'].search(domain, order='name asc')
        contactos = self.env['x_crm_lead_line_eaa1f'].search(domain, order='x_name asc')
        _logger.info('STATUS: Buscando contacto.')

        return contactos
    
    def _preparar_vals_contacto_financiero(self, contacto):
        """
        Preparar los valores para crear un registro de contacto financiero
        """
        # Determinar el cargo basado en información disponible
        cargo = self._determinar_cargo_contacto(contacto)
        
        # Preparar los valores del contacto financiero
        vals = {
            'x_name': cargo,
            'x_studio_empresa_id': self.partner_id.id,
            'x_studio_finan_empresa_name': self.partner_id.name,
            'x_studio_finan_partner_id': contacto.id,
            'x_studio_finan_partner_celular': contacto.mobile or contacto.phone or '',
            'x_studio_finan_partner_telefono': contacto.phone or contacto.mobile or '',
            'x_studio_finan_partner_email': contacto.email or '',
            'x_studio_finan_partner_direccion': self._formatear_direccion_contacto(contacto),
            'x_studio_finan_partner_notas': f'Contacto cargado automáticamente desde empresa {self.partner_id.name}',
            'x_crm_lead_id': self.id,
        }
        
        return vals
    
    def _determinar_cargo_contacto(self, contacto):
        """
        Determinar el cargo del contacto basado en información disponible
        """
        # Si el contacto tiene un cargo definido
        if contacto.function:
            return contacto.function
        
        # Si es el contacto principal de la empresa
        if contacto.id == self.partner_id.id:
            return 'Gerente General'
        
        # Si tiene keywords financieros en el nombre o título
        nombre_lower = (contacto.name or '').lower()
        keywords_financieros = [
            'financiero', 'finanzas', 'contable', 'contador', 'tesorero',
            'gerente', 'director', 'administrador', 'cfp', 'cfo'
        ]
        
        for keyword in keywords_financieros:
            if keyword in nombre_lower:
                return f'Área {keyword.title()}'
        
        # Cargo por defecto
        return 'Contacto Financiero'
    
    def _formatear_direccion_contacto(self, contacto):
        """
        Formatear la dirección del contacto de manera legible
        """
        direccion_parts = []
        
        if contacto.street:
            direccion_parts.append(contacto.street)
        if contacto.street2:
            direccion_parts.append(contacto.street2)
        if contacto.city:
            direccion_parts.append(contacto.city)
        if contacto.state_id:
            direccion_parts.append(contacto.state_id.name)
        if contacto.country_id:
            direccion_parts.append(contacto.country_id.name)
        
        return ', '.join(direccion_parts) if direccion_parts else ''
    
    # ------------------------------
    # MÉTODO MANUAL PARA RECARGAR CONTACTOS
    # ------------------------------
    def action_recargar_contactos_financieros(self):
        """
        Acción manual para recargar contactos financieros
        """
        self.ensure_one()
        
        if not self.partner_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('⚠️ Cliente Requerido'),
                    'message': _('Debe seleccionar un cliente antes de cargar contactos financieros.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Cargar contactos
        contactos_antes = len(self.x_studio_contactos_financieros)
        self._cargar_contactos_financieros()
        contactos_despues = len(self.x_studio_contactos_financieros)
        
        # Crear mensaje en el chatter
        self.message_post(
            body=_(
                '🔄 <strong>CONTACTOS FINANCIEROS RECARGADOS</strong><br/>'
                '👤 <strong>Cliente:</strong> %s<br/>'
                '📊 <strong>Contactos anteriores:</strong> %s<br/>'
                '📊 <strong>Contactos cargados:</strong> %s<br/>'
                '👤 <strong>Usuario:</strong> %s<br/>'
                '📅 <strong>Fecha:</strong> %s'
            ) % (
                self.partner_id.name,
                contactos_antes,
                contactos_despues,
                self.env.user.name,
                fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            ),
            subject='Contactos Financieros Recargados',
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Contactos Recargados'),
                'message': _('Se han cargado %s contactos financieros para %s') % (contactos_despues, self.partner_id.name),
                'sticky': False,
                'type': 'success',
            }
        }
    
    # ------------------------------
    # CARGAR CONTACTOS AL ABRIR EL FORMULARIO
    # ------------------------------
    @api.model
    def default_get(self, fields_list):
        """
        Override para cargar valores por defecto, incluyendo contactos financieros
        """
        _logger.info('STATUS: Ingresó al FORM y listo para cargar.')
        result = super(CRMLead, self).default_get(fields_list)
        return result
    
    def _cargar_contactos_al_abrir(self):
        """
        Método separado para cargar contactos sin recursión
        """
        try:
            if self.partner_id and not self.x_studio_contactos_financieros:
                # Usar sudo para evitar problemas de permisos
                self.sudo()._cargar_contactos_financieros()
                _logger.info('Contactos financieros cargados automáticamente para %s', self.name or 'Nueva oportunidad')
        except Exception as e:
            _logger.warning('Error al cargar contactos financieros automáticamente: %s', str(e))
    
    @api.model
    def web_read(self, fields):
        """
        Override específico para la lectura web que evita recursión
        """
        result = super(CRMLead, self).web_read(fields)
        
        # Solo para registros individuales
        if len(self) == 1:
            try:
                # Verificar y cargar contactos si es necesario
                self._cargar_contactos_al_abrir()
            except Exception as e:
                _logger.warning('Error en web_read al cargar contactos: %s', str(e))
        
        return result
    
    
    # ------------------------------
    # MÉTODO ALTERNATIVO CON WRITE (MÁS ROBUSTO) - MEJORADO
    # ------------------------------
    def write(self, vals):
        """
        Validación adicional en el método write para mayor seguridad
        """
        try:
            # Si se está intentando cambiar el porcentaje de probabilidad a 100%
            if 'x_studio_porcentaje_probabilidad' in vals and vals['x_studio_porcentaje_probabilidad'] == '100':
                for record in self:
                    try:
                        contador_contactos = len(record.x_studio_contactos_financieros) if record.x_studio_contactos_financieros else 0
                        
                        if (self.x_studio_monto_de_operacion_entero > 0):
                            if contador_contactos == 0:
                                # Cambiar el valor a 30% antes de continuar
                                vals['x_studio_porcentaje_probabilidad'] = '30'
                                
                                # Log para auditoría
                                _logger.warning(
                                    'Usuario %s (ID: %s) intentó marcar oportunidad %s como GANADA sin contactos. Acción bloqueada.',
                                    self.env.user.name, self.env.user.id, record.name or 'Nueva'
                                )
                                
                                # Crear mensaje en el chatter para auditoría (sin causar recursión)
                                try:
                                    record.with_context(tracking_disable=True).message_post(
                                        body=_(
                                            '⚠️ <strong>INTENTO DE CAMBIO A GANADA BLOQUEADO</strong><br/>'
                                            '🚨 <strong>Motivo:</strong> No hay contactos financieros registrados<br/>'
                                            '📅 <strong>Fecha:</strong> %s<br/>'
                                            '👤 <strong>Usuario:</strong> %s<br/>'
                                            '🔄 <strong>Acción:</strong> Porcentaje revertido automáticamente a 30%%'
                                        ) % (
                                            fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                                            self.env.user.name
                                        ),
                                        subject='Validación de Contactos - GANADA Bloqueada',
                                        message_type='notification'
                                    )
                                except Exception as e:
                                    _logger.warning('Error al crear mensaje en chatter: %s', str(e))
                    except Exception as e:
                        _logger.error('Error al validar contactos en write: %s', str(e))
                        # En caso de error, permitir continuar pero registrar
                        
            return super(CRMLead, self).write(vals)
            
        except Exception as e:
            _logger.error('Error general en write del CRM: %s', str(e))
            # En caso de error crítico, llamar al método padre sin validaciones
            return super(CRMLead, self).write(vals)
    
    # ------------------------------
    # MÉTODO PARA VERIFICAR CONTACTOS FINANCIEROS - MEJORADO
    # ------------------------------
    def verificar_contactos_financieros(self):
        """
        Método auxiliar para verificar si existen contactos financieros válidos
        """
        self.ensure_one()
        
        try:
            # Contar contactos financieros de manera segura
            contador = len(self.x_studio_contactos_financieros) if self.x_studio_contactos_financieros else 0
            
            # También buscar contactos relacionados a esta oportunidad como alternativa
            contactos_relacionados = 0
            if self.partner_id:
                try:
                    contactos_relacionados = self.env['res.partner'].search_count([
                        ('parent_id', '=', self.partner_id.id if self.partner_id else False),
                        ('active', '=', True)
                    ])
                except Exception as e:
                    _logger.warning('Error al contar contactos relacionados: %s', str(e))
            
            resultado = {
                'tiene_contactos': contador > 0,
                'cantidad_contactos': contador,
                'contactos_relacionados': contactos_relacionados,
                'mensaje': ''
            }
            
            if not resultado['tiene_contactos']:
                resultado['mensaje'] = _(
                    'Se requiere registrar al menos un contacto financiero '
                    'antes de poder marcar esta oportunidad como GANADA.'
                )
            
            return resultado
            
        except Exception as e:
            _logger.error('Error en verificar_contactos_financieros: %s', str(e))
            return {
                'tiene_contactos': False,
                'cantidad_contactos': 0,
                'contactos_relacionados': 0,
                'mensaje': 'Error al verificar contactos. Por favor, intente nuevamente.'
            }
    
    # ------------------------------
    # ACCIÓN MANUAL PARA VERIFICAR CONTACTOS
    # ------------------------------
    def action_verificar_contactos_ganada(self):
        """
        Acción manual para verificar si se puede marcar como GANADA
        """
        self.ensure_one()
        
        verificacion = self.verificar_contactos_financieros()
        
        if (self.x_studio_monto_de_operacion_entero > 0):
            if verificacion['tiene_contactos']:
                # Si tiene contactos, permitir cambiar a GANADA
                self.write({'x_studio_porcentaje_probabilidad': '100'})
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ VALIDACIÓN EXITOSA'),
                        'message': _('La oportunidad puede ser marcada como GANADA. Contactos verificados: %s') % verificacion['cantidad_contactos'],
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                # Si no tiene contactos, mostrar alerta
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('⚠️ VALIDACIÓN FALLIDA'),
                        'message': verificacion['mensaje'],
                        'sticky': True,
                        'type': 'warning',
                        'className': 'o_notification_shake',
                    }
                }
        
    # ------------------------------
    # MÉTODO RECOMENDADO: USAR EL DECORADOR @api.model_create_multi MEJORADO
    # ------------------------------
    def read(self, fields=None, load='_classic_read'):
        """
        Override seguro del método read - SIN RECURSIÓN
        """
        # Verificar si estamos en contexto de carga automática para evitar bucles
        if self.env.context.get('loading_contacts') or self.env.context.get('install_mode'):
            return super(CRMLead, self).read(fields, load)
        
        result = super(CRMLead, self).read(fields, load)
        _logger.info('STATUS: Ingresó al READ del FORM y listo para cargar.')

        # Solo ejecutar para registros individuales y si no estamos en vista lista
        if (len(self) == 1 and 
            not self.env.context.get('active_model') == 'crm.lead' and
            not self.env.context.get('disable_auto_load_contacts')):
            
            try:
                # Cargar contactos si es necesario, CON CONTEXTO para evitar recursión
                if self.partner_id and not self.x_studio_contactos_financieros:
                    self.with_context(loading_contacts=True, disable_auto_load_contacts=True)._cargar_contactos_financieros()
                    
                    # Si se cargaron contactos, re-leer los datos
                    if fields and 'x_studio_contactos_financieros' in (fields or []):
                        result = super(CRMLead, self).with_context(loading_contacts=True).read(fields, load)
                        
            except Exception as e:
                _logger.warning('Error seguro en read al cargar contactos: %s', str(e))
        
        return result

    # ==================================================================================================================
    # FIN: CONTACTOS FINANCIEROS - ADMIN
    # ==================================================================================================================

    # ------------------------------
    # MARCA LEADS EXTEMPORÁNEOS
    # ------------------------------
    def action_marca_extemporaneos(self):
        # Verificar acceso de usuario directamente sin usar campos computados
        if self.env.user.id not in [2, 8]:
            raise UserError(_('No tiene permisos para realizar esta acción.'))
        
        # Buscar todas las oportunidades que cumplan con los criterios
        # - Estado seleccionado = "Abierto"
        # - Fecha de oportunidad < 2025
        domain = [
            ('x_studio_estado_seleccionado', '=', 'Abierto'),
            ('x_studio_fecha_de_oportunidad', '<', '2025-01-01')
        ]
        
        # Obtener los registros que cumplen con el criterio
        leads_to_mark = self.env['crm.lead'].search(domain)
        
        # Contador para estadísticas
        count_updated = 0
        
        # Marcar como extemporáneas
        for lead in leads_to_mark:
            lead.write({'x_cens_on_extemporanea': True})
            count_updated += 1
            
        # Log para fines de auditoría
        _logger.info('Usuario %s (ID: %s) marcó %s oportunidades como extemporáneas', 
                    self.env.user.name, self.env.user.id, count_updated)
        
        # Notificación al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('%s registros marcados como extemporáneos correctamente.') % count_updated,
                'sticky': False,
                'type': 'success',
            }
        }


    # -------------------------------------
    # VALIDACIÓN DE CONTACTOS PARA GANADA
    # -------------------------------------
    @api.onchange('x_studio_porcentaje_probabilidad')
    def _onchange_porcentaje_probabilidad(self):
        """
        Validar que existan contactos registrados cuando se selecciona 100% (GANADA)
        """
        if self.x_studio_porcentaje_probabilidad == '100':
            # Verificar si el contador de contactos es cero
            contador_contactos = self.x_studio_contador_contactos or 0
            
            if (self.x_studio_monto_de_operacion_entero > 0):
                if contador_contactos == 0:
                    # Mostrar mensaje de alerta y resetear el valor y lo ajusta a 70%
                    self.x_studio_porcentaje_probabilidad = '70'  # Regresar a "70% - Mucha posibilidad de ganar. - "
                    
                    # Retornar mensaje de advertencia
                    return {
                        'warning': {
                            'title': _('⚠️ ALERTA - CONTACTOS REQUERIDOS'),
                            'message': _(
                                '🚨 CUIDADO:  Por directiva de la GERENCIA ADMINISTRATIVA, esta Oportunidad de Negocio NO puede pasar a GANADA sin antes  \n'
                                '                       registrar uno o más contactos relacionados a la parte FINANCIERA.\n\n'
                                '📋 Acciones requeridas:\n'
                                '      • Registrar al menos un contacto financiero\n'
                                '      • Deberás asignar como ETIQUETA principal la descripción del CARGO o el ÁREA involucrada.\n'
                                '      • Luego debes seleccionar una persona ya registrada o agregar una nueva.\n'
                                '      • Recuerda que debes colocar un contacto con el que se pueda tratar temas relacionados a la \n'
                                '        gestión de financiamiento, desembolsos, contratos, adendas, cobranzas, entre otras. \n\n'
                                '🔄 En este momento el porcentaje de Probabilidad será revertido automáticamente a 70% (Mucha posibilidad \n'
                                '      de ganar), hasta que ingreses el contacto requerido.'
                            ),
                        },
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('⚠️ CONTACTOS REQUERIDOS'),
                            'message': _('No se puede marcar como GANADA sin Contactos Financieros registrados.'),
                            'sticky': True,
                            'type': 'warning',
                            'className': 'o_notification_shake',  # Efecto visual de shake
                        }
                    }

    # ------------------------------
    # AUTORIZA PROPUESTA ECONÓMICA
    # ------------------------------
    def action_autoriza_propuesta(self):
        # Verificar acceso de usuario directamente sin usar campos computados
        if self.env.user.id not in [2, 8]:
            raise UserError(_('No tiene permisos para realizar esta acción.'))
           
        # Log para fines de auditoría
        #_logger.info('Usuario %s (ID: %s) marcó %s oportunidades como extemporáneas', 
        #            self.env.user.name, self.env.user.id, count_updated)
        
        # Notificación al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('La Propuesta Económica fue AUTORIZADA correctamente.'),
                'sticky': False,
                'type': 'success',
            }
        }


    # ------------------------------
    # ENVÍA SOLICITUD DE APROBACIÓN
    # ------------------------------
    def action_solicita_aprobacion(self):
        # Verificar acceso de usuario directamente
        if self.env.user.id not in [2, 8]:
            raise UserError(_('No tiene permisos para realizar esta acción.'))
                
        # Contador para estadísticas
        count_updated = 0
        # -------------------------------
        # Procesa envío de la Solicitud
        # -------------------------------
        # Log para fines de auditoría
        _logger.info('Usuario %s (ID: %s) marcó %s oportunidades como extemporáneas', 
                    self.env.user.name, self.env.user.id, count_updated)
        
        # Notificación al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Éxito'),
                'message': _('%s solicitud de Aprobación de Propuesta Económica.') % count_updated,
                'sticky': False,
                'type': 'success',
            }
        }


    # ------------------------------
    # CARGA IMAGEN DESDE URL
    # ------------------------------
    @api.model
    def _cargar_imagen_aviso(self):
        try:
            url_imagen = "https://sisac-peru.com/Aviso-Novedades-04.jpg"
            response = requests.get(url_imagen, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                return False
        except Exception as e:
            return False
    
    # ------------------------------
    # AÑADIR ADJUNTO DE IMAGEN AL CHATTER
    # ------------------------------
    def _crear_adjunto_imagen(self):
        imagen_contenido = self._cargar_imagen_aviso()
        if not imagen_contenido:
            return False
            
        # Crear el adjunto
        attachment_vals = {
            'name': 'Aviso-Novedades-04.jpg',
            'datas': base64.b64encode(imagen_contenido),
            'res_model': 'crm.lead',
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'image/jpeg',
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)
        return attachment.id
    
    # ------------------------------------------
    # REGISTRAR MENSAJE CON IMAGEN ADJUNTA
    # ------------------------------------------
    def agregar_imagen_como_mensaje(self):
        for record in self:
            attachment_id = record._crear_adjunto_imagen()
            if not attachment_id:
                raise UserError(_('No se pudo cargar la imagen desde la URL especificada.'))
            
            # Crear mensaje con adjunto
            self.env['mail.message'].create({
                'model': 'crm.lead',
                'res_id': record.id,
                'message_type': 'comment',
                'body': _('<p>Aviso importante: Se adjunta imagen con información relevante.</p>'),
                'attachment_ids': [(4, attachment_id)],  # Usar 4 para añadir al many2many
                'author_id': self.env.user.partner_id.id,
                'email_from': self.env.user.email,
                'subtype_id': self.env.ref('mail.mt_comment').id,
            })
            
            # También actualizamos la actividad si existe
            activity = self.env['mail.activity'].search([
                ('res_id', '=', record.id),
                ('res_model', '=', 'crm.lead')
            ], limit=1)
            
            if activity:
                activity.write({
                    'attachment_ids': [(4, attachment_id)]
                })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Imagen adjuntada correctamente al historial de mensajes.'),
                    'sticky': False,
                }
            }
    
    # ----------------------------------------------------
    # ENVIAR CORREO DE ALERTA - SOLICITA CAMBIO A GANADA
    # ----------------------------------------------------
    def enviar_correo_solicita_ganada(self):
        self.ensure_one()
        template_id = self.env.ref('studio_customization.alerta_solicita_opor_ac464d32-6b47-4809-9432-b0fba3a7ebf4')
        if not template_id:
            _logger.error('No se encontró la plantilla de correo con ID XML: studio_customization.alerta_solicita_opor_ac464d32-6b47-4809-9432-b0fba3a7ebf4')
            return False
            
        # Enviar correo usando la plantilla
        try:
            template_id.send_mail(self.id, force_send=True)
            _logger.info('Correo de SOLICITUD CAMBIO DE ESTADO fue enviado correctamente  (ID: %s)', self.id)
            return True
        except Exception as e:
            _logger.error('Error al enviar correo de SOLICITUD: %s', str(e))
            return False

    # ----------------------------------------------------
    # ENVIAR WHATSA DE ALERTA - SOLICITA CAMBIO A GANADA
    # ----------------------------------------------------
    def enviar_whatsa_solicita_ganada(self):
        self.ensure_one()
        
        return {
            'name': _('SERVICIO DE ENVÍO WHATSAPP'), 
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.info.dialog', 
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': _("ALERTA:  Este servicio se encuentra en pleno desarrollo y muy pronto estará \n"
                                    "disponible para que sus solicitudes de cambio de estatus a GANADA lleguen \n"
                                    "directamente a los WhatsApp de los PMO.🚧 \n"
                            ),
                'default_lead_id': self.id,
            }
        }
            
 
    # --------------------------------------------
    # ENVIAR CORREO DE ALERTA - NUEVA OPORTUNIDAD
    # --------------------------------------------
    def enviar_correo_alerta(self):
        self.ensure_one()
        template_id = self.env.ref('studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
        if not template_id:
            _logger.error('No se encontró la plantilla de correo con ID XML: studio_customization.alerta_nueva_oportun_22e58b58-24a7-42ad-ad6b-dc23df4cb1c5')
            return False
            
        # Enviar correo usando la plantilla
        try:
            template_id.send_mail(self.id, force_send=True)
            _logger.info('Correo de alerta enviado correctamente para el lead ID: %s', self.id)
            return True
        except Exception as e:
            _logger.error('Error al enviar correo de alerta: %s', str(e))
            return False
    
    # ---------------------------------------------------------------
    # MÉTODO PARA CREAR NUEVOS REGISTROS CON IMAGEN Y ENVIAR CORREO
    # ---------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super(CRMLead, self).create(vals_list)
        for record in records:

            # Enviar correo de alerta
            record.enviar_correo_alerta()

            # Adjuntar la imagen automáticamente
            record.agregar_imagen_como_mensaje()
            
        return records

