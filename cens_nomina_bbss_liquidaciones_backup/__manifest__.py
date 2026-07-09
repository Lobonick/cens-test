{
    'name': "Nómina - Respaldo Liquidación BBSS - CENS",

    'summary': """
        Respaldo y restauración de los datos del modelo hr.payslip.liquidacion,
        para no perder información al desinstalar/reinstalar
        cens_nomina_bbss_liquidaciones.""",

    'description': """
        Módulo INDEPENDIENTE de respaldo/restauración para el modelo
        hr.payslip.liquidacion (Liquidación de Beneficios Sociales).

        Problema que resuelve:
        Al agregar campos nuevos a un modelo Python en Odoo.sh, algunas
        veces el módulo de origen no puede actualizarse (UPGRADE) y exige
        desinstalarlo y reinstalarlo, perdiendo todos los registros
        existentes.

        Este módulo permite:
        - Tomar una "foto" (respaldo) de TODOS los registros actuales de
          hr.payslip.liquidacion, guardando sus valores en un modelo propio
          (hr.payslip.liquidacion.backup), en formato JSON.
        - Restaurar esos registros luego de volver a instalar el módulo de
          origen, recreándolos con los mismos datos.

        A propósito, este módulo NO depende de cens_nomina_bbss_liquidaciones,
        de modo que sobrevive intacto aunque ese módulo se desinstale.
        CENS-PERÚ
    """,

    'author': "Área de Sistemas - ODOO-CENS-PERÚ",
    'website': "https://www.cens.com.pe",
    'category': 'Human Resources/Payroll',
    'version': '16.0.1.03',
    'license': 'Other proprietary',
    'contributors': [
        'Enrique Alcántara <ealcantara@cens.com.pe>',
    ],

    'depends': ['base', 'hr', 'hr_payroll'],

    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_liquidacion_backup_views.xml',
        'views/hr_payslip_liquidacion_backup_wizard_views.xml',
        'data/ir_actions_server.xml',
    ],

    'qweb': [],
 	'installable': True,
	'application': True,
	'auto_install': False,
    'icon': "https://sisac-peru.com/CENS-LOGO%20-%20Baja%20-%20Transparente.png",
    "sequence": 1,
}
