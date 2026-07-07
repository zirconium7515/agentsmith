import psutil
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

RECOMMENDED_MODELS = ["qwen2", "gemma2", "llama3"]

def get_system_ram_gb() -> float:
    return psutil.virtual_memory().total / (1024**3)

def select_best_model() -> str:
    """Selects the best available Ollama model or recommends one."""
    if not OLLAMA_AVAILABLE:
        return "ollama_not_installed"
        
    try:
        response = ollama.list()
        installed_models = [m['name'] for m in response.get('models', [])]
    except Exception:
        return "ollama_service_down"
        
    if not installed_models:
        # Check RAM to recommend
        ram_gb = get_system_ram_gb()
        if ram_gb > 15:
            return "recommend:gemma2"
        else:
            return "recommend:qwen2"
            
    # Prefer recommended models if already installed
    for rec in RECOMMENDED_MODELS:
        for installed in installed_models:
            if rec in installed.lower():
                return installed
                
    # Fallback to the first installed model
    return installed_models[0]
