import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from commonlib.environmentUtil import getEnv
from commonlib.terminalColor import cyan

MODEL_ID = getEnv('AI_ENRICHNEW_MODEL_ID', "Qwen/Qwen2.5-1.5B-Instruct")
_PIPELINE = None

def get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        print(cyan(f"Loading local model: {MODEL_ID}..."))
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, padding_side='left')
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        _PIPELINE = pipeline(
            "text-generation", 
            model=model, 
            tokenizer=tokenizer, 
            max_new_tokens=int(getEnv('AI_ENRICHNEW_MAX_NEW_TOKENS', '2048')), 
            temperature=float(getEnv('AI_ENRICHNEW_TEMPERATURE', '0.1')), 
            top_p=float(getEnv('AI_ENRICHNEW_TOP_P', '0.9')),
            repetition_penalty=float(getEnv('AI_ENRICHNEW_REPETITION_PENALTY', '1.1')),
            return_full_text=False,
            batch_size=int(getEnv('AI_ENRICHNEW_BATCH_SIZE', '10')) # Explicitly pass batch_size to pipeline init if needed, though usually handled at call time
        )
        print(cyan("Local model loaded."))
    return _PIPELINE
