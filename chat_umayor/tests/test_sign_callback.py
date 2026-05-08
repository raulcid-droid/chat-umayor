"""Tests del callback de firma (override de ``sign.request._sign``).

Testeamos ``SignRequest._notify_chat_umayor_contracts`` directamente
en vez de ejercer ``super()._sign()`` real. Rationale: la API de
Odoo Sign requiere firmantes reales, PDF, tokens… innecesario para
lo que queremos probar (que nuestro callback mueve el contrato a
``signed`` y cierra la sesión).

La integración end-to-end con Sign real vive en
``tests/manual/test_sign_integration.py`` (no corre con
``--test-enable``).
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


_SIGN_LOGGER = "odoo.addons.chat_umayor.models.sign_request"


@tagged("chat_umayor", "post_install", "-at_install")
class TestSignCallback(TransactionCase):
    """Propagación de la firma al ``chat_umayor.contract`` vinculado."""

    def _make_signing_contract(self):
        """Crea sesión + contrato en ``signing`` listos para el callback."""
        session = self.env["chatbot.session"]._create_with_greeting()
        for target in (
            "discovery",
            "product_info",
            "data_collection",
            "review",
            "signing",
        ):
            session._do_transition(target)
        partner = self.env["res.partner"].create(
            {"name": "Juan Pérez", "vat": "12345678-5"}
        )
        # Creamos un ``sign.request`` mínimo. En un tenant con ``sign``
        # instalado podemos crear registros directos porque los campos
        # required del modelo se toleran con valores falsy o mediante
        # el stack de tests de Odoo. Si la creación falla por
        # constraints de sign.request, el test fallará en setUp y
        # habrá que mockear también el search.
        SignRequest = self.env["sign.request"].sudo()
        # NOTA: creamos con valores mínimos; si Odoo 19 requiere más
        # campos (template_id, request_item_ids...), se ajusta aquí.
        sign_request = SignRequest.create({})

        contract = self.env["chat_umayor.contract"].create(
            {
                "session_id": session.id,
                "partner_id": partner.id,
                "partner_name": partner.name,
                "partner_vat": partner.vat,
                "product_code": "soap",
                "state": "signing",
                "sign_request_id": sign_request.id,
            }
        )
        return session, contract, sign_request

    def test_sign_callback_transitions_contract_to_signed(self) -> None:
        """``_notify_chat_umayor_contracts`` mueve el contrato a signed."""
        session, contract, sign_request = self._make_signing_contract()

        sign_request._notify_chat_umayor_contracts()

        contract.invalidate_recordset()
        self.assertEqual(contract.state, "signed")
        self.assertTrue(contract.signed_at)

    def test_sign_callback_closes_session(self) -> None:
        """El callback también transiciona la sesión a ``closed``."""
        session, contract, sign_request = self._make_signing_contract()

        sign_request._notify_chat_umayor_contracts()

        session.invalidate_recordset()
        self.assertEqual(session.state, "closed")

    @mute_logger(_SIGN_LOGGER)
    def test_sign_callback_ignores_non_chatbot_requests(self) -> None:
        """Un sign.request sin contrato asociado no rompe el callback."""
        # Creamos un sign.request aislado, sin chat_umayor.contract.
        sign_request = self.env["sign.request"].sudo().create({})

        # No debe levantar excepción, simplemente no hace nada.
        sign_request._notify_chat_umayor_contracts()
