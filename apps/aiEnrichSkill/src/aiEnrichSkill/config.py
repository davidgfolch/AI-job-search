from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.envFileUtil import getEnvFile
from commonlib.ollama_config import OLLAMA_HOST_BASE_URL


def get_enabled() -> bool:
    return getEnvBool("AI_ENRICHSKILL_ENABLED", True)


def get_backend() -> str:
    """Read the provider from .env so Settings switches apply on the next cycle."""
    return getEnvFile("AI_ENRICHSKILL_BACKEND", "ollama")


def get_ollama_model() -> str:
    return getEnv("AI_ENRICHSKILL_OLLAMA_MODEL", "ollama/qwen2.5:3b")


def get_ollama_base_url() -> str:
    return getEnv("AI_ENRICHSKILL_OLLAMA_BASE_URL", OLLAMA_HOST_BASE_URL)


def get_max_new_tokens() -> int:
    return int(getEnv("AI_ENRICHSKILL_MAX_NEW_TOKENS", "2048"))


def get_hf_model_id() -> str:
    return getEnv("AI_ENRICHSKILL_HF_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")


def get_hf_temperature() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_TEMPERATURE", "0.1"))


def get_hf_top_p() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_TOP_P", "0.9"))


def get_hf_repetition_penalty() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_REPETITION_PENALTY", "1.1"))


def get_batch_size() -> int:
    return int(getEnv("AI_ENRICHSKILL_BATCH_SIZE", "10"))


def get_input_max_len() -> int:
    return int(getEnv("AI_ENRICHSKILL_INPUT_MAX_LEN", "12000"))


def get_timeout() -> float:
    return float(getEnv("AI_ENRICHSKILL_TIMEOUT", "90"))


def get_gpu_cleanup() -> bool:
    return getEnv("AI_ENRICHSKILL_GPU_CLEANUP", "True") == "True"


def get_skill_categories() -> str:
    return getEnv("AI_ENRICHSKILL_CATEGORIES", required=True)


def get_enrich_limit() -> int:
    return int(getEnv("AI_ENRICHSKILL_ENRICH_LIMIT", "10"))


def get_max_ollama_failures() -> int:
    return int(getEnv("AI_ENRICHSKILL_MAX_OLLAMA_FAILURES", "3"))


def get_learning_paths_enabled() -> bool:
    return getEnvBool("AI_ENRICHSKILL_LEARNING_PATHS", True)


def get_learning_path_max() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_MAX", "3"))


def get_learning_path_batch() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_BATCH", "1"))


def get_learning_path_timeout() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_TIMEOUT", "5"))


def get_learning_path_search_enabled() -> bool:
    return getEnvBool("AI_ENRICHSKILL_LEARNING_PATH_SEARCH", True)


def get_learning_path_search_results() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_SEARCH_RESULTS", "10"))


def get_learning_path_max_failures() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_MAX_FAILURES", "3"))


def get_learning_path_retry_seconds() -> int:
    return int(getEnv("AI_ENRICHSKILL_LEARNING_PATH_RETRY_SECONDS", "900"))


DEFAULT_LEARNING_DOMAINS = (
    "developer.mozilla.org", "docs.python.org", "python.org", "dev.java", "docs.oracle.com",
    "go.dev", "golang.org", "rust-lang.org", "doc.rust-lang.org", "typescriptlang.org",
    "react.dev", "vuejs.org", "angular.dev", "nodejs.org", "nextjs.org", "svelte.dev",
    "djangoproject.com", "flask.palletsprojects.com", "fastapi.tiangolo.com", "spring.io",
    "kubernetes.io", "docker.com", "docs.docker.com", "terraform.io", "developer.hashicorp.com",
    "aws.amazon.com", "cloud.google.com", "learn.microsoft.com", "azure.microsoft.com",
    "postgresql.org", "mysql.com", "dev.mysql.com", "mongodb.com", "redis.io", "elastic.co",
    "grafana.com", "prometheus.io", "jenkins.io", "git-scm.com", "kernel.org", "linux.org",
    "coursera.org", "udemy.com", "edx.org", "freecodecamp.org", "roadmap.sh", "youtube.com",
    "youtu.be", "w3schools.com", "baeldung.com", "digitalocean.com", "martinfowler.com",
    "refactoring.guru", "devdocs.io", "readthedocs.io",
)


def get_learning_domains() -> tuple[str, ...]:
    configured = getEnv("AI_ENRICHSKILL_LEARNING_DOMAINS", "")
    if not configured.strip():
        return DEFAULT_LEARNING_DOMAINS
    return tuple(d.strip().lower().removeprefix("www.") for d in configured.split(",") if d.strip())


def get_skill_system_prompt() -> str:
    categories = get_skill_categories()
    learning_path = _learning_path_instructions() if get_learning_paths_enabled() else ""
    return f"""You are an expert technical recruiter and software engineer.
Your task is to provide a structured description for a given technical skill.
The structure MUST be:
1. **Summary**: A concise 1-2 sentence overview of what the skill is.
2. **Deep Technical Details**: A detailed explanation including:
   - Core Functionality
   - Usage Types (library, framework, etc.)
   - Key Modules/Components
   - Integration with co-occurring technologies
3. **Category**: One or more of [{categories}] (comma separated).
{learning_path}Output ONLY the structured text. Do not include any conversational text. Use 'Category: ' prefix for the category line."""


def _learning_path_instructions() -> str:
    max_links = get_learning_path_max()
    return f"""4. **Learning Path**: exactly {max_links} URLs, one per line, each prefixed with "- ":
   - first: a deep link to the official documentation or reference page for this exact skill
   - second: a hands-on tutorial or guided course about this exact skill
   - third: a single video watch URL about this exact skill (secondary alternative), not a playlist or channel
Every URL must be a real, existing deep link whose path or query names the skill.
A bare homepage like https://www.youtube.com/ is invalid; a video or social link is always secondary to documentation.
No placeholders, no generic landing pages, no search-result links. Use the context line to disambiguate similar names.
Start this section with a 'Learning Path:' header line.
"""


def get_learning_path_system_prompt() -> str:
    max_links = get_learning_path_max()
    return f"""You are an expert technical recruiter and software engineer.
List {max_links} learning resources for a given technical skill, in this priority order.
The structure MUST be:
Learning Path:
- <official documentation or reference deep link for this exact skill>
- <hands-on tutorial or guided course about this exact skill>
- <single video watch URL about this exact skill, as a secondary alternative; no playlists or channels>
Rules:
- Output ONLY the 'Learning Path:' header line and the URLs, one per line, prefixed with "- ".
- No explanations, no titles, no conversational text.
- Every URL must be a real, existing deep link whose path or query names the skill. A bare homepage like https://www.youtube.com/ is invalid.
- Authentic documentation comes first; video/social links are secondary alternatives, never the only resource.
- Use the context line when present to pick resources for the right technology with a similar name.
- No placeholders, no generic landing pages, no search-result links."""

