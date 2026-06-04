const API_BASE = "http://127.0.0.1:8080";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "ai-form-filler-answer",
    title: "Answer with AI",
    contexts: ["editable"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "ai-form-filler-answer") {
    chrome.storage.session.set({ activeField: { tabId: tab.id, frameId: info.frameId } });
    chrome.sidePanel.open({ tabId: tab.id });
    chrome.tabs.sendMessage(tab.id, { action: "detect-question" }, { frameId: info.frameId });
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "question-detected") {
    chrome.storage.session.set({ detectedQuestion: msg.question, fieldSelector: msg.selector });
  } else if (msg.action === "get-question") {
    chrome.storage.session.get(["detectedQuestion", "fieldSelector"]).then((data) => {
      sendResponse(data);
    });
    return true;
  } else if (msg.action === "fill-field") {
    chrome.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "fill-answer", text: msg.text });
    });
  } else if (msg.action === "fill-all-fields") {
    chrome.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "fill-all-fields", fields: msg.fields });
    });
  } else if (msg.action === "answer-question") {
    callAnswerAPI(msg.question, msg.provider).then(sendResponse);
    return true;
  } else if (msg.action === "answer-batch") {
    callBatchAnswerAPI(msg.questions, msg.provider).then(sendResponse);
    return true;
  } else if (msg.action === "detect-all-questions") {
    chrome.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "detect-all-questions" }).then(sendResponse);
    });
    return true;
  } else if (msg.action === "follow-up") {
    callFollowUpAPI(msg.originalQuestion, msg.clarificationAnswer).then(sendResponse);
    return true;
  } else if (msg.action === "health") {
    callHealthAPI().then(sendResponse);
    return true;
  }
});

async function callBatchAnswerAPI(questions, provider) {
  try {
    const resp = await fetch(`${API_BASE}/api/answer/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ questions, provider: provider || "auto" }),
    });
    return await resp.json();
  } catch (e) {
    return { answers: questions.map((_, i) => ({ index: i, type: "error", text: `Connection error: ${e.message}`, provider: "none" })) };
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

async function callFollowUpAPI(originalQuestion, clarificationAnswer) {
  try {
    const resp = await fetch(`${API_BASE}/api/answer/follow-up`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_question: originalQuestion, clarification_answer: clarificationAnswer }),
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
