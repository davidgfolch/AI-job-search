import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootPass@localhost:27017/")
MONGO_READ_URI = os.getenv("MONGO_READ_URI") or MONGO_URI
MONGO_WRITE_URI = os.getenv("MONGO_WRITE_URI") or MONGO_URI
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "jobs")

COMMONLIB_DB_HOST = os.getenv("COMMONLIB_DB_HOST", "127.0.0.1")

CRON_SALARY_CADENCY = os.getenv("CRON_SALARY_CADENCY", "1h")

CHECK_INTERVAL_SECONDS = 60
