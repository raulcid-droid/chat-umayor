from odoo import models, fields, api


class MiModeloLine(models.Model):
    _name = 'mi_modulo.mi_modelo_line'
    _description = 'Línea de Mi Modelo'

    parent_id = fields.Many2one(
        'mi_modulo.mi_modelo', string='Documento',
        required=True, ondelete='cascade'
    )
    name = fields.Char(string='Descripción', required=True)
    quantity = fields.Float(string='Cantidad', default=1.0)
    price_unit = fields.Float(string='Precio Unitario')
    subtotal = fields.Float(
        string='Subtotal', compute='_compute_subtotal', store=True
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
