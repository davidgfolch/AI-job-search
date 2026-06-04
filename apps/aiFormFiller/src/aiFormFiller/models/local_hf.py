import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from commonlib.terminalColor import cyan
from .base import AIProvider, AnswerResult


_PIPELINE = None
_MODEL_ID = None


def get_pipeline(model_id: str):
    global _PIPELINE, _MODEL_ID
    if _PIPELINE is None or _MODEL_ID != model_id:
        print(cyan(f"Loading local HF model: {model_id}..."))
        tokenizer = AutoTokenizer.from_pretrained(model_id, padding_side='left')
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        _PIPELINE = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            return_full_text=False,
            batch_size=1
        )
        _MODEL_ID = model_id
        print(cyan("Local HF model loaded."))
    return _PIPELINE


class LocalHFProvider(AIProvider):
    def __init__(self, model_id: str):
        self.model_id = model_id

    def generate(self, system_prompt: str, user_message: str, timeout: float, max_tokens: int, temperature: float) -> AnswerResult:
        pipe = get_pipeline(self.model_id)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False)
        outputs = pipe(prompt, max_new_tokens=max_tokens, temperature=temperature, max_time=timeout)
        text = outputs[0]['generated_text'].strip()
        is_clarification = text.upper().startswith("CLARIFICACIÓN:") or text.upper().startswith("CLARIFICATION:")
        return AnswerResult(text=text, is_clarification=is_clarification, provider="local")
