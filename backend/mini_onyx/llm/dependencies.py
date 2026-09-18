from mini_onyx.config import get_llm_settings
from mini_onyx.llm.interfaces import LLM
from mini_onyx.llm.litellm_client import LiteLLMClient


def get_llm() -> LLM:
    settings = get_llm_settings()
    return LiteLLMClient(model=settings.model)
