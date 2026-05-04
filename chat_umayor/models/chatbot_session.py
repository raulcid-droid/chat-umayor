"""Modelo de sesión del chatbot con máquina de estados (FSM).

La sesión es la unidad de conversación del chatbot bancario. Su estado
(``state``) rige qué puede pedir el usuario y qué puede responder el
bot. Las transiciones están definidas en §6 de ``AGENTS.md`` local:

    greeting → discovery → product_info → data_collection
             → review → signing → closed
                     ↑___________________|
                     (cambio de producto)

Toda transición pasa por ``_transition_to_<estado>()`` y valida contra
el mapa ``_ALLOWED_TRANSITIONS``. Intentar una transición no permitida
levanta ``UserError`` con un mensaje en español apto para mostrar al
usuario final.

El modelo es el único responsable del FSM: ni el controller ni Gemini
deben setear ``state`` directamente.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError


class ChatbotSession(models.Model):
    """Sesión de conversación del chatbot bancario."""

    _name = "chatbot.session"
    _description = "Chatbot Session"

    # Mapa único de transiciones permitidas. Fuente de verdad del FSM.
    # Forma: {estado_actual: (estados_destino_permitidos, ...)}.
    _ALLOWED_TRANSITIONS: dict[str, tuple[str, ...]] = {
        "greeting": ("discovery",),
        "discovery": ("product_info",),
        "product_info": ("discovery", "data_collection"),
        "data_collection": ("review",),
        "review": ("signing",),
        "signing": ("closed",),
        "closed": (),
    }

    state = fields.Selection(
        selection=[
            ("greeting", "Saludo"),
            ("discovery", "Descubrimiento"),
            ("product_info", "Información del producto"),
            ("data_collection", "Recolección de datos"),
            ("review", "Revisión"),
            ("signing", "Firma"),
            ("closed", "Cerrada"),
        ],
        string="Estado",
        default="greeting",
        required=True,
        copy=False,
        index=True,
        help="Estado actual de la conversación. Rige qué transiciones "
        "son válidas (ver _ALLOWED_TRANSITIONS).",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente",
        help="Cliente asociado a la sesión. Se completa cuando el "
        "usuario envía el formulario de datos (endpoint /submit_data).",
    )

    product_code = fields.Selection(
        selection=[
            ("soap", "SOAP"),
            ("deposit", "Depósito a Plazo"),
        ],
        string="Producto",
        help="Producto elegido por el cliente en la fase de descubrimiento.",
    )

    # ------------------------------------------------------------------
    # Motor genérico del FSM
    # ------------------------------------------------------------------

    def _assert_transition(self, target: str) -> None:
        """Valida que la transición del estado actual a ``target`` sea legal.

        Args:
            target: Estado destino al que se quiere transicionar.

        Raises:
            UserError: Si la transición no está en ``_ALLOWED_TRANSITIONS``.
        """
        self.ensure_one()
        allowed = self._ALLOWED_TRANSITIONS.get(self.state, ())
        if target not in allowed:
            raise UserError(
                _(
                    "No se puede pasar del estado %(current)s a %(target)s. "
                    "Transición inválida."
                )
                % {"current": self.state, "target": target}
            )

    def _do_transition(self, target: str) -> None:
        """Valida y aplica la transición al estado ``target``.

        Args:
            target: Estado destino.
        """
        self._assert_transition(target)
        self.state = target

    # ------------------------------------------------------------------
    # Transiciones públicas (una por estado destino)
    # ------------------------------------------------------------------

    def _transition_to_greeting(self) -> None:
        """Transiciona a ``greeting``. En la práctica nunca es válida."""
        self._do_transition("greeting")

    def _transition_to_discovery(self) -> None:
        """Transiciona a ``discovery``."""
        self._do_transition("discovery")

    def _transition_to_product_info(self) -> None:
        """Transiciona a ``product_info``."""
        self._do_transition("product_info")

    def _transition_to_data_collection(self) -> None:
        """Transiciona a ``data_collection``."""
        self._do_transition("data_collection")

    def _transition_to_review(self) -> None:
        """Transiciona a ``review``."""
        self._do_transition("review")

    def _transition_to_signing(self) -> None:
        """Transiciona a ``signing``."""
        self._do_transition("signing")

    def _transition_to_closed(self) -> None:
        """Transiciona a ``closed`` (estado terminal)."""
        self._do_transition("closed")
