import os
from tempfile import mkdtemp
from unittest.mock import MagicMock


class TempFiles:
    def __init__(self, cv_content="5 years Java experience", lf_content="Salary: 80k"):
        self.temp_dir = mkdtemp()
        self.cv_path = os.path.join(self.temp_dir, "cv.txt")
        self.lf_path = os.path.join(self.temp_dir, "looking-for.txt")
        if cv_content is not None:
            with open(self.cv_path, "w") as f:
                f.write(cv_content)
        if lf_content is not None:
            with open(self.lf_path, "w") as f:
                f.write(lf_content)

    def cleanup(self):
        for f in [self.cv_path, self.lf_path]:
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(self.temp_dir)


_BASE_CFG = dict(get_provider="local", get_hf_model="model", get_timeout=30, get_max_tokens=512, get_temperature=0.1)
_PROVIDER_CFG = {
    "local": dict(get_hf_model="Qwen/Qwen2.5-1.5B-Instruct"),
    "openai": dict(get_openai_api_key="sk-test", get_openai_model="gpt-4o-mini"),
    "openrouter": dict(get_openrouter_api_key="sk-or-test", get_openrouter_model="openai/gpt-4o-mini"),
}


def make_mock_cfg(mock_cfg, provider="local"):
    values = {**_BASE_CFG, **_PROVIDER_CFG.get(provider, {})}
    for attr, val in values.items():
        getattr(mock_cfg, attr).return_value = val


def make_mock_provider(text="Answer", is_clarification=False, provider="local"):
    mock = MagicMock()
    mock.generate.return_value = MagicMock(text=text, is_clarification=is_clarification, provider=provider)
    return mock
