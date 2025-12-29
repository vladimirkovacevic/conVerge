"""Services for business logic"""
from .llm import OpenRouterClient, get_llm_client

__all__ = ["OpenRouterClient", "get_llm_client"]

# Provide llm_client as a function call for lazy initialization
def llm_client():
    return get_llm_client()
