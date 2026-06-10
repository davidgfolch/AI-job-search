import re

_SUFFIXES = {
    "inc", "llc", "ltd",
    "sa", "sl", "s.l.", "s.a.", "s.r.l.",
    "gmbh", "bv", "nv", "plc", "ag", "kg",
    "co", "group", "holding",
}


def normalize_company_name(name: str | None) -> str:
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\b(?:' + '|'.join(re.escape(s) for s in sorted(_SUFFIXES, key=len, reverse=True)) + r')\.?(?=\s|$|\.)', '', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name
