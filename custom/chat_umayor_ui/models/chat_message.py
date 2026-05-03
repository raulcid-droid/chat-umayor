# -*- coding: utf-8 -*-
"""
Modelo de Mensaje de Chat
=========================
Cada mensaje individual dentro de una sesión. El campo `response_time_ms`
es clave para la métrica de viabilidad (Punto 6 del trabajo: "el bot
debe responder en menos de 5 segundos").
"""
from odoo import models, fields


class ChatMessage(models.Model):
    _name = 'chat.umayor.message'
    _description = 'Mensaje del Chat UMayor'
    _order = 'create_date asc, id asc'

    session_id = fields.Many2one(
        'chat.umayor.session',
        string='Sesión',
        required=True,
        ondelete='cascade',
        index=True,
    )

    role = fields.Selection(
        [
            ('user', 'Usuario'),
            ('bot', 'Bot'),
            ('system', 'Sistema'),
        ],
        string='Rol',
        required=True,
        default='user',
    )

    content = fields.Text(
        string='Contenido',
        required=True,
    )

    response_time_ms = fields.Integer(
        string='Tiempo de respuesta (ms)',
        default=0,
        help='Solo aplica a mensajes del bot: cuánto tardó en responder '
             'al último mensaje del usuario. Meta del proyecto: < 5000 ms.',
    )
