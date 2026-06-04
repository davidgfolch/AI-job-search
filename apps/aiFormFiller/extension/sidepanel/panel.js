const answerAllBtn = document.getElementById("answer-all-btn");
const fillAllBtn = document.getElementById("fill-all-btn");
const container = document.getElementById("questions-container");
const errorSection = document.getElementById("error-section");
const errorText = document.getElementById("error-text");
const statusDot = document.getElementById("status");
const providerInfo = document.getElementById("provider-info");

let fields = [];

async function checkHealth() {
  const resp = await chrome.runtime.sendMessage({ action: "health" });
  if (resp && resp.status === "ok") {
    statusDot.className = "status-dot connected";
    statusDot.title = "Connected";
    providerInfo.textContent = `Provider: ${resp.provider} | CV: ${resp.cv_loaded ? "✓" : "✗"} Looking: ${resp.looking_for_loaded ? "✓" : "✗"}`;
    answerAllBtn.disabled = fields.length === 0;
  } else {
    statusDot.className = "status-dot disconnected";
    statusDot.title = "Disconnected";
    providerInfo.textContent = "Backend not reachable";
    answerAllBtn.disabled = true;
    fillAllBtn.disabled = true;
  }
}

async function detectAllFields() {
  fields = await chrome.runtime.sendMessage({ action: "detect-all-questions" });
  fields = fields || [];
  fields.forEach(f => f.answer = null);
  renderFields();
  answerAllBtn.disabled = fields.length === 0;
  fillAllBtn.disabled = true;
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
  const resp = await chrome.runtime.sendMessage({ action: "answer-batch", questions, provider: "auto" });

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

answerAllBtn.addEventListener("click", answerAll);

fillAllBtn.addEventListener("click", () => {
  const fillable = fields.filter(f => f.answer && f.answer.type === "answer")
    .map(f => ({ selector: f.selector, text: f.answer.text }));
  chrome.runtime.sendMessage({ action: "fill-all-fields", fields: fillable });
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

checkHealth();
detectAllFields();
setInterval(checkHealth, 30000);
