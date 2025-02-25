from ai_job_search.tools.util import getEnv
from ai_job_search.viewer.util.stUtil import sortFields, stripFields


LIST_HEIGHT = 400
COLUMNS_WIDTH: float = 0.5

# FORM FILTER KEYS
FF_KEY_BOOL_FIELDS = 'boolFieldsFilter'
FF_KEY_BOOL_NOT_FIELDS = 'boolFieldsNotFilter'
FF_KEY_SEARCH = 'searchFilter'
FF_KEY_SALARY = 'salaryFilter'
FF_KEY_DAYS_OLD = 'daysOldFilter'
FF_KEY_WHERE = 'whereFilter'
FF_KEY_ORDER = 'selectOrderFilter'
FF_KEY_SINGLE_SELECT = 'singleSelect'
FF_KEY_LIST_HEIGHT = 'listHeight'
FF_KEY_PRESELECTED_ROWS = 'preSelectedRows'
FF_KEY_COLUMNS_WIDTH = 'columnsWidth'
# FORM KEYS
F_KEY_COMMENTS = 'comments'
F_KEY_SALARY = 'salary'
F_KEY_COMPANY = 'company'
F_KEY_CLIENT = 'client'
# COLUMNS (MYSQL & DATAFRAME)
VISIBLE_COLUMNS = """
salary,title,company"""
DB_FIELDS_BOOL = """flagged,`like`,ignored,seen,applied,discarded,closed,
interview_rh,interview,interview_tech,interview_technical_test,interview_technical_test_done,
ai_enriched,easy_apply"""
DB_FIELDS = f"""id,salary,title,required_technologies,optional_technologies,
web_page,company,client,markdown,location,url,created,modified,
comments,{DB_FIELDS_BOOL},ai_enrich_error"""
# FILTERS
RLIKE = getEnv('WHERE_FILTER_REGEX')
DEFAULT_SQL_FILTER = f"""
required_technologies rlike '{RLIKE}'
 or title rlike '{RLIKE}'
 or markdown rlike '{RLIKE}'"""
DEFAULT_DAYS_OLD = "1"
DEFAULT_ORDER = "created desc"
# DETAIL FORMAT
DETAIL_FORMAT = """
## [{title}]({url}) ({id})
- Source: :green[{web_page}] <span style="font-size: small">
(created :green[{created}] :green[{createdTime}] updated: :green[{modified}])
</span>
- Company: :green[{company}]
"""

LIST_VISIBLE_COLUMNS = stripFields(VISIBLE_COLUMNS)
FIELDS = stripFields(DB_FIELDS)
FIELDS_BOOL = stripFields(DB_FIELDS_BOOL)
FIELDS_SORTED = sortFields(DB_FIELDS, 'id,' + VISIBLE_COLUMNS).split(',')
DEFAULT_BOOL_FILTERS = stripFields('ai_enriched')
DEFAULT_NOT_FILTERS = stripFields('seen,ignored,applied,discarded,closed')


SEARCH_COLUMNS = ['title', 'company', 'client', 'markdown', 'comments']
SEARCH_INPUT_HELP = f"""
Search in {'/'.join(SEARCH_COLUMNS)}, enter search concepts
 (plain text or separated by commas to use mysql regex)"""


# CHANGES PRIMARY TABLE COLOR
STYLE_JOBS_TABLE = """
    <style>
        .st-key-jobsListTable .stDataFrame > *,
        .st-key-jobsListTable .stDataFrame > div > * {
            background-color: darkcyan;
        }
    </style>
    """
# REMOVES VERTICAL SPACE IN FORM FILTER CHECK+INPUT
STYLE_FILTER_FORM = """
    <style>
        div[data-testid=stExpanderDetails] .stColumn .stVerticalBlock {
            gap: 0rem;
        }
    </style>
    """
