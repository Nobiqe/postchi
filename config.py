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
    custom_footer: Optional[str] = None
    use_ai_agent: bool = False
    ai_system_prompt: Optional[str] = None
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

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.telegram_config = TelegramConfig()
        self.ai_config = AIConfig()
        self.channel_mappings: Dict[str, ChannelMapping] = {}
        self.saved_footers: List[str] = []
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Load Telegram config
                if 'telegram' in config_data:
                    tg_data = config_data['telegram']
                    self.telegram_config = TelegramConfig(**tg_data)
                
                # Load AI config
                if 'ai' in config_data:
                    ai_data = config_data['ai']
                    self.ai_config = AIConfig(**ai_data)
                
                # Load channel mappings
                if 'channel_mappings' in config_data:
                    for mapping_data in config_data['channel_mappings']:
                        mapping = ChannelMapping(**mapping_data)
                        self.channel_mappings[mapping.id] = mapping
                if 'saved_footers' in config_data:
                    self.saved_footers = config_data['saved_footers']  

                logging.info("Configuration loaded successfully")
            else:
                logging.info("No config file found, creating default configuration")
                self.create_default_config()
                
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.create_default_config()
    
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            config_data = {
                'telegram': asdict(self.telegram_config),
                'ai': asdict(self.ai_config),
                'channel_mappings': [asdict(mapping) for mapping in self.channel_mappings.values()],
                'saved_footers': self.saved_footers 
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logging.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            return False
    
    def create_default_config(self) -> None:
        """Create default configuration."""
        # Set your provided API key
        self.ai_config.api_key = "AIzaSyC5OROh5fCG_E8vEax5RhjfeH_CYWDK7xc"
        
        # Create default mapping with your channels
        default_mapping = ChannelMapping(
            id="fundamental_to_turkey",
            source_channel_id=-1001124685506,
            source_channel_name="ديدگاه بنيادى در بازارهاى مالى",
            target_channel_id=-1001670168544,
            target_channel_name="turkey",
            keywords=["@Fundamental_View"],
            signature="@Fundamental_View"
        )
        
        self.channel_mappings[default_mapping.id] = default_mapping
        self.save_config()
    
    def add_channel_mapping(self, mapping: ChannelMapping) -> bool:
        """Add a new channel mapping."""
        try:
            self.channel_mappings[mapping.id] = mapping
            return self.save_config()
        except Exception as e:
            logging.error(f"Error adding channel mapping: {e}")
            return False
    
    def remove_channel_mapping(self, mapping_id: str) -> bool:
        """Remove a channel mapping."""
        try:
            if mapping_id in self.channel_mappings:
                del self.channel_mappings[mapping_id]
                return self.save_config()
            return False
        except Exception as e:
            logging.error(f"Error removing channel mapping: {e}")
            return False
    
    def get_active_mappings(self) -> List[ChannelMapping]:
        """Get all active channel mappings."""
        return [mapping for mapping in self.channel_mappings.values() if mapping.active]

