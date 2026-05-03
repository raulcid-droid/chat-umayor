# -*- coding: utf-8 -*-
"""
Producto Financiero
===================
Catálogo simple de productos que el bot puede ofrecer (créditos de
consumo, tarjetas, cuentas, etc.). Si el módulo del compañero define
un modelo más completo, este puede deprecarse o extenderse.
"""
from odoo import models, fields


class FinancialProduct(models.Model):
    _name = 'chat.umayor.product'
    _description = 'Producto Financiero UMayor'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código interno', required=True)
    sequence = fields.Integer(string='Orden', default=10)
    description = fields.Text(string='Descripción', translate=True)
    short_description = fields.Char(
        string='Descripción corta',
        help='Texto que el bot usa al ofrecer el producto.',
        translate=True,
    )
    active = fields.Boolean(default=True)

    # Datos comerciales mínimos (mock para la demo)
    interest_rate = fields.Float(string='Tasa de interés mensual (%)')
    min_amount = fields.Float(string='Monto mínimo')
    max_amount = fields.Float(string='Monto máximo')

    # Plantilla a enviar a Odoo Sign cuando el cliente acepta contratar
    sign_template_id = fields.Many2one(
        'sign.template',
        string='Plantilla de contrato (Odoo Sign)',
        ondelete='set null',
        help='Plantilla que se envía al cliente para firmar.',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código del producto debe ser único.'),
    ]
