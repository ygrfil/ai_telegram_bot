from environs import Env
from typing import List, Dict, Any
from pathlib import Path

class Config:
    def __init__(self,
                 bot_token: str,
                 allowed_user_ids: List[str],
                 admin_id: str,
                 openrouter_api_key: str,
                 fal_api_key: str,
                 gemini_api_key: str,
                 max_tokens: int = 1024,
                 polling_settings: Dict[str, Any] = None):
        self.bot_token = bot_token
        self.allowed_user_ids = allowed_user_ids
        self.admin_id = admin_id
        self.openrouter_api_key = openrouter_api_key
        self.fal_api_key = fal_api_key
        self.gemini_api_key = gemini_api_key
        self.max_tokens = max_tokens
        
        # Default polling settings
        self.polling_settings = polling_settings or {
            "timeout": 10,
            "poll_interval": 0.5,
            "backoff": {
                "max_delay": 5.0,
                "start_delay": 1.0,
                "factor": 1.5,
                "jitter": 0.1,
            }
        }

    @classmethod
    def from_env(cls):
        env = Env()
        env.read_env()
        
        allowed_ids = [id.strip() for id in env.str("ALLOWED_USER_IDS").split(',')]
        
        # Load polling settings from environment if provided
        polling_settings = {
            "timeout": env.int("POLLING_TIMEOUT", 10),
            "poll_interval": env.float("POLLING_INTERVAL", 0.5),
            "backoff": {
                "max_delay": env.float("POLLING_MAX_DELAY", 5.0),
                "start_delay": env.float("POLLING_START_DELAY", 1.0),
                "factor": env.float("POLLING_BACKOFF_FACTOR", 1.5),
                "jitter": env.float("POLLING_JITTER", 0.1),
            }
        }
        
        return cls(
            bot_token=env.str("BOT_TOKEN"),
            allowed_user_ids=allowed_ids,
            admin_id=env.str("ADMIN_ID"),
            openrouter_api_key=env.str("OPENROUTER_API_KEY"),
            fal_api_key=env.str("FAL_API_KEY"),
            gemini_api_key=env.str("GEMINI_API_KEY", ""),  # Make it optional with empty default
            max_tokens=env.int("MAX_TOKENS", 4096),
            polling_settings=polling_settings
        )