import yaml
import os
import json

# Get the directory where this config.py file is located
config_dir = os.path.dirname(os.path.abspath(__file__))
config_yaml_path = os.path.join(config_dir, "config.yaml")

def load_config():
    """Load configuration from environment variables or config.yaml"""
    
    # Try to load from environment variables first (for production)
    if os.getenv("USE_ENV_CONFIG") == "true":
        return {
            "api_keys": {
                "android_studio": {
                    "keys": json.loads(os.getenv("GEMINI_API_KEYS", "[]"))
                },
                "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
                "google_search": {
                    "keys": json.loads(os.getenv("GOOGLE_SEARCH_KEYS", "[]")),
                    "Engine_id": json.loads(os.getenv("GOOGLE_SEARCH_ENGINE_IDS", "[]"))
                },
                "tavily": {
                    "api_key": os.getenv("TAVILY_API_KEY", "")
                }
            }
        }
    
    # Fall back to config.yaml (for local development)
    if os.path.exists(config_yaml_path):
        with open(config_yaml_path, "r") as f:
            return yaml.safe_load(f)
    
    # If neither exists, raise an error
    raise FileNotFoundError(
        "No configuration found. Either set USE_ENV_CONFIG=true with environment variables "
        "or create config/config.yaml from config.yaml.example"
    )

config = load_config()

# Gemini API Keys (multiple keys for rotation)
GEMINI_API_KEYS = config["api_keys"]["android_studio"]["keys"]

# GitHub Tokens for GPT-5 access (multiple tokens for rotation)
GITHUB_TOKENS = config["api_keys"]["GITHUB_TOKEN"]
GITHUB_ENDPOINT = "https://models.github.ai/inference"

# Google Search API Keys
GOOGLE_SEARCH_KEY_0 = config["api_keys"]["google_search"]["keys"][0] if len(config["api_keys"]["google_search"]["keys"]) > 0 else ""
CX_ID_0 = config["api_keys"]["google_search"]["Engine_id"][0] if len(config["api_keys"]["google_search"]["Engine_id"]) > 0 else ""

GOOGLE_SEARCH_KEY_1 = config["api_keys"]["google_search"]["keys"][1] if len(config["api_keys"]["google_search"]["keys"]) > 1 else ""
CX_ID_1 = config["api_keys"]["google_search"]["Engine_id"][1] if len(config["api_keys"]["google_search"]["Engine_id"]) > 1 else ""

# Tavily Search API Key
TAVILY_SEARCH_KEY = config["api_keys"]["tavily"]["api_key"]

# System Configuration
MAX_RETRIES = 3
CHECKPOINT_DIR = "checkpoints"
AUTO_RESUME = True
