"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from apps.content.models import ContentResource, DigitalTextbook
from apps.courses.models import Course
from apps.curriculum.models import Competency, LearningOutcome

MAX_QUESTION_LENGTH = 1000
MIN_GROUNDING_SCORE = 4
TOP_MATCHES = 3
_HTTP_TIMEOUT_SECONDS = 10

_WORD_RE = re.compile(r"[a-z0-9]+")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")

# Words that help a human ask a question but carry no curriculum meaning.
_STOP_WORDS = frozenset({
    "a", "about", "am", "an", "and", "any", "are", "as", "at", "be", "been",
    "but", "by", "can", "could", "did", "do", "does", "for", "from", "get",
    "give", "go", "have", "help", "how", "i", "if", "in", "is", "it", "me",
    "my", "of", "on", "or", "our", "please", "question", "show", "so", "tell",
    "that", "the", "their", "this", "to", "us", "want", "was", "we", "what",
    "when", "where", "which", "who", "why", "will", "with", "would", "you",
    "your", "explain", "describe", "define", "means", "mean",
})

# A deliberately small signal set: it only decides whether to bother searching,
# never what answer to give. Every answer still comes from stored records.
_EDUCATION_TERMS = frozenset({
    "add", "addition", "agriculture", "answer", "art", "assignment", "biology",
    "book", "business", "calculate", "chapter", "chemistry", "class", "compare",
    "competency", "computer", "course", "creative", "curriculum", "divide",
    "division", "english", "exercise", "exam", "fraction", "fractions",
    "geography", "geometry", "grade", "history", "homework", "ict", "kiswahili",
    "learning", "lesson", "marks", "math", "mathematics", "maths", "measurement",
    "music", "number", "numbers", "outcome", "physics", "practice", "practise",
    "question", "quiz", "represent", "resource", "revision", "revise", "science",
    "score", "solve", "sports", "standard", "strand", "study", "subject",
    "subtraction", "teacher", "test", "textbook", "topic", "whole", "write",
})

_SOURCE_LABELS = {
    "outcome": "Learning outcome",
    "competency": "Competency",
    "resource": "Learning resource",
    "textbook": "Textbook",
    "course": "Course",
}

_FALLBACK_ANSWER = (
    "I could not find a matching curriculum record for that question. "
    "Try rephrasing it with the subject, topic or curriculum code, or ask your teacher."
)
_FALLBACK_SUGGESTIONS = [
    "Rephrase your question with a subject or topic.",
    "Ask your teacher for guidance.",
]


def _strip_controls(value: Any) -> str:
    """Remove C0/C1 control characters while keeping normal line breaks."""
    return "".join(
        char for char in str(value or "")
        if char in "\n\r\t" or unicodedata.category(char) != "Cc"
    )


def _safe_text(value: Any) -> str:
    """Collapse whitespace and drop URLs/e-mail addresses from stored text.

    Stored records are the only source of answer text. URLs and e-mail addresses
    are removed so a malformed import cannot turn into a link or personal data
    in a tutor reply.
    """
    text = _strip_controls(value)
    text = _URL_RE.sub("", text)
    text = _EMAIL_RE.sub("", text)
    return " ".join(text.split())


def clean_question(question: Any) -> str:
    """Strip control characters, normalise whitespace and cap question length."""
    return " ".join(_strip_controls(question).split())[:MAX_QUESTION_LENGTH]


def tokenise(value: Any) -> list[str]:
    """Lowercase, strip punctuation and return word/number tokens."""
    return _WORD_RE.findall(_strip_controls(value).lower())


def _is_learning_related(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if any(token in _EDUCATION_TERMS for token in tokens):
        return True
    # "What is 12 x 4?" is a learning question even without a subject word.
    return any(any(char.isdigit() for char in token) for token in tokens)


def format_source(source: Any) -> str:
    """Human-readable, label-only rendering of a stored source reference."""
    if not isinstance(source, dict):
        return ""
    kind = str(source.get("kind") or "record")
    code = _safe_text(source.get("code"))[:60]
    label = _safe_text(source.get("label"))[:180]
    prefix = _SOURCE_LABELS.get(kind, "Record")
    header = f"{prefix} {code}".strip()
    return f"{header}: {label}" if label else header


def _fallback() -> dict:
    return {
        "answer": _FALLBACK_ANSWER,
        "sources": [],
        "suggestions": list(_FALLBACK_SUGGESTIONS),
        "grounded": False,
    }


def _candidate(
    kind: str,
    instance: Any,
    fields: tuple[str, ...],
    code_field: int | None = 0,
) -> dict:
    values = [_safe_text(getattr(instance, name, "")) for name in fields]
    if code_field is None:
        # Models without a stored business code get a stable local identifier.
        code = f"{kind.upper()}-{instance.pk}"
        label_parts = values
    else:
        code = values[code_field] if code_field < len(values) and values[code_field] else ""
        code = code or f"{kind.upper()}-{instance.pk}"
        label_parts = [
            value for index, value in enumerate(values) if index != code_field and value
        ]
    label_text = " ".join(label_parts) or code
    return {
        "kind": kind,
        "code": code[:60],
        "label": label_text[:180],
        "texts": [value for value in values if value],
        "score": 0,
    }


def _candidate_records(institution: Any) -> list[dict]:
    """Build locally scoped candidates.

    Learning outcomes, competencies, textbooks and resources are platform-level
    catalogue/reference records with no institution field, so they are shared.
    Courses are private school records and are filtered strictly by institution.
    No learner-owned or assessment-owned record is ever a candidate.
    """
    candidates = [
        _candidate("outcome", record, ("code", "description"))
        for record in LearningOutcome.objects.all()
    ]
    candidates.extend(
        _candidate("competency", record, ("code", "name", "description"))
        for record in Competency.objects.all()
    )
    candidates.extend(
        _candidate("textbook", record, ("isbn", "title", "subtitle", "description"))
        for record in DigitalTextbook.objects.all()
    )
    candidates.extend(
        _candidate("resource", record, ("title", "description", "resource_type"), code_field=None)
        for record in ContentResource.objects.all()
    )
    if institution is not None and getattr(institution, "pk", None) is not None:
        candidates.extend(
            _candidate("course", record, ("code", "title", "description"))
            for record in Course.objects.filter(institution=institution)
        )
    return candidates


def _score_candidate(question_text: str, significant: set[str], candidate: dict) -> int:
    score = 0
    for text in candidate["texts"]:
        normalised = " ".join(tokenise(text))
        if not normalised:
            continue
        if question_text and question_text in normalised:
            score += 12
        score += 4 * len(significant.intersection(normalised.split()))
    # An explicit code or outcome identifier is a strong, exact signal.
    for token in tokenise(candidate["code"]):
        if len(token) > 2 and token in significant:
            score += 6
    return score


def _suggestions(matches: list[dict]) -> list[str]:
    suggestions: list[str] = []
    for match in matches:
        label = match["label"]
        code = match["code"]
        if match["kind"] == "resource":
            suggestion = f'Open the learning resource "{label}" from your course materials.'
        elif match["kind"] == "textbook":
            suggestion = f'Read the relevant section of "{label}".'
        elif match["kind"] == "outcome":
            suggestion = f'Practise the outcome "{code}" with your teacher or in class.'
        elif match["kind"] == "competency":
            suggestion = f'Practise the competency "{label}" in class.'
        else:
            suggestion = f'Review the course "{label}".'
        if suggestion not in suggestions:
            suggestions.append(suggestion)
    suggestions.append("Ask your teacher if you need help with this topic.")
    return suggestions[:5]


def answer_question(question: Any, institution: Any) -> dict:
    """Return {answer, sources, suggestions, grounded} using stored records only."""
    cleaned = clean_question(question)
    tokens = tokenise(cleaned)
    if not _is_learning_related(tokens):
        return _fallback()

    question_text = " ".join(tokens)
    significant = {
        token for token in tokens
        if token not in _STOP_WORDS and len(token) > 1
    }
    if not significant:
        return _fallback()

    scored = []
    for candidate in _candidate_records(institution):
        candidate["score"] = _score_candidate(question_text, significant, candidate)
        if candidate["score"] >= MIN_GROUNDING_SCORE:
            scored.append(candidate)
    if not scored:
        return _fallback()

    # Fully deterministic ordering: score first, then stable identity fields.
    scored.sort(key=lambda item: (
        -item["score"], item["kind"], item["code"], item["label"],
    ))
    matches = scored[:TOP_MATCHES]
    sources = [
        {"kind": item["kind"], "code": item["code"], "label": item["label"]}
        for item in matches
    ]
    lines = ["I found matching information in the stored curriculum records:"]
    lines.extend(f"- {format_source(source)}" for source in sources)
    return {
        "answer": "\n".join(lines),
        "sources": sources,
        "suggestions": _suggestions(matches),
        "grounded": True,
    }


class ProviderAdapter(Protocol):
    """Minimal contract shared by the local and optional HTTP adapters."""

    name: str

    def answer(self, question: Any, institution: Any) -> dict:
        ...


class LocalProvider:
    """Default adapter: deterministic, offline and grounded in stored records."""

    name = "local"

    def answer(self, question: Any, institution: Any) -> dict:
        return answer_question(question, institution)


class HttpProvider:
    """Optional adapter. Credentials are read from the environment per call.

    If either variable is unset the local answer is returned without any
    network access. A remote answer is accepted only when it is a verbatim
    excerpt of the grounded local answer, so it cannot add marks, URLs or
    invented facts. The key is sent as a header only: it is never logged,
    returned or serialised.
    """

    name = "http"

    def _configuration(self) -> tuple[str, str]:
        return (
            (os.environ.get("KLB_TUTOR_API_URL") or "").strip(),
            (os.environ.get("KLB_TUTOR_API_KEY") or "").strip(),
        )

    def answer(self, question: Any, institution: Any) -> dict:
        local = answer_question(question, institution)
        url, key = self._configuration()
        if not url or not key:
            return local

        payload = json.dumps({
            "question": clean_question(question),
            "institution_id": getattr(institution, "pk", None),
        }).encode("utf-8")
        request = Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (URLError, OSError, ValueError, UnicodeDecodeError):
            return local

        if not isinstance(data, dict):
            return local
        remote_answer = data.get("answer")
        if not isinstance(remote_answer, str):
            return local
        remote_answer = " ".join(remote_answer.split())
        if not remote_answer or remote_answer not in local["answer"]:
            return local
        return {**local, "answer": remote_answer}


def get_provider() -> ProviderAdapter:
    """Select the adapter by name; unknown or unset values stay fully local."""
    name = (os.environ.get("KLB_TUTOR_PROVIDER") or "local").strip().lower()
    if name == "http":
        return HttpProvider()
    return LocalProvider()
