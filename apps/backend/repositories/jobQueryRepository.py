from typing import List, Dict, Any, Union
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from commonlib.sqlUtil import scapeRegexChars, avoidInjection
from commonlib.sql.mysqlUtil import (
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

    def find_applied_by_companies(
        self, companies: List[str], client: str = None
    ) -> List[tuple]:
        for c in companies:
            avoidInjection(c, "company")
        if client:
            avoidInjection(client, "client")
        lookups = [scapeRegexChars(c) for c in companies]
        return self.find_applied_jobs_by_regex(lookups, client)

    def find_applied_jobs_by_regex(
        self, regex_lookup: Union[str, List[str]], client_filter: str = None
    ) -> List[tuple]:
        if isinstance(regex_lookup, list):
            patterns = "|".join(
                f"(^|[^a-z0-9]){r}($|[^a-z0-9])" for r in regex_lookup
            )
        else:
            patterns = f"(^|[^a-z0-9]){regex_lookup}($|[^a-z0-9])"
        with self.get_db() as db:
            if client_filter:
                qry = f"""select id, created from jobs
 where applied and lower(company) rlike '{patterns}' and id != 0 """
                qry += SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
                qry += SELECT_APPLIED_JOB_ORDER_BY
                params = {"client": client_filter}
            else:
                qry = f"""select id, created from jobs
 where applied and lower(company) rlike '{patterns}' and id != 0 """
                qry += SELECT_APPLIED_JOB_ORDER_BY
                params = {}
            return db.fetchAll(qry.format(**params))
