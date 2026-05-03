/** @odoo-module **/
/* =========================================================================
 * chatbot_extras.js
 * -------------------------------------------------------------------------
 * Aporte de Romina Beca al módulo chat_umayor.
 *
 * Este archivo NO toca el widget original (chatbot.js de Raúl).
 * En su lugar, lo OBSERVA y le AGREGA tres capacidades nuevas que no
 * existían y que están definidas en docs/api.md:
 *
 *   1. Chips de sugerencias (campo `suggestions` del backend).
 *   2. Formulario de captura de datos (estado `data_collection`).
 *   3. Botón de firma de contrato (estado `review` -> `signing`).
 *
 * Además, cuando el backend de Jonathan aún no está implementado,
 * activa un MODO DEMO que simula respuestas siguiendo el mismo
 * contrato de la API. Eso permite presentar el flujo completo
 * sin depender del backend.
 *
 * Autora: Romina Beca
 * Cubre puntos 3 (UI) y 4 (Sign) del informe sumativo.
 * ========================================================================= */

(function () {
  "use strict";

  // ---------------------------------------------------------------
  // Configuración
  // ---------------------------------------------------------------
  const ENDPOINTS = {
    new: "/chat_umayor/session/new",
    message: (id) => `/chat_umayor/session/${id}/message`,
    submitData: (id) => `/chat_umayor/session/${id}/submit_data`,
    sign: (id) => `/chat_umayor/session/${id}/sign`,
  };

  // Estado interno - vinculado a la sesión de Jonathan cuando exista
  const sessionState = {
    sessionId: null,
    currentState: "greeting",
    demoMode: false, // se activa solo si los endpoints fallan
  };

  // ---------------------------------------------------------------
  // Punto de entrada
  // ---------------------------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initExtras);
  } else {
    // Esperamos un tick para que el widget de Raúl ya esté en el DOM
    setTimeout(initExtras, 100);
  }

  function initExtras() {
    const messagesEl = document.getElementById("chatbot-messages");
    const sendBtn = document.getElementById("chatbot-send");
    const inputEl = document.getElementById("chatbot-input");

    if (!messagesEl || !sendBtn || !inputEl) {
      // El widget de Raúl aún no se montó - reintentamos
      setTimeout(initExtras, 200);
      return;
    }

    console.log("[chatbot_extras] Inicializado por Romina Beca");

    // Interceptamos el botón de enviar para usar nuestros endpoints
    // (en modo demo o real). El interceptor también dispara la
    // renderización de chips, formulario y botón de firma según
    // el estado que devuelva el backend.
    sendBtn.addEventListener("click", handleSendInterception, true);
    inputEl.addEventListener(
      "keydown",
      (e) => {
        if (e.key === "Enter") handleSendInterception(e);
      },
      true,
    );

    // Probamos crear la sesión al cargar (silenciosamente)
    startSession();
  }

  // ---------------------------------------------------------------
  // Sesión (endpoint /session/new)
  // ---------------------------------------------------------------
  async function startSession() {
    try {
      const res = await callEndpoint(ENDPOINTS.new, {});
      if (res && res.ok && res.data && res.data.session_id) {
        sessionState.sessionId = res.data.session_id;
        sessionState.currentState = res.data.state || "greeting";
        console.log(
          "[chatbot_extras] Sesión real iniciada:",
          sessionState.sessionId,
        );
      } else {
        throw new Error("Respuesta inválida");
      }
    } catch (err) {
      // Backend no disponible -> activamos modo demo
      sessionState.demoMode = true;
      sessionState.sessionId = "demo-" + Date.now();
      sessionState.currentState = "greeting";
      console.warn(
        "[chatbot_extras] Backend no disponible, activando MODO DEMO",
      );
      showDemoBadge();
    }
  }

  function showDemoBadge() {
    const header = document.querySelector(".chatbot-header-status");
    if (header) {
      header.textContent = "Modo demo";
      header.style.color = "#ffd54f";
    }
  }

  // ---------------------------------------------------------------
  // Interceptor del envío
  // ---------------------------------------------------------------
  let isHandlingSend = false;

  async function handleSendInterception(ev) {
    if (isHandlingSend) return; // evita doble disparo
    const inputEl = document.getElementById("chatbot-input");
    const text = inputEl.value.trim();
    if (!text) return;

    isHandlingSend = true;
    try {
      await sendUserMessage(text);
    } finally {
      isHandlingSend = false;
    }
  }

  async function sendUserMessage(text) {
    const inputEl = document.getElementById("chatbot-input");
    const msgsEl = document.getElementById("chatbot-messages");

    // 1. Limpiamos chips/formularios/botones extras anteriores
    clearExtras();

    // 2. Renderizamos el mensaje del usuario
    appendMessage(text, "user");
    inputEl.value = "";

    // 3. Mostramos indicador "escribiendo..."
    const typingEl = appendTyping();

    // 4. Llamamos al endpoint correspondiente (real o demo)
    const t0 = performance.now();
    let response;
    try {
      if (sessionState.demoMode) {
        response = await demoReply(text);
      } else {
        response = await callEndpoint(
          ENDPOINTS.message(sessionState.sessionId),
          { content: text },
        );
      }
    } catch (err) {
      response = { ok: false, error: { message: "Error de conexión." } };
    }
    const elapsed = Math.round(performance.now() - t0);

    // 5. Quitamos el typing y renderizamos la respuesta del bot
    if (typingEl) typingEl.remove();

    if (response && response.ok && response.data) {
      const data = response.data;
      appendMessage(data.reply || "(sin respuesta)", "bot");

      // Actualizamos el estado conversacional
      if (data.state) sessionState.currentState = data.state;

      // Renderizamos extras según el contrato
      if (data.suggestions && data.suggestions.length > 0) {
        renderSuggestions(data.suggestions);
      }
      if (data.state === "data_collection") {
        renderDataForm(data.product_code || detectProduct(data.reply));
      }
      if (data.state === "review") {
        renderSignButton();
      }
    } else {
      const errMsg =
        (response && response.error && response.error.message) ||
        "El asistente no respondió. Intenta nuevamente.";
      appendMessage(errMsg, "bot");
    }

    // 6. Logueamos el tiempo (útil para Punto 6)
    console.log(
      `[chatbot_extras] Respuesta en ${elapsed} ms (estado: ${sessionState.currentState})`,
    );
    if (window.__chatbotMetrics) {
      window.__chatbotMetrics.push({
        ms: elapsed,
        state: sessionState.currentState,
      });
    }
  }

  // ---------------------------------------------------------------
  // Render de extras
  // ---------------------------------------------------------------
  function clearExtras() {
    document.querySelectorAll(".cu-extras").forEach((el) => el.remove());
  }

  function renderSuggestions(suggestions) {
    const msgsEl = document.getElementById("chatbot-messages");
    const wrap = document.createElement("div");
    wrap.className = "cu-extras cu-suggestions";
    suggestions.forEach((sug) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "cu-chip";
      chip.textContent = sug;
      chip.addEventListener("click", () => {
        sendUserMessage(sug);
      });
      wrap.appendChild(chip);
    });
    msgsEl.appendChild(wrap);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  function renderDataForm(productCode) {
    const msgsEl = document.getElementById("chatbot-messages");
    const isSoap = (productCode || "").toLowerCase() === "soap";
    const isDeposit = (productCode || "").toLowerCase() === "deposit";

    const form = document.createElement("form");
    form.className = "cu-extras cu-form";
    form.innerHTML = `
            <div class="cu-form-title">Completa tus datos</div>
            <div class="cu-form-row">
                <label>Nombre completo</label>
                <input type="text" name="name" required="required" />
            </div>
            <div class="cu-form-row">
                <label>RUT / Documento</label>
                <input type="text" name="document_id" required="required" placeholder="12.345.678-9" />
            </div>
            <div class="cu-form-row">
                <label>Email</label>
                <input type="email" name="email" required="required" />
            </div>
            <div class="cu-form-row">
                <label>Teléfono</label>
                <input type="tel" name="phone" placeholder="+56 9 ..." />
            </div>
            ${
              isSoap
                ? `
                <div class="cu-form-divider">Datos del vehículo</div>
                <div class="cu-form-row">
                    <label>Patente</label>
                    <input type="text" name="vehicle_plate" required="required" placeholder="ABCD12" />
                </div>
                <div class="cu-form-row">
                    <label>Año</label>
                    <input type="number" name="vehicle_year" required="required" min="1980" max="2030" />
                </div>
            `
                : ""
            }
            ${
              isDeposit
                ? `
                <div class="cu-form-divider">Datos del depósito</div>
                <div class="cu-form-row">
                    <label>Monto (CLP)</label>
                    <input type="number" name="amount" required="required" min="100000" />
                </div>
                <div class="cu-form-row">
                    <label>Plazo (días)</label>
                    <input type="number" name="term_days" required="required" min="30" max="365" />
                </div>
            `
                : ""
            }
            <button type="submit" class="cu-form-submit">Enviar datos</button>
            <div class="cu-form-error" style="display:none"></div>
        `;
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      await submitDataForm(form, productCode);
    });
    msgsEl.appendChild(form);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  async function submitDataForm(form, productCode) {
    const errBox = form.querySelector(".cu-form-error");
    errBox.style.display = "none";
    errBox.textContent = "";

    const data = new FormData(form);
    const payload = {
      product_code: productCode || "soap",
      partner: {
        name: data.get("name"),
        document_id: data.get("document_id"),
        email: data.get("email"),
        phone: data.get("phone") || "",
      },
      product_data: {},
    };
    if (data.get("vehicle_plate")) {
      payload.product_data.vehicle_plate = data.get("vehicle_plate");
      payload.product_data.vehicle_year = parseInt(
        data.get("vehicle_year"),
        10,
      );
    }
    if (data.get("amount")) {
      payload.product_data.amount = parseFloat(data.get("amount"));
      payload.product_data.term_days = parseInt(data.get("term_days"), 10);
    }

    const submitBtn = form.querySelector(".cu-form-submit");
    submitBtn.disabled = true;
    submitBtn.textContent = "Enviando...";

    let response;
    try {
      if (sessionState.demoMode) {
        response = await demoSubmitData(payload);
      } else {
        response = await callEndpoint(
          ENDPOINTS.submitData(sessionState.sessionId),
          payload,
        );
      }
    } catch (err) {
      response = {
        ok: false,
        error: { message: "Error de conexión al enviar." },
      };
    }

    if (response && response.ok && response.data) {
      // Quitamos el formulario y mostramos resumen
      form.remove();
      const summary = response.data.summary || {};
      const text = `✓ Datos recibidos. ${summary.product_name || ""} a nombre de ${summary.partner_name || ""}.`;
      appendMessage(text, "bot");

      sessionState.currentState = response.data.state || "review";
      if (sessionState.currentState === "review") {
        renderSignButton();
      }
    } else {
      const errMsg =
        (response && response.error && response.error.message) ||
        "Hubo un error al enviar los datos.";
      errBox.textContent = errMsg;
      errBox.style.display = "block";
      submitBtn.disabled = false;
      submitBtn.textContent = "Enviar datos";
    }
  }

  function renderSignButton() {
    const msgsEl = document.getElementById("chatbot-messages");
    const wrap = document.createElement("div");
    wrap.className = "cu-extras cu-sign";
    wrap.innerHTML = `
            <button type="button" class="cu-sign-btn">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"
                     style="vertical-align: middle; margin-right: 6px">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34a.996.996 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                </svg>
                Firmar contrato
            </button>
            <p class="cu-sign-help">Te abriremos el documento en una pestaña segura.</p>
        `;
    wrap.querySelector(".cu-sign-btn").addEventListener("click", launchSign);
    msgsEl.appendChild(wrap);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  async function launchSign() {
    const wrap = document.querySelector(".cu-sign");
    if (wrap) wrap.querySelector(".cu-sign-btn").disabled = true;

    let response;
    try {
      if (sessionState.demoMode) {
        response = await demoSign();
      } else {
        response = await callEndpoint(
          ENDPOINTS.sign(sessionState.sessionId),
          {},
        );
      }
    } catch (err) {
      response = { ok: false, error: { message: "Error al iniciar firma." } };
    }

    if (response && response.ok && response.data && response.data.sign_url) {
      appendMessage("Te llevamos al documento de firma.", "bot");
      window.open(response.data.sign_url, "_blank", "noopener");
      if (wrap) wrap.remove();
    } else {
      const errMsg =
        (response && response.error && response.error.message) ||
        "No se pudo iniciar la firma.";
      appendMessage(errMsg, "bot");
      if (wrap) wrap.querySelector(".cu-sign-btn").disabled = false;
    }
  }

  // ---------------------------------------------------------------
  // MODO DEMO (cuando backend de Jonathan no responde)
  // ---------------------------------------------------------------
  async function demoReply(userText) {
    await sleep(400 + Math.random() * 600); // simula latencia real
    const text = userText.toLowerCase();

    if (
      sessionState.currentState === "greeting" ||
      sessionState.currentState === "discovery"
    ) {
      if (text.includes("soap") || text.includes("seguro")) {
        sessionState.currentState = "product_info";
        return {
          ok: true,
          data: {
            reply:
              "El SOAP cubre accidentes personales con cobertura nacional. La prima depende del año del vehículo. ¿Te interesa contratarlo?",
            state: "product_info",
            suggestions: ["Sí, contratar", "Más información"],
          },
        };
      }
      if (
        text.includes("depósito") ||
        text.includes("deposito") ||
        text.includes("ahorro")
      ) {
        sessionState.currentState = "product_info";
        return {
          ok: true,
          data: {
            reply:
              "Nuestro Depósito a Plazo ofrece tasa del 0.45% mensual capitalizable. Plazos desde 30 hasta 365 días. ¿Quieres contratarlo?",
            state: "product_info",
            suggestions: ["Sí, contratar", "Más información"],
          },
        };
      }
      return {
        ok: true,
        data: {
          reply:
            "Hola, soy el asistente de UMayor. ¿Te interesa SOAP o Depósito a Plazo?",
          state: "discovery",
          suggestions: ["SOAP", "Depósito a Plazo"],
        },
      };
    }

    if (sessionState.currentState === "product_info") {
      if (
        text.includes("contratar") ||
        text.includes("sí") ||
        text.includes("si")
      ) {
        sessionState.currentState = "data_collection";
        const lastBot = getLastBotText().toLowerCase();
        const productCode = lastBot.includes("soap") ? "soap" : "deposit";
        return {
          ok: true,
          data: {
            reply:
              "Perfecto, necesito algunos datos para preparar el contrato.",
            state: "data_collection",
            product_code: productCode,
          },
        };
      }
      return {
        ok: true,
        data: {
          reply: "¿Quieres avanzar con la contratación?",
          state: "product_info",
          suggestions: ["Sí, contratar", "Volver"],
        },
      };
    }

    return {
      ok: true,
      data: {
        reply: "Disculpa, no entendí. ¿Puedes reformular?",
        state: sessionState.currentState,
      },
    };
  }

  async function demoSubmitData(payload) {
    await sleep(500);
    const isSoap = payload.product_code === "soap";
    return {
      ok: true,
      data: {
        state: "review",
        summary: {
          product_name: isSoap ? "SOAP" : "Depósito a Plazo",
          partner_name: payload.partner.name,
          calculated: isSoap
            ? { premium: 7890, currency: "CLP" }
            : {
                interest: Math.round(
                  payload.product_data.amount *
                    0.0045 *
                    (payload.product_data.term_days / 30),
                ),
                currency: "CLP",
              },
        },
      },
    };
  }

  async function demoSign() {
    await sleep(400);
    return {
      ok: true,
      data: {
        contract_id: 999,
        sign_url: "/web#action=base.action_res_partner_form", // página existente para no romper
        state: "signing",
      },
    };
  }

  // ---------------------------------------------------------------
  // Helpers DOM
  // ---------------------------------------------------------------
  function appendMessage(text, from) {
    const msgsEl = document.getElementById("chatbot-messages");
    const div = document.createElement("div");
    div.className = `chatbot-message chatbot-message--${from}`;
    div.innerHTML = `<div class="chatbot-bubble"></div>`;
    div.querySelector(".chatbot-bubble").textContent = text;
    msgsEl.appendChild(div);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return div;
  }

  function appendTyping() {
    const msgsEl = document.getElementById("chatbot-messages");
    const div = document.createElement("div");
    div.className = "chatbot-message chatbot-message--bot cu-extras";
    div.innerHTML = `
            <div class="chatbot-bubble chatbot-typing">
                <span></span><span></span><span></span>
            </div>
        `;
    msgsEl.appendChild(div);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return div;
  }

  function getLastBotText() {
    const msgs = document.querySelectorAll(
      ".chatbot-message--bot .chatbot-bubble",
    );
    return msgs.length > 0 ? msgs[msgs.length - 1].textContent : "";
  }

  function detectProduct(replyText) {
    const t = (replyText || "").toLowerCase();
    if (t.includes("soap") || t.includes("vehículo") || t.includes("vehiculo"))
      return "soap";
    if (t.includes("depósito") || t.includes("deposito")) return "deposit";
    return "soap";
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ---------------------------------------------------------------
  // Wrapper para llamar a los endpoints (formato JSON-RPC de Odoo)
  // ---------------------------------------------------------------
  async function callEndpoint(url, params) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: params || {},
      }),
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const json = await res.json();
    // Odoo envuelve el resultado en `result`
    return json.result;
  }

  // ---------------------------------------------------------------
  // Hook para tests / métricas
  // ---------------------------------------------------------------
  window.__chatbotMetrics = window.__chatbotMetrics || [];
  window.__chatbotExtras = {
    getSessionState: () => Object.assign({}, sessionState),
    getMetrics: () => window.__chatbotMetrics.slice(),
    clearMetrics: () => {
      window.__chatbotMetrics = [];
    },
  };
})();
