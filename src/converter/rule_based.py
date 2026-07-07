import re

def convert_rule_based(raw_text: str) -> dict:
    """
    Mode A: Fast, deterministic rule-based conversion.
    Returns a dictionary matching the expected JSON structure for templates.
    """
    context_data = {
        "project": [],
        "environment": [],
        "workflow": [],
        "rules": [],
        "forbidden": [],
        "verification": []
    }
    
    # Very basic heuristic classification
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Basic filler removal (Korean)
        line = re.sub(r'^(음|아|그러니까|저기|그냥|이게)\s*', '', line)
        
        # Classification by keyword
        if any(kw in line for kw in ["금지", "하지 마", "안돼", "never", "do not"]):
            context_data["forbidden"].append(line)
        elif any(kw in line for kw in ["워크플로", "진행", "순서", "단계"]):
            context_data["workflow"].append(line)
        elif any(kw in line for kw in ["환경", "버전", "설치", "OS"]):
            context_data["environment"].append(line)
        elif any(kw in line for kw in ["테스트", "검증", "확인", "test"]):
            context_data["verification"].append(line)
        elif any(kw in line for kw in ["규칙", "코딩", "스타일", "rule"]):
            context_data["rules"].append(line)
        else:
            # Default to project description
            context_data["project"].append(line)
            
    # Deduplication
    for k in context_data:
        context_data[k] = list(dict.fromkeys(context_data[k]))
        
    return context_data
