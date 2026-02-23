import json
import re
import traceback

from commonlib.terminalColor import red, yellow

def decode_unicode_escapes(parsed_dict: dict) -> None:
    # CrewAI/LiteLLM can return literal unicode escapes like \u00f3 instead of native characters
    for k, v in parsed_dict.items():
        if isinstance(v, str):
            try:
                # Manually evaluate double-escaped unicode strings
                if '\\u' in v:
                    # encoding to raw bytes sequence and using unicode_escape decodes \uXXXX properly
                    parsed_dict[k] = v.encode('utf-8', 'surrogatepass').decode('unicode_escape')
            except Exception:
                pass


def rawToJson(raw: str) -> dict[str, str]:
    res = raw
    try:
        IM = re.I | re.M
        # remove Agent Thought or Note (from crewHelper)
        res = re.sub(r'\n(Thought|Note):(.*\n)*', '', res, flags=IM)
        # remove json prefix
        res = re.sub(r'(```(json)?\n?)', '', res, flags=IM) # Merged from jsonHelper/crewHelper
        res = re.sub(r'json *object *', '', res, flags=IM)
        # CrewHelper fixers
        res = fixJsonStartCurlyBraces(res)
        res = fixJsonEndCurlyBraces(res)
        res = fixJsonInvalidAttribute(res)
        # repl \& or \. (...) by & or .
        res = re.sub(r'\\([&.*-+#])', r'\1', res, re.I | re.M)
        parsed_dict = dict(json.loads(f'{res}', cls=LazyDecoder))
        
        decode_unicode_escapes(parsed_dict)
        return parsed_dict
    except Exception as ex:
        printJsonException(ex, res, raw)
        raise ex


class LazyDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
            (re.compile(r',(\s*])'), r'\1'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)


def printJsonException(ex: Exception, res: str, raw: str) -> None:
    print(red(f'Could not parse json after clean it: '))
    # Traceback is already printed by caller usually, but logic in crewHelper prints it.
    # jsonHelper commented it out. We will keep it but maybe concise?
    print(red(traceback.format_exc()))
    print(red(f'Json after clean:\n{res}'))
    print(yellow(f'Original json:\n{raw}'))
    raise ex


def fixJsonInvalidAttribute(raw):
    """Fixes LLM invalid json value, f.ex.:
    "salary": "xx" + "yy",
    "salary": "xx",",
    """
    raw = re.sub(r'" \+ "', ' + ', raw)
    # {"salary":
    # "$\text{Salary determined by the market and your experience} \\\$",
    raw = re.sub(r'"[$]\\text\{([^\}]+)\} \\\\\\\$"', r'\1', raw)
    return re.sub(r'(.+)",",', r'\1",', raw)


def fixJsonEndCurlyBraces(raw):
    # Only replace if it matches exactly ") or "\ at the very end to prevent stripping valid backslashes like \u20ac
    raw = re.sub(r'"[)\\]\s*$', '"}', raw)
    raw = re.sub(r'[}]{2,}', '}', raw) # remove dobule curly braces at the end }}
    raw = re.sub(r',[ \n]*[}]', '\n}', raw) # remove exta comma at the end ,}
    idx = raw.rfind('}')
    if idx > 0 and idx + 1 < len(raw):  # remove extra text after }
        return raw[0:idx+1]
    if idx == -1:  # sometimes LLM forgets to close }
        return raw + '}'
    return raw


def fixJsonStartCurlyBraces(raw):
    idx = raw.rfind('{')
    if idx > 0 and idx + 1 < len(raw):
        # remove extra text before {
        return raw[idx:]
    return raw
