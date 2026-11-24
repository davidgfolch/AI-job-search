const API_BASE = "http://127.0.0.1:8080";
const PANEL_PATH = "sidepanel/panel.html";
let enabledTabs = new Set();

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "ai-form-filler-answer",
    title: "Answer with AI",
    contexts: ["editable"],
  });
  chrome.sidePanel.setOptions({ enabled: false });
});

async function loadEnabledTabs() {
  if (enabledTabs.size) return enabledTabs;
  const data = await chrome.storage.session.get("panelTabs");
  enabledTabs = new Set(data.panelTabs || []);
  return enabledTabs;
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== "ai-form-filler-answer") return;
  enabledTabs.add(tab.id);
  chrome.storage.session.set({ panelTabs: [...enabledTabs] });
  chrome.sidePanel.setOptions({ tabId: tab.id, path: PANEL_PATH, enabled: true });
  chrome.sidePanel.open({ tabId: tab.id });
  chrome.storage.session.set({ formTabId: tab.id });
  chrome.tabs.sendMessage(tab.id, { action: "detect-question" });
  chrome.runtime.sendMessage({ action: "refresh-fields", tabId: tab.id });
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const tabs = await loadEnabledTabs();
  chrome.sidePanel.setOptions(tabs.has(tabId) ? { tabId, path: PANEL_PATH, enabled: true } : { tabId, enabled: false });
});

async function activeTabId() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs.length ? tabs[0].id : null;
}

async function formTabId() {
  const data = await chrome.storage.session.get("formTabId");
  return data.formTabId ?? await activeTabId();
}

async function sendToForm(message, explicitTabId) {
  const tabId = explicitTabId ?? await formTabId();
  if (tabId == null) return undefined;
  try {
    return await chrome.tabs.sendMessage(tabId, message);
  } catch (e) {
    return undefined;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "question-detected") {
    chrome.storage.session.set({ detectedQuestion: msg.question, fieldSelector: msg.selector });
  } else if (msg.action === "get-question") {
    chrome.storage.session.get(["detectedQuestion", "fieldSelector"]).then((data) => {
      sendResponse(data);
    });
    return true;
  } else if (msg.action === "active-tab") {
    activeTabId().then(sendResponse);
    return true;
  } else if (msg.action === "fill-field") {
    sendToForm({ action: "fill-answer", text: msg.text }, msg.tabId);
  } else if (msg.action === "fill-all-fields") {
    sendToForm({ action: "fill-all-fields", fields: msg.fields }, msg.tabId);
  } else if (msg.action === "answer-question") {
    callAnswerAPI(msg.question, msg.provider).then(sendResponse);
    return true;
  } else if (msg.action === "answer-batch") {
    callBatchAnswerAPI(msg.questions, msg.provider).then(sendResponse);
    return true;
  } else if (msg.action === "detect-all-questions") {
    sendToForm({ action: "detect-all-questions" }, msg.tabId).then(sendResponse);
    return true;
  } else if (msg.action === "follow-up") {
    callFollowUpAPI(msg.originalQuestion, msg.clarificationAnswer, msg.provider).then(sendResponse);
    return true;
  } else if (msg.action === "health") {
    callHealthAPI().then(sendResponse);
    return true;
  }
});

async function callBatchAnswerAPI(payload, provider) {
  const isFields = Array.isArray(payload) && payload.length > 0 && typeof payload[0] === "object";
  const body = isFields
    ? { fields: payload, provider: provider || "auto" }
    : { questions: payload, provider: provider || "auto" };
  try {
    const resp = await fetch(`${API_BASE}/api/answer/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await resp.json();
  } catch (e) {
    const count = Array.isArray(payload) ? payload.length : 0;
    return { answers: Array.from({ length: count }, (_, i) => ({ index: i, type: "error", text: `Connection error: ${e.message}`, provider: "none" })) };
  }
}

async function callAnswerAPI(question, provider) {
  try {
    const resp = await fetch(`${API_BASE}/api/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, provider: provider || "auto" }),
    });
    return await resp.json();
  } catch (e) {
    return { type: "error", text: `Connection error: ${e.message}`, provider: "none" };
  }
}

async function callFollowUpAPI(originalQuestion, clarificationAnswer, provider) {
  try {
    const resp = await fetch(`${API_BASE}/api/answer/follow-up`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_question: originalQuestion, clarification_answer: clarificationAnswer, provider: provider || "auto" }),
    });
    return await resp.json();
  } catch (e) {
    return { type: "error", text: `Connection error: ${e.message}`, provider: "none" };
  }
}

async function callHealthAPI() {
  try {
    const resp = await fetch(`${API_BASE}/api/health`);
    return await resp.json();
  } catch (e) {
    return { status: "error", detail: e.message };
  }
}
