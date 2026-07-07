from __future__ import annotations

import re

from src.converter.schema import dedupe, empty_context, normalize_context


FILLER_PREFIXES = (
    "그러니까",
    "약간",
    "그냥",
    "뭐랄까",
    "일단",
    "그리고",
    "아 그리고",
    "좋아",
    "음",
)

KEYWORDS = {
    "goal": [
        "목표",
        "목적",
        "만들고",
        "하고 싶은",
        "구현",
        "개발",
        "기능",
        "goal",
        "objective",
    ],
    "environment": [
        "환경",
        "버전",
        "설치",
        "윈도우",
        "windows",
        "python",
        "ollama",
        "dependency",
        "의존성",
        "os",
    ],
    "workflow": [
        "워크플로우",
        "절차",
        "순서",
        "진행",
        "프로세스",
        "구글 드라이브",
        "구글드라이브",
        "google drive",
        "googledrive",
        "github",
        "git pull",
        "배포",
        "업데이트",
        "삭제",
        "설치",
        "workflow",
    ],
    "rules": [
        "규칙",
        "원칙",
        "지켜",
        "유지",
        "보존",
        "스타일",
        "정책",
        "rule",
        "policy",
    ],
    "git_rules": [
        "git push",
        "commit",
        "커밋",
        "브랜치",
        "branch",
        "github",
        "깃헙",
        "깃허브",
    ],
    "versioning_rules": [
        "버전",
        "vx.y.z",
        "version",
        "패치",
        "인덱스",
    ],
    "dependency_rules": [
        "venv",
        "dependency",
        "의존성",
        "pip",
        "패키지",
    ],
    "ignore_rules": [
        "gitignore",
        "무거운",
        "제외",
        "ignore",
    ],
    "constraints": [
        "제약",
        "조건",
        "범위",
        "토글",
        "모드",
        "우선순위",
        "constraint",
        "scope",
    ],
    "forbidden": [
        "금지",
        "하지 마",
        "하지마",
        "하면 안",
        "절대",
        "코딩하지",
        "수정하지",
        "삭제하지",
        "never",
        "do not",
        "don't",
        "forbidden",
    ],
    "verification": [
        "테스트",
        "검증",
        "확인",
        "실행",
        "빌드",
        "pytest",
        "compile",
        "run",
        "verification",
        "check",
    ],
    "output_format": [
        "출력",
        "보고",
        "정리",
        "포맷",
        "형식",
        "문서",
        "파일",
        "output",
        "format",
        "report",
    ],
}

FILE_PATTERN = re.compile(
    r"(?P<path>(?:[\w.-]+[\\/])+[\w .가-힣()-]+\.[A-Za-z0-9]+|[\w.-]+\.(?:md|txt|py|json|bat|cs|yml|yaml|toml|ini))"
)


def clean_line(line: str) -> str:
    text = " ".join(line.strip().split())
    text = re.sub(r"^[#>*\-\d.)\s]+", "", text).strip()
    for prefix in FILLER_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :].strip(" ,:.-")
    return text


def split_sentences(raw_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in raw_text.replace("\r\n", "\n").split("\n"):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not stripped.startswith(("-", "*", "#")):
            parts = re.split(r"(?<=[.!?。])\s+", stripped)
            lines.extend(part for part in parts if part.strip())
        else:
            lines.append(stripped)
    return lines


def classify_line(line: str) -> str:
    lowered = line.lower()
    for field in (
        "forbidden",
        "ignore_rules",
        "dependency_rules",
        "versioning_rules",
        "git_rules",
        "workflow",
        "verification",
        "environment",
        "goal",
        "constraints",
        "rules",
        "output_format",
    ):
        if field in KEYWORDS and any(keyword in lowered for keyword in KEYWORDS[field]):
            return field
    return "context"


def extract_files(line: str) -> list[str]:
    return [match.group("path") for match in FILE_PATTERN.finditer(line)]


def convert_rule_based(raw_text: str) -> dict[str, list[str]]:
    """
    Fast offline conversion for Korean project notes and task requests.
    It favors deterministic cleanup over semantic rewriting.
    """
    context_data = empty_context()

    for raw_line in split_sentences(raw_text):
        line = clean_line(raw_line)
        if not line:
            continue

        for file_path in extract_files(line):
            context_data["files"].append(file_path)

        field = classify_line(line)
        context_data[field].append(line)

    return normalize_context({key: dedupe(value) for key, value in context_data.items()})
