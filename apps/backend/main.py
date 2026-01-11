from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import jobs
from api import salary
from api import ddl
from api import statistics
from api import skills

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

@app.get("/health")
def health_check():
    return {"status": "ok"}
