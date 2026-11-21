const answerAllBtn = document.getElementById("answer-all-btn");
const fillAllBtn = document.getElementById("fill-all-btn");
const container = document.getElementById("questions-container");
const errorSection = document.getElementById("error-section");
const errorText = document.getElementById("error-text");
const statusDot = document.getElementById("status");
const providerInfo = document.getElementById("provider-info");
const providerSelect = document.getElementById("provider-select");

let fields = [];
const stateByTab = new Map();
let activeTabId = null;
let renderVersion = 0;
let selectedProvider = "auto";
let backendProvider = "unknown";
let cvLoaded = false;
let lookingForLoaded = false;

function renderProviderInfo() {
  const suffix = selectedProvider === "auto" ? ` (${backendProvider})` : "";
  providerInfo.textContent = `Provider: ${selectedProvider}${suffix} | CV: ${cvLoaded ? "✓" : "✗"} Looking: ${lookingForLoaded ? "✓" : "✗"}`;
}

async function initProvider() {
  const data = await chrome.storage.local.get("provider");
  const valid = [...providerSelect.options].some(option => option.value === data.provider);
  selectedProvider = valid ? data.provider : "auto";
  providerSelect.value = selectedProvider;
  renderProviderInfo();
}

providerSelect.addEventListener("change", () => {
  selectedProvider = providerSelect.value;
  chrome.storage.local.set({ provider: selectedProvider });
  renderProviderInfo();
});

async function checkHealth() {
  const resp = await chrome.runtime.sendMessage({ action: "health" });
  if (resp && resp.status === "ok") {
    statusDot.className = "status-dot connected";
    statusDot.title = "Connected";
    backendProvider = resp.provider;
    cvLoaded = resp.cv_loaded;
    lookingForLoaded = resp.looking_for_loaded;
    renderProviderInfo();
    answerAllBtn.disabled = fields.length === 0;
  } else {
    statusDot.className = "status-dot disconnected";
    statusDot.title = "Disconnected";
    providerInfo.textContent = "Backend not reachable";
    answerAllBtn.disabled = true;
    fillAllBtn.disabled = true;
  }
}

async function fieldsForTab(tabId, force = false) {
  const cached = stateByTab.get(tabId);
  if (!force && cached) return cached;
  const detected = (await chrome.runtime.sendMessage({ action: "detect-all-questions", tabId })) || [];
  const previous = new Map((cached || []).map(f => [f.selector, f.answer]));
  detected.forEach(f => f.answer = previous.get(f.selector) || null);
  stateByTab.set(tabId, detected);
  return detected;
}

async function showTab(tabId, force = false) {
  if (tabId == null) return;
  const version = ++renderVersion;
  const nextFields = await fieldsForTab(tabId, force);
  if (version !== renderVersion) return;
  activeTabId = tabId;
  fields = nextFields;
  renderFields();
  answerAllBtn.disabled = fields.length === 0;
  fillAllBtn.disabled = !fields.some(f => f.answer && f.answer.type === "answer");
}

async function initActiveTab() {
  const tabId = await chrome.runtime.sendMessage({ action: "active-tab" });
  await showTab(tabId);
}

function renderFields() {
  container.innerHTML = "";
  if (fields.length === 0) {
    container.innerHTML = '<div class="question-item"><div class="a-text pending">No se detectaron campos de formulario con preguntas.</div></div>';
    return;
  }
  for (const f of fields) {
    const item = document.createElement("div");
    item.className = "question-item";
    item.id = `item-${f.id}`;

    const label = document.createElement("div");
    label.className = "q-label";
    label.textContent = `${fields.indexOf(f) + 1} of ${fields.length}`;
    item.appendChild(label);

    const qText = document.createElement("div");
    qText.className = "q-text";
    qText.textContent = f.question;
    item.appendChild(qText);

    const aText = document.createElement("div");
    aText.className = "a-text pending";
    if (f.answer) {
      aText.textContent = f.answer.text;
      aText.className = `a-text ${f.answer.type}`;
    } else {
      aText.textContent = "Esperando respuesta...";
    }
    item.appendChild(aText);

    container.appendChild(item);
  }
}

function updateFieldAnswer(index, result) {
  fields[index].answer = { type: result.type, text: result.text, provider: result.provider };
  const item = document.getElementById(`item-${fields[index].id}`);
  if (item) {
    const aText = item.querySelector(".a-text");
    aText.textContent = result.text;
    aText.className = `a-text ${result.type}`;
  }
}

async function answerAll() {
  answerAllBtn.disabled = true;
  answerAllBtn.textContent = "Pensando...";
  hideError();

  const questions = fields.map(f => f.question);
  const resp = await chrome.runtime.sendMessage({ action: "answer-batch", questions, provider: selectedProvider });

  answerAllBtn.disabled = false;
  answerAllBtn.textContent = "Answer All";

  if (resp && resp.answers) {
    for (const a of resp.answers) {
      updateFieldAnswer(a.index, a);
    }
  } else {
    showError("Error al obtener respuestas del servidor");
  }

  const hasAnswers = fields.some(f => f.answer && f.answer.type === "answer");
  fillAllBtn.disabled = !hasAnswers;
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "refresh-fields") showTab(msg.tabId, true);
});

chrome.tabs.onActivated.addListener(({ tabId }) => showTab(tabId));

answerAllBtn.addEventListener("click", answerAll);

fillAllBtn.addEventListener("click", () => {
  const fillable = fields.filter(f => f.answer && f.answer.type === "answer")
    .map(f => ({ selector: f.selector, text: f.answer.text }));
  chrome.runtime.sendMessage({ action: "fill-all-fields", fields: fillable, tabId: activeTabId });
  fillAllBtn.textContent = "Rellenado!";
  setTimeout(() => { fillAllBtn.textContent = "Fill All"; }, 2000);
});

function hideError() {
  errorSection.classList.add("hidden");
}

function showError(text) {
  errorText.textContent = text;
  errorSection.classList.remove("hidden");
}

initProvider();
checkHealth();
initActiveTab();
setInterval(checkHealth, 30000);
