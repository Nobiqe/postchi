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
            print(f"      ❌ Empty message text")
            return False
        
        print(f"      Checking criteria for: '{message_text[:30]}...'")
        print(f"      Required signature: '{mapping.signature}'")
        print(f"      Required keywords: {mapping.keywords}")
        
        # If no signature and no keywords are set, accept all messages
        if not mapping.signature and not mapping.keywords:
            print(f"      ✅ No criteria set - accepting all messages")
            return True
        
        message_lower = message_text.lower()
        
        # Check for signature (if set)
        signature_match = True
        if mapping.signature:
            signature_match = mapping.signature.lower() in message_lower
            print(f"      Signature match: {signature_match}")
        
        # Check for keywords (if set)
        keyword_match = True
        if mapping.keywords:
            keyword_matches = [keyword.lower() in message_lower for keyword in mapping.keywords]
            keyword_match = any(keyword_matches)
            print(f"      Keyword matches: {keyword_matches} -> {keyword_match}")
        
        result = signature_match and keyword_match
        print(f"      Final result: {result}")
        return result
    
    async def _process_single_message(self, msg_data: Dict[str, Any], mapping: ChannelMapping) -> None:
            """Process a single message with smart AI processing based on content length and media."""
            try:
                # Check if already processed
                last_id = self.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
                if last_id and msg_data['id'] <= last_id:
                    return
                
                # Get session config
                prompt_to_use = mapping.prompt_template
                custom_footer = None
                
                # Determine if AI processing is needed
                should_use_ai = False
                text_length = len(msg_data['text']) if msg_data['text'] else 0
                
                if hasattr(self, 'session_config'):
                    custom_footer = self.session_config['custom_footer']
                    
                    # Always process captions (messages with media)
                    if msg_data.get('has_media', False):
                        should_use_ai = True  # Always process captions
                    elif self.session_config.get('apply_ai_to_all', False):
                        # Only apply AI to non-caption messages if user requested it
                        should_use_ai = True
                    
                    if should_use_ai and self.session_config['ai_system_prompt']:
                        prompt_to_use = self.session_config['ai_system_prompt']

                # Process text
                if should_use_ai:
                    print(f"    🤖 Processing with AI (length: {text_length})")
                    processed_text = await self.ai_processor.process_message(
                        msg_data['text'], 
                        prompt_to_use,
                        custom_footer
                    )
                    if not processed_text:
                        # Fallback to original if AI fails
                        processed_text = msg_data['text']
                        if custom_footer:
                            processed_text += custom_footer
                else:
                    print(f"    📝 Using original text (length: {text_length})")
                    processed_text = msg_data['text']
                    if hasattr(self, 'session_config') and self.session_config.get('custom_footer'):
                        processed_text += self.session_config['custom_footer']
        
                if processed_text:
                    # Handle media download if enabled and present
                    media_path = None
                    if (hasattr(self, 'session_config') and 
                        self.session_config.get('include_media') and 
                        msg_data.get('has_media')):
                        
                        print(f"    🎬 Downloading media for message {msg_data['id']}")
                        media_path = await self.telegram_client.download_media(
                            msg_data['id'], 
                            mapping.source_channel_id, 
                            msg_data.get('media_file_id')
                        )
                        if media_path:
                            print(f"    ✅ Media downloaded to: {media_path}")
                        else:
                            print(f"    ❌ Failed to download media")

                    # Save to database with media info
                    message = ProcessedMessage(
                        message_id=msg_data['id'],
                        source_channel_id=mapping.source_channel_id,
                        target_channel_id=mapping.target_channel_id,
                        mapping_id=mapping.id,
                        original_message=msg_data['text'],
                        processed_message=processed_text,
                        date=msg_data['date'],
                        has_media=msg_data.get('has_media', False),
                        media_type=msg_data.get('media_type'),
                        media_path=media_path,
                        media_file_id=msg_data.get('media_file_id')
                    )
                    
                    if self.db_manager.save_processed_message(message):
                        action = "AI-processed" if should_use_ai else "Original"
                        logging.info(f"{action} and saved message {msg_data['id']} for mapping {mapping.id}")
                    else:
                        logging.error(f"Failed to save message {msg_data['id']} for mapping {mapping.id}")
                
            except Exception as e:
                logging.error(f"Error processing message {msg_data['id']} for mapping {mapping.id}: {e}")

    async def _process_single_message_with_config(self, msg_data, mapping, session_config):
        """Process a single message with session configuration including smart AI processing."""
        try:
            last_id = self.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            if last_id and msg_data['id'] <= last_id:
                return
            
            # Handle media download if enabled
            media_path = None
            if session_config['include_media'] and msg_data.get('has_media'):
                media_path = await self.telegram_client.download_media(
                    msg_data['id'], mapping.source_channel_id, msg_data.get('media_file_id')
                )
            
            # Determine if AI processing should be applied
            text_length = len(msg_data['text']) if msg_data['text'] else 0
            should_use_ai = False
            
            if session_config.get('apply_ai_to_all', False):
                # Apply AI to all messages if user requested
                should_use_ai = True
            elif msg_data.get('has_media', False):
                # Always process captions (messages with media)
                should_use_ai = True
            
            # Process text with AI if needed
            processed_text = msg_data['text']
            if should_use_ai and session_config['ai_system_prompt']:
                prompt_to_use = session_config['ai_system_prompt']
                processed_text = await self.ai_processor.process_message(
                    msg_data['text'], 
                    prompt_to_use,
                    session_config['custom_footer']
                ) or msg_data['text']
            elif session_config['custom_footer']:
                processed_text += session_config['custom_footer']
            
            # Create ProcessedMessage with media info
            from database import ProcessedMessage
            message = ProcessedMessage(
                message_id=msg_data['id'],
                source_channel_id=mapping.source_channel_id,
                target_channel_id=mapping.target_channel_id,
                mapping_id=mapping.id,
                original_message=msg_data['text'],
                processed_message=processed_text,
                date=msg_data['date'],
                has_media=msg_data.get('has_media', False),
                media_type=msg_data.get('media_type'),
                media_path=media_path,
                media_file_id=msg_data.get('media_file_id')
            )
            
            if self.db_manager.save_processed_message(message):
                action = "AI-processed" if should_use_ai else "Original"
                logging.info(f"{action} and saved message {msg_data['id']} for mapping {mapping.id}")
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
                    # Only use the immediate processing method
                    await self._process_and_post_immediately(mapping)
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every minute
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
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

    async def _process_and_post_immediately(self, mapping: ChannelMapping) -> None:
        """Process new messages, save to database, then post immediately with media."""
        try:
            print(f"\n🔍 Checking mapping: {mapping.id}")
            print(f"   Source: {mapping.source_channel_id} -> Target: {mapping.target_channel_id}")
            
            last_id = self.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            
            # If this is the first run (no last_id), get the latest message ID to start monitoring from
            if last_id is None:
                # Get only the most recent message to establish a baseline
                recent_messages = await self.telegram_client.get_channel_messages(
                    mapping.source_channel_id, limit=1
                )
                if recent_messages:
                    last_id = recent_messages[0]['id']
                    print(f"   Initialized monitoring from message ID: {last_id}")
                    
                    # SAVE THE BASELINE TO DATABASE - This is the fix
                    # Create a dummy processed message to establish the baseline
                    from database import ProcessedMessage
                    baseline_message = ProcessedMessage(
                        message_id=last_id,
                        source_channel_id=mapping.source_channel_id,
                        target_channel_id=mapping.target_channel_id,
                        mapping_id=mapping.id,
                        original_message="[BASELINE - DO NOT POST]",
                        processed_message="[BASELINE - DO NOT POST]",
                        date=recent_messages[0]['date'],
                        has_media=False,
                        media_type=None,
                        media_path=None,
                        media_file_id=None
                    )
                    
                    # Save and immediately mark as posted so it won't be processed
                    if self.db_manager.save_processed_message(baseline_message):
                        self.db_manager.mark_as_posted(last_id, mapping.id)
                        print(f"   ✅ Baseline saved - now monitoring for new messages only")
                    
                    return  # Skip processing on first run, just establish baseline
                else:
                    print(f"   No messages found in channel")
                    return
            
            print(f"   Last processed message ID: {last_id}")
            
            new_messages = await self.telegram_client.get_channel_messages(
                mapping.source_channel_id, last_message_id=last_id, limit=20
            )
            
            print(f"   Found {len(new_messages)} new messages")
            
            for i, msg_data in enumerate(new_messages):
                print(f"\n📨 Message {i+1}: ID={msg_data['id']}")
                print(f"    Text: '{msg_data['text'][:50]}...' (length: {len(msg_data['text'])})")
                print(f"    Date: {msg_data['date']}")
                print(f"    Has Media: {msg_data.get('has_media', False)}")
                print(f"    Media Type: {msg_data.get('media_type', 'None')}")
                
                matches = self._message_matches_criteria(msg_data['text'], mapping)
                print(f"    Matches criteria: {matches}")
                
                if matches:
                    print(f"    ✅ Processing message {msg_data['id']}")
                    
                    # First process and save to database
                    await self._process_single_message(msg_data, mapping)
                    
                    # Then get the specific message we just processed
                    specific_message = self.db_manager.get_specific_unposted_message(mapping.id, msg_data['id'])
                    print(f"    Looking for message ID: {msg_data['id']}")
                    
                    if specific_message:
                        message = specific_message
                        print(f"    Found specific unposted message ID: {message.message_id}")
                        print(f"    📤 Sending to channel {mapping.target_channel_id}")
                        print(f"    Message content: '{message.processed_message[:100]}...'")
                        
                        # Send with media if available
                        if message.has_media and message.media_path:
                            print(f"    🎬 Including media: {message.media_path}")
                            success = await self.telegram_client.send_message(
                                mapping.target_channel_id, 
                                message.processed_message,
                                message.media_path
                            )
                        else:
                            success = await self.telegram_client.send_message(
                                mapping.target_channel_id, 
                                message.processed_message
                            )
                        
                        if success:
                            self.db_manager.mark_as_posted(message.message_id, mapping.id)
                            print(f"    ✅ Successfully posted message {message.message_id}")
                            if message.has_media:
                                print(f"    ✅ Media forwarded successfully")
                            logging.info(f"Posted message {message.message_id} immediately for mapping {mapping.id}")
                        else:
                            print(f"    ❌ Failed to send message {message.message_id}")
                            logging.error(f"Failed to send message {message.message_id} for mapping {mapping.id}")
                    else:
                        print(f"    ❌ No unposted message found for ID: {msg_data['id']}")
                else:
                    print(f"    ⭕ Skipping message (doesn't match criteria)")
                    
        except Exception as e:
            print(f"❌ Error in immediate processing for mapping {mapping.id}: {e}")
            logging.error(f"Error in immediate processing for mapping {mapping.id}: {e}")