from ai_job_search.scrapper.util import getEnv
from ai_job_search.viewer.util.stUtil import sortFields, stripFields


HEIGHT = 300

# FORM FILTER KEYS
FF_KEY_BOOL_FIELDS = 'boolFieldsFilter'
FF_KEY_BOOL_NOT_FIELDS = 'boolFieldsNotFilter'
FF_KEY_SEARCH = 'searchFilter'
FF_KEY_SALARY = 'salaryFilter'
FF_KEY_DAYS_OLD = 'daysOldFilter'
FF_KEY_WHERE = 'whereFilter'
FF_KEY_ORDER = 'selectOrder'
# COLUMNS (MYSQL & DATAFRAME)
VISIBLE_COLUMNS = """
salary,title,company,client,required_technologies,created"""
DB_FIELDS_BOOL = """flagged,`like`,ignored,seen,applied,discarded,closed,
interview_rh,interview,interview_tech,interview_technical_test,interview_technical_test_done,
ai_enriched,scrapper_enriched,relocation,easy_apply"""
DB_FIELDS = f"""id,salary,title,required_technologies,optional_technologies,
web_page,company,client,markdown,business_sector,required_languages,location,url,created,
comments,{DB_FIELDS_BOOL}"""
DB_FIELDS_MERGE = """salary,required_technologies,optional_technologies,
company,client,business_sector,required_languages,comments"""
# FILTERS
RLIKE = getEnv('WHERE_FILTER_REGEX')
DEFAULT_SQL_FILTER = f"""
required_technologies rlike '{RLIKE}'
 or title rlike '{RLIKE}'
 or markdown rlike '{RLIKE}'"""
DEFAULT_SALARY_REGEX_FILTER = getEnv('SALARY_FILTER_REGEX')
DEFAULT_DAYS_OLD = "1"
DEFAULT_ORDER = "created desc"
# DETAIL FORMAT
DETAIL_FORMAT = """
## [{title}]({url})

- Source: `{web_page}`
- Company: `{company}`
- Client: `{client}`
- Salary: `{salary}`
- Skills
  - Required: `{required_technologies}`
  - Optional: `{optional_technologies}`

`{created}` - `{createdTime}`

{markdown}
"""

LIST_VISIBLE_COLUMNS = stripFields(VISIBLE_COLUMNS)
FIELDS = stripFields(DB_FIELDS)
FIELDS_BOOL = stripFields(DB_FIELDS_BOOL)
FIELDS_MERGE = stripFields(DB_FIELDS_MERGE)
FIELDS_SORTED = sortFields(DB_FIELDS, 'id,' + VISIBLE_COLUMNS).split(',')
DEFAULT_BOOL_FILTERS = stripFields('ai_enriched')
DEFAULT_NOT_FILTERS = stripFields('seen,ignored,applied,discarded,closed')


SEARCH_COLUMNS = ['title', 'company', 'client', 'markdown', 'comments']
SEARCH_INPUT_HELP = f"""
Search in {'/'.join(SEARCH_COLUMNS)}, enter search concepts
 (plain text or separated by commas to use mysql regex)"""


STYLE_JOBS_TABLE = """
    <style>
        .st-key-jobsListTable .stDataFrame > *,
        .st-key-jobsListTable .stDataFrame > div > * {
            background-color: darkcyan;
        }
    </style>
    """
