import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional,Dict
from dataclasses import dataclass
from pathlib import Path
import logging


@dataclass
class ProcessedMessage:
    """Data class for processed messages."""
    original_message: str
    processed_message: str
    message_id: int
    date: datetime
    source_channel_id: int
    target_channel_id: int
    mapping_id: str
    posted: bool = False


class DatabaseManager:
    """Enhanced database manager with support for multiple channel mappings."""
    
    def __init__(self, db_path: str = "telegram_messages.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enhanced processed_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    source_channel_id INTEGER,
                    target_channel_id INTEGER,
                    mapping_id TEXT,
                    original_message TEXT,
                    processed_message TEXT,
                    date_received TIMESTAMP,
                    date_processed TIMESTAMP,
                    posted BOOLEAN DEFAULT 0,
                    date_posted TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, source_channel_id, target_channel_id)
                )
            """)
            
            # Enhanced posting schedule table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posting_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mapping_id TEXT UNIQUE,
                    last_post_time TIMESTAMP,
                    messages_posted_today INTEGER DEFAULT 0,
                    post_interval_hours INTEGER DEFAULT 12,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Channel information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY,
                    channel_id INTEGER UNIQUE,
                    channel_name TEXT,
                    channel_type TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_processed_message(self, message: ProcessedMessage) -> bool:
        """Save a processed message to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO processed_messages 
                    (message_id, source_channel_id, target_channel_id, mapping_id,
                     original_message, processed_message, date_received, date_processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.message_id,
                    message.source_channel_id,
                    message.target_channel_id,
                    message.mapping_id,
                    message.original_message,
                    message.processed_message,
                    message.date,
                    datetime.now()
                ))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error saving message to database: {e}")
            return False
    
    def get_unposted_messages(self, mapping_id: str, limit: int = 1) -> List[ProcessedMessage]:
        """Get unposted messages for a specific mapping."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT message_id, source_channel_id, target_channel_id, mapping_id,
                           original_message, processed_message, date_received, posted
                    FROM processed_messages 
                    WHERE posted = 0 AND mapping_id = ?
                    ORDER BY date_received ASC 
                    LIMIT ?
                """, (mapping_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append(ProcessedMessage(
                        message_id=row[0],
                        source_channel_id=row[1],
                        target_channel_id=row[2],
                        mapping_id=row[3],
                        original_message=row[4],
                        processed_message=row[5],
                        date=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                        posted=bool(row[7])
                    ))
                return messages
        except Exception as e:
            logging.error(f"Error getting unposted messages: {e}")
            return []
    
    def mark_as_posted(self, message_id: int, mapping_id: str) -> bool:
        """Mark a message as posted."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE processed_messages 
                    SET posted = 1, date_posted = ? 
                    WHERE message_id = ? AND mapping_id = ?
                """, (datetime.now(), message_id, mapping_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error marking message as posted: {e}")
            return False
    
    def get_last_message_id(self, source_channel_id: int, mapping_id: str) -> Optional[int]:
        """Get the last processed message ID for a channel mapping."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(message_id) FROM processed_messages 
                    WHERE source_channel_id = ? AND mapping_id = ?
                """, (source_channel_id, mapping_id))
                result = cursor.fetchone()[0]
                return result
        except Exception as e:
            logging.error(f"Error getting last message ID: {e}")
            return None
    
    def should_post_now(self, mapping_id: str) -> bool:
        """Check if it's time to post for a specific mapping."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT last_post_time, post_interval_hours 
                    FROM posting_schedule 
                    WHERE mapping_id = ?
                """, (mapping_id,))
                
                result = cursor.fetchone()
                if not result:
                    # Create initial schedule
                    cursor.execute("""
                        INSERT INTO posting_schedule (mapping_id, last_post_time, post_interval_hours)
                        VALUES (?, ?, 12)
                    """, (mapping_id, datetime.now() - timedelta(hours=12)))
                    conn.commit()
                    return True
                
                last_post_time = datetime.fromisoformat(result[0])
                interval_hours = result[1]
                return datetime.now() - last_post_time >= timedelta(hours=interval_hours)
                
        except Exception as e:
            logging.error(f"Error checking post schedule: {e}")
            return False
    
    def update_post_schedule(self, mapping_id: str) -> None:
        """Update the posting schedule for a mapping."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO posting_schedule 
                    (mapping_id, last_post_time, messages_posted_today)
                    VALUES (?, ?, COALESCE((SELECT messages_posted_today FROM posting_schedule WHERE mapping_id = ?), 0) + 1)
                """, (mapping_id, datetime.now(), mapping_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating post schedule: {e}")
    
    def save_channel_info(self, channel_id: int, channel_name: str, channel_type: str) -> None:
        """Save channel information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO channels 
                    (channel_id, channel_name, channel_type, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (channel_id, channel_name, channel_type, datetime.now()))
                conn.commit()
        except Exception as e:
            logging.error(f"Error saving channel info: {e}")
    
    def get_all_channels(self) -> List[Dict]:
        """Get all saved channel information."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT channel_id, channel_name, channel_type FROM channels")
                return [{'id': row[0], 'name': row[1], 'type': row[2]} for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting channels: {e}")
            return []