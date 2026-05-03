# -*- coding: utf-8 -*-
"""
Tests del modelo chat.umayor.session
Punto 6 del proyecto: Validar la viabilidad mediante pruebas.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged('chat_umayor', 'post_install', '-at_install')
class TestChatSession(TransactionCase):

    def test_01_create_session_generates_token(self):
        """Cada sesión nueva debe nacer con un token UUID único."""
        s1 = self.env['chat.umayor.session'].create({})
        s2 = self.env['chat.umayor.session'].create({})
        self.assertTrue(s1.token, "La sesión 1 debe tener token")
        self.assertTrue(s2.token, "La sesión 2 debe tener token")
        self.assertNotEqual(s1.token, s2.token,
                            "Los tokens deben ser únicos entre sesiones")
        self.assertEqual(len(s1.token), 36,
                         "El token debe ser un UUID estándar (36 chars)")

    def test_02_default_state_is_draft(self):
        """El estado inicial es 'draft' antes de mensajes."""
        s = self.env['chat.umayor.session'].create({})
        self.assertEqual(s.state, 'draft')

    def test_03_message_count_is_computed(self):
        """El contador de mensajes refleja los mensajes reales."""
        session = self.env['chat.umayor.session'].create({'state': 'active'})
        self.env['chat.umayor.message'].create({
            'session_id': session.id, 'role': 'user', 'content': 'hola',
        })
        self.env['chat.umayor.message'].create({
            'session_id': session.id, 'role': 'bot', 'content': 'hola, ¿en qué te ayudo?',
        })
        self.assertEqual(session.message_count, 2)

    def test_04_response_avg_only_for_bot_messages(self):
        """El promedio de tiempos solo considera mensajes del bot con tiempo > 0."""
        session = self.env['chat.umayor.session'].create({'state': 'active'})
        Msg = self.env['chat.umayor.message']
        Msg.create({'session_id': session.id, 'role': 'user', 'content': 'a'})
        Msg.create({'session_id': session.id, 'role': 'bot',  'content': 'b',
                    'response_time_ms': 1000})
        Msg.create({'session_id': session.id, 'role': 'bot',  'content': 'c',
                    'response_time_ms': 2000})
        self.assertEqual(session.response_avg_ms, 1500.0)

    def test_05_action_mark_completed(self):
        """El botón de cierre cambia el estado a completed."""
        s = self.env['chat.umayor.session'].create({'state': 'active'})
        s.action_mark_completed()
        self.assertEqual(s.state, 'completed')
