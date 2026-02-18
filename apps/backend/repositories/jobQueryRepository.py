from typing import List, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection
from commonlib.sqlUtil import scapeRegexChars, avoidInjection
from commonlib.mysqlUtil import (
    SELECT_APPLIED_JOB_IDS_BY_COMPANY,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT,
    SELECT_APPLIED_JOB_ORDER_BY,
)


class JobQueryRepository:
    def __init__(self, mysql: MysqlUtil = None):
        self._mysql = mysql

    def get_db(self) -> MysqlUtil:
        if self._mysql:
            return self._mysql
        return MysqlUtil(getConnection())

    def find_applied_by_company(self, company: str, client: str = None) -> List[tuple]:
        avoidInjection(company, "company")
        if client:
            avoidInjection(client, "client")
        regex_lookup = scapeRegexChars(company)
        return self.find_applied_jobs_by_regex(regex_lookup, client)

    def find_applied_jobs_by_regex(
        self, regex_lookup: str, client_filter: str = None
    ) -> List[tuple]:
        with self.get_db() as db:
            if client_filter:
                qry = SELECT_APPLIED_JOB_IDS_BY_COMPANY
                qry += SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
                qry += SELECT_APPLIED_JOB_ORDER_BY
                params = {"company": regex_lookup, "id": "0", "client": client_filter}
            else:
                qry = SELECT_APPLIED_JOB_IDS_BY_COMPANY + SELECT_APPLIED_JOB_ORDER_BY
                params = {"company": regex_lookup, "id": "0"}
            return db.fetchAll(qry.format(**params))
