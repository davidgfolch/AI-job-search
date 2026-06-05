from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from commonlib.sql.scrapper_state_repository import ScrapperStateRepository as CommonScrapperStateRepo


class ScrapperStateRepository:

    def get_db(self):
        return MysqlUtil(getConnection())

    def get_all(self) -> dict:
        with self.get_db() as db:
            return db.get_scrapper_state()

    def replace_all(self, state: dict) -> dict:
        with self.get_db() as db:
            db.update_scrapper_state(state)
        return state
