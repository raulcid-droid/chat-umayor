# -*- coding: utf-8 -*-
"""
Tests de los endpoints HTTP del controlador.
Usamos HttpCase para simular peticiones reales del navegador.
"""
import json
from odoo.tests.common import HttpCase, tagged


@tagged('chat_umayor', 'post_install', '-at_install')
class TestChatController(HttpCase):

    def _json_call(self, route, params):
        """Helper: hace una llamada JSON-RPC y devuelve el campo `result`."""
        response = self.url_open(
            route,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200,
                         "El endpoint %s respondió HTTP %s" % (route, response.status_code))
        return response.json().get("result")

    def test_01_start_returns_token_and_greeting(self):
        """POST /chat/api/start crea sesión y devuelve saludo del bot."""
        result = self._json_call("/chat/api/start", {})
        self.assertIn("token", result)
        self.assertIn("greeting", result)
        self.assertTrue(len(result["token"]) > 10)
        self.assertIn("UMayor", result["greeting"])

    def test_02_send_returns_reply_within_5_seconds(self):
        """
        Punto 6 - Métrica clave: el bot debe responder en < 5000 ms.
        Aunque el fallback es instantáneo, este test deja la barrera fijada
        para cuando se conecte el motor real (Gemini).
        """
        start = self._json_call("/chat/api/start", {})
        token = start["token"]
        result = self._json_call("/chat/api/send", {
            "token": token, "message": "Quiero información de créditos",
        })
        self.assertIn("reply", result)
        self.assertLess(result["response_time_ms"], 5000,
                        "El bot debe responder en menos de 5 segundos. "
                        "Tiempo real: %s ms" % result["response_time_ms"])

    def test_03_send_without_token_returns_error(self):
        """Sin token, el endpoint devuelve error pero no falla."""
        result = self._json_call("/chat/api/send", {"message": "hola"})
        self.assertIn("error", result)

    def test_04_products_endpoint_returns_list(self):
        """El endpoint de productos devuelve los productos demo cargados."""
        result = self._json_call("/chat/api/products", {})
        self.assertIsInstance(result, list)
        # Debería traer al menos los 3 productos del seed data
        self.assertGreaterEqual(len(result), 3)
        codes = {p["code"] for p in result}
        self.assertIn("CRED_CONSUMO", codes)

    def test_05_sign_request_without_sign_module(self):
        """
        Si Odoo Sign no está instalado, el endpoint devuelve mode='stub'
        y no rompe el flujo. (Si está instalado, devuelve mode='live').
        """
        start = self._json_call("/chat/api/start", {})
        result = self._json_call("/chat/api/sign_request", {
            "token": start["token"],
            "product_code": "CRED_CONSUMO",
            "signer_name": "Cliente de Prueba",
            "signer_email": "test@umayor.cl",
        })
        # Aceptamos cualquiera de los dos modos
        self.assertIn(result.get("mode"), ("stub", "live"))
