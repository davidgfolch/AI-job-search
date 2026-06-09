from commonlib.mongodb_provider import MongoDbProvider


class CronStateRepository:
    def __init__(self, mongo_provider: MongoDbProvider):
        self._col = mongo_provider.get_database(write=True)["cron_state"]

    def get_state(self, job_name: str) -> dict | None:
        doc = self._col.find_one({"_id": job_name})
        if doc:
            doc.pop("_id", None)
        return doc

    def update_state(self, job_name: str, state: dict):
        self._col.update_one({"_id": job_name}, {"$set": state}, upsert=True)
