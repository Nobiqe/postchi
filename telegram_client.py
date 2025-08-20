# Add to telegram_client.py

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from datetime import datetime, timedelta
from pathlib import Path


class TelegramChannelClient:
    """Enhanced Telegram client with media support."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str):
        self.client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
        self.phone_number = phone_number
        self.media_dir = Path("media")
        self.media_dir.mkdir(exist_ok=True)
    
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
        """Get messages from a specific channel with media support."""
        try:
            messages = []
            kwargs = {'reverse': True}
            
            if since_date:
                kwargs['offset_date'] = since_date
            elif last_message_id:
                kwargs['min_id'] = last_message_id
            else:
                kwargs['limit'] = limit or 10
            
            if limit:
                kwargs['limit'] = limit
            
            async for message in self.client.iter_messages(channel_id, **kwargs):
                if message:
                    # Extract media information
                    media_info = await self._extract_media_info(message)
                    
                    messages.append({
                        'id': message.id,
                        'text': message.text or '',
                        'date': message.date,
                        'has_media': media_info['has_media'],
                        'media_type': media_info['media_type'],
                        'media_file_id': media_info['media_file_id']
                    })
            
            return messages
            
        except ChannelPrivateError:
            logging.error(f"Channel {channel_id} is private or not accessible")
            return []
        except Exception as e:
            logging.error(f"Error getting messages from channel {channel_id}: {e}")
            return []
    
    async def _extract_media_info(self, message) -> Dict[str, Any]:
        """Extract media information from a message."""
        media_info = {
            'has_media': False,
            'media_type': None,
            'media_file_id': None
        }
        
        if message.media:
            media_info['has_media'] = True
            
            if isinstance(message.media, MessageMediaPhoto):
                media_info['media_type'] = 'photo'
                media_info['media_file_id'] = str(message.media.photo.id)
            elif isinstance(message.media, MessageMediaDocument):
                doc = message.media.document
                if doc.mime_type:
                    if doc.mime_type.startswith('image/'):
                        media_info['media_type'] = 'photo'
                    elif doc.mime_type.startswith('video/'):
                        media_info['media_type'] = 'video'
                    elif doc.mime_type.startswith('audio/'):
                        media_info['media_type'] = 'audio'
                    else:
                        media_info['media_type'] = 'document'
                else:
                    media_info['media_type'] = 'document'
                media_info['media_file_id'] = str(doc.id)
        
        return media_info
    
    async def download_media(self, message_id: int, channel_id: int, media_file_id: str) -> Optional[str]:
        """Download media from a message and return the file path."""
        try:
            message = await self.client.get_messages(channel_id, ids=[message_id])
            if not message or not message[0].media:
                return None
            
            # Create filename
            file_extension = self._get_file_extension(message[0].media)
            filename = f"{media_file_id}{file_extension}"
            file_path = self.media_dir / filename
            
            # Download if not exists
            if not file_path.exists():
                await self.client.download_media(message[0].media, file_path)
                logging.info(f"Downloaded media: {file_path}")
            
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Error downloading media {media_file_id}: {e}")
            return None
    
    def _get_file_extension(self, media) -> str:
        """Get appropriate file extension for media."""
        if isinstance(media, MessageMediaPhoto):
            return '.jpg'
        elif isinstance(media, MessageMediaDocument):
            doc = media.document
            if doc.mime_type:
                if 'jpeg' in doc.mime_type or 'jpg' in doc.mime_type:
                    return '.jpg'
                elif 'png' in doc.mime_type:
                    return '.png'
                elif 'gif' in doc.mime_type:
                    return '.gif'
                elif 'mp4' in doc.mime_type:
                    return '.mp4'
                elif 'webm' in doc.mime_type:
                    return '.webm'
                elif 'mp3' in doc.mime_type:
                    return '.mp3'
            # Try to get from attributes
            for attr in doc.attributes:
                if hasattr(attr, 'file_name') and attr.file_name:
                    return Path(attr.file_name).suffix
            return '.bin'
        return '.bin'
    
    async def send_message(self, channel_id: int, message_text: str, media_path: Optional[str] = None) -> bool:
        """Send a message to a channel with optional media."""
        try:
            if media_path and Path(media_path).exists():
                await self.client.send_file(channel_id, media_path, caption=message_text)
            else:
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