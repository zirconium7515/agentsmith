import json
try:
    import ollama
except ImportError:
    pass

PROMPT_TEMPLATE = """
다음의 거친 한국어 프로젝트 노트와 컨텍스트를 분석하여 AI 코딩 에이전트가 이해하기 쉬운 형태의 JSON으로 변환해줘.
감정적인 표현이나 중복된 내용은 제거하고, 간결한 기술적 영어(Technical English) 요약(Bullet point 형식)으로 작성해줘. 한국어는 필요한 경우에만 유지해.

반드시 다음 JSON 스키마를 엄격하게 준수해서 출력해:
{
  "project": ["project description bullet 1", "bullet 2"],
  "environment": ["env detail 1", "env detail 2"],
  "workflow": ["step 1", "step 2"],
  "rules": ["coding rule 1", "rule 2"],
  "forbidden": ["forbidden action 1"],
  "verification": ["test command 1"]
}

원본 텍스트:
{raw_text}
"""

def convert_llm_based(raw_text: str, model_name: str) -> dict:
    """
    Mode B: High-quality LLM-based semantic compression.
    """
    prompt = PROMPT_TEMPLATE.replace("{raw_text}", raw_text)
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.0},
            format='json'
        )
        
        result_text = response['message']['content']
        return json.loads(result_text)
    except Exception as e:
        print(f"LLM Conversion Error: {e}")
        return {
            "error": str(e)
        }
