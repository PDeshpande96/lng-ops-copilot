from pydantic import BaseModel, Field
from typing import List


class AnalyzeRequest(BaseModel):
    issue: str = Field(..., min_length=5)
    asset_id: str = Field(..., min_length=3)


class IncidentAnalysis(BaseModel):
    summary: str
    possible_causes: List[str]
    recommended_checks: List[str]
    confidence: str
    tools_used: List[str]
    sources: List[str]