const form = document.querySelector("#configForm");
const statusEl = document.querySelector("#saveStatus");
const keyHint = document.querySelector("#keyHint");
const clearKey = document.querySelector("#clearKey");
const reloadConfig = document.querySelector("#reloadConfig");
const openAiPreset = document.querySelector("#openAiPreset");

let clearApiKey = false;

function setStatus(text, state = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${state}`.trim();
}

function setField(name, value) {
  const field = form.elements[name];
  if (field) field.value = value ?? "";
}

function applyConfig(config) {
  for (const name of [
    "provider",
    "api_base_url",
    "model",
    "stt_model",
    "tts_model",
    "voice",
    "agent_name",
    "system_prompt",
  ]) {
    setField(name, config[name]);
  }
  form.elements.api_key.value = "";
  clearApiKey = false;
  keyHint.textContent = config.api_key_present
    ? `Saved key present ${config.api_key_preview}`
    : "No key saved";
  setStatus("Loaded", "saved");
}

async function loadConfig() {
  setStatus("Loading");
  const response = await fetch("/api/config");
  if (!response.ok) throw new Error(`Load failed: ${response.status}`);
  applyConfig(await response.json());
}

async function saveConfig(event) {
  event.preventDefault();
  setStatus("Saving");
  const data = Object.fromEntries(new FormData(form).entries());
  data.clear_api_key = clearApiKey;
  const response = await fetch("/api/config", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Save failed: ${response.status}`);
  applyConfig(await response.json());
  setStatus("Saved", "saved");
}

form.addEventListener("submit", (event) => {
  saveConfig(event).catch((error) => {
    console.error(error);
    setStatus("Save error", "error");
  });
});

clearKey.addEventListener("click", () => {
  clearApiKey = true;
  form.elements.api_key.value = "";
  keyHint.textContent = "Key will be cleared on save";
  setStatus("Unsaved");
});

reloadConfig.addEventListener("click", () => {
  loadConfig().catch((error) => {
    console.error(error);
    setStatus("Load error", "error");
  });
});

openAiPreset.addEventListener("click", () => {
  setField("provider", "openai");
  setField("api_base_url", "https://api.openai.com/v1");
  setField("model", "gpt-5-mini");
  setField("stt_model", "gpt-4o-mini-transcribe");
  setField("tts_model", "gpt-4o-mini-tts");
  setField("voice", "marin");
  setStatus("Unsaved");
});

form.addEventListener("input", () => setStatus("Unsaved"));

loadConfig().catch((error) => {
  console.error(error);
  setStatus("Load error", "error");
});
