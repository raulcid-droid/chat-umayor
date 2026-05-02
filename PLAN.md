# PLAN — Auditoría inicial de `chat_umayor` (rol backend)

## Objetivo
Entender qué existe, contrastar con el `AGENTS.md`, producir roadmap backend.
**Solo lectura.**

## Alcance
- ✅ Leer archivos, listar directorios, `git status`, `git log`.
- ✅ Revisar **todo** el repo para tener contexto, aunque luego solo edite lo mío.
- ❌ No `ruff`, no instalar, no tests, no editar nada.

## Pasos

### 1. Inventario
- `tree chat_umayor/` o `ls -R chat_umayor/`.
- `git status` + `git log --oneline -15`.

### 2. Lectura (todos los archivos del repo)
- `chat_umayor/__manifest__.py` → `depends`, `data`, `assets`, versión.
- `chat_umayor/__init__.py` → qué subpaquetes importa.
- `chat_umayor/controllers/main.py` → rutas, `auth`, si hay llamada a Gemini desde aquí.
- `chat_umayor/views/assets.xml` → qué JS/CSS carga (solo informativo, no lo toco).
- `chat_umayor/static/src/js/chatbot.js` → si ya hay lógica de chat o llamadas HTTP (informativo).
- `chat_umayor/static/src/css/chatbot.css` → ojeada.
- `README.md` → contexto y entregables declarados.

### 3. Detección de ausencias (mi trabajo)
¿Existen?
- `chat_umayor/models/` y su `__init__.py`.
- `chat_umayor/services/gemini_client.py`.
- `chat_umayor/security/ir.model.access.csv`.
- `chat_umayor/data/` (productos, prompt).
- `chat_umayor/tests/`.
- `docs/api.md` con el contrato backend↔frontend.

### 4. Preguntas a responder
1. ¿El módulo se instala en Odoo 19 según el `__manifest__.py`? (solo inferir).
2. ¿Dónde vive hoy la lógica del chat — frontend, backend, ambos, ninguno?
3. ¿Hay llamada a Gemini? ¿Desde JS (🔴 inseguro) o desde Python?
4. ¿Hay **secretos hardcoded**? Buscar `API_KEY`, `sk-`, `AIza` en todo el repo.
5. ¿`__manifest__.py` depende ya de `sign`? ¿De `website`?
6. ¿Hay señales de un **contrato de API** acordado con el compañero de UI? Si no, hay que proponerlo.

## Entregable
Mensaje en el chat con tres bloques:

- **✅ Implementado** — qué hay, quién lo hizo (backend/frontend).
- **❌ Falta / roto (mi área)** — con severidad 🔴 crítico / 🟡 importante / 🟢 menor.
- **🛣️ Roadmap backend** — lista ordenada de próximos `PLAN.md`, cada uno con 1 objetivo atómico. Esperable: (1) alinear `__manifest__.py`, (2) crear modelos base + FSM, (3) wrapper Gemini, (4) endpoints + `docs/api.md`, (5) integración Sign, (6) tests.

## Riesgos
Ninguno — solo lectura.

## Rollback
N/A.

<!-- v0.2 · 2026-05-02 · ajustado para rol backend -->
