# -*- coding: utf-8 -*-
"""
Tests de performance / pruebas de estrés.

Punto 6 del trabajo: "Validar la viabilidad mediante pruebas de usuario y QA
(verificar que el bot responda en <5s)".

Estos tests producen métricas que el equipo puede pegar directamente
en el informe de QA o en la presentación final.

Para ejecutarlos:
    odoo-bin -d <db> -i chat_umayor_ui --test-tags chat_umayor --stop-after-init
"""
import json
import logging
import statistics
import time

from odoo.tests.common import HttpCase, tagged

_logger = logging.getLogger(__name__)


@tagged('chat_umayor', 'chat_umayor_perf', 'post_install', '-at_install')
class TestChatPerformance(HttpCase):

    PERF_THRESHOLD_MS = 5000   # SLA del proyecto: <5s
    BURST_SIZE = 20            # Mensajes consecutivos de prueba

    def _call(self, route, params):
        r = self.url_open(
            route,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}),
            headers={"Content-Type": "application/json"},
        )
        return r.json().get("result")

    def test_01_burst_of_messages_under_5s(self):
        """
        Envía N mensajes consecutivos y comprueba que el percentil 95
        de los tiempos de respuesta esté por debajo del SLA de 5s.
        """
        start = self._call("/chat/api/start", {})
        token = start["token"]

        prompts = [
            "Hola", "¿Qué productos tienen?", "Cuéntame del crédito",
            "¿Cuánto es la tasa?", "Quiero una tarjeta", "Y un crédito hipotecario?",
            "¿Atienden los sábados?", "Quiero firmar", "Necesito mi correo",
            "Mi correo es x@y.cl", "Gracias", "¿Algo más?",
            "Cuenta de ahorro?", "¿Cuánto rinde?", "Perfecto",
            "Adiós", "Espera, una más", "¿Tienen app?", "OK", "Listo",
        ][:self.BURST_SIZE]

        elapsed = []
        wall_start = time.monotonic()
        for p in prompts:
            r = self._call("/chat/api/send", {"token": token, "message": p})
            elapsed.append(r["response_time_ms"])
        wall_total = (time.monotonic() - wall_start) * 1000

        # Estadísticas para el informe
        avg = statistics.mean(elapsed)
        p95 = sorted(elapsed)[int(len(elapsed) * 0.95) - 1]
        worst = max(elapsed)

        _logger.info(
            "[PERF] %s mensajes en %.0f ms | media=%.0f ms | p95=%s ms | peor=%s ms",
            len(prompts), wall_total, avg, p95, worst,
        )

        self.assertLess(p95, self.PERF_THRESHOLD_MS,
                        "El percentil 95 de tiempos de respuesta superó el SLA "
                        "(%s ms >= %s ms). Tiempos: %s"
                        % (p95, self.PERF_THRESHOLD_MS, elapsed))

    def test_02_concurrent_sessions(self):
        """
        Crea 10 sesiones independientes y verifica que cada una mantenga
        sus mensajes aislados (no haya filtración entre conversaciones).
        """
        tokens = []
        for i in range(10):
            r = self._call("/chat/api/start", {})
            tokens.append(r["token"])
        self.assertEqual(len(set(tokens)), 10,
                         "Los 10 tokens deben ser distintos.")

        # Mandamos un mensaje único en cada sesión
        for i, tk in enumerate(tokens):
            self._call("/chat/api/send", {"token": tk, "message": "msg-%d" % i})

        # Verificamos en BD que cada sesión tenga exactamente 3 mensajes
        # (saludo del bot + mensaje user + respuesta bot).
        Session = self.env['chat.umayor.session']
        for i, tk in enumerate(tokens):
            s = Session.search([('token', '=', tk)], limit=1)
            self.assertEqual(len(s.message_ids), 3,
                             "Sesión %s debería tener 3 mensajes." % i)
            user_msgs = s.message_ids.filtered(lambda m: m.role == 'user')
            self.assertEqual(user_msgs.content, "msg-%d" % i,
                             "El mensaje user de la sesión %s no coincide." % i)
