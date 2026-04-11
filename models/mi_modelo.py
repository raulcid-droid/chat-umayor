from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MiModelo(models.Model):
    _name = 'mi_modulo.mi_modelo'
    _description = 'Mi Modelo'
    _order = 'name asc'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    active = fields.Boolean(string='Activo', default=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Hecho'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    date = fields.Date(string='Fecha')
    amount = fields.Float(string='Monto', digits=(16, 2))
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users', string='Responsable',
        default=lambda self: self.env.user
    )
    line_ids = fields.One2many(
        'mi_modulo.mi_modelo_line', 'parent_id', string='Líneas'
    )

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError('El monto no puede ser negativo.')

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_draft(self):
        self.state = 'draft'
