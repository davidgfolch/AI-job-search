from commonlib.aiEnrichRepository import AiEnrichRepository


class MockMysqlUtil:
    def __init__(self):
        self.count_result = 0
        self.fetch_all_result = []
        self.configs_result = []
        self.match_batches = []
        self.fallback_batches = []
        self.fetch_one_result = None
        self.update_called = False
        self.updates = []
        self.fetch_all_calls = []
        self.last_query = None
        self.last_params = None

    def count(self, query):
        self.last_query = query
        return self.count_result

    def fetchAll(self, query, params=None):
        self.last_query = query
        self.last_params = params
        self.fetch_all_calls.append((query, params))
        if "filter_configurations" in query:
            return self.configs_result
        if "created DESC, id DESC" in query:
            return self.match_batches.pop(0) if self.match_batches else []
        if "created desc LIMIT %s" in query:
            return self.fallback_batches.pop(0) if self.fallback_batches else []
        return self.fetch_all_result

    def fetchOne(self, query, *args):
        return self.fetch_one_result

    def updateFromAI(self, query, params):
        self.update_called = True
        self.updates.append((query, params))
        self.last_query = query
        self.last_params = params

    def executeAndCommit(self, query, params):
        self.last_query = query
        self.last_params = params
        return 1


def mockRepo():
    mock_mysql = MockMysqlUtil()
    repo = AiEnrichRepository(mock_mysql)
    return mock_mysql, repo
