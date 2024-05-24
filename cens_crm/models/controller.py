from odoo import http

class LeadController(http.Controller):

    @http.route('/cens_crm/views/import_to_spreadsheet', type='http', auth='user')
    def import_to_spreadsheet(self, **kwargs):
        leads = http.request.env['crm.lead'].search([])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'spreadsheet.sheet',
            'view_mode': 'form',
            'view_id': http.request.env.ref('spreadsheet.view_spreadsheet_sheet_form').id,
            'target': 'new',
            'context': {
                'active_ids': leads.ids,
                'active_model': 'crm.lead',
            },
        }

