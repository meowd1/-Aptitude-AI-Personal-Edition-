import os
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"

def load_config():
    if not CONFIG_PATH.exists():
        return {
            "tier": "C",
            "cloud_provider": "omniroute",
            "cloud_api_key": "",
            "cloud_base_url": "https://api.omniroute.dev/v1",
            "embedding_backend": "omniroute"
        }
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()

def get_llm() -> BaseChatModel:
    api_key = os.environ.get("OMNIROUTE_API_KEY") or config.get("cloud_api_key", "")
    base_url = config.get("cloud_base_url", "https://api.omniroute.dev/v1")
    
    # Using LangChain OpenAI wrapper pointing to Omniroute
    return ChatOpenAI(
        model="gpt-4o-mini", # Replace with preferred model if needed
        api_key=api_key,
        base_url=base_url
    )

def get_embeddings() -> Embeddings:
    api_key = os.environ.get("OMNIROUTE_API_KEY") or config.get("cloud_api_key", "")
    base_url = config.get("cloud_base_url", "https://api.omniroute.dev/v1")
    
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
        base_url=base_url
    )
