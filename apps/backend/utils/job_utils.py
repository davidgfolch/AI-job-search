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
