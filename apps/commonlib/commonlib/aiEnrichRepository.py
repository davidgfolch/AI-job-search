from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import emptyToNone, maxLen, updateFieldsQuery
from commonlib.environmentUtil import getEnv
from commonlib.ai_helpers import MAX_AI_ENRICH_ERROR_LEN, RETRY_ERROR_PREFIX

class AiEnrichRepository:
    def __init__(self, mysql: MysqlUtil):
        self.mysql = mysql

    # Enrichment Queries
    def count_pending_enrichment(self) -> int:
        query = """SELECT count(id) 
                   FROM jobs
                   WHERE (ai_enriched IS NULL OR not ai_enriched) and
                   not (ignored or discarded or closed)
                   ORDER BY created desc"""
        return self.mysql.count(query)

    def get_pending_enrichment_ids(self) -> list[int]:
        query = """SELECT id 
                   FROM jobs
                   WHERE (ai_enriched IS NULL OR not ai_enriched) and
                   not (ignored or discarded or closed)
                   ORDER BY created desc"""
        return [row[0] for row in self.mysql.fetchAll(query)]
        
    def get_job_to_enrich(self, id: int):
        query = """
            SELECT id, title, markdown, company
            FROM jobs
            WHERE id=%s and not ai_enriched and not (ignored or discarded or closed)
            ORDER BY created desc"""
        return self.mysql.fetchOne(query, id)

    def get_enrichment_error_id_retry(self) -> int | None:
        query = f"""
            SELECT id FROM jobs 
            WHERE ai_enrich_error IS NOT NULL AND ai_enrich_error != '' 
            AND ai_enrich_error NOT LIKE '{RETRY_ERROR_PREFIX}%'
            AND created > DATE_SUB(NOW(), INTERVAL 2 DAY)
            ORDER BY created DESC LIMIT 1"""
        rows = self.mysql.fetchAll(query)
        return rows[0][0] if rows else None

    def get_job_to_retry(self, id: int):
        query = """
            SELECT id, title, markdown, company
            FROM jobs
            WHERE id=%s"""
        return self.mysql.fetchOne(query, id)

    def update_enrichment(self, id: int, salary, required_tech, optional_tech):
        query = """
            UPDATE jobs SET
                salary=%s,
                required_technologies=%s,
                optional_technologies=%s,
                ai_enriched=1,
                ai_enrich_error=NULL
            WHERE id=%s"""
        # Note: Caller is responsible for maxLen/emptyToNone or we do it here?
        # Ideally repository handles data preparation if it's purely schema related.
        # But for now, let's assume caller passes clean data or we apply same utils.
        # The original code used maxLen(emptyToNone(...))
        params = maxLen(emptyToNone(
                        (salary,
                         required_tech,
                         optional_tech,
                         id)),
                        (200, 1000, 1000, None))
        self.mysql.updateFromAI(query, params)

    def update_enrichment_error(self, id: int, error_msg: str, is_enrichment: bool):
        error_msg = error_msg[:MAX_AI_ENRICH_ERROR_LEN]
        fields = {'ai_enrich_error': error_msg, 'ai_enriched': True} if is_enrichment else {'cv_match_percentage': -1}
        query, params = updateFieldsQuery([id], fields)
        return self.mysql.executeAndCommit(query, params)

    # CV Match Queries
    def count_pending_cv_match(self) -> int:
        query = """SELECT count(id) 
                   FROM jobs
                   WHERE cv_match_percentage is null and not (ignored or discarded or closed)
                   ORDER BY created desc"""
        return self.mysql.count(query)

    def get_pending_cv_match_ids(self, limit: int) -> list[int]:
        query = f"""SELECT id 
                   FROM jobs
                   WHERE cv_match_percentage is null and not (ignored or discarded or closed)
                   ORDER BY created desc LIMIT {limit}"""
        return [row[0] for row in self.mysql.fetchAll(query)]

    def get_job_to_match_cv(self, id: int):
        query = """
            SELECT id, title, markdown, company
            FROM jobs
            WHERE id=%s and cv_match_percentage is null and not (ignored or discarded or closed)
            ORDER BY created desc 
            """
        return self.mysql.fetchOne(query, id)

    def update_cv_match(self, id: int, percentage: int | None):
        query = """UPDATE jobs SET cv_match_percentage=%s WHERE id=%s"""
        params = maxLen(emptyToNone((percentage, id)), (None, None))
        self.mysql.updateFromAI(query, params)
