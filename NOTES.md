# NOTES.md — Estado del proyecto chat_umayor

## Sesión 2026-05-02: Reinicio de plan + arranque backend

### Resumen ejecutivo
Sesión larga con tres planes cerrados y un cuarto pendiente de validación
en staging. El módulo pasa de ser un esqueleto vacío a tener su primer
endpoint HTTP funcional y un contrato de API consensuable con UI.

### Logros
- ✅ **PLAN 01**: `AGENTS.md` reconciliado (path real `chat_umayor/` en raíz). Docs locales bajo control de versiones.
  - `c6877d3 docs(agents): add real module path at repo root`
  - `4268aa2 docs: add local AGENTS, NOTES and PLAN working notes`
- ✅ **PLAN 02**: `docs/api.md v0` — contrato formal de los 4 endpoints, catálogo de 8 errores, 6 TBDs explícitos.
  - `d8e1c2d docs(api): add v0 draft of backend-frontend contract`
- 🔄 `PLAN.md` sobrescrito: pasó de plan de auditoría a roadmap de desarrollo (10 filas).
  - `afff850 docs(plan): replace audit plan with backend dev roadmap`
  - `11ab0eb docs(notes): log 2026-05-02 session progress and plan reset`
- ✅ **PLAN 02.1**: `docs/api.md v0.1` — transporte clarificado como **JSON-RPC 2.0 nativo de Odoo** (no REST plano). Cierra TBD de CSRF.
  - `c988a38 docs(api): clarify JSON-RPC transport in v0.1`
- 🟡 **PLAN 03** (código escrito, pendiente validar en Odoo.sh staging): endpoint `/chat_umayor/ping` + cadena de imports + `TestSmokePing`.
  - `a219e27 feat(controllers): add health ping endpoint and smoke test`

### Decisiones técnicas clave
- **Transporte**: JSON-RPC 2.0 nativo de Odoo (`type='json'`), no REST plano. Razón: idiomático en Odoo 19, CSRF gestionado automáticamente, la UI puede usar el helper `rpc` de Odoo sin boilerplate.
- **Shape interno**: dentro del `result` del JSON-RPC seguimos usando `{ok, data|error}` con catálogo de códigos de error tipado.
- **Tests**: `HttpCase` + tags `chat_umayor`, `post_install`. Odoo auto-descubre `tests/` — **no** importarlo desde `__init__.py` raíz.

### En qué quedamos
- Jonathan va a **validar PLAN 03 en Odoo.sh staging** y trae resultado mañana.
- Comando de validación: `./odoo-bin --addons-path=addons,. -d chatbot_test --test-enable --stop-after-init -i chat_umayor --test-tags=/chat_umayor`.
- Puntos de fallo probables si algo explota: signatura de `HttpCase.url_open` en Odoo 19, o manejo de `type='json'` en el test. Si falla, traer traceback.
- Mientras no haya green en staging, **no avanzar a PLAN 04**.

### Acuerdos operativos
- Los `git push` los hace Jonathan (ya pusheó todos los commits de esta sesión).
- Cada fila del roadmap es un `PLAN.md` atómico nuevo, consensuado antes de ejecutar.

### Pendiente inmediato (mañana)
1. Confirmar resultado de validación de PLAN 03 en staging.
2. Si green → arrancar **PLAN 04**: modelo `chatbot.session` con FSM + ACL + tests RED→GREEN.
3. Si red → fix sobre PLAN 03 antes de seguir.

---


## Ruta de trabajo
`~/Proyectos/chatbot_bancario/chat-umayor/`

El módulo Odoo vive en `./chat_umayor/` (en la **raíz del repo**, no en
`custom_addons/`). Nombre definitivo del módulo: **`chat_umayor`**.

## Última sesión — 2026-05-01 · Auditoría inicial

### Decisiones tomadas
- **Nombre del módulo**: se mantiene `chat_umayor` (no se renombra a
  `banking_chatbot`). Razón: ya hay 7 commits y una compañera trabajando
  con esa estructura. Se actualiza `AGENTS.md` para reflejar la realidad.
- **Archivos vacíos intencionales**: `chat_umayor/__init__.py`,
  `controllers/__init__.py`, `controllers/main.py`, `views/assets.xml`,
  `static/src/js/chatbot.js`, `static/src/css/chatbot.css` son **stubs
  acordados** con la compañera de frontend para compartir estructura de
  carpetas. No son bugs.
- **Basura detectada y eliminada**: directorio literal
  `chat_umayor/static/src/{js,css}/` (residuo de `mkdir` sin brace
  expansion).

### Auditoría — ✅ Implementado
- Esqueleto mínimo de módulo Odoo 19:
  - `__manifest__.py` válido: `version: 19.0.1.0.0`, `depends: ['website']`,
    `license: LGPL-3`, `installable: True`.
  - Assets declarados en bundle `web.assets_frontend` (CSS + JS stubs).
- Git limpio, rama `dev_jona` sincronizada con `origin`.
- Cero secretos en el repo (grep de `AIza`, `API_KEY`, `sk-`, `GEMINI`
  → 0 matches).

### Auditoría — ❌ Falta (pendiente de implementar)

Severidades actualizadas tras la aclaración sobre stubs intencionales.

| Sev | Falta |
|---|---|
| 🔴 | **Cero modelos**: `models/` no existe. Falta `chatbot.session` (FSM §5 de AGENTS.md), `chatbot.message`, `chatbot.contract`. |
| 🔴 | **Cero integración Gemini**: no existe `services/gemini_client.py`. `google-genai` no declarado como dependencia. |
| 🔴 | No existe `security/ir.model.access.csv` (obligatorio al crear modelos). |
| 🟡 | Stubs por rellenar (coordinado con frontend): `__init__.py` raíz y `controllers/__init__.py` deben importar módulos cuando existan; `controllers/main.py` debe exponer `/chatbot`; `views/assets.xml` debe declarar templates QWeb. |
| 🟡 | `chatbot.js` y `chatbot.css` son stubs — la compañera los llenará. |
| 🟡 | No existe `data/` (productos SOAP/Depósito ni `system_prompt.xml`). |
| 🟡 | No existe `tests/`. |
| 🟡 | No existe `i18n/es.po`. |

### Respuestas a preguntas del PLAN de auditoría
1. ¿Instala en Odoo 19? **Sí**, pero instalaría un módulo vacío sin
   funcionalidad (el manifest es válido).
2. ¿Código que llame a Gemini? **No**, desde ningún lado.
3. ¿Modelos/persistencia? **No**, nada.
4. ¿Secretos hardcoded? **No**, confirmado por grep.
5. ¿Coincide el nombre con `AGENTS.md`? **No** → resuelto en PLAN 01.

## Roadmap (planes atómicos previstos)

1. ✅ **PLAN 01** — Reconciliar `AGENTS.md` + limpiar basura. *(en curso)*
2. **PLAN 02** — Módulo instalable end-to-end mínimo (controller `/chatbot`
   + template QWeb placeholder). Coordinar con frontend qué stubs rellenar.
3. **PLAN 03** — Modelo `chatbot.session` con FSM + ACL + tests.
4. **PLAN 04** — Modelo `chatbot.message` + `_sanitize_for_llm()` + ACL + tests.
5. **PLAN 05** — `services/gemini_client.py` con mocks, `ir.config_parameter`
   para API key y system prompt.
6. **PLAN 06** — Widget OWL del chat + endpoints JSON.
7. **PLAN 07** — Productos SOAP y Depósito en `data/products.xml` + cálculos.
8. **PLAN 08** — Formulario cliente + modelo `chatbot.contract`.
9. **PLAN 09** — Firma canvas + hash SHA-256.
10. **PLAN 10** — `i18n/es.po` + README de entrega académica.

## Pendiente inmediato
- Terminar PLAN 01 (actualizar `AGENTS.md`, limpiar dir basura).
- Luego esperar mi "ok" para arrancar PLAN 02.

<!-- v0.2 · 2026-05-01 · tras auditoría inicial -->
