from odoo import models, fields

class MiModelo(models.Model):
    _name = 'mi.modelo'
    _description = 'Modelo de prueba'

    name = fields.Char(string="Nombre")