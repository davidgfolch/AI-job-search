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
  const allNodes = () => [...fields, ...dialogs];
  const sandbox = {
    chrome: { runtime: { onMessage: { addListener(fn) { listeners.message = fn; } }, sendMessage: (msg) => sentMessages.push(msg) } },
    document: {
      querySelectorAll: (selector) => {
        if (isDialogSelector(selector)) return dialogs;
        const match = selector.match(/^input\[type="(radio|checkbox)"\]$/);
        if (match) return fields.filter(f => f.tagName === "INPUT" && f.type === match[1]);
        return fields.filter(f => typeof f.matches === "function" ? f.matches(selector) : true);
      },
      querySelector: (selector) => {
        const forMatch = selector.match(/^label\[for="(.+)"\]$/);
        if (forMatch) return fields.find(f => f.labelFor === forMatch[1]) || null;
        return fields.find(f => f.selector === selector) || null;
      },
      getElementById: (id) => allNodes().find(f => f.id === id) || null,
      contains: () => true,
      addEventListener: (type, fn) => { documentListeners[type] = fn; }
    },
    getComputedStyle: (node) => node.style || defaultStyle,
    Node: { ELEMENT_NODE: 1 },
    Event: class { constructor(type, options) { this.type = type; this.options = options; } },
    CSS: { escape: (v) => String(v) }
  };
  runInNewContext(source, sandbox);
  sandbox.document.querySelector = (selector) => {
    const forMatch = selector.match(/^label\[for="(.+)"\]$/);
    if (forMatch) return fields.find(f => f.labelFor === forMatch[1]) || null;
    return fields.find(f => f.selector === selector) || null;
  };
  return { ...sandbox, listeners, documentListeners, sentMessages };
}

function isDialogSelector(selector) {
  return selector.includes("dialog") || selector.includes("modal");
}

function field(overrides = {}) {
  const { placeholder = "", ariaLabel = "", ariaHidden = null, type = "text", checked = false, options = [], ...rest } = overrides;
  const node = {
    tagName: "INPUT", id: "", name: "", value: "", events: [], nodeType: 1, parentElement: null,
    type, checked, options,
    getClientRects: () => [{}],
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 100, height: 20 }),
    getAttribute: (name) => ({ placeholder, "aria-label": ariaLabel, "aria-hidden": ariaHidden })[name] ?? null,
    matches: (selector) => !selector || selector.includes(node.tagName.toLowerCase()) || selector.includes(`type="${node.type}"`),
    closest: () => null,
    contains: (other) => other === node,
    dispatchEvent(event) { this.events.push(event.type); },
    ...rest
  };
  return node;
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

test("radio group is detected once with options", () => {
  const r1 = field({ id: "r1", name: "auth", type: "radio", value: "yes", selector: "#r1", labelFor: "r1" });
  const r2 = field({ id: "r2", name: "auth", type: "radio", value: "no", selector: "#r2", labelFor: "r2" });
  const legend = { textContent: "Authorized to work?" };
  const fieldset = { querySelector: (sel) => sel === "legend" ? legend : null, closest: () => null, nodeType: 1, textContent: "" };
  r1.closest = (sel) => sel === "fieldset" ? fieldset : null;
  r2.closest = (sel) => sel === "fieldset" ? fieldset : null;
  const sandbox = load({ fields: [r1, r2] });
  sandbox.document.querySelector = (selector) => {
    if (selector === 'label[for="r1"]') return { textContent: "Yes" };
    if (selector === 'label[for="r2"]') return { textContent: "No" };
    return null;
  };
  const questions = sandbox.detectAllQuestions();
  assert.equal(questions.length, 1);
  assert.equal(questions[0].type, "radio");
  assert.equal(questions[0].question, "Authorized to work?");
  assert.equal(questions[0].options[0].label, "Yes");
  assert.equal(questions[0].options[1].label, "No");
});

test("radio group fill checks matching option", () => {
  const r1 = field({ id: "r1", name: "auth", type: "radio", value: "yes", selector: "#r1" });
  const r2 = field({ id: "r2", name: "auth", type: "radio", value: "no", selector: "#r2" });
  r1.closest = () => null; r2.closest = () => null;
  const sandbox = load({ fields: [r1, r2] });
  sandbox.document.querySelector = (selector) => {
    if (selector === 'label[for="r1"]') return { textContent: "Yes" };
    if (selector === 'label[for="r2"]') return { textContent: "No" };
    return [r1, r2].find(f => f.selector === selector) || null;
  };
  sandbox.listeners.message({ action: "fill-all-fields", fields: [{ selector: "#r1", text: "Yes" }] });
  assert.equal(r1.checked, true);
  assert.equal(r2.checked, false);
  assert.ok(r1.events.includes("change"));
});

test("checkbox group fills multiple answers", () => {
  const c1 = field({ id: "c1", name: "skills", type: "checkbox", value: "js", selector: "#c1" });
  const c2 = field({ id: "c2", name: "skills", type: "checkbox", value: "py", selector: "#c2" });
  const c3 = field({ id: "c3", name: "skills", type: "checkbox", value: "go", selector: "#c3" });
  [c1, c2, c3].forEach(c => { c.closest = () => null; });
  const sandbox = load({ fields: [c1, c2, c3] });
  sandbox.document.querySelector = (selector) => {
    if (selector === 'label[for="c1"]') return { textContent: "JavaScript" };
    if (selector === 'label[for="c2"]') return { textContent: "Python" };
    if (selector === 'label[for="c3"]') return { textContent: "Go" };
    return [c1, c2, c3].find(f => f.selector === selector) || null;
  };
  sandbox.listeners.message({ action: "fill-all-fields", fields: [{ selector: "#c1", text: "JavaScript, Go" }] });
  assert.equal(c1.checked, true);
  assert.equal(c2.checked, false);
  assert.equal(c3.checked, true);
});

test("select multiple fills selected options", () => {
  const opt1 = { text: "Java", value: "java", selected: false };
  const opt2 = { text: "Python", value: "python", selected: false };
  const opt3 = { text: "Go", value: "go", selected: false };
  const select = field({ tagName: "SELECT", multiple: true, options: [opt1, opt2, opt3], selector: "#skills" });
  const sandbox = load({ fields: [select] });
  sandbox.listeners.message({ action: "fill-all-fields", fields: [{ selector: "#skills", text: "Java, Go" }] });
  assert.equal(opt1.selected, true);
  assert.equal(opt2.selected, false);
  assert.equal(opt3.selected, true);
  assert.ok(select.events.includes("change"));
});
