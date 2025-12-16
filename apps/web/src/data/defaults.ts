/**
 * Default persistence data.
 * Update this file and commit to Git to share default configurations.
 */

// Paste this into apps/web/src/data/defaults.ts
export const defaultFilterConfigurations = [
    {
        "name": "Clean - Ignore jobs by title",
        "filters": {
            "page": 1,
            "size": 20,
            "search": "",
            "order": "created desc",
            "salary": "",
            "sql_filter": "LOWER(title) rlike '(^|[^a-z])(sap|abap|hana|cobol|devops|devsecops|junior|internship|prácticas|becario|front-?end|android|ios|scrum master|qa|\\.net|salesforce|site reliability engineer|ingeniero de redes)([^a-z]|$)'",
            "ignored": false,
            "applied": false
        }
    },
    {
        "name": "By company",
        "filters": {
            "page": 1,
            "size": 20,
            "search": "",
            "order": "created desc",
            "ai_enriched": true,
            "salary": "",
            "sql_filter": "lower(company) rlike 'INNOCV|Horizon Neulogy|initi8|primeit|Acid tango'",
            "days_old": 120,
            "ignored": false,
            "seen": false,
            "applied": true,
            "discarded": false,
            "closed": false
        }
    },
    {
        "name": "Java backend only",
        "filters": {
            "page": 1,
            "size": 20,
            "search": "",
            "order": "created desc",
            "ai_enriched": true,
            "salary": "\\d",
            "sql_filter": "(lower(required_technologies) rlike 'java([^script]|$)|\\bscala\\b|clojure' or lower(title) rlike 'java([^script]|$)|\\bscala\\b|clojure') and not lower(title) rlike 'full(-?stack)?'",
            "days_old": 1,
            "ignored": false,
            "seen": false,
            "applied": false,
            "discarded": false,
            "closed": false
        }
    },
    {
        "name": "Applied active comments by date",
        "filters": {
            "page": 1,
            "size": 20,
            "search": "",
            "order": "created asc",
            "ai_enriched": true,
            "salary": "",
            "sql_filter": "comments is not null and comments rlike '.+\\n.+'",
            "days_old": 120,
            "ignored": false,
            "seen": false,
            "applied": true,
            "discarded": false,
            "closed": false
        }
    }
];

// Initial data for history (example)
const defaultHistory = ["React", "Python", "Remote"];

export const persistenceDefaults: Record<string, any> = {
    'filter_configurations': defaultFilterConfigurations,
    'test-history': defaultHistory, 
    // Add real keys used in the app here
    // 'field_history_key': ...
};
