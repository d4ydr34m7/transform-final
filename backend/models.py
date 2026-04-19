from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AnalyzeRequest(BaseModel):
    repo: str
    initiated_by: Optional[str] = None

class AnalyzeResponse(BaseModel):
    analysis_id: str

class FileListResponse(BaseModel):
    files: List[str]

class AnalysisMetadata(BaseModel):
    analysis_id: str
    repo: str
    created_at: datetime
    status: str
    initiated_by: Optional[str] = None

class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisMetadata]

class ChatRequest(BaseModel):
    analysis_id: str
    question: str
    file: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str


class AnalysisChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Bedrock agent session; use same value for multi-turn


class ValidationReport(BaseModel):
    passed: bool
    violations: List[str]


class AnalysisChatResponse(BaseModel):
    answer: str
    sources: List[str]
    validation_report: Optional[ValidationReport] = None
