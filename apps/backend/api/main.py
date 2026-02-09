from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from api import jobs
from api import salary
from api import ddl
from api import statistics
from api import skills
from api import filter_configurations

app = FastAPI(title="AI Job Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(salary.router, prefix="/api/salary", tags=["salary"])
app.include_router(ddl.router, prefix="/api/ddl", tags=["ddl"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(filter_configurations.router, prefix="/api/filter-configurations", tags=["filter-configurations"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/system/timezone", tags=["system"])
def get_timezone():
    """
    Returns the server's UTC offset in minutes.
    Example: UTC+1 returns 60.
    """
    offset_seconds = datetime.now().astimezone().utcoffset().total_seconds()
    offset_minutes = int(offset_seconds / 60)
    return {"offset_minutes": offset_minutes}

