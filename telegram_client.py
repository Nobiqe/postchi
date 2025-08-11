import asyncio
import logging
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from datetime import datetime, timedelta


class TelegramChannelClient:
    """Enhanced Telegram client with multi-channel support."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str):
        self.client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
        self.phone_number = phone_number
    
    async def initialize(self) -> bool:
        """Initialize and authenticate the client."""
        try:
            await self.client.start(phone=self.phone_number)
            logging.info("Telegram client initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Error initializing Telegram client: {e}")
            print(f"Connection failed: {e}")
            print("Please check:")
            print("1. Internet connection")
            print("2. Telegram API credentials")
            print("3. Phone number format (+1234567890)")
            return False
    
    async def get_all_chats(self) -> List[Dict[str, Any]]:
        """Get all available chats/channels."""
        try:
            dialogs = await self.client.get_dialogs()
            chats = []
            
            for dialog in dialogs:
                chats.append({
                    'id': dialog.id,
                    'name': dialog.title or 'No Name',
                    'type': type(dialog.entity).__name__,
                    'is_channel': hasattr(dialog.entity, 'broadcast'),
                    'is_group': hasattr(dialog.entity, 'megagroup'),
                })
            
            return chats
        except Exception as e:
            logging.error(f"Error getting chats: {e}")
            return []
    
    async def get_channel_messages(self, channel_id: int, since_date: Optional[datetime] = None, 
                                 last_message_id: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from a specific channel."""
        try:
            messages = []
            kwargs = {'reverse': True}
            
            if since_date:
                kwargs['offset_date'] = since_date
            if last_message_id:
                kwargs['min_id'] = last_message_id
            if limit:
                kwargs['limit'] = limit
            
            async for message in self.client.iter_messages(channel_id, **kwargs):
                if message and message.text:
                    messages.append({
                        'id': message.id,
                        'text': message.text,
                        'date': message.date
                    })
            
            return messages
            
        except ChannelPrivateError:
            logging.error(f"Channel {channel_id} is private or not accessible")
            return []
        except Exception as e:
            logging.error(f"Error getting messages from channel {channel_id}: {e}")
            return []
    
    async def send_message(self, channel_id: int, message_text: str) -> bool:
        """Send a message to a channel."""
        try:
            await self.client.send_message(channel_id, message_text)
            return True
            
        except FloodWaitError as e:
            logging.warning(f"Flood wait error: {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            return False
            
        except Exception as e:
            logging.error(f"Error sending message to channel {channel_id}: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        try:
            await self.client.disconnect()
            logging.info("Disconnected from Telegram")
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")