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
        "버그",
        "에러",
        "오류",
        "디버그",
        "수정",
        "해결",
        "개선",
        "작업",
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
        "push",
        "푸시",
        "git pull",
        "git status",
        "commit message",
        "version in commit",
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


def normalize_lookup_key(text: str) -> str:
    return re.sub(r"[\s.,\/#!$%\^&\*;:{}=\-_`~()\[\]\"'?|]", "", text).lower()


KOREAN_TO_ENGLISH_MAP = {
    # Workflow
    "프로젝트를 개발할 때는 원본 코드가 있는 윈도우의 구글 드라이브 상에서 진행한다": "Active development must happen in the Windows Google Drive workspace.",
    "구글 드라이브 스트림 모드를 통해 윈도우 파일 탐색기 상에서 원본 코드를 개발 및 수정 한다": "Use Google Drive stream mode to edit source files in Windows File Explorer.",
    "프로젝트는 구글 드라이브에서 개발을 하며, 실제 코드 실행 및 배포는 해당 코드를 개발한 구글 드라이브 혹은 로컬에서 구동한다": "Active development is in Google Drive; execution and deployment happen in Google Drive or local runtime.",
    "로컬에서 구동할 경우 git pull을 통해 업데이트를 받는다": "Runtime machines update through git pull.",
    "따라서 개발은 반드시 구글드라이브 상에서만 한다": "Active development must happen in the Google Drive workspace.",
    # Git rules
    "개발한 코드는 깃헙에 push 한다": "Push developed code to GitHub.",
    "git push를 할 경우 commit 메세지에 버전을 표기한다": "Include the version in the commit message when pushing to GitHub.",
    "버전룰에 맞춰서 push한다": "Push to GitHub according to versioning rules.",
    "깃헙에 push는 다음의 버전룰에 맞춰서 push한다": "Push to GitHub according to versioning rules.",
    # Versioning rules
    "버전룰: 버전은 다음과 같이 표시한다. vX.Y.Z": "Use version format vX.Y.Z.",
    "버전룰: 버전은 다음과 같이 표시한다": "Use version format vX.Y.Z.",
    "버전은 다음과 같이 표시한다": "Use version format vX.Y.Z.",
    "vx.y.z 다음의 x y z인덱스는 모두 만족하는 조건의 패치가 있을 때마다 1씩 올린다": "Increment X, Y, and Z indexes by 1 when patch conditions are met.",
    "vX.Y.Z 다음의 X Y Z인덱스는 모두 만족하는 조건의 패치가 있을 때마다 1씩 올린다": "Increment X, Y, and Z indexes by 1 when patch conditions are met.",
    "다음의 X Y Z인덱스는 모두 만족하는 조건의 패치가 있을 때마다 1씩 올린다": "Increment X, Y, and Z indexes by 1 when patch conditions are met.",
    "X는 대규모 패치이다": "Increment X for large-scale patches.",
    "Y는 X버전 상에서 주요 기능의 추가 및 개편이 있는 패치이다": "Increment Y for major feature additions or redesigns within the same X version.",
    "Z는 Y버전 상에서 소규모 기능의 패치 혹은 버그 패치 등 자잘한 패치이다": "Increment Z for small feature patches, bug fixes, or minor maintenance patches within the same Y version.",
    # Ignore rules
    "venv등의 무거운 실행 프로그램들은 구글 드라이브 상에서 구동하기 힘드므로 gitignore에 넣는다": "Add virtual environments such as venv/ to .gitignore.",
}

NORM_KOREAN_TO_ENGLISH_MAP = {
    normalize_lookup_key(ko): en for ko, en in KOREAN_TO_ENGLISH_MAP.items()
}


def translate_line(line: str) -> str:
    key = normalize_lookup_key(line)
    if key in NORM_KOREAN_TO_ENGLISH_MAP:
        return NORM_KOREAN_TO_ENGLISH_MAP[key]
    return line


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
        line = translate_line(line)
        context_data[field].append(line)

    return normalize_context({key: dedupe(value) for key, value in context_data.items()})
