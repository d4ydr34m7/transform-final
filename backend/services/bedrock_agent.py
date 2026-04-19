"""Bedrock Agent + KB chat and ingestion."""
import os
import logging
from fastapi import HTTPException

from config import get_region

logger = logging.getLogger(__name__)


def bedrock_enabled() -> bool:
    return os.environ.get("BEDROCK_ENABLED", "").lower() in {"1", "true", "yes", "on"}


def get_bedrock_region() -> str:
    return get_region() or "us-east-1"


def get_bedrock_agent_client():
    try:
        import boto3  # type: ignore
        from botocore.config import Config  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"boto3 is required for Bedrock agent: {e}")
    read_timeout = int(os.environ.get("BEDROCK_AGENT_TIMEOUT_SECONDS", "60"))
    config = Config(read_timeout=read_timeout, connect_timeout=10)
    return boto3.client("bedrock-agent-runtime", region_name=get_bedrock_region(), config=config)


def _strip_agent_meta_intro(text: str) -> str:
    if not text or "I don't need to use the search tool" not in text:
        return text
    markers = (
        "I can answer your question based on that information.",
        "I can answer your question based on that information",
        "based on that information.",
    )
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            rest = text[idx + len(marker) :].lstrip()
            if rest and len(rest) > 30:
                return rest
    return text


def citation_uri_to_display_name(location: dict) -> str | None:
    """S3 URI or similar → filename for display."""
    if not location or not isinstance(location, dict):
        return None
    s3 = location.get("s3Location") or {}
    uri = (s3.get("uri") or "").strip()
    if uri:
        parts = uri.rstrip("/").split("/")
        return parts[-1] if parts else uri
    for key in ("customDocumentLocation", "webLocation", "confluenceLocation"):
        loc = location.get(key) or {}
        url = (loc.get("url") or loc.get("uri") or loc.get("id") or "").strip()
        if url:
            parts = url.rstrip("/").split("/")
            return parts[-1] if parts else url
    return None


def invoke_agent(analysis_id: str, session_id: str, message: str) -> tuple[str, list[str]]:
    agent_id = os.environ.get("BEDROCK_AGENT_ID", "").strip()
    alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "").strip()
    if not agent_id or not alias_id:
        raise HTTPException(
            status_code=503,
            detail="BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID must be set",
        )
    client = get_bedrock_agent_client()
    try:
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=message,
            enableTrace=True,
        )
    except Exception as e:
        logger.exception(
            "Bedrock invoke_agent failed analysis_id=%s agentId=%s aliasId=%s: %s",
            analysis_id, agent_id, alias_id, e,
        )
        raise HTTPException(status_code=502, detail=f"Agent failed: {e}")

    completion_stream = response.get("completion")
    if not completion_stream:
        raise HTTPException(status_code=502, detail="Agent returned no completion stream")

    answer_parts: list[str] = []
    seen_sources: set[str] = set()
    for event in completion_stream:
        if "chunk" not in event:
            continue
        chunk = event["chunk"]
        if "bytes" in chunk:
            answer_parts.append(chunk["bytes"].decode("utf-8", errors="replace"))
        attribution = chunk.get("attribution") or {}
        citations = attribution.get("citations") or []
        for citation in citations:
            for ref in citation.get("retrievedReferences") or []:
                loc = ref.get("location") if isinstance(ref, dict) else None
                name = citation_uri_to_display_name(loc) if loc else None
                if name:
                    seen_sources.add(name)
    answer = "".join(answer_parts).strip()
    answer = _strip_agent_meta_intro(answer)
    sources = sorted(seen_sources)
    if not sources and not answer:
        answer = "Not found in analysis."
    return answer, sources


def start_kb_ingestion() -> None:
    kb_id = os.environ.get("BEDROCK_KB_ID", "").strip()
    ds_id = os.environ.get("BEDROCK_KB_DATA_SOURCE_ID", "").strip()
    if not kb_id or not ds_id:
        logger.debug("KB ingestion skipped: BEDROCK_KB_ID or BEDROCK_KB_DATA_SOURCE_ID not set")
        return
    try:
        import boto3  # type: ignore
        client = boto3.client("bedrock-agent", region_name=get_bedrock_region())
        client.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)
        logger.info("KB ingestion started knowledgeBaseId=%s dataSourceId=%s", kb_id, ds_id)
    except Exception as e:
        logger.warning("KB ingestion start failed: %s", e)
