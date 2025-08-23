import asyncio
import logging
import os
import time
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from datetime import datetime, timedelta
from pathlib import Path


class TelegramChannelClient:
    """Enhanced Telegram client with media support and database lock prevention."""
    
    def __init__(self, api_id: str, api_hash: str, phone_number: str):
        # Use consistent session name instead of unique ones
        session_name = f'session_{phone_number.replace("+", "")}'
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.phone_number = phone_number
        self.session_name = session_name
        self.media_dir = Path("media")
        self.media_dir.mkdir(exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize and authenticate the client with session reuse."""
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
    
    def _cleanup_session_files(self):
        """Clean up old session files to prevent conflicts."""
        try:
            current_dir = Path('.')
            session_files = list(current_dir.glob('session_*.session*'))
            
            for session_file in session_files:
                try:
                    # Only remove files older than 1 hour
                    if time.time() - session_file.stat().st_mtime > 3600:
                        session_file.unlink()
                        logging.info(f"Cleaned up old session file: {session_file}")
                except Exception as e:
                    logging.warning(f"Could not remove session file {session_file}: {e}")
        except Exception as e:
            logging.warning(f"Error during session cleanup: {e}")
    
    async def get_all_chats(self) -> List[Dict[str, Any]]:
        """Get all available chats/channels with error handling."""
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
        """Get messages from a specific channel with media support and improved error handling."""
        try:
            messages = []
            kwargs = {}
            
            if since_date:
                kwargs['offset_date'] = since_date
            elif last_message_id:
                kwargs['min_id'] = last_message_id
            elif limit:
                kwargs['limit'] = limit
            else:
                kwargs['limit'] = 10
            
            # Only set limit if specified
            if limit and 'limit' not in kwargs:
                kwargs['limit'] = limit
            
            # Add timeout to prevent hanging
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
            
            # Sort by message ID descending (newest first) when using min_id
            if last_message_id:
                messages.sort(key=lambda x: x['id'], reverse=True)
            
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
        """Download media from a message and return the file path with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
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
                logging.error(f"Error downloading media {media_file_id} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
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
        """Send a message to a channel with optional media as single post."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if media_path and Path(media_path).exists():
                    # For media posts, use caption (max 1024 chars)
                    if len(message_text) > 1024:
                        # Truncate to fit in single caption
                        caption = message_text[:1020] + "..."
                        await self.client.send_file(channel_id, media_path, caption=caption)
                    else:
                        await self.client.send_file(channel_id, media_path, caption=message_text)
                else:
                    # For text-only posts, Telegram allows up to 4096 characters
                    if len(message_text) > 4096:
                        # Truncate to fit in single message
                        message_text = message_text[:4090] + "..."
                    
                    await self.client.send_message(channel_id, message_text)
                return True
                
            except FloodWaitError as e:
                logging.warning(f"Flood wait error: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                return False
                
            except Exception as e:
                logging.error(f"Error sending message to channel {channel_id} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    return False
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram with proper cleanup."""
        try:
            if self.client.is_connected():
                await self.client.disconnect()
            logging.info("Disconnected from Telegram")
            
            # Clean up session files after disconnect
            await asyncio.sleep(1)  # Give time for files to be released
            self._cleanup_current_session()
            
        except Exception as e:
            logging.error(f"Error disconnecting: {e}")
    
    def _cleanup_current_session(self):
        """Clean up current session files."""
        try:
            session_files = [
                f"{self.session_name}.session",
                f"{self.session_name}.session-journal"
            ]
            
            for filename in session_files:
                file_path = Path(filename)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        logging.info(f"Cleaned up session file: {filename}")
                    except Exception as e:
                        logging.warning(f"Could not remove {filename}: {e}")
        except Exception as e:
            logging.warning(f"Error cleaning up session files: {e}")