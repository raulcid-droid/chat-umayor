from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class ChatbotMessage(models.Model):
    _name = 'chatbot.message'
    _description = 'Mensajes Chatbot'
    _order = 'create_date desc'

    user_message = fields.Text(string="Mensaje Usuario", required=True)
    bot_response = fields.Text(string="Respuesta Bot", readonly=True)
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Respondido'),
        ('error', 'Error'),
    ], default='pending', string="Estado")
    
    # URL configurable desde ajustes de Odoo (recomendado)
    api_url = fields.Char(
        string="URL de API",
        default="https://TU_API_AQUI.com/chat"
    )

    def send_to_api(self):
        for record in self:
            if not record.user_message:
                raise UserError("El mensaje del usuario no puede estar vacío.")

            api_url = record.api_url or self.env['ir.config_parameter'].sudo().get_param(
                'chatbot.api_url', default='https://TU_API_AQUI.com/chat'
            )

            payload = {
                "message": record.user_message
            }

            try:
                response = requests.post(
                    api_url,
                    json=payload,
                    timeout=10,  # Evita que cuelgue indefinidamente
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()  # Lanza excepción si status >= 400

                data = response.json()
                record.write({
                    'bot_response': data.get("response", "Sin respuesta"),
                    'state': 'done',
                })

            except requests.exceptions.Timeout:
                _logger.warning("Timeout al conectar con la API del chatbot.")
                record.write({'bot_response': "Tiempo de espera agotado.", 'state': 'error'})

            except requests.exceptions.ConnectionError:
                _logger.error("No se pudo conectar con la API del chatbot.")
                record.write({'bot_response': "Error de conexión con la API.", 'state': 'error'})

            except requests.exceptions.HTTPError as e:
                _logger.error("Error HTTP: %s", e)
                record.write({'bot_response': f"Error HTTP: {e}", 'state': 'error'})

            except Exception as e:
                _logger.exception("Error inesperado en chatbot: %s", e)
                record.write({'bot_response': "Error inesperado.", 'state': 'error'})