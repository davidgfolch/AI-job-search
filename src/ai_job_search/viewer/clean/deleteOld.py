from ai_job_search.viewer.util.stUtil import stripFields


INFO = 'Delete oldest ignored jobs'
COLUMNS = stripFields('Id,Title,Company,Created')
IDS_IDX = 0
SELECT = """
select id,title,company,created
from jobs
where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 30 DAY) and not (applied)
order by created desc
"""


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Delete old in selection',
                       on_click=delete,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def delete(selectedRows):
    pass
