import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from commonlib.terminalColor import cyan

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
_PIPELINE = None

def get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        print(cyan(f"Loading local model: {MODEL_ID}..."))
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        _PIPELINE = pipeline(
            "text-generation", 
            model=model, 
            tokenizer=tokenizer, 
            max_new_tokens=2048, 
            temperature=0.1, 
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=False
        )
        print(cyan("Local model loaded."))
    return _PIPELINE
