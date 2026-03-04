from typing import List
from repositories.ddl_repository import DdlRepository


class DdlService:
    def __init__(self):
        self.repo = DdlRepository()

    def get_schema(self):
        return self.repo.get_schema()

    def get_keywords(self):
        return self.repo.get_keywords()

    def get_enum_values(self, table_name: str, column_name: str) -> List[str]:
        return self.repo.get_enum_values(table_name, column_name)
