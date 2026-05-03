# Aporte al módulo `chat_umayor` — Romina Beca

> Este documento describe los archivos y funcionalidades que aporté
> al proyecto del chatbot bancario UMayor. Cubre los puntos 3, 4 y 6
> que me fueron asignados en el reparto de trabajo del equipo.

---

## Reparto de tareas (acordado por el equipo)

| Punto | Tarea | Responsable |
|-------|-------|-------------|
| 1 | Motor lógico (IA + Python) | Jonathan |
| 2 | Flujo conversacional (lógica) | Jonathan |
| 5 | Sincronización de datos al backend | Jonathan |
| **3** | **Diseñar y maquetar la interfaz (UI)** | **Romina** |
| **4** | **Integrar con Odoo Sign** | **Romina** |
| **6** | **Validar viabilidad mediante pruebas** | **Romina** |

---

## Archivos de mi autoría

```
chat_umayor/
├── static/src/
│   ├── js/
│   │   └── chatbot_extras.js          ← Mejoras de UI + integración Sign
│   ├── css/
│   │   └── chatbot_extras.css         ← Estilos de los componentes nuevos
│   └── tests/
│       └── chatbot.test.js            ← Suite de pruebas frontend
└── docs_romina/
    └── README.md                       ← Este documento
```

**Archivos modificados (por necesidad técnica):**

- `__manifest__.py`: agregada **una línea** para registrar mis assets en
  el frontend de Odoo. Sin esta línea, los archivos no se cargarían.

**Archivos NO modificados:**

- `chatbot.js` y `chatbot.css` (de Raúl) — quedaron intactos.
- `controllers/main.py` — territorio del backend (Jonathan).

---

## Punto 3 — Interfaz (UI)

Las mejoras visuales que aporté al widget existente son tres,
diseñadas siguiendo el contrato `docs/api.md` definido por Jonathan:

### 3.1 Chips de sugerencias

Cuando el bot devuelve una respuesta con `suggestions`, mi código
renderiza botones-chip debajo del último mensaje. Al tocarlos, se
envía el texto del chip como mensaje del usuario.

**Por qué importa**: agiliza la conversación. El usuario no tiene
que escribir "SOAP" o "Depósito a Plazo" — solo toca el chip. Reduce
fricción y errores de tipeo.

### 3.2 Formulario de captura de datos

Cuando el bot avanza al estado `data_collection` (definido en el
contrato API), mi código renderiza dentro del chat un formulario
con los campos requeridos:

- Datos del cliente: nombre, RUT, email, teléfono.
- Datos del producto SOAP: patente, año del vehículo.
- Datos del producto Depósito: monto, plazo en días.

El formulario tiene **validación HTML5 nativa** (campos requeridos,
tipos email/number, rangos numéricos) y maneja errores de envío.

### 3.3 Diseño consistente

Los estilos que escribí mantienen la paleta del widget original
(azul #1a73e8) para no romper la coherencia visual. Agregué
animaciones suaves (`fadein`), estados hover/focus accesibles, y
un breakpoint responsive para pantallas <480px.

---

## Punto 4 — Integración con Odoo Sign

Cuando el bot avanza al estado `review` (datos confirmados), mi
código renderiza un **botón "Firmar contrato"**. Al tocarlo:

1. Llama al endpoint `/chat_umayor/session/<id>/sign` del backend.
2. Recibe la `sign_url` que devuelve Odoo Sign.
3. Abre el documento de firma en una pestaña nueva (con `noopener`
   por seguridad — evita que el sitio firmante acceda a `window.opener`).

**Decisión técnica**: opté por abrir en pestaña nueva en lugar de
iframe porque Odoo Sign en algunos casos rechaza ser embebido y
porque es más usable en móvil.

---

## Punto 6 — Pruebas de viabilidad

Creé una suite de **7 pruebas frontend** en `chatbot.test.js`. Se
ejecutan desde la consola del navegador con un solo comando:

```javascript
ChatbotTests.runAll()
```

### Cobertura

| # | Prueba | Qué valida |
|---|--------|------------|
| 1 | Estructura DOM | Que todos los elementos del widget existan |
| 2 | Accesibilidad | Roles ARIA básicos, placeholders, semántica |
| 3 | Toggle widget | Apertura/cierre del panel |
| 4 | **SLA <5s** | **Que el bot responda en menos de 5 segundos** |
| 5 | Validación input | Que mensajes vacíos no se envíen |
| 6 | Resistencia XSS | Que el HTML inyectado no se ejecute |
| 7 | Burst de mensajes | Performance con 5 mensajes seguidos |

La prueba 4 es la métrica clave del trabajo: garantiza el SLA de
viabilidad técnica.

### Cómo correrlo

1. Abrir el sitio público con el chatbot cargado.
2. Abrir DevTools del navegador (F12).
3. Pegar el contenido de `chatbot.test.js` en la consola.
4. Ejecutar `ChatbotTests.runAll()`.

Las pruebas imprimen un reporte coloreado con cada caso y un resumen
final de cuántas pasaron/fallaron.

---

## Modo demo

Como el backend de Jonathan estaba en desarrollo al momento de mi
entrega, agregué un **modo demo** que se activa automáticamente
cuando los endpoints reales no responden. En este modo, mi código
simula respuestas siguiendo exactamente el contrato `docs/api.md`,
permitiendo presentar el flujo completo (saludo → producto →
formulario → firma) sin depender del backend.

Cuando Jonathan termine sus endpoints, el modo demo se desactivará
automáticamente y todo funcionará contra el backend real, sin
cambiar una sola línea de código.

**Esto es lo que en arquitectura se llama "graceful degradation"**:
si una capa falla, la siguiente sigue funcionando.

---

## Cómo se integra todo

```
┌────────────────────────────────────────────┐
│  USUARIO escribe en el chat                │
└─────────────────┬──────────────────────────┘
                  ↓
┌────────────────────────────────────────────┐
│  chatbot.js (Raúl) renderiza el mensaje    │
│  Mi chatbot_extras.js intercepta el envío  │
└─────────────────┬──────────────────────────┘
                  ↓
        ┌─────────┴─────────┐
        ↓                   ↓
   ¿Backend OK?        ¿Backend caído?
        ↓                   ↓
  Llama endpoints       Activa modo demo
  reales de Jonathan    y simula respuestas
        ↓                   ↓
        └─────────┬─────────┘
                  ↓
┌────────────────────────────────────────────┐
│  Mi código renderiza:                      │
│  • Chips de sugerencias                    │
│  • Formulario de captura                   │
│  • Botón de "Firmar contrato"              │
└────────────────────────────────────────────┘
```

---

## Frase para la presentación

> *"Mi parte se enfoca en cerrar el flujo de venta del lado del cliente:
> chips para acelerar la conversación, formulario para capturar datos,
> y botón de firma para finalizar el contrato. Todo se integra con
> el backend de Jonathan a través del contrato API que él definió,
> y tiene un modo demo para que el flujo sea defendible aunque el
> backend esté en desarrollo. Las pruebas frontend validan que el bot
> cumple el SLA de menos de 5 segundos."*

---

_Romina Beca · 2026-05-03_
