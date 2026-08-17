"""Application and model provider configuration."""

from __future__ import annotations

import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class ModelProvider(str, Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OLLAMA = "ollama"


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_GROQ_MODEL = "groq/llama-3.3-70b-versatile"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def get_model_provider() -> ModelProvider:
    provider = os.getenv("MODEL_PROVIDER", "gemini").strip().lower()
    try:
        return ModelProvider(provider)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported MODEL_PROVIDER '{provider}'. Use gemini, groq, or ollama."
        ) from exc


def get_api_key(provider: ModelProvider | None = None) -> str | None:
    provider = provider or get_model_provider()
    if provider == ModelProvider.GEMINI:
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if provider == ModelProvider.GROQ:
        return os.getenv("GROQ_API_KEY")
    return None


def get_model_id(provider: ModelProvider | None = None) -> str:
    provider = provider or get_model_provider()
    if provider == ModelProvider.GEMINI:
        return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    if provider == ModelProvider.GROQ:
        return os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


def validate_configuration() -> tuple[bool, str]:
    """Validate that required configuration is present for the selected provider."""
    try:
        provider = get_model_provider()
    except ValueError as exc:
        return False, str(exc)

    if provider == ModelProvider.OLLAMA:
        return True, "Ollama configured (local model, no API key required)."

    api_key = get_api_key(provider)
    if not api_key:
        key_name = "GEMINI_API_KEY" if provider == ModelProvider.GEMINI else "GROQ_API_KEY"
        return False, f"Missing API key. Set {key_name} in your .env file."

    if len(api_key.strip()) < 10:
        return False, "API key appears invalid (too short)."

    return True, f"{provider.value.title()} provider configured successfully."


def create_model():
    """Create a Strands model instance based on environment configuration."""
    provider = get_model_provider()
    model_id = get_model_id(provider)
    temperature = float(os.getenv("MODEL_TEMPERATURE", "0.3"))
    max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "8192"))

    common_params = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }

    if provider == ModelProvider.GEMINI:
        from strands.models.gemini import GeminiModel

        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider.")
        return GeminiModel(
            client_args={"api_key": api_key},
            model_id=model_id,
            params=common_params,
        )

    if provider == ModelProvider.GROQ:
        from strands.models.litellm import LiteLLMModel

        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for Groq provider.")
        return LiteLLMModel(
            client_args={"api_key": api_key},
            model_id=model_id,
            params={"temperature": temperature, "max_tokens": max_tokens},
        )

    try:
        from strands.models.ollama import OllamaModel
    except ModuleNotFoundError as exc:
        raise ValueError(
            "Ollama provider requires optional dependency. "
            "Install with: pip install 'strands-agents[ollama]'"
        ) from exc

    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    return OllamaModel(
        host=host,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
    )
