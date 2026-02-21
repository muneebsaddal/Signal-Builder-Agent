import os
from typing import Any
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm() -> Any:
    """
    Get LLM based on provider configuration.
    Supports both Ollama (free, local) and OpenAI.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        # Ollama setup (free, runs on CPU)
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        
        return Ollama(
            model=model,
            base_url=base_url,
            temperature=0.1,  # Low temperature for deterministic outputs
        )
    
    elif provider == "openai":
        # OpenAI setup (for production/showcase)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
        return ChatOpenAI(
            model=model,
            temperature=0.1,
            api_key=api_key
        )
    
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def get_provider_info() -> dict:
    """Get current LLM provider information"""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        return {
            "provider": "ollama",
            "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "cost": "free"
        }
    elif provider == "openai":
        return {
            "provider": "openai",
            "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            "cost": "paid"
        }
    
    return {"provider": "unknown"}
