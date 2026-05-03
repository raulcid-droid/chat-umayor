# -*- coding: utf-8 -*-
{
    'name': 'Chat UMayor - UI y Firma Digital',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Interfaz web del chatbot bancario UMayor con integración Odoo Sign',
    'description': """
Chatbot Bancario UMayor - Módulo de Interfaz
=============================================

Este módulo aporta al proyecto:
* Widget flotante de chat en el sitio web público (HTML/SCSS/JS).
* Página dedicada /chat para una experiencia ampliada.
* Endpoints HTTP para enviar/recibir mensajes desde el frontend.
* Integración con Odoo Sign: dispara una solicitud de firma cuando el
  usuario acepta contratar un producto financiero a través del bot.
* Hooks para el módulo de lógica/IA del compañero (chat_umayor_core),
  con fallback de eco si el módulo de lógica aún no está instalado.

Roles del proyecto cubiertos por este módulo:
- Punto 3: Diseñar y maquetar la interfaz (UI).
- Punto 4: Integrar con Odoo Sign.
- Punto 6: Validar la viabilidad mediante pruebas automatizadas.
    """,
    'author': 'Romina Beca - Equipo Chat UMayor',
    'website': 'https://github.com/raulcid-droid/chat-umayor',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web',
        'website',
        'mail',
        # 'sign' es OPCIONAL en runtime: si está instalado, se usa; si no,
        # el módulo igual carga y la integración queda en modo "stub".
        # Para activarlo en producción, descomentar la línea de abajo:
        # 'sign',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/chat_umayor_data.xml',
        'views/chat_session_views.xml',
        'views/chat_message_views.xml',
        'views/website_chat_templates.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'chat_umayor_ui/static/src/scss/chat_widget.scss',
            'chat_umayor_ui/static/src/js/chat_widget.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
