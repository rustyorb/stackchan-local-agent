const form = document.querySelector("#settingsForm");
const statusEl = document.querySelector("#status");
const clearState = { llm: false, asr: false, tts: false };

function setStatus(text, state = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${state}`.trim();
}

function setField(name, value) {
  const field = form.elements[name];
  if (field) field.value = value ?? "";
}

function keyText(key) {
  return key?.present ? `Saved key present ${key.preview}` : "No key saved";
}

function applyConfig(config) {
  document.querySelector("#otaUrl").textContent = config.server.ota_url;
  document.querySelector("#websocketUrl").textContent = config.server.websocket_url;

  setField("agent_name", config.agent_name);
  setField("system_prompt", config.system_prompt);

  setField("llm_provider", config.llm.provider);
  setField("llm_base_url", config.llm.base_url);
  setField("llm_model", config.llm.model);
  setField("llm_temperature", config.llm.temperature);
  setField("llm_max_tokens", config.llm.max_tokens);

  setField("asr_provider", config.asr.provider);
  setField("asr_api_url", config.asr.api_url);
  setField("asr_model", config.asr.model);

  setField("tts_provider", config.tts.provider);
  setField("tts_voice", config.tts.voice);
  setField("tts_api_url", config.tts.api_url);
  setField("tts_model", config.tts.model);

  for (const name of ["llm_api_key", "asr_api_key", "tts_api_key"]) {
    form.elements[name].value = "";
  }
  clearState.llm = false;
  clearState.asr = false;
  clearState.tts = false;

  document.querySelector("#llmKeyHint").textContent = keyText(config.llm.api_key);
  document.querySelector("#asrKeyHint").textContent = keyText(config.asr.api_key);
  document.querySelector("#ttsKeyHint").textContent = keyText(config.tts.api_key);

  setStatus(config.restart_required ? "Restart required" : "Loaded", config.restart_required ? "warn" : "saved");
}

async function loadConfig() {
  setStatus("Loading");
  const response = await fetch("/api/local-config");
  if (!response.ok) throw new Error(`Load failed: ${response.status}`);
  applyConfig(await response.json());
}

async function saveConfig(event) {
  event.preventDefault();
  setStatus("Saving");
  const data = Object.fromEntries(new FormData(form).entries());
  data.clear_llm_api_key = clearState.llm;
  data.clear_asr_api_key = clearState.asr;
  data.clear_tts_api_key = clearState.tts;

  const response = await fetch("/api/local-config", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Save failed: ${response.status}`);
  applyConfig(await response.json());
  setStatus("Saved - restart required", "warn");
}

function presetOpenAI() {
  setField("llm_provider", "openai");
  setField("llm_base_url", "https://api.openai.com/v1");
  setField("llm_model", "gpt-5-mini");
  setField("asr_provider", "openai");
  setField("asr_api_url", "https://api.openai.com/v1/audio/transcriptions");
  setField("asr_model", "gpt-4o-mini-transcribe");
  setField("tts_provider", "edge");
  setField("tts_voice", "en-US-AriaNeural");
  setStatus("Unsaved");
}

function presetOpenRouter() {
  setField("llm_provider", "openrouter");
  setField("llm_base_url", "https://openrouter.ai/api/v1");
  setField("llm_model", "openai/gpt-4o-mini");
  setField("asr_provider", "openai");
  setField("asr_api_url", "https://api.openai.com/v1/audio/transcriptions");
  setField("tts_provider", "edge");
  setStatus("Unsaved");
}

function presetOllama() {
  setField("llm_provider", "ollama");
  setField("llm_base_url", "http://localhost:11434/v1");
  setField("llm_model", "llama3.2");
  setField("asr_provider", "openai");
  setField("tts_provider", "edge");
  setStatus("Unsaved");
}

form.addEventListener("submit", (event) => {
  saveConfig(event).catch((error) => {
    console.error(error);
    setStatus("Save error", "error");
  });
});

form.addEventListener("input", () => setStatus("Unsaved"));
document.querySelector("#reload").addEventListener("click", () => loadConfig().catch(console.error));
document.querySelector("#presetOpenAI").addEventListener("click", presetOpenAI);
document.querySelector("#presetOpenRouter").addEventListener("click", presetOpenRouter);
document.querySelector("#presetOllama").addEventListener("click", presetOllama);

document.querySelectorAll("[data-clear]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.clear;
    clearState[target] = true;
    form.elements[`${target}_api_key`].value = "";
    document.querySelector(`#${target}KeyHint`).textContent = "Key will be cleared on save";
    setStatus("Unsaved");
  });
});

loadConfig().catch((error) => {
  console.error(error);
  setStatus("Load error", "error");
});
