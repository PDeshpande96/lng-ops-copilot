from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import run_agent
from schemas import AnalyzeRequest


app = FastAPI(title="LNG Ops Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    return run_agent(request.issue, request.asset_id)