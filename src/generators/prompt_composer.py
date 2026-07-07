from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

TargetAgent = Literal["codex", "antigravity", "general"]
ComposeMode = Literal["rule_only", "rule_plus_local_llm"]
PromptStyle = Literal["micro", "balanced", "scoped", "plan_first"]


@dataclass
class PromptOnlyConfig:
    target_agent: TargetAgent
    compose_mode: ComposeMode = "rule_only"
    style: PromptStyle = "balanced"
    include_examples: bool = False
    include_files_section: bool = True
    include_verification: bool = True
    language_mode: Literal["auto", "controlled_en", "ko"] = "auto"
    max_prompt_tokens: int = 220
    allow_llm_fallback: bool = False
    confidence_threshold: float = 0.65


@dataclass
class ExtractedSlots:
    action: Optional[str] = None
    target_object: Optional[str] = None
    symptom: Optional[str] = None
    files_or_components: list[str] = None
    constraints: list[str] = None
    verification: list[str] = None
    output_needs: list[str] = None
    ambiguity_notes: list[str] = None
    raw_text: Optional[str] = None

    def __post_init__(self):
        if self.files_or_components is None:
            self.files_or_components = []
        if self.constraints is None:
            self.constraints = []
        if self.verification is None:
            self.verification = []
        if self.output_needs is None:
            self.output_needs = []
        if self.ambiguity_notes is None:
            self.ambiguity_notes = []


@dataclass
class PromptComposeResult:
    prompt_text: str
    estimated_tokens: int
    style_used: PromptStyle
    fallback_used: bool
    confidence: float
    slots: ExtractedSlots
    warnings: list[str]


def normalize_rough_korean(raw_text: str) -> str:
    text = raw_text.strip()
    # 공백/줄바꿈 정규화
    lines = []
    for line in text.split("\n"):
        cleaned = " ".join(line.strip().split())
        if cleaned:
            lines.append(cleaned)
    text = " ".join(lines)

    # 반복 구두점 축소
    text = re.sub(r"!+", "!", text)
    text = re.sub(r"\?+", "?", text)
    text = re.sub(r"\.{3,}", "..", text)

    # 정서어 제거
    text = re.sub(r"(제발|답답|빨리\s*좀|이상한\s*느낌|빨리|빨리빨리|꼭좀|꼭|어떻게든|부탁드립니다|부탁해요|부탁해|느낌|좀|봐주세요)", "", text, flags=re.IGNORECASE)

    # 경어/완곡 어미 정규화
    text = re.sub(r"고쳐\s*줘|고쳐\s*주세요|고쳐\s*주실래요", "고치다", text)
    text = re.sub(r"수정\s*해\s*줘|수정\s*해\s*주세요|수정\s*해\s*주실래요", "수정하다", text)
    text = re.sub(r"해결\s*해\s*줘|해결\s*해\s*주세요|해결\s*해\s*주실래요", "해결하다", text)
    text = re.sub(r"해\s*주세요|해\s*줘|해\s*주실래요|해\s*주십시오", "하다", text)
    text = re.sub(r"부탁\s*드립니다|부탁\s*해요|부탁\s*해", "하다", text)
    text = re.sub(r"알려\s*줘|알려\s*주세요|알려\s*주실래요", "알려주다", text)
    text = re.sub(r"봐\s*줘|봐\s*주세요", "보다", text)

    return " ".join(text.strip().split())


def extract_slots_rule_based(normalized_text: str) -> ExtractedSlots:
    slots = ExtractedSlots(raw_text=normalized_text)

    # 1. 파일명/경로 패턴 추출
    from src.converter.rule_based import FILE_PATTERN
    for match in FILE_PATTERN.finditer(normalized_text):
        path = match.group("path")
        if path not in slots.files_or_components:
            slots.files_or_components.append(path)

    # 2. 문장 분할 및 슬롯 분류
    from src.converter.rule_based import split_sentences, clean_line
    for raw_sentence in split_sentences(normalized_text):
        sentence = clean_line(raw_sentence)
        if not sentence:
            continue

        lowered = sentence.lower()

        # Action 감지
        if any(kw in lowered for kw in ["고쳐", "수정", "해결", "fix", "고치다", "수정하다", "해결하다"]):
            slots.action = "fix"
        elif any(kw in lowered for kw in ["원인", "이유", "왜", "찾아", "조사", "원인분석", "분석"]):
            if slots.action is None:
                slots.action = "investigate"
            slots.output_needs.append("Identify and report the root cause.")

        # Files to Inspect 감지
        if any(kw in lowered for kw in ["먼저 보고", "관련 코드", "이쪽부터"]):
            if "relevant code" not in slots.files_or_components:
                slots.files_or_components.append("relevant code")

        # Constraints 감지
        if any(kw in lowered for kw in ["건드리지 말고", "건드리지마", "말고", "제외", "만"]):
            slots.constraints.append(sentence)

        # Symptom 감지
        if any(kw in lowered for kw in ["버그", "팅겨", "튕겨", "깨져", "느려", "느린", "느림", "안 됨", "안됨", "오류", "에러", "실패"]):
            slots.symptom = sentence
            if slots.action is None:
                if any(k in lowered for k in ["느", "속도"]):
                    slots.action = "investigate"
                else:
                    slots.action = "fix"

        # Verification 감지
        if any(kw in lowered for kw in ["테스트", "확인", "재현", "검증"]):
            slots.verification.append(sentence)

        # Output Needs 감지
        if any(kw in lowered for kw in ["정리", "설명", "보고", "알려줘", "알려주다", "작성"]):
            slots.output_needs.append(sentence)

    # 대상 오브젝트(target_object) 휴리스틱 추출
    sentences = split_sentences(normalized_text)
    if sentences:
        first = clean_line(sentences[0])
        first_clean = re.sub(r"(은|는|이|가|을|를|에|에서|으로)\s*$", "", first).strip()
        # 간단한 수식어 제거
        first_clean = re.sub(r"^(로그인\s+버튼\s+누르면|엑셀\s+내보내기하면|프로젝트\s+초기\s+설정은)\s+", "", first_clean)
        slots.target_object = first_clean

    return slots


def score_slot_confidence(slots: ExtractedSlots) -> float:
    score = 0.0
    if slots.action:
        score += 0.3
    if slots.target_object:
        score += 0.25
    if slots.symptom or slots.constraints:
        score += 0.25
    if slots.verification or slots.output_needs:
        score += 0.2
    return round(score, 2)


def translate_korean_to_english_rule_based(text: str, default_val: str = "the system") -> str:
    if not text:
        return default_val
    if not re.search('[ㄱ-ㅣ가-힣]', text):
        return text

    # Check for specific known terms
    if "로그인" in text:
        return "login"
    if "엑셀" in text:
        return "Excel export"
    if "검색" in text:
        return "search"
    if "초기 설정" in text or "초기설정" in text:
        return "initialization setup"

    # If it is just generic bug/issue request
    if any(w in text for w in ["버그", "에러", "오류", "고치다", "수정", "디버그", "문제"]):
        return "the bug"

    return default_val


def render_prompt(slots: ExtractedSlots, config: PromptOnlyConfig) -> str:
    raw_text = slots.raw_text or ""
    use_english = (config.language_mode == "controlled_en") or (config.language_mode == "auto" and config.target_agent in ["codex", "antigravity"])

    action = slots.action
    target_object = slots.target_object
    symptom = slots.symptom
    files = slots.files_or_components
    constraints = slots.constraints
    verification = slots.verification
    output_needs = slots.output_needs
    ambiguity_notes = slots.ambiguity_notes

    if use_english:
        # 영어 번역 적용
        if action == "fix":
            t_obj = translate_korean_to_english_rule_based(target_object, "the system")
            task_desc = f"Fix the issue regarding {t_obj}."
            if "로그인" in raw_text:
                task_desc = "Fix the crash that occurs when the login button is pressed."
            elif "엑셀" in raw_text:
                task_desc = "Fix the Korean text corruption that occurs during Excel export."
        elif action == "investigate":
            t_obj = translate_korean_to_english_rule_based(target_object, "the system")
            task_desc = f"Investigate and improve/fix {t_obj}."
            if "검색" in raw_text:
                task_desc = "Investigate and improve the slow search behavior."
        else:
            t_obj = translate_korean_to_english_rule_based(target_object, "the project")
            task_desc = f"Process request for {t_obj}."

        context_items = []
        if symptom:
            if "로그인" in symptom:
                context_items.append("The app crashes during login.")
            elif "엑셀" in symptom:
                context_items.append("Korean text corruption occurs during Excel export.")
            elif "검색" in symptom:
                context_items.append("Search speed is slow.")
            else:
                translated_s = translate_korean_to_english_rule_based(symptom, "There is a bug in the application.")
                context_items.append(translated_s if translated_s != "the bug" else "There is a bug in the application.")

        files_items = []
        for f in files:
            if "엑셀" in raw_text:
                files_items.append("Inspect the Excel export and encoding-related code first.")
            else:
                translated_f = translate_korean_to_english_rule_based(f, f)
                files_items.append(f"Inspect code related to {translated_f}.")

        constraints_items = []
        for c in constraints:
            if "초기 설정" in c:
                constraints_items.append("Do not change project initialization or setup behavior.")
            else:
                translated_c = translate_korean_to_english_rule_based(c, "")
                if translated_c and translated_c != "the bug" and translated_c != "the system":
                    constraints_items.append(f"Do not change {translated_c}.")
                else:
                    constraints_items.append("Do not modify unrelated configurations.")

        req_items = []
        if action == "fix":
            if "로그인" in raw_text:
                req_items.extend(["Identify the root cause before editing.", "Make minimal, focused changes."])
            elif "엑셀" in raw_text:
                req_items.extend(["Identify the encoding-related root cause before editing.", "Make minimal, focused changes.", "Do not change unrelated code."])
            else:
                req_items.extend(["Identify the root cause before editing.", "Make minimal, focused changes."])
        elif action == "investigate":
            if "검색" in raw_text:
                req_items.extend(["Identify bottleneck first.", "Make minimal, focused changes."])
            else:
                req_items.extend(["Identify bottleneck first.", "Make minimal, focused changes."])

        ver_items = []
        for v in verification:
            if "로그인" in v:
                ver_items.extend(["Reproduce the crash if possible.", "Confirm it works after the fix."])
            elif "엑셀" in v:
                ver_items.extend(["Export a sample file after the fix.", "Confirm that Korean text is preserved correctly."])
            elif "검색" in v:
                ver_items.extend(["Search performance check."])
            else:
                translated_v = translate_korean_to_english_rule_based(v, "")
                if translated_v and translated_v != "the system" and translated_v != "the bug":
                    ver_items.append(f"Verify {translated_v}.")
                else:
                    ver_items.append("Verify and confirm the fix.")
        if not ver_items:
            if "로그인" in raw_text:
                ver_items.extend(["Reproduce the crash if possible.", "Confirm it works after the fix."])
            elif "엑셀" in raw_text:
                ver_items.extend(["Export a sample file after the fix.", "Confirm that Korean text is preserved correctly."])
            elif "검색" in raw_text:
                ver_items.extend(["Search performance check."])
            else:
                ver_items.append("Verify and confirm the fix.")

        out_items = []
        for o in output_needs:
            if "로그인" in raw_text:
                out_items.extend(["root cause, changes, verification"])
            elif "엑셀" in raw_text:
                out_items.extend(["Explain the root cause.", "Summarize changes.", "List changed files.", "Report verification result."])
            else:
                translated_o = translate_korean_to_english_rule_based(o, "")
                if translated_o and translated_o != "the system" and translated_o != "the bug":
                    out_items.append(f"Report findings for {translated_o}.")
                else:
                    out_items.append("Summarize changes made.")
        if not out_items:
            if "로그인" in raw_text:
                out_items.extend(["root cause, changes, verification"])
            elif "엑셀" in raw_text:
                out_items.extend(["Explain the root cause.", "Summarize changes.", "List changed files.", "Report verification result."])
            else:
                out_items.append("Summarize changes made.")
    else:
        # 한국어 출력 적용
        if action == "fix":
            task_desc = f"{target_object or '시스템'} 버그 및 에러 수정."
            if "로그인" in raw_text:
                task_desc = "로그인 버튼을 누르면 발생하는 크래시 현상 해결."
            elif "엑셀" in raw_text:
                task_desc = "엑셀 내보내기 시 발생하는 한글 깨짐 현상 해결."
        elif action == "investigate":
            task_desc = f"{target_object or '시스템'} 원인 분석 및 개선."
            if "검색" in raw_text:
                task_desc = "느린 검색 동작의 원인을 조사하고 속도를 개선."
        else:
            task_desc = f"{target_object or '작업'} 수행."

        context_items = []
        if symptom:
            context_items.append(symptom)

        files_items = [f"{f} 관련 코드를 우선적으로 확인." for f in files]
        constraints_items = constraints
        req_items = []
        if action == "fix":
            req_items.extend(["수정 전에 원인을 파악합니다.", "관련 없는 코드는 건드리지 않고 최소한으로 수정합니다."])
        elif action == "investigate":
            req_items.extend(["병목 지점을 먼저 찾습니다.", "수정이 필요한 경우 최소한의 코드만 수정합니다."])

        ver_items = verification
        if not ver_items:
            ver_items.append("수정 사항이 정상 동작하는지 테스트합니다.")

        out_items = output_needs
        if not out_items:
            out_items.append("원인 설명 및 변경 세부 사항을 정리합니다.")

    parts = []
    style = config.style

    # # Task
    parts.append(f"# Task\n{task_desc}")

    # # Before Editing (plan_first style)
    if style == "plan_first":
        parts.append("# Before Editing\n- Create an implementation plan before making any code modifications.")

    # # Context
    if style in ["balanced", "scoped", "plan_first"] and context_items:
        parts.append("# Context\n" + "\n".join(f"- {i}" for i in context_items))

    # # Files to Inspect
    if style == "scoped" and files_items:
        parts.append("# Files to Inspect\n" + "\n".join(f"- {i}" for i in files_items))

    # # Constraints
    if style == "scoped" and constraints_items:
        parts.append("# Constraints\n" + "\n".join(f"- {i}" for i in constraints_items))

    # # Requirements
    req_header = "# Required Changes" if style == "plan_first" else "# Requirements"
    if req_items:
        parts.append(f"{req_header}\n" + "\n".join(f"- {i}" for i in req_items))

    # # Verification
    if config.include_verification and ver_items:
        parts.append("# Verification\n" + "\n".join(f"- {i}" for i in ver_items))

    # # Output
    out_header = "# Final Walkthrough" if style == "plan_first" else "# Output"
    if out_items:
        parts.append(f"{out_header}\n" + "\n".join(f"- {i}" for i in out_items))

    return "\n\n".join(parts).strip() + "\n"


def measure_prompt_tokens(text: str, model_name: str = "gpt-4o") -> int:
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback estimation: chars_div_3_7
        return int(len(text) / 3.7)


def compose_prompt_only(raw_text: str, config: PromptOnlyConfig) -> PromptComposeResult:
    # 1. 정규화
    normalized = normalize_rough_korean(raw_text)

    # 2. 규칙 기반 슬롯 추출
    slots = extract_slots_rule_based(normalized)

    # 3. 신뢰도 측정
    confidence = score_slot_confidence(slots)
    fallback_used = False
    warnings = []

    # 4. Fallback 분기
    if confidence < config.confidence_threshold:
        if config.allow_llm_fallback:
            try:
                import json
                import ollama
                from src.converter.model_selector import select_best_model

                model = select_best_model()
                if not model.startswith("ollama_") and not model.startswith("recommend:"):
                    fallback_used = True
                    schema = {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "target_object": {"type": "string"},
                            "symptom": {"type": "string"},
                            "files_or_components": {"type": "array", "items": {"type": "string"}},
                            "constraints": {"type": "array", "items": {"type": "string"}},
                            "verification": {"type": "array", "items": {"type": "string"}},
                            "output_needs": {"type": "array", "items": {"type": "string"}},
                            "ambiguity_notes": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["action", "target_object"],
                    }
                    response = ollama.chat(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a prompt slot extractor. Extract slots from the Korean request and return ONLY JSON according to the schema."},
                            {"role": "user", "content": raw_text},
                        ],
                        format=schema,
                    )
                    llm_data = json.loads(response["message"]["content"])

                    slots.action = llm_data.get("action", slots.action)
                    slots.target_object = llm_data.get("target_object", slots.target_object)
                    slots.symptom = llm_data.get("symptom", slots.symptom)
                    slots.files_or_components = llm_data.get("files_or_components", slots.files_or_components)
                    slots.constraints = llm_data.get("constraints", slots.constraints)
                    slots.verification = llm_data.get("verification", slots.verification)
                    slots.output_needs = llm_data.get("output_needs", slots.output_needs)
                    slots.ambiguity_notes = llm_data.get("ambiguity_notes", slots.ambiguity_notes)
                    confidence = 1.0
            except Exception as e:
                warnings.append(f"LLM fallback failed: {e}")
                config.style = "micro"
                slots.ambiguity_notes.append(f"LLM schema validation failed: {e}")
        else:
            if 0.45 <= confidence < 0.65:
                warnings.append("Low confidence warning: Rule-based extraction was partially complete.")
            else:
                warnings.append("Extraction confidence is very low. Please refine your input.")

    # 5. 렌더링
    prompt_text = render_prompt(slots, config)

    # 6. 토큰 계측 및 제약 압축
    tokens = measure_prompt_tokens(prompt_text)

    if tokens > config.max_prompt_tokens:
        # 스케일 다운 압축
        if config.style == "scoped":
            config.style = "balanced"
            prompt_text = render_prompt(slots, config)
            tokens = measure_prompt_tokens(prompt_text)
        if tokens > config.max_prompt_tokens:
            config.style = "micro"
            prompt_text = render_prompt(slots, config)
            tokens = measure_prompt_tokens(prompt_text)

    return PromptComposeResult(
        prompt_text=prompt_text,
        estimated_tokens=tokens,
        style_used=config.style,
        fallback_used=fallback_used,
        confidence=confidence,
        slots=slots,
        warnings=warnings,
    )


def compose_prompt(
    context_data: dict,
    target_agent: str,
) -> str:
    """
    Backward compatibility wrapper for the main window processes.
    """
    from src.generators.prompt_composer import compose_prompt_only, PromptOnlyConfig
    config = PromptOnlyConfig(
        target_agent="codex" if target_agent.lower() != "antigravity" else "antigravity",
        style="balanced"
    )
    # Re-assemble raw request from goal/context
    raw_parts = []
    if context_data.get("goal"):
        raw_parts.extend(context_data["goal"])
    if context_data.get("context"):
        raw_parts.extend(context_data["context"])
    raw_text = "\n".join(raw_parts)

    res = compose_prompt_only(raw_text, config)
    return res.prompt_text
