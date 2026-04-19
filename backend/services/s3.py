"""S3 and SNS for analysis artifacts."""
import json
import os
import logging
from datetime import datetime

from fastapi import HTTPException

from config import get_region

logger = logging.getLogger(__name__)


def s3_enabled() -> bool:
    return os.environ.get("S3_ENABLED", "").lower() in {"1", "true", "yes", "on"}


def send_completion_notification_enabled() -> bool:
    return os.environ.get("SEND_COMPLETION_NOTIFICATION", "").lower() in {"1", "true", "yes", "on"}


def _get_sns_topic_arn() -> str | None:
    return (os.environ.get("SNS_TOPIC_ARN", "") or "").strip() or None


def publish_completion_notification(
    analysis_id: str, repo: str, status: str, initiated_by: str | None
) -> None:
    """Publish to SNS when SEND_COMPLETION_NOTIFICATION and SNS_TOPIC_ARN are set."""
    if not send_completion_notification_enabled():
        return
    topic_arn = _get_sns_topic_arn()
    if not topic_arn:
        logger.warning("SEND_COMPLETION_NOTIFICATION is on but SNS_TOPIC_ARN is empty")
        return
    try:
        import boto3  # type: ignore
        sns = boto3.client("sns", region_name=get_region() or "us-east-1")
        message = json.dumps({
            "analysis_id": analysis_id,
            "repo": repo,
            "status": status,
            "initiated_by": initiated_by,
            "message": f"VERAMOD analysis {status}: {repo} (analysis_id={analysis_id})",
        })
        sns.publish(TopicArn=topic_arn, Message=message, Subject=f"VERAMOD analysis {status}: {repo}")
        logger.info("SNS notification sent analysis_id=%s topic=%s", analysis_id, topic_arn)
    except Exception as e:
        logger.warning("SNS publish failed: %s", str(e))


def get_s3_bucket() -> str:
    bucket = os.environ.get("S3_BUCKET", "").strip()
    if not bucket:
        raise HTTPException(status_code=500, detail="S3_BUCKET env var is required when S3 is enabled")
    return bucket


def get_s3_region() -> str | None:
    return get_region()


def get_s3_client():
    try:
        import boto3  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"boto3 is required for S3 mode: {e}")
    region = get_s3_region()
    if region:
        return boto3.client("s3", region_name=region)
    return boto3.client("s3")


def s3_prefix(analysis_id: str) -> str:
    return f"analysis/{analysis_id}/"


def s3_key(analysis_id: str, file_name: str) -> str:
    return f"{s3_prefix(analysis_id)}{file_name}"


def s3_put_text(analysis_id: str, file_name: str, content: str) -> None:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    key = s3_key(analysis_id, file_name)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/markdown; charset=utf-8",
    )


def s3_put_plain_text(analysis_id: str, file_name: str, content: str) -> None:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    key = s3_key(analysis_id, file_name)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )


def s3_put_bytes(
    analysis_id: str,
    file_name: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    key = s3_key(analysis_id, file_name)
    s3.put_object(Bucket=bucket, Key=key, Body=content, ContentType=content_type)


def s3_list_files(analysis_id: str) -> list[str]:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    prefix = s3_prefix(analysis_id)
    files: list[str] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []) or []:
            key = obj.get("Key", "")
            if not key or not key.startswith(prefix):
                continue
            name = key[len(prefix):]
            if not name or name.endswith("/"):
                continue
            files.append(name)
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
            continue
        break
    return sorted(set(files), key=lambda s: s.lower())


def s3_get_text(analysis_id: str, file_name: str) -> str:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    key = s3_key(analysis_id, file_name)
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")
    body = resp.get("Body")
    if not body:
        return ""
    data = body.read()
    try:
        return data.decode("utf-8")
    except Exception:
        return data.decode("utf-8", errors="replace")


def s3_get_bytes(analysis_id: str, file_name: str) -> bytes:
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    key = s3_key(analysis_id, file_name)
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")
    body = resp.get("Body")
    if not body:
        return b""
    return body.read()


def delete_s3_prefix(analysis_id: str) -> None:
    """Delete all objects under analysis/{analysis_id}/ in S3."""
    s3 = get_s3_client()
    bucket = get_s3_bucket()
    prefix = s3_prefix(analysis_id)
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        contents = resp.get("Contents") or []
        keys = [{"Key": obj.get("Key")} for obj in contents if obj.get("Key")]
        if keys:
            try:
                s3.delete_objects(Bucket=bucket, Delete={"Objects": keys, "Quiet": True})
                print(f"[retention] deleted {len(keys)} S3 objects under {bucket}/{prefix}")
            except Exception as e:
                print(f"[retention] failed deleting S3 objects under {bucket}/{prefix}: {e}")
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
            continue
        break
