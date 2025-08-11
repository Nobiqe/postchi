import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from config import ConfigManager, ChannelMapping
from database import DatabaseManager, ProcessedMessage
from ai_processor import UniversalMessageProcessor
from telegram_client import TelegramChannelClient


class MultiChannelProcessor:
    """Main processor that handles multiple channel mappings."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.db_manager = DatabaseManager()
        
        # Initialize Telegram client
        tg_config = config_manager.telegram_config
        self.telegram_client = TelegramChannelClient(
            tg_config.api_id, tg_config.api_hash, tg_config.phone_number
        )
        
        # Initialize AI processor
        ai_config = config_manager.ai_config
        self.ai_processor = UniversalMessageProcessor(
            ai_config.api_key, 
            ai_config.model, 
            ai_config.provider, 
            ai_config.base_url
        )
        
        self.is_running = False
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        return await self.telegram_client.initialize()
    
    async def process_historical_messages(self, mapping_id: str) -> None:
        """Process historical messages for a specific mapping."""
        mapping = self.config_manager.channel_mappings.get(mapping_id)
        if not mapping:
            logging.error(f"Mapping {mapping_id} not found")
            return
        
        since_date = datetime.now() - timedelta(days=7)
        messages = await self.telegram_client.get_channel_messages(
            mapping.source_channel_id, since_date=since_date
        )
        
        processed_count = 0
        for msg_data in messages:
            if self._message_matches_criteria(msg_data['text'], mapping):
                await self._process_single_message(msg_data, mapping)
                processed_count += 1
        
        print(f"  Processed {processed_count} messages for {mapping_id}")
    
    async def process_all_historical_messages(self) -> None:
        """Process historical messages for all active mappings."""
        for mapping_id in self.config_manager.channel_mappings:
            mapping = self.config_manager.channel_mappings[mapping_id]
            if mapping.active:
                await self.process_historical_messages(mapping_id)
    
    def _message_matches_criteria(self, message_text: str, mapping: ChannelMapping) -> bool:
        """Check if message matches the mapping criteria."""
        if not message_text:
            return False
        
        # Check for signature
        if mapping.signature and mapping.signature not in message_text:
            return False
        
        # Check for keywords
        if mapping.keywords:
            message_lower = message_text.lower()
            return any(keyword.lower() in message_lower for keyword in mapping.keywords)
        
        return True
    
    async def _process_single_message(self, msg_data: Dict[str, Any], mapping: ChannelMapping) -> None:
        """Process a single message."""
        try:
            # Check if already processed
            last_id = self.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            if last_id and msg_data['id'] <= last_id:
                return
            
            # Use session config if available
            prompt_to_use = mapping.prompt_template
            custom_footer = None
            
            if hasattr(self, 'session_config'):
                if self.session_config['use_ai_agent'] and self.session_config['ai_system_prompt']:
                    prompt_to_use = f"{self.session_config['ai_system_prompt']}\n\nOriginal text: {{original_text}}\n\nPlease provide only the rewritten text."
                custom_footer = self.session_config['custom_footer']
            
            # Process with AI
            processed_text = await self.ai_processor.process_message(
                msg_data['text'], 
                prompt_to_use,
                custom_footer
            )
            
            if processed_text:
                # Save to database
                message = ProcessedMessage(
                    message_id=msg_data['id'],
                    source_channel_id=mapping.source_channel_id,
                    target_channel_id=mapping.target_channel_id,
                    mapping_id=mapping.id,
                    original_message=msg_data['text'],
                    processed_message=processed_text,
                    date=msg_data['date']
                )
                
                if self.db_manager.save_processed_message(message):
                    logging.info(f"Processed and saved message {msg_data['id']} for mapping {mapping.id}")
                else:
                    logging.error(f"Failed to save message {msg_data['id']} for mapping {mapping.id}")
            
        except Exception as e:
            logging.error(f"Error processing message {msg_data['id']} for mapping {mapping.id}: {e}")
    
    async def start_monitoring(self) -> None:
        """Start monitoring all active channel mappings."""
        self.is_running = True
        logging.info("Starting multi-channel monitoring...")
        
        while self.is_running:
            try:
                active_mappings = self.config_manager.get_active_mappings()
                
                for mapping in active_mappings:
                    await self._process_mapping(mapping)
                    
                    # Check if it's time to post
                    if self.db_manager.should_post_now(mapping.id):
                        await self._post_scheduled_message(mapping)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _process_mapping(self, mapping: ChannelMapping) -> None:
        """Process new messages for a specific mapping."""
        try:
            last_id = self.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            new_messages = await self.telegram_client.get_channel_messages(
                mapping.source_channel_id, last_message_id=last_id
            )
            
            for msg_data in new_messages:
                if self._message_matches_criteria(msg_data['text'], mapping):
                    await self._process_single_message(msg_data, mapping)
                    
        except Exception as e:
            logging.error(f"Error processing mapping {mapping.id}: {e}")
    
    async def _post_scheduled_message(self, mapping: ChannelMapping) -> None:
        """Post a scheduled message for a specific mapping."""
        try:
            messages = self.db_manager.get_unposted_messages(mapping.id, 1)
            
            if messages:
                message = messages[0]
                
                if await self.telegram_client.send_message(mapping.target_channel_id, message.processed_message):
                    self.db_manager.mark_as_posted(message.message_id, mapping.id)
                    self.db_manager.update_post_schedule(mapping.id)
                    logging.info(f"Posted message {message.message_id} for mapping {mapping.id}")
                else:
                    logging.error(f"Failed to post message {message.message_id} for mapping {mapping.id}")
            else:
                logging.info(f"No messages to post for mapping {mapping.id}")
                
        except Exception as e:
            logging.error(f"Error posting scheduled message for mapping {mapping.id}: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process."""
        self.is_running = False
        logging.info("Monitoring stopped")
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        await self.telegram_client.disconnect()