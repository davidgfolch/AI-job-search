from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import jobs

app = FastAPI(title="AI Job Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
