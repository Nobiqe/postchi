import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging


@dataclass
class ChannelMapping:
    """Configuration for source-target channel mapping."""
    id: str
    source_channel_id: int
    source_channel_name: str
    target_channel_id: int
    target_channel_name: str
    keywords: List[str]
    signature: str
    prompt_template: Optional[str] = None
    active: bool = True


@dataclass
class TelegramConfig:
    """Telegram API configuration."""
    api_id: str = ""
    api_hash: str = ""
    phone_number: str = ""


@dataclass
class AIConfig:
    """AI configuration."""
    api_key: str = ""
    model: str = "gemini-pro"
    provider: str = "gemini"
    base_url: str = ""

