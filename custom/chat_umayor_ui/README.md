# chat_umayor_ui — Módulo de Romina

Este módulo cubre los **puntos 3, 4 y 6** del trabajo:

| Punto | Descripción                            | Dónde está                                     |
|-------|----------------------------------------|------------------------------------------------|
| 3     | Diseñar y maquetar la interfaz (UI)    | `static/src/scss`, `static/src/js`, `views/website_chat_templates.xml` |
| 4     | Integrar con Odoo Sign                 | `controllers/chat_controller.py` (endpoint `/chat/api/sign_request`) |
| 6     | Validar la viabilidad (pruebas)        | `tests/`                                       |

---

## 1. Cómo instalarlo (en Odoo.sh o local)

### Opción A · Odoo.sh (lo que ustedes usan)
1. Sube esta carpeta `chat_umayor_ui` a la raíz del repo, en tu rama `dev_romina`.
2. Haz commit y push.
3. Odoo.sh detecta el módulo y reconstruye la build.
4. En la pestaña **Apps** de tu instancia, busca "Chat UMayor" y pulsa **Instalar**.
5. (Opcional pero recomendado para el Punto 4) instala también el módulo
   estándar **Sign** desde Apps. Cuando esté instalado, el bot generará
   solicitudes de firma reales; mientras no esté, funcionará en modo demo.

### Opción B · Odoo local (Ubuntu 24.04 + Odoo 19)
```bash
# Copia la carpeta a tu directorio de addons custom:
cp -r chat_umayor_ui /opt/odoo/custom-addons/

# Reinicia Odoo y actualiza la lista de módulos:
sudo systemctl restart odoo
# Luego desde la UI: Apps -> Actualizar lista -> instalar "Chat UMayor"
```

---

## 2. Cómo probar la UI

1. Una vez instalado, abre el sitio web público de Odoo (por ejemplo
   `https://tu-build.odoo.com/`).
2. En la esquina inferior derecha verás la **burbuja azul con un punto verde pulsante**.
3. Haz clic. Se abre el panel del chat con un saludo del bot.
4. Prueba con frases como: *"quiero un crédito"*, *"tarjeta gold"*, *"firmar"*.
5. También puedes ir a `/chat` para la página dedicada.

> **Tip de demo**: si abres la URL con `?debug=1` (ej. `/contactus?debug=1`),
> verás bajo cada respuesta del bot el tiempo en milisegundos.
> Es perfecto para mostrar al profesor en la presentación que cumples el SLA.

---

## 3. Cómo integrar con el módulo de Jonathan

Tu controlador llama así al motor de IA del compañero:

```python
engine_model = request.env.get('chat.umayor.core.engine')
if engine_model is not None:
    return engine_model.sudo().generate_reply(session, user_message)
```

**Pídele a Jonathan que su módulo defina:**

```python
class CoreEngine(models.AbstractModel):
    _name = 'chat.umayor.core.engine'
    _description = 'Motor de IA del Chat UMayor'

    def generate_reply(self, session, user_message):
        # Aquí va su llamada a Gemini / la lógica conversacional
        return "respuesta del bot"
```

Si su modelo se llama distinto, solo cambia **una línea** en
`controllers/chat_controller.py` (método `_delegate_to_core`). Mientras
tanto, tu módulo funciona solo gracias al **fallback de eco con keywords**.

---

## 4. Cómo correr las pruebas (Punto 6)

Dentro de tu build de Odoo.sh o local:

```bash
# Todas las pruebas del módulo
odoo-bin -d <nombre_db> -i chat_umayor_ui \
         --test-tags chat_umayor \
         --stop-after-init --log-level=test

# Solo las de performance (las más vistosas para la presentación)
odoo-bin -d <nombre_db> -i chat_umayor_ui \
         --test-tags chat_umayor_perf \
         --stop-after-init --log-level=test
```

Lo que reporta cada test:

* `test_chat_session.py` — modelos y campos calculados (5 tests).
* `test_chat_controller.py` — endpoints HTTP (5 tests, incluye SLA <5s).
* `test_performance.py` — burst de 20 mensajes + 10 sesiones concurrentes.
  Imprime en el log la media, percentil 95 y peor caso. **Pega esos
  números en el informe de QA**.

---

## 5. Configurar la firma digital (Punto 4)

Para que el bot envíe contratos reales:

1. Instala el módulo **Sign** (Apps → buscar "Sign" → Instalar).
2. En Odoo: **Sign → Plantillas → Subir** un PDF con tu contrato modelo.
   Marca el área donde el cliente debe firmar y guarda.
3. Ve a **Chat UMayor → (en el menú lateral, busca tus productos)**
   y a cada producto asígnale la plantilla de Sign creada arriba.
4. Listo. Cuando un usuario pida contratar el producto, el endpoint
   `/chat/api/sign_request` creará una solicitud real, devolverá la URL
   pública (ej. `/sign/document/<id>/<token>`) y el cliente firmará desde
   su navegador.

> El módulo está pensado para **funcionar igual sin Sign instalado**: en
> ese caso devuelve `mode: "stub"` y un mensaje claro. Esto evita que la
> demo se rompa si algo falla el día de la presentación.

---

## 6. Estructura de archivos

```
chat_umayor_ui/
├── __init__.py
├── __manifest__.py
├── README.md                          ← este archivo
├── controllers/
│   ├── __init__.py
│   └── chat_controller.py             ← endpoints /chat/api/*
├── models/
│   ├── __init__.py
│   ├── chat_session.py                ← sesiones de chat
│   ├── chat_message.py                ← mensajes individuales
│   └── financial_product.py           ← catálogo de productos
├── data/
│   └── chat_umayor_data.xml           ← productos demo
├── security/
│   └── ir.model.access.csv            ← permisos
├── views/
│   ├── chat_session_views.xml
│   ├── chat_message_views.xml
│   ├── menu_views.xml
│   └── website_chat_templates.xml     ← markup del widget
├── static/src/
│   ├── js/chat_widget.js              ← lógica del widget
│   └── scss/chat_widget.scss          ← estilos del widget
└── tests/
    ├── __init__.py
    ├── test_chat_session.py
    ├── test_chat_controller.py
    └── test_performance.py            ← métricas para el informe
```

---

## 7. Qué decir el día de la presentación (Punto 3.7 del informe)

Si te tocó **Operadora del sistema** o **Soporte técnico**, este código
te respalda. Algunas ideas concretas que puedes mencionar:

- *"Diseñé el widget como una burbuja flotante porque es el patrón estándar
  en banca digital y no obliga al usuario a abandonar la página que está leyendo."*
- *"La integración con Odoo Sign es defensiva: si el módulo no está instalado,
  el flujo no se rompe, simplemente entra en modo demo. Esto es lo que se llama
  graceful degradation y nos protege ante imprevistos en la demo en vivo."*
- *"Para validar la viabilidad escribí 13 tests automáticos que verifican el
  SLA de menos de 5 segundos por respuesta, incluyendo una prueba de estrés
  con 20 mensajes consecutivos y 10 sesiones concurrentes."*
