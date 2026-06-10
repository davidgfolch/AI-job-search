import re


def search_partial_company(company_raw: str):
    if not company_raw:
        return []
    company_words = company_raw.split(' ')
    while len(company_words) > 1:
        company_words = company_words[:-1]
        words = ' '.join(company_words)
        part1 = re.escape(words)
        if len(part1) > 2 and part1.lower() not in ['grupo', 'the', 'inc', 'ltd', 'llc']:
            return f'(^| ){part1}($| )'
    return []


def get_best_candidate(company_name: str | None) -> str | None:
    if not company_name:
        return None
    words = company_name.strip().split()
    while len(words) > 1:
        words = words[:-1]
        candidate = ' '.join(words)
        if len(candidate) > 2 and candidate.lower() not in ['grupo', 'the', 'inc', 'ltd', 'llc']:
            return candidate
    return None
