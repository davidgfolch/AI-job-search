import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../extension/background.js", import.meta.url), "utf8");

function load({ activeTabId = 1, stored = {}, panelTabs = [], fetchImpl } = {}) {
  const listeners = { installed: [], activation: [], contextMenu: [], message: [] };
  const sent = [];
  const tabMessages = [];
  const panelCalls = [];
  const fetchCalls = [];
  let session = { panelTabs, ...stored };
  const sandbox = {
    chrome: {
      runtime: {
        onInstalled: { addListener(fn) { listeners.installed.push(fn); } },
        onMessage: { addListener(fn) { listeners.message.push(fn); } },
        sendMessage: msg => { sent.push(msg); return Promise.resolve(); }
      },
      contextMenus: {
        create() {},
        onClicked: { addListener(fn) { listeners.contextMenu.push(fn); } }
      },
      storage: { session: {
        get: key => Promise.resolve(key === undefined ? { ...session } : { [key]: session[key] }),
        set: value => { session = { ...session, ...value }; return Promise.resolve(); }
      } },
      tabs: {
        query: () => Promise.resolve([{ id: activeTabId }]),
        onActivated: { addListener(fn) { listeners.activation.push(fn); } },
        sendMessage: (tabId, msg) => { tabMessages.push({ tabId, msg }); return Promise.resolve("ok"); }
      },
      sidePanel: {
        setOptions: options => { panelCalls.push({ method: "setOptions", options }); return Promise.resolve(); },
        open: options => { panelCalls.push({ method: "open", options }); return Promise.resolve(); }
      }
    },
    fetch: async (url, options) => {
      fetchCalls.push({ url, options });
      if (fetchImpl) return fetchImpl(url, options);
      return { json: async () => ({}) };
    },
    console
  };
  runInNewContext(source, sandbox);
  return { listeners, sent, tabMessages, panelCalls, fetchCalls, session: () => session };
}

async function dispatch(app, msg) {
  app.listeners.message[0](msg, {}, () => {});
  await new Promise(resolve => setImmediate(resolve));
}

test("install disables the panel globally so only opted-in tabs show it", async () => {
  const app = load();
  await app.listeners.installed[0]();
  assert.ok(app.panelCalls.some(call => call.method === "setOptions" && call.options.enabled === false && call.options.tabId === undefined));
});

test("right-click enables the tab-specific panel before opening it", async () => {
  const app = load();
  app.listeners.contextMenu[0]({ menuItemId: "ai-form-filler-answer" }, { id: 42 });
  const enable = app.panelCalls.find(call => call.method === "setOptions" && call.options.tabId === 42);
  const open = app.panelCalls.find(call => call.method === "open");
  assert.equal(enable.options.enabled, true);
  assert.equal(enable.options.path, "sidepanel/panel.html");
  assert.equal(open.options.tabId, 42);
  assert.ok(app.panelCalls.indexOf(enable) < app.panelCalls.indexOf(open));
  assert.equal(app.session().panelTabs[0], 42);
});

test("switching to a tab without a panel disables it", async () => {
  const app = load({ panelTabs: [42] });
  await app.listeners.activation[0]({ tabId: 7 });
  const options = app.panelCalls.at(-1).options;
  assert.equal(options.tabId, 7);
  assert.equal(options.enabled, false);
});

test("switching back to an opted-in tab re-enables its panel", async () => {
  const app = load({ panelTabs: [42] });
  await app.listeners.activation[0]({ tabId: 42 });
  const options = app.panelCalls.at(-1).options;
  assert.equal(options.tabId, 42);
  assert.equal(options.enabled, true);
  assert.equal(options.path, "sidepanel/panel.html");
});

test("right-click records the tab and asks the panel to refresh", async () => {
  const app = load();
  await app.listeners.contextMenu[0]({ menuItemId: "ai-form-filler-answer" }, { id: 42 });
  assert.equal(app.session().formTabId, 42);
  const refresh = app.sent.find(msg => msg.action === "refresh-fields");
  assert.ok(refresh);
  assert.equal(refresh.tabId, 42);
  assert.ok(app.tabMessages.some(m => m.tabId === 42 && m.msg.action === "detect-question"));
});

test("right-click in another tab replaces the tracked tab", async () => {
  const app = load();
  await app.listeners.contextMenu[0]({ menuItemId: "ai-form-filler-answer" }, { id: 42 });
  await app.listeners.contextMenu[0]({ menuItemId: "ai-form-filler-answer" }, { id: 99 });
  assert.equal(app.session().formTabId, 99);
});

test("active-tab reports the current tab to the panel", async () => {
  const app = load({ activeTabId: 7 });
  let response;
  app.listeners.message[0]({ action: "active-tab" }, {}, value => { response = value; });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(response, 7);
});

test("detect-all-questions targets the tracked tab, not the active tab", async () => {
  const app = load({ activeTabId: 7, stored: { formTabId: 42 } });
  await dispatch(app, { action: "detect-all-questions" });
  const detects = app.tabMessages.filter(m => m.msg.action === "detect-all-questions");
  assert.equal(detects.length, 1);
  assert.equal(detects[0].tabId, 42);
});

test("explicit tab id wins over stored and active tab", async () => {
  const app = load({ activeTabId: 7, stored: { formTabId: 42 } });
  await dispatch(app, { action: "detect-all-questions", tabId: 99 });
  const detects = app.tabMessages.filter(m => m.msg.action === "detect-all-questions");
  assert.equal(detects.length, 1);
  assert.equal(detects[0].tabId, 99);
});

test("fill operations target the tracked tab", async () => {
  const app = load({ activeTabId: 7, stored: { formTabId: 42 } });
  await dispatch(app, { action: "fill-all-fields", fields: [] });
  assert.equal(app.tabMessages[0].tabId, 42);
  assert.equal(app.tabMessages[0].msg.action, "fill-all-fields");
});

test("fill all uses the displayed tab when provided", async () => {
  const app = load({ activeTabId: 7, stored: { formTabId: 42 } });
  await dispatch(app, { action: "fill-all-fields", fields: [], tabId: 99 });
  assert.equal(app.tabMessages[0].tabId, 99);
});

test("falls back to the active tab when no tab was tracked", async () => {
  const app = load({ activeTabId: 7 });
  await dispatch(app, { action: "detect-all-questions" });
  assert.equal(app.tabMessages[0].tabId, 7);
});

test("answer-batch forwards field metadata payload", async () => {
  const app = load({ fetchImpl: async () => ({ json: async () => ({ answers: [] }) }) });
  let response;
  app.listeners.message[0]({ action: "answer-batch", questions: [{ question: "Q?", type: "radio", options: ["Yes"] }], provider: "auto" }, {}, value => { response = value; });
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(response, { answers: [] });
  const body = JSON.parse(app.fetchCalls[0].options.body);
  assert.deepEqual(body.fields, [{ question: "Q?", type: "radio", options: ["Yes"] }]);
  assert.equal(body.provider, "auto");
});
