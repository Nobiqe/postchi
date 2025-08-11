import asyncio
from typing import Optional
from config import ConfigManager, ChannelMapping, TelegramConfig, AIConfig
from main_processor import MultiChannelProcessor
from database import DatabaseManager
import logging
from datetime import datetime, timedelta


class MenuSystem:
    """Interactive menu system for the application."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.processor: Optional[MultiChannelProcessor] = None
        self.db_manager = DatabaseManager()
        self.setup_logging()

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('telegram_processor.log'),
                logging.StreamHandler()
            ]
        )
