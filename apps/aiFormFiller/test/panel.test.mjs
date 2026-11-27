import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../extension/sidepanel/panel.js", import.meta.url), "utf8");
const ids = ["answer-all-btn", "fill-all-btn", "questions-container", "error-section", "error-text", "status", "provider-info", "provider-select"];

function element(id) {
  const el = {
    id, textContent: "", className: "", disabled: false, value: "", options: [], listeners: {}, children: [],
    classList: { add() {}, remove() {} },
    addEventListener(type, fn) { this.listeners[type] = fn; },
    appendChild(child) { this.children.push(child); },
    querySelector(selector) {
      const cls = selector.replace(".", "");
      return this.children.find(child => child.className && child.className.split(" ").includes(cls)) || null;
    }
  };
  Object.defineProperty(el, "innerHTML", {
    get() { return el._html || ""; },
    set(value) { el._html = value; if (value === "") el.children = []; }
  });
  return el;
}

function texts(elements, className) {
  return elements["questions-container"].children.map(item =>
    item.children.find(child => child.className && child.className.split(" ").includes(className))?.textContent);
}

function load({ storedProvider = "auto", backendProvider = "openrouter", fieldsByTab = {}, activeTabId = 1 } = {}) {
  const elements = Object.fromEntries(ids.map(id => [id, element(id)]));
  elements["provider-select"].options = ["auto", "local", "openrouter", "openai"].map(value => ({ value }));
  const sent = [];
  const writes = [];
  const messageListeners = [];
  const activationListeners = [];
  const responses = { ...fieldsByTab };
  let stored = { provider: storedProvider };
  const sandbox = {
    document: {
      getElementById: id => elements[id] || elements["questions-container"].children.find(child => child.id === id) || null,
      createElement: tag => element(tag)
    },
    chrome: {
      runtime: {
        onMessage: { addListener(fn) { messageListeners.push(fn); } },
        sendMessage: msg => {
          sent.push(msg);
          let response;
          if (msg.action === "health") response = { status: "ok", provider: backendProvider, cv_loaded: true, looking_for_loaded: false };
          else if (msg.action === "active-tab") response = activeTabId;
          else if (msg.action === "detect-all-questions") response = responses[msg.tabId] || [];
          else if (msg.action === "answer-batch") response = { answers: msg.questions.map((q, i) => ({ index: i, type: "answer", text: `A-${typeof q === "string" ? q : q.question}`, provider: "openrouter" })) };
          return Promise.resolve(response);
        }
      },
      storage: { local: {
        get: () => Promise.resolve(stored),
        set: value => { stored = { ...stored, ...value }; writes.push(value); }
      } },
      tabs: { onActivated: { addListener(fn) { activationListeners.push(fn); } } }
    },
    setInterval: () => 0,
    setTimeout: () => 0,
    console
  };
  runInNewContext(source, sandbox);
  return {
    elements, sent, writes, messageListeners,
    setFields: (tabId, value) => { responses[tabId] = value; },
    activate: tabId => activationListeners[0]({ tabId }),
    flush: () => new Promise(resolve => setImmediate(resolve))
  };
}

test("selector restores the persisted provider", async () => {
  const { elements, flush } = load({ storedProvider: "openrouter" });
  await flush();
  assert.equal(elements["provider-select"].value, "openrouter");
  assert.match(elements["provider-info"].textContent, /Provider: openrouter/);
});

test("auto shows the backend provider from health", async () => {
  const { elements, flush } = load({ backendProvider: "openrouter" });
  await flush();
  assert.match(elements["provider-info"].textContent, /Provider: auto \(openrouter\)/);
});

test("changing the selector persists and shows the new provider", async () => {
  const { elements, writes, flush } = load();
  await flush();
  elements["provider-select"].value = "local";
  elements["provider-select"].listeners.change();
  assert.equal(writes.length, 1);
  assert.equal(writes[0].provider, "local");
  assert.match(elements["provider-info"].textContent, /Provider: local/);
});

test("answer all sends the selected provider", async () => {
  const { elements, sent, flush } = load({ storedProvider: "openrouter", fieldsByTab: { 1: [{ id: "1", question: "Q?", selector: "#q" }] } });
  await flush();
  elements["answer-all-btn"].listeners.click();
  await flush();
  assert.equal(sent.find(msg => msg.action === "answer-batch").provider, "openrouter");
});

test("refresh-fields forces a re-detect on the targeted tab", async () => {
  const { sent, messageListeners, setFields, flush } = load({ fieldsByTab: { 1: [{ id: "1", question: "Form A", selector: "#a" }] } });
  await flush();
  setFields(42, [{ id: "1", question: "Form B", selector: "#b" }]);
  messageListeners[0]({ action: "refresh-fields", tabId: 42 });
  await flush();
  const detects = sent.filter(msg => msg.action === "detect-all-questions");
  assert.equal(detects.length, 2);
  assert.equal(detects[1].tabId, 42);
});

test("switching tabs keeps each tab's questions and answers", async () => {
  const { elements, activate, flush } = load({ fieldsByTab: {
    1: [{ id: "1", question: "Form A", selector: "#a" }],
    2: [{ id: "1", question: "Form B", selector: "#b" }]
  } });
  await flush();
  assert.deepEqual(texts(elements, "q-text"), ["Form A"]);
  elements["answer-all-btn"].listeners.click();
  await flush();
  assert.deepEqual(texts(elements, "a-text"), ["A-Form A"]);
  activate(2);
  await flush();
  assert.deepEqual(texts(elements, "q-text"), ["Form B"]);
  assert.deepEqual(texts(elements, "a-text"), ["Esperando respuesta..."]);
  activate(1);
  await flush();
  assert.deepEqual(texts(elements, "q-text"), ["Form A"]);
  assert.deepEqual(texts(elements, "a-text"), ["A-Form A"]);
});

test("fill all targets the displayed tab", async () => {
  const { elements, sent, activate, flush } = load({ fieldsByTab: {
    1: [{ id: "1", question: "A", selector: "#a" }],
    2: [{ id: "1", question: "B", selector: "#b" }]
  } });
  await flush();
  elements["answer-all-btn"].listeners.click();
  await flush();
  activate(2);
  await flush();
  elements["answer-all-btn"].listeners.click();
  await flush();
  elements["fill-all-btn"].listeners.click();
  await flush();
  assert.equal(sent.find(msg => msg.action === "fill-all-fields").tabId, 2);
});
