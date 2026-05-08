"""Tests unitarios del modelo ``chat_umayor.contract`` y el helper
``chatbot.session._launch_signature``.

Cubren:
    - Campos denormalizados copiados desde el partner al crear.
    - Snapshot inmutable: mutar el partner después no afecta al contrato.
    - Transición a ``signed`` + cierre de la sesión.
    - Formato de ``reference`` (``CH-NNNNNN``).

``_launch_signature`` mockea ``sign.request.create`` y el parámetro
``chat_umayor.sign_template_id`` para no tocar Sign real.
"""

import json
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("chat_umayor", "post_install", "-at_install")
class TestChatbotContract(TransactionCase):
    """Modelo ``chat_umayor.contract`` y ``_launch_signature``."""

    def _make_review_session(self, partner_values=None, summary=None):
        """Crea una sesión en ``review`` con partner y submit_summary.

        Monta el estado mínimo necesario para poder lanzar la firma:
        sesión que recorrió el FSM hasta ``review``, un ``res.partner``
        asociado y el JSON de ``submit_summary`` que persiste PLAN 08.
        """
        session = self.env["chatbot.session"]._create_with_greeting()
        for target in ("discovery", "product_info", "data_collection", "review"):
            session._do_transition(target)

        partner_defaults = {
            "name": "Juan Pérez",
            "vat": "12345678-5",
            "email": "juan@example.com",
            "phone": "+56911112222",
        }
        partner_defaults.update(partner_values or {})
        partner = self.env["res.partner"].create(partner_defaults)
        session.partner_id = partner.id
        session.product_code = "soap"

        summary_defaults = {
            "product_code": "soap",
            "product_data": {
                "vehicle_plate": "BCDF12",
                "vehicle_year": 2020,
                "vehicle_type": "particular",
            },
            "calculated": {
                "premium": 7990,
                "currency": "CLP",
                "vehicle_type": "particular",
            },
        }
        session.submit_summary = json.dumps(summary or summary_defaults)
        return session, partner

    def _patch_sign_stack(self, template_exists=True):
        """Devuelve context manager que parchea sign.template y sign.request.

        ``template_exists=False`` simula una plantilla configurada pero
        inexistente (caso ``SIGN_UNAVAILABLE``). El contexto setea el
        parámetro ``chat_umayor.sign_template_id`` a 999 y mockea el
        browse/exists para controlarlo.
        """
        self.env["ir.config_parameter"].sudo().set_param(
            "chat_umayor.sign_template_id", "999"
        )
        fake_template = MagicMock()
        fake_template.id = 999
        fake_template.exists.return_value = fake_template if template_exists else self.env["sign.template"]

        fake_sign_request = MagicMock()
        fake_sign_request.id = 12345
        fake_sign_request.request_item_ids = []

        return fake_template, fake_sign_request

    # ------------------------------------------------------------------
    # _compute_reference
    # ------------------------------------------------------------------

    def test_reference_format(self) -> None:
        """``reference`` usa formato ``CH-NNNNNN`` con padding a 6 dígitos."""
        session, partner = self._make_review_session()
        contract = self.env["chat_umayor.contract"].create(
            {
                "session_id": session.id,
                "partner_id": partner.id,
                "partner_name": partner.name,
                "partner_vat": partner.vat,
                "partner_email": partner.email,
                "partner_phone": partner.phone,
                "product_code": "soap",
            }
        )
        self.assertEqual(contract.reference, f"CH-{contract.id:06d}")
        self.assertTrue(contract.reference.startswith("CH-"))
        self.assertEqual(len(contract.reference), 9)  # CH- + 6 dígitos

    # ------------------------------------------------------------------
    # _launch_signature: create + snapshot denormalizado
    # ------------------------------------------------------------------

    def test_create_contract_from_submit_summary(self) -> None:
        """``_launch_signature`` crea contrato con snapshot de partner."""
        session, partner = self._make_review_session()
        fake_template, fake_sign_request = self._patch_sign_stack()

        with patch.object(
            type(self.env["sign.template"]),
            "browse",
            return_value=fake_template,
        ), patch.object(
            type(self.env["sign.request"]),
            "create",
            return_value=fake_sign_request,
        ):
            contract, sign_url = session._launch_signature()

        self.assertEqual(contract.session_id.id, session.id)
        self.assertEqual(contract.partner_id.id, partner.id)
        # Snapshot denormalizado:
        self.assertEqual(contract.partner_name, "Juan Pérez")
        self.assertEqual(contract.partner_vat, "12345678-5")
        self.assertEqual(contract.partner_email, "juan@example.com")
        self.assertEqual(contract.partner_phone, "+56911112222")
        # Producto y cálculo preservados:
        self.assertEqual(contract.product_code, "soap")
        product_data = json.loads(contract.product_data_json)
        self.assertEqual(product_data["vehicle_plate"], "BCDF12")
        calculated = json.loads(contract.calculated_json)
        self.assertEqual(calculated["premium"], 7990)
        # Estado y URL:
        self.assertEqual(contract.state, "signing")
        self.assertEqual(contract.sign_request_id.id, 12345)
        self.assertIn("/sign/document/12345", sign_url)

    def test_partner_snapshot_is_immutable_on_partner_change(self) -> None:
        """Mutar el partner después NO afecta al contrato (snapshot)."""
        session, partner = self._make_review_session()
        fake_template, fake_sign_request = self._patch_sign_stack()

        with patch.object(
            type(self.env["sign.template"]),
            "browse",
            return_value=fake_template,
        ), patch.object(
            type(self.env["sign.request"]),
            "create",
            return_value=fake_sign_request,
        ):
            contract, _ = session._launch_signature()

        # Mutación posterior del partner:
        partner.write(
            {
                "email": "otro@dominio.cl",
                "phone": "+56999999999",
                "name": "Nombre Cambiado",
            }
        )

        # El contrato conserva los valores originales:
        contract.invalidate_recordset()
        self.assertEqual(contract.partner_email, "juan@example.com")
        self.assertEqual(contract.partner_phone, "+56911112222")
        self.assertEqual(contract.partner_name, "Juan Pérez")

    # ------------------------------------------------------------------
    # _mark_signed
    # ------------------------------------------------------------------

    def test_mark_signed_updates_state_and_closes_session(self) -> None:
        """``_mark_signed`` pasa contrato a signed y sesión a closed."""
        session, partner = self._make_review_session()
        # Creamos el contrato directamente en ``signing`` sin lanzar
        # ``_launch_signature`` (aquí no queremos testear eso).
        contract = self.env["chat_umayor.contract"].create(
            {
                "session_id": session.id,
                "partner_id": partner.id,
                "partner_name": partner.name,
                "partner_vat": partner.vat,
                "partner_email": partner.email,
                "partner_phone": partner.phone,
                "product_code": "soap",
                "state": "signing",
            }
        )
        # La sesión también tiene que estar en signing para que el FSM
        # acepte la transición a closed.
        session._do_transition("signing")

        contract._mark_signed()

        self.assertEqual(contract.state, "signed")
        self.assertTrue(contract.signed_at)
        self.assertEqual(contract.session_id.state, "closed")

    def test_mark_signed_is_idempotent(self) -> None:
        """Llamar ``_mark_signed`` dos veces no rompe ni cambia nada."""
        session, partner = self._make_review_session()
        contract = self.env["chat_umayor.contract"].create(
            {
                "session_id": session.id,
                "partner_id": partner.id,
                "partner_name": partner.name,
                "partner_vat": partner.vat,
                "product_code": "soap",
                "state": "signing",
            }
        )
        session._do_transition("signing")

        contract._mark_signed()
        first_signed_at = contract.signed_at
        # Segunda llamada: debe ser no-op (idempotente).
        contract._mark_signed()
        self.assertEqual(contract.state, "signed")
        self.assertEqual(contract.signed_at, first_signed_at)
