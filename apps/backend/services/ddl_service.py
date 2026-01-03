from repositories.ddl_repository import DdlRepository

class DdlService:
    def __init__(self):
        self.repo = DdlRepository()

    def get_schema(self):
        return self.repo.get_schema()

    def get_keywords(self):
        return self.repo.get_keywords()
