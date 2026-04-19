"""
Automated response validation for Bedrock chat output.
Ensures responses are grounded, safe, and enterprise-ready.
"""
from __future__ import annotations

import re
import math
from collections import Counter

# Thresholds
CITATION_COVERAGE_THRESHOLD = 0.80
GROUNDING_DELTA_SIMILARITY_THRESHOLD = 0.6


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens."""
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def _cosine_similarity(a: str, b: str) -> float:
    """Cosine similarity between two strings (word bag)."""
    va = Counter(_tokenize(a))
    vb = Counter(_tokenize(b))
    if not va or not vb:
        return 0.0
    dot = sum(va[k] * vb[k] for k in va if k in vb)
    na = math.sqrt(sum(x * x for x in va.values()))
    nb = math.sqrt(sum(x * x for x in vb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _forbidden_check(text: str) -> list[str]:
    """Hard fail if response contains forbidden content."""
    violations = []
    # days, weeks, hours (as standalone words or with numbers)
    if re.search(r"\b\d*\s*(day|days|week|weeks|hour|hours)\b", text, re.I):
        violations.append("Contains forbidden timeline (days/weeks/hours)")
    if re.search(r"\$\d|%\s*\d|\d\s*%", text):
        violations.append("Contains $ or % (costs/percentages)")
    if re.search(r"\bCVE-\d", text, re.I):
        violations.append("Contains CVE reference")
    # Follow-up questions: line ending with ?
    for line in text.split("\n"):
        if line.strip().endswith("?"):
            violations.append("Contains follow-up question (line ending with ?)")
            break
    return violations


def _citation_coverage(text: str) -> tuple[float, str | None]:
    """Split into sentences; require >= 80% to include a filename (*.md)."""
    text = text.strip()
    if not text:
        return 1.0, None
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return 1.0, None
    cited = sum(1 for s in sentences if re.search(r"[^\s]+\.md", s))
    ratio = cited / len(sentences)
    if ratio < CITATION_COVERAGE_THRESHOLD:
        return ratio, f"Citation coverage {ratio:.0%} below {CITATION_COVERAGE_THRESHOLD:.0%} (weakly grounded)"
    return ratio, None


def _inference_labeling(text: str) -> list[str]:
    """Any sentence without citation must start with '[Inference]'."""
    violations = []
    text = text.strip()
    if not text:
        return violations
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    for s in sentences:
        has_citation = bool(re.search(r"[^\s]+\.md", s))
        if not has_citation and not s.startswith("[Inference]"):
            violations.append(f"Uncited sentence must start with [Inference]: \"{s[:60]}...\"")
    return violations


def validate_response(
    answer: str,
    empty_context_answer: str | None = None,
    similarity_threshold: float = GROUNDING_DELTA_SIMILARITY_THRESHOLD,
) -> dict:
    """
    Run all validation checks. Do not crash; return report.
    Returns: { "passed": bool, "violations": list[str] }
    """
    violations: list[str] = []

    # 1. Forbidden content (hard fail)
    violations.extend(_forbidden_check(answer))

    # 2. Citation coverage
    _, citation_v = _citation_coverage(answer)
    if citation_v:
        violations.append(citation_v)

    # 3. Inference labeling
    violations.extend(_inference_labeling(answer))

    # 4. Grounding delta (if empty-context answer provided)
    if empty_context_answer is not None:
        sim = _cosine_similarity(answer, empty_context_answer)
        if sim > similarity_threshold:
            violations.append(f"Grounding delta: similarity with empty-context answer {sim:.2f} > {similarity_threshold} (hallucination risk)")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }
