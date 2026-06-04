function detectAllQuestions() {
  const fields = document.querySelectorAll("input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]):not([type=checkbox]):not([type=radio]), textarea, select");
  const results = [];
  let index = 0;
  for (const el of fields) {
    if (el.disabled || el.readOnly) continue;
    const detection = detectQuestion(el);
    if (detection.question) {
      results.push({
        id: `field-${index}`,
        question: detection.question,
        selector: detection.selector,
        tagName: el.tagName,
      });
      index++;
    }
  }
  return results;
}

function detectQuestion(input) {
  // Try label with for attribute
  const id = input.id;
  if (id) {
    const label = document.querySelector(`label[for="${id}"]`);
    if (label) return { question: label.textContent.trim(), selector: cssSelector(input) };
  }

  // Try aria-labelledby
  const labelledBy = input.getAttribute("aria-labelledby");
  if (labelledBy) {
    const label = document.getElementById(labelledBy);
    if (label) return { question: label.textContent.trim(), selector: cssSelector(input) };
  }

  // Try placeholder
  const placeholder = input.getAttribute("placeholder");
  if (placeholder) return { question: placeholder.trim(), selector: cssSelector(input) };

  // Try previous sibling text
  let prev = input.previousElementSibling;
  while (prev) {
    const text = prev.textContent.trim();
    if (text) return { question: text, selector: cssSelector(input) };
    prev = prev.previousElementSibling;
  }

  // Try closest fieldset legend
  const fieldset = input.closest("fieldset");
  if (fieldset) {
    const legend = fieldset.querySelector("legend");
    if (legend) return { question: legend.textContent.trim(), selector: cssSelector(input) };
  }

  // Try parent div text
  const parent = input.parentElement;
  if (parent) {
    const parentText = parent.textContent.replace(input.textContent, "").trim();
    if (parentText) return { question: parentText, selector: cssSelector(input) };
  }

  return { question: "", selector: cssSelector(input) };
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
    const active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.tagName === "SELECT")) {
      const result = detectQuestion(active);
      chrome.runtime.sendMessage({ action: "question-detected", question: result.question, selector: result.selector });
    } else {
      chrome.runtime.sendMessage({ action: "question-detected", question: "", selector: "" });
    }
  } else if (msg.action === "fill-answer") {
    const el = document.activeElement;
    if (el) fillField(el, msg.text);
  } else if (msg.action === "fill-all-fields") {
    for (const item of msg.fields) {
      const el = document.querySelector(item.selector);
      if (el) fillField(el, item.text);
    }
  }
});

function fillField(el, text) {
  if (el.tagName === "SELECT") {
    const options = Array.from(el.options);
    const match = options.find(o => o.text.toLowerCase().includes(text.toLowerCase()) || text.toLowerCase().includes(o.text.toLowerCase()));
    if (match) { el.value = match.value; }
  } else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    el.value = text;
  }
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
}
