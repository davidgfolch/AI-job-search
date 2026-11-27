const SITE_CONTROL = /(^|[-_:\s])(lang|language|locale|idioma|theme|moneda|currency)([-_:\s]|$)/i;
const LANGUAGE_CODES = new Set(["ar", "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko", "nl", "pl", "sv", "tr"]);
const FIELD_SELECTOR = "input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=file]):not([type=image]), textarea, select";
const DIALOG_SELECTOR = 'dialog[open], [role="dialog"], [role="alertdialog"], [aria-modal="true"], .modal';
const GROUP_SELECTOR = 'dialog, [role="dialog"], [aria-modal="true"], form, fieldset';

function isSiteControl(el) {
  const label = [el.id, el.name, el.getAttribute("aria-label"), el.getAttribute("placeholder")].filter(Boolean).join(" ");
  if (SITE_CONTROL.test(label)) return true;
  if (el.tagName !== "SELECT") return false;
  const values = Array.from(el.options).map(o => String(o.value).trim().toLowerCase());
  return values.length > 1 && values.every(v => LANGUAGE_CODES.has(v));
}
function isAvailable(el) {
  if (el.disabled || el.readOnly || isSiteControl(el)) return false;
  if (el.getAttribute("aria-hidden") === "true" || el.closest("[inert]")) return false;
  if (!el.getClientRects || el.getClientRects().length === 0) return false;
  for (let node = el; node && node.nodeType === Node.ELEMENT_NODE; node = node.parentElement) {
    const style = getComputedStyle(node);
    if (!style || style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) return false;
  }
  return true;
}
function isReachable(el) {
  if (!el.getBoundingClientRect) return true;
  const rect = el.getBoundingClientRect();
  if (!rect.width || !rect.height) return false;
  const hit = document.elementFromPoint ? document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2) : null;
  if (!hit || el === hit || el.contains(hit) || (hit.contains && hit.contains(el))) return true;
  const hitGroup = hit.closest ? hit.closest(GROUP_SELECTOR) : null;
  const elGroup = el.closest ? el.closest(GROUP_SELECTOR) : null;
  return Boolean(hitGroup && hitGroup === elGroup);
}
function activeDialog() {
  const dialogs = Array.from(document.querySelectorAll(DIALOG_SELECTOR)).filter(isAvailable);
  return dialogs.length ? dialogs[dialogs.length - 1] : document;
}
function fieldGroup(el) {
  return el.closest(GROUP_SELECTOR) || document.body;
}
function questionScope(el) {
  return el.closest(DIALOG_SELECTOR) || el.closest(GROUP_SELECTOR) || document;
}
function targetField(anchor) {
  if (!anchor) return null;
  if (anchor.matches && anchor.matches(FIELD_SELECTOR)) return anchor;
  if (anchor.closest) return anchor.closest(FIELD_SELECTOR);
  return null;
}
let contextField = null;
function rememberField(event) {
  const target = event.target;
  contextField = target && target.closest ? target.closest(FIELD_SELECTOR) : null;
}
document.addEventListener("contextmenu", rememberField);
document.addEventListener("focusin", rememberField);

function detectionAnchor() {
  const active = document.activeElement;
  if (!contextField) return targetField(active);
  if (active && contextField !== active && targetField(active) === contextField) return contextField;
  return contextField;
}

function fieldKind(el) {
  if (el.tagName === "SELECT") return "select";
  if (el.tagName === "TEXTAREA") return "textarea";
  if (el.tagName !== "INPUT") return "text";
  const type = String(el.type || "text").toLowerCase();
  if (type === "radio") return "radio";
  if (type === "checkbox") return "checkbox";
  return type || "text";
}

function groupKey(el, kind) {
  if ((kind === "radio" || kind === "checkbox") && el.name) return `${kind}:${el.name}`;
  return null;
}

function optionLabel(el) {
  if (el.id) {
    const label = document.querySelector(`label[for="${cssEscape(el.id)}"]`);
    if (label && label.textContent) return label.textContent.trim();
  }
  const parent = el.closest("label");
  if (parent) return String(parent.textContent || "").replace(String(el.value || ""), "").trim();
  return String(el.value || "").trim();
}

function fieldOptions(el, kind) {
  if (kind === "select") {
    return Array.from(el.options).filter(o => String(o.value).trim() !== "" || String(o.text).trim() !== "").map(o => ({
      value: String(o.value || "").trim(),
      label: String(o.text || "").trim(),
    }));
  }
  if (kind === "radio" || kind === "checkbox") {
    const scope = questionScope(el);
    const name = el.name;
    const group = name
      ? Array.from(scope.querySelectorAll(`input[type="${kind}"]`)).filter(i => i.name === name)
      : [el];
    return group.map(i => ({ value: String(i.value || "").trim(), label: optionLabel(i) }));
  }
  return [];
}

function detectAllQuestions() {
  const anchor = detectionAnchor();
  const group = anchor && isAvailable(anchor) ? fieldGroup(anchor) : null;
  const scope = group && group !== document.body ? group : activeDialog();
  const fields = scope.querySelectorAll(FIELD_SELECTOR);
  const results = [];
  const seenGroups = new Set();
  let index = 0;
  for (const el of fields) {
    if (!isAvailable(el) || !isReachable(el)) continue;
    const kind = fieldKind(el);
    const key = groupKey(el, kind);
    if (key) {
      if (seenGroups.has(key)) continue;
      seenGroups.add(key);
    }
    const detection = detectQuestion(el, kind);
    if (detection.question) {
      const type = kind === "select" && el.multiple ? "select-multiple" : kind;
      results.push({
        id: `field-${index}`,
        question: detection.question,
        selector: detection.selector,
        tagName: el.tagName,
        type,
        options: fieldOptions(el, kind),
      });
      index++;
    }
  }
  return results;
}

function detectQuestion(input, kind = fieldKind(input)) {
  const scope = questionScope(input);
  const selector = cssSelector(input);
  const labelledBy = input.getAttribute("aria-labelledby");
  const fieldset = input.closest("fieldset");
  const clean = value => String(value && value.textContent !== undefined ? value.textContent : value || "").trim();
  const groupLabel = (kind === "radio" || kind === "checkbox") && fieldset
    ? clean(fieldset.querySelector("legend"))
    : "";
  const direct = [
    groupLabel,
    input.id && scope.querySelector(`label[for="${cssEscape(input.id)}"]`),
    labelledBy && document.getElementById(labelledBy),
    input.getAttribute("aria-label"),
    input.getAttribute("placeholder"),
    !groupLabel && fieldset && fieldset.querySelector("legend")
  ].map(clean).find(Boolean);
  if (direct) return { question: direct, selector };
  for (let node = input; node && node !== scope; node = node.parentElement) {
    let prev = node.previousElementSibling;
    while (prev) {
      const text = clean(prev);
      if (text) return { question: text, selector };
      prev = prev.previousElementSibling;
    }
  }
  const parent = input.parentElement;
  const parentText = parent ? clean(parent).replace(clean(input), "").trim() : "";
  return { question: parentText, selector };
}

function cssSelector(el) {
  const parts = [];
  while (el && el.nodeType === Node.ELEMENT_NODE) {
    let selector = el.tagName.toLowerCase();
    if (el.id) {
      selector = `#${el.id}`;
      parts.unshift(selector);
      break;
    }
    const parent = el.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children).filter((c) => c.tagName === el.tagName);
      if (siblings.length > 1) {
        selector += `:nth-child(${Array.from(parent.children).indexOf(el) + 1})`;
      }
    }
    parts.unshift(selector);
    el = parent;
  }
  return parts.join(" > ");
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "detect-all-questions") {
    sendResponse(detectAllQuestions());
  } else if (msg.action === "detect-question") {
    const active = targetField(contextField || document.activeElement);
    if (active && isAvailable(active)) {
      const result = detectQuestion(active);
      chrome.runtime.sendMessage({ action: "question-detected", question: result.question, selector: result.selector });
    } else {
      chrome.runtime.sendMessage({ action: "question-detected", question: "", selector: "" });
    }
  } else if (msg.action === "fill-answer") {
    const el = targetField(contextField || document.activeElement);
    if (el && isAvailable(el)) fillField(el, msg.text);
    contextField = null;
  } else if (msg.action === "fill-all-fields") {
    const anchor = detectionAnchor();
    const group = anchor && isAvailable(anchor) ? fieldGroup(anchor) : null;
    const scope = group && group !== document.body ? group : activeDialog();
    for (const item of msg.fields) {
      const el = document.querySelector(item.selector);
      if (el && scope.contains(el) && isAvailable(el) && isReachable(el)) fillField(el, item.text);
    }
  }
});
function cssEscape(value) {
  if (globalThis.CSS && typeof globalThis.CSS.escape === "function") return globalThis.CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

function normalized(value) {
  return String(value || "").trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

function splitAnswers(text) {
  return String(text || "").split(/[\n,;|]+/).map(s => normalized(s)).filter(Boolean);
}

function matchesOption(answer, option) {
  const value = normalized(option.value);
  const label = normalized(option.label || option.text);
  return answer === value || answer === label;
}

function optionLabel(el) {
  if (el.id) {
    const label = document.querySelector(`label[for="${cssEscape(el.id)}"]`);
    if (label && label.textContent) return label.textContent.trim();
  }
  const parent = el.closest("label");
  if (parent) return String(parent.textContent || "").replace(String(el.value || ""), "").trim();
  return String(el.value || "").trim();
}

function fillSelect(el, text) {
  const answer = normalized(text);
  if (!answer) return false;
  if (el.multiple) {
    const answers = splitAnswers(text);
    if (!answers.length) return false;
    let changed = false;
    for (const option of Array.from(el.options)) {
      const shouldSelect = answers.some(a => matchesOption(a, { value: option.value, text: option.text }));
      if (option.selected !== shouldSelect) { option.selected = shouldSelect; changed = true; }
    }
    return changed;
  }
  if (answer.length > 120) return false;
  const options = Array.from(el.options).map(o => ({ option: o, value: o.value, text: o.text }));
  const matches = options.filter(o => matchesOption(answer, o));
  if (matches.length !== 1) return false;
  el.value = matches[0].option.value;
  return true;
}

function fillChoiceGroup(el, kind, text) {
  const scope = questionScope(el);
  const name = el.name;
  const group = name
    ? Array.from(scope.querySelectorAll(`input[type="${kind}"]`)).filter(i => i.name === name && isAvailable(i))
    : [el];
  const answers = kind === "checkbox" ? splitAnswers(text) : [normalized(text)];
  if (!answers.length || answers.every(a => !a)) return false;
  let changed = false;
  for (const input of group) {
    const option = { value: input.value, label: optionLabel(input) };
    const shouldCheck = answers.some(a => matchesOption(a, option));
    if (kind === "radio") {
      if (shouldCheck && !input.checked) { input.checked = true; changed = true; }
    } else if (input.checked !== shouldCheck) { input.checked = shouldCheck; changed = true; }
  }
  return changed;
}

function fillField(el, text) {
  if (isSiteControl(el)) return false;
  const kind = fieldKind(el);
  let changed = false;
  if (kind === "select") changed = fillSelect(el, text);
  else if (kind === "radio" || kind === "checkbox") changed = fillChoiceGroup(el, kind, text);
  else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") { el.value = text; changed = true; }
  else return false;
  if (!changed) return false;
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  if (kind === "radio" || kind === "checkbox") el.dispatchEvent(new Event("click", { bubbles: true }));
  return true;
}
