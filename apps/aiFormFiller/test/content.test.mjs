import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../extension/content.js", import.meta.url), "utf8");
const defaultStyle = { display: "block", visibility: "visible", opacity: "1" };

function load({ fields = [], dialogs = [] } = {}) {
  const listeners = {};
  const documentListeners = {};
  const sentMessages = [];
  const sandbox = {
    chrome: { runtime: { onMessage: { addListener(fn) { listeners.message = fn; } }, sendMessage: (msg) => sentMessages.push(msg) } },
    document: {
      querySelectorAll: (selector) => isDialogSelector(selector) ? dialogs : fields,
      querySelector: () => null,
      getElementById: () => null,
      contains: () => true,
      addEventListener: (type, fn) => { documentListeners[type] = fn; }
    },
    getComputedStyle: (node) => node.style || defaultStyle,
    Node: { ELEMENT_NODE: 1 },
    Event: class { constructor(type, options) { this.type = type; this.options = options; } }
  };
  runInNewContext(source, sandbox);
  sandbox.document.querySelector = (selector) => fields.find(f => f.selector === selector) || null;
  return { ...sandbox, listeners, documentListeners, sentMessages };
}

function isDialogSelector(selector) {
  return selector.includes("dialog") || selector.includes("modal");
}

function field(overrides = {}) {
  const { placeholder = "", ariaLabel = "", ariaHidden = null, ...rest } = overrides;
  const field = {
    tagName: "INPUT", id: "", name: "", value: "", events: [], nodeType: 1, parentElement: null,
    getClientRects: () => [{}],
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 20 }),
    getAttribute: (name) => ({ placeholder, "aria-label": ariaLabel, "aria-hidden": ariaHidden })[name] ?? null,
    matches: () => true,
    closest: () => null,
    contains: (other) => other === field,
    dispatchEvent(event) { this.events.push(event.type); },
    ...rest
  };
  return field;
}

function dialog(children, overrides = {}) {
  return {
    tagName: "DIV", id: "", name: "", nodeType: 1, parentElement: null,
    getClientRects: () => [{}],
    getAttribute: () => null,
    closest: () => null,
    querySelectorAll: () => children,
    contains: (el) => children.includes(el),
    ...overrides
  };
}

test("free-text answers never select a language option", () => {
  const { fillField } = load();
  const select = field({ tagName: "SELECT", options: [
    { text: "ar", value: "ar" }, { text: "en", value: "en" }, { text: "es", value: "es" }
  ] });
  fillField(select, "Trabajo en áreas de desarrollo");
  assert.equal(select.value, "");
  assert.deepEqual(select.events, []);
});

test("exact option answers still fill selects", () => {
  const { fillField } = load();
  const select = field({ tagName: "SELECT", options: [{ text: "Sí", value: "yes" }, { text: "No", value: "no" }] });
  fillField(select, "  sí  ");
  assert.equal(select.value, "yes");
  assert.deepEqual(select.events, ["input", "change"]);
});

test("site language switchers are not detected as form questions", () => {
  const sandbox = load({ fields: [field({ id: "lang", placeholder: "Language" })] });
  assert.equal(sandbox.detectAllQuestions().length, 0);
});

test("site language switchers are never filled", () => {
  const { fillField } = load();
  const select = field({ name: "site_locale", tagName: "SELECT", options: [
    { text: "English", value: "en" }, { text: "العربية", value: "ar" }
  ] });
  fillField(select, "العربية");
  assert.equal(select.value, "");
  assert.deepEqual(select.events, []);
});

test("text inputs and textareas are still filled", () => {
  const { fillField } = load();
  const textarea = field({ tagName: "TEXTAREA" });
  fillField(textarea, "Mi respuesta");
  assert.equal(textarea.value, "Mi respuesta");
  assert.deepEqual(textarea.events, ["input", "change"]);
});

test("hidden and collapsed fields are not detected", () => {
  const hidden = field({ placeholder: "Hidden", getClientRects: () => [] });
  const collapsed = field({ placeholder: "Collapsed", style: { display: "none", visibility: "visible", opacity: "1" } });
  const visible = field({ placeholder: "Visible" });
  const sandbox = load({ fields: [hidden, collapsed, visible] });
  const questions = sandbox.detectAllQuestions();
  assert.equal(questions.length, 1);
  assert.equal(questions[0].question, "Visible");
});

test("only fields in the active dialog are detected", () => {
  const behind = field({ placeholder: "Behind modal" });
  const inside = field({ placeholder: "Modal question" });
  const sandbox = load({ fields: [behind], dialogs: [dialog([inside])] });
  const questions = sandbox.detectAllQuestions();
  assert.equal(questions.length, 1);
  assert.equal(questions[0].question, "Modal question");
});

test("fields covered by an overlay are not detected or filled", () => {
  const covered = field({ placeholder: "Covered", selector: "#covered" });
  const free = field({ placeholder: "Free", selector: "#free" });
  const sandbox = load({ fields: [covered, free] });
  const overlay = {};
  sandbox.document.elementFromPoint = () => overlay;
  covered.getBoundingClientRect = () => ({ left: 200, top: 200, width: 100, height: 20 });
  free.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 20 });
  free.contains = () => true;
  assert.equal(sandbox.detectAllQuestions().map(q => q.question).join(","), "Free");
  sandbox.listeners.message({ action: "fill-all-fields", fields: [
    { selector: "#covered", text: "Wrong" }, { selector: "#free", text: "Right" }
  ] });
  assert.equal(covered.value, "");
  assert.equal(free.value, "Right");
});

test("fill all ignores fields outside the active dialog", () => {
  const behind = field({ selector: "#behind" });
  const inside = field({ selector: "#inside" });
  const sandbox = load({ fields: [behind, inside], dialogs: [dialog([inside])] });
  sandbox.listeners.message({ action: "fill-all-fields", fields: [
    { selector: "#behind", text: "Wrong" }, { selector: "#inside", text: "Right" }
  ] });
  assert.equal(behind.value, "");
  assert.equal(inside.value, "Right");
});

test("right-clicked field wins over document.activeElement", () => {
  const wrong = field({ placeholder: "Wrong" });
  const right = field({ placeholder: "Right" });
  const sandbox = load({ fields: [wrong, right] });
  sandbox.document.activeElement = wrong;
  sandbox.documentListeners.contextmenu({ target: { closest: () => right } });
  sandbox.listeners.message({ action: "detect-question" });
  assert.equal(sandbox.sentMessages.at(-1).question, "Right");
});

test("fill-answer targets the remembered field", () => {
  const wrong = field({ placeholder: "Wrong" });
  const right = field({ placeholder: "Right" });
  const sandbox = load({ fields: [wrong, right] });
  sandbox.document.activeElement = wrong;
  sandbox.documentListeners.focusin({ target: { closest: () => right } });
  sandbox.listeners.message({ action: "fill-answer", text: "Mi respuesta" });
  assert.equal(right.value, "Mi respuesta");
  assert.equal(wrong.value, "");
});

test("aria-label is used when the question has no label element", () => {
  const question = "¿Cuántos años de experiencia aportas en Java Microservicios?";
  const input = field({ ariaLabel: question });
  const sandbox = load({ fields: [input] });
  assert.equal(sandbox.detectAllQuestions().map(q => q.question).join(","), question);
});

test("question text outside the input parent is found", () => {
  const question = { textContent: "¿Cuántos años de experiencia aportas en AWS?" };
  const wrapper = { textContent: "", children: [], previousElementSibling: question, parentElement: null };
  const input = field({ parentElement: wrapper, previousElementSibling: null });
  const sandbox = load({ fields: [input] });
  assert.equal(sandbox.detectAllQuestions().map(q => q.question).join(","), question.textContent);
});
