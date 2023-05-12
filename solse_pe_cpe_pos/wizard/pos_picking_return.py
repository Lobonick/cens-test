# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPickingLine(models.TransientModel):
	_name = "pos.return.picking.line"
	_description = 'Línea de recogida de devolución'
	_rec_name = 'product_id'

	product_id = fields.Many2one('product.product', string="Producto", required=True, domain="[('id', '=', product_id)]")
	quantity = fields.Float("Cantidad", digits='Product Unit of Measure', required=True)
	uom_id = fields.Many2one('product.uom', string='Unidad de medida', related='move_id.product_uom')
	wizard_id = fields.Many2one('pos.return.picking', string="Wizard")
	move_id = fields.Many2one('stock.move', "Movimiento")


class ReturnPicking(models.TransientModel):
	_name = 'pos.return.picking'
	_description = 'Recogida de devoluciones'

	picking_id = fields.Many2one('stock.picking')
	product_return_moves = fields.One2many('pos.return.picking.line', 'wizard_id', 'Movimientos')
	move_dest_exists = fields.Boolean('Chained Move Exists', readonly=True)
	original_location_id = fields.Many2one('stock.location')
	parent_location_id = fields.Many2one('stock.location')
	location_id = fields.Many2one(
		'stock.location', 'Ubicación de devolución',
		domain="['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]")

	@api.model
	def default_get(self, fields):
		if len(self.env.context.get('active_ids', list())) > 1:
			raise UserError("¡Solo puede devolver una recolección a la vez!")
		res = super(ReturnPicking, self).default_get(fields)

		move_dest_exists = False
		product_return_moves = []
		picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
		if picking:
			res.update({'picking_id': picking.id})
			#if picking.state != 'done':
			#    raise UserError(_("Solo puede devolver las recolecciones realizadas"))
			if not res.get('product_return_moves'):
				for move in picking.move_lines:
					if move.scrapped:
						continue
					if move.move_dest_ids:
						move_dest_exists = True
					quantity = move.product_qty - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
													  mapped('move_line_ids').mapped('product_qty'))
					quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
					product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))
			else:
				product_return_moves = res.get('product_return_moves')
			if not product_return_moves:
				raise UserError(_("No hay productos para devolver (solo se pueden devolver las líneas en estado Listo y no devueltas por completo)."))
			if 'product_return_moves' in fields:
				res.update({'product_return_moves': product_return_moves})
			if 'move_dest_exists' in fields:
				res.update({'move_dest_exists': move_dest_exists})
			if 'original_location_id' in fields:
				res.update({'original_location_id': picking.location_id.id})
			if 'location_id' in fields:
				location_id = picking.location_id.id
				if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
					location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
				res['location_id'] = location_id
		return res

	def _prepare_move_default_values(self, return_line, new_picking):
		vals = {
			'product_id': return_line.product_id.id,
			'product_uom_qty': return_line.quantity,
			'product_uom': return_line.product_id.uom_id.id,
			'picking_id': new_picking.id,
			'state': 'draft',
			'location_id': return_line.move_id.location_dest_id.id,
			'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
			'picking_type_id': new_picking.picking_type_id.id,
			'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
			'origin_returned_move_id': return_line.move_id.id,
			'procure_method': 'make_to_stock',
		}
		return vals

	def _create_returns(self):
		# TODO sle: the unreserve of the next moves could be less brutal
		for return_move in self.product_return_moves.mapped('move_id'):
			return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

		# create new picking for returned products
		picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
		new_picking = self.picking_id.copy({
			'move_lines': [],
			'picking_type_id': picking_type_id,
			'state': 'draft',
			'origin': _("Return of %s") % self.picking_id.name,
			'location_id': self.picking_id.location_dest_id.id,
			'location_dest_id': self.location_id.id})
		new_picking.message_post_with_view('mail.message_origin_link',
			values={'self': new_picking, 'origin': self.picking_id},
			subtype_id=self.env.ref('mail.mt_note').id)
		returned_lines = 0
		for return_line in self.product_return_moves:
			if not return_line.move_id:
				raise UserError(_("Ha creado líneas de productos manualmente, elimínelas para continuar"))
			# TODO sle: float_is_zero?
			if return_line.quantity:
				returned_lines += 1
				vals = self._prepare_move_default_values(return_line, new_picking)
				r = return_line.move_id.copy(vals)
				vals = {}

				# +--------------------------------------------------------------------------------------------------------+
				# |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
				# |              | returned_move_ids              ↑                                  | returned_move_ids
				# |              ↓                                | return_line.move_id              ↓
				# |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
				# +--------------------------------------------------------------------------------------------------------+
				move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
				move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
				vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
				vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
				r.write(vals)
		if not returned_lines:
			raise UserError(_("Especifique al menos una cantidad distinta de cero."))

		new_picking.action_confirm()
		new_picking.action_assign()
		return new_picking.id, picking_type_id


