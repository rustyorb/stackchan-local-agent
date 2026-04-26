const form = document.querySelector("#settingsForm");
const statusEl = document.querySelector("#status");
const clearState = { llm: false, asr: false, tts: false };
let voicePreviewUrl = "";

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

function fillDatalist(id, values) {
  const datalist = document.querySelector(id);
  datalist.replaceChildren();
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    datalist.append(option);
  }
}

function ensureVoiceOption(voice) {
  const select = form.elements.tts_voice;
  if (![...select.options].some((option) => option.value === voice)) {
    const option = document.createElement("option");
    option.value = voice;
    option.textContent = voice;
    select.append(option);
  }
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
  ensureVoiceOption(config.tts.voice);
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

  setStatus(config.restart_required ? "Saved - restart voice server to activate" : "Loaded", config.restart_required ? "warn" : "saved");
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
  await refreshProviderLists(false);
  setStatus("Saved - restart voice server to activate", "warn");
}

async function fetchModels(provider, datalistId, fieldName, announce = true) {
  if (announce) setStatus(`Fetching ${provider.toUpperCase()} models`);
  const response = await fetch(`/api/provider-models/${provider}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Model fetch failed: ${response.status}`);
  fillDatalist(datalistId, payload.models || []);
  if (!form.elements[fieldName].value && payload.models?.length) {
    setField(fieldName, payload.models[0]);
  }
  if (announce) setStatus(`${payload.models?.length || 0} ${provider.toUpperCase()} models loaded`, "saved");
  return payload.models || [];
}

async function fetchVoices(announce = true) {
  if (announce) setStatus("Fetching voices");
  const current = form.elements.tts_voice.value;
  const response = await fetch("/api/tts-voices/edge");
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Voice fetch failed: ${response.status}`);

  const select = form.elements.tts_voice;
  select.replaceChildren();
  for (const voice of payload.voices || []) {
    const option = document.createElement("option");
    option.value = voice.name;
    option.textContent = `${voice.name} ${voice.gender ? `(${voice.gender})` : ""}`;
    select.append(option);
  }
  if (current) {
    ensureVoiceOption(current);
    setField("tts_voice", current);
  }
  if (announce) setStatus(`${payload.voices?.length || 0} voices loaded`, "saved");
  return payload.voices || [];
}

async function refreshProviderLists(announce = true) {
  const tasks = [
    fetchModels("llm", "#llmModels", "llm_model", false),
    fetchModels("asr", "#asrModels", "asr_model", false),
    fetchVoices(false),
  ];
  const results = await Promise.allSettled(tasks);
  const failures = results.filter((result) => result.status === "rejected");
  if (failures.length && announce) {
    setStatus("Some lists failed to load", "error");
    console.error(failures.map((failure) => failure.reason));
    return;
  }
  if (announce) setStatus("Provider lists refreshed", "saved");
}

async function playVoicePreview() {
  setStatus("Generating voice preview");
  const response = await fetch("/api/tts-preview/edge", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      voice: form.elements.tts_voice.value,
      text: document.querySelector("#voicePreviewText").value,
    }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || `Preview failed: ${response.status}`);
  }
  const blob = await response.blob();
  if (voicePreviewUrl) URL.revokeObjectURL(voicePreviewUrl);
  voicePreviewUrl = URL.createObjectURL(blob);
  const audio = document.querySelector("#voicePreview");
  audio.src = voicePreviewUrl;
  await audio.play();
  setStatus("Preview playing", "saved");
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
document.querySelector("#fetchLlmModels").addEventListener("click", () => fetchModels("llm", "#llmModels", "llm_model").catch((error) => {
  console.error(error);
  setStatus("Model fetch error", "error");
}));
document.querySelector("#fetchAsrModels").addEventListener("click", () => fetchModels("asr", "#asrModels", "asr_model").catch((error) => {
  console.error(error);
  setStatus("Model fetch error", "error");
}));
document.querySelector("#fetchVoices").addEventListener("click", () => fetchVoices().catch((error) => {
  console.error(error);
  setStatus("Voice fetch error", "error");
}));
document.querySelector("#playVoice").addEventListener("click", () => playVoicePreview().catch((error) => {
  console.error(error);
  setStatus("Preview error", "error");
}));
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

loadConfig()
  .then(() => refreshProviderLists(false).catch(console.error))
  .catch((error) => {
    console.error(error);
    setStatus("Load error", "error");
  });
