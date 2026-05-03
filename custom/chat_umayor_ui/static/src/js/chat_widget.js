/* ==========================================================================
 * Chat UMayor - Widget de chat flotante
 * ==========================================================================
 *
 * JS vanilla (sin frameworks) para el widget que se monta en el sitio web
 * público. Habla con los endpoints `/chat/api/*` definidos en
 * `controllers/chat_controller.py`.
 *
 * Flujo:
 *   1. Al abrir el widget por primera vez -> POST /chat/api/start
 *      Recibe un token y guarda en sessionStorage del navegador.
 *   2. Por cada mensaje del usuario -> POST /chat/api/send
 *      Muestra typing indicator mientras espera respuesta.
 *   3. Cuando el usuario decide contratar -> POST /chat/api/sign_request
 *      Si Odoo Sign está instalado, redirige a la URL de firma.
 *
 * Endpoints `type='json'` esperan: { jsonrpc:"2.0", method:"call", params:{...} }
 * y devuelven: { jsonrpc:"2.0", id:..., result: <lo_que_devuelve_python> }
 * ========================================================================== */

(function () {
    "use strict";

    // ---- Helpers --------------------------------------------------------
    /**
     * Llama a un endpoint JSON de Odoo. Devuelve directamente `result`.
     */
    async function callJson(url, params) {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
            }),
        });
        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error.data && data.error.data.message
                            ? data.error.data.message
                            : "Error del servidor");
        }
        return data.result;
    }

    function el(html) {
        const tpl = document.createElement("template");
        tpl.innerHTML = html.trim();
        return tpl.content.firstElementChild;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // ---- Widget principal ----------------------------------------------
    function initChatWidget() {
        const widget = document.getElementById("cu_chat_widget");
        if (!widget) return;  // El template no está renderizado en esta página

        const toggleBtn  = document.getElementById("cu_chat_toggle");
        const minBtn     = document.getElementById("cu_chat_minimize");
        const form       = document.getElementById("cu_chat_form");
        const input      = document.getElementById("cu_chat_input");
        const messagesEl = document.getElementById("cu_chat_messages");
        const suggestEl  = document.getElementById("cu_chat_suggestions");

        let token = sessionStorage.getItem("cu_chat_token") || null;
        let started = false;
        let isSending = false;

        // Toggle abrir/cerrar
        toggleBtn.addEventListener("click", async () => {
            const isOpen = widget.classList.toggle("is-open");
            widget.querySelector(".cu-widget__panel")
                  .setAttribute("aria-hidden", !isOpen);

            if (isOpen && !started) {
                started = true;
                await startSession();
                await loadProducts();
            }
            if (isOpen) input.focus();
        });

        minBtn.addEventListener("click", () => {
            widget.classList.remove("is-open");
            widget.querySelector(".cu-widget__panel")
                  .setAttribute("aria-hidden", "true");
        });

        // Submit del formulario
        form.addEventListener("submit", async (ev) => {
            ev.preventDefault();
            const text = input.value.trim();
            if (!text || isSending) return;
            input.value = "";
            await sendMessage(text);
        });

        // ---- Funciones de la sesión ------------------------------------
        async function startSession() {
            try {
                if (!token) {
                    const result = await callJson("/chat/api/start", {});
                    token = result.token;
                    sessionStorage.setItem("cu_chat_token", token);
                    appendMessage("bot", result.greeting);
                } else {
                    // Si ya teníamos token pero abrimos de nuevo, saludo simple
                    appendMessage("bot",
                        "Bienvenida de vuelta. ¿En qué te ayudo?");
                }
            } catch (e) {
                appendMessage("system",
                    "No pudimos iniciar el chat. Intenta nuevamente.");
                console.error("[chat_umayor] startSession:", e);
            }
        }

        async function loadProducts() {
            try {
                const products = await callJson("/chat/api/products", {});
                suggestEl.innerHTML = "";
                products.slice(0, 4).forEach((p) => {
                    const chip = el(
                        `<button type="button" class="cu-chip">${escapeHtml(p.name)}</button>`
                    );
                    chip.addEventListener("click", () => sendMessage(
                        "Quiero información sobre " + p.name));
                    suggestEl.appendChild(chip);
                });
            } catch (e) {
                console.warn("[chat_umayor] loadProducts:", e);
            }
        }

        async function sendMessage(text) {
            isSending = true;
            appendMessage("user", text);
            const typing = appendTyping();

            try {
                const result = await callJson("/chat/api/send", {
                    token: token,
                    message: text,
                });
                typing.remove();

                if (result.error) {
                    appendMessage("system",
                        "Error: " + (result.error || "desconocido"));
                } else {
                    appendMessage("bot", result.reply);

                    // Métrica visible de QA (Punto 6) - solo en modo debug
                    if (window.location.search.includes("debug")) {
                        appendMessage("system",
                            `[debug] respuesta en ${result.response_time_ms} ms`);
                    }
                }
            } catch (e) {
                typing.remove();
                appendMessage("system",
                    "El asistente no respondió a tiempo. Intenta de nuevo.");
                console.error("[chat_umayor] sendMessage:", e);
            } finally {
                isSending = false;
                input.focus();
            }
        }

        // ---- Render ----------------------------------------------------
        function appendMessage(role, content) {
            const cls = "cu-msg cu-msg--" + role;
            const msg = el(
                `<div class="${cls}">${escapeHtml(content)}</div>`
            );
            messagesEl.appendChild(msg);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return msg;
        }

        function appendTyping() {
            const t = el(
                `<div class="cu-typing" aria-label="Escribiendo">
                    <span></span><span></span><span></span>
                </div>`
            );
            messagesEl.appendChild(t);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return t;
        }
    }

    // Iniciar cuando el DOM esté listo
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initChatWidget);
    } else {
        initChatWidget();
    }
})();
