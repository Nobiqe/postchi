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

    async def run(self) -> None:
        """Main application loop."""
        print("Welcome to Telegram Multi-Channel Processor!")
        
        while True:
            try:
                self.display_main_menu()
                choice = input("Enter your choice (1-7): ").strip()
                
                if choice == "1":
                    await self.configure_telegram()
                    
                elif choice == "2":
                    await self.configure_ai()
                    
                elif choice == "3":
                    await self.manage_channel_mappings()
                    
                elif choice == "4":
                    await self.list_all_chats()
                    
                elif choice == "5":
                    await self.start_processing()
                    
                elif choice == "6":
                    self.view_database_status()
                    
                elif choice == "7":
                    print("Goodbye!")
                    break
                    
                else:
                    print("Invalid choice. Please enter 1-7.")
                
                if choice != "5":  # Don't pause after processing
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                print(f"An error occurred: {e}")
        
        # Cleanup
        if self.processor:
            await self.processor.disconnect()

    def display_main_menu(self) -> None:
        """Display the main menu."""
        print("\n" + "="*60)
        print("TELEGRAM MULTI-CHANNEL PROCESSOR")
        print("="*60)
        print("1. Configure Telegram Settings")
        print("2. Configure AI Settings")
        print("3. Manage Channel Mappings")
        print("4. List All Chats")
        print("5. Start Processing")
        print("6. View Database Status")
        print("7. Exit")
        print("="*60)

    async def configure_telegram(self) -> None:
        """Configure Telegram settings."""
        print("\n--- Telegram Configuration ---")
        
        current = self.config_manager.telegram_config
        print(f"Current API ID: {current.api_id or 'Not set'}")
        print(f"Current Phone: {current.phone_number or 'Not set'}")
        
        api_id = input("Enter API ID (or press Enter to keep current): ").strip()
        api_hash = input("Enter API Hash (or press Enter to keep current): ").strip()
        phone = input("Enter Phone Number (or press Enter to keep current): ").strip()
        
        if api_id:
            current.api_id = api_id
        if api_hash:
            current.api_hash = api_hash
        if phone:
            current.phone_number = phone
        
        if self.config_manager.save_config():
            print("Telegram configuration saved successfully!")
        else:
            print("Error saving configuration!")

        # Test the connection
        if api_id and api_hash and phone:
            print("Testing Telegram connection...")
            try:
                from telegram_client import TelegramChannelClient
                test_client = TelegramChannelClient(api_id, api_hash, phone)
                if await test_client.initialize():
                    print("✓ Telegram authentication successful!")
                    # Get user info
                    me = await test_client.client.get_me()
                    print(f"✓ Logged in as: {me.first_name} {me.last_name or ''}")
                else:
                    print("✗ Telegram authentication failed!")
                await test_client.disconnect()
            except Exception as e:
                print(f"✗ Connection test failed: {e}")

    async def configure_ai(self) -> None:
        """Configure AI settings with connection testing."""
        print("\n--- AI Configuration ---")
        
        current = self.config_manager.ai_config
        print(f"Current Provider: {current.provider}")
        print(f"Current API Key: {'*' * len(current.api_key[:10]) + '...' if current.api_key else 'Not set'}")
        print(f"Current Model: {current.model}")
        print(f"Current Base URL: {getattr(current, 'base_url', 'Default')}")
        
        # Provider selection
        print("\nSelect AI Provider:")
        print("1. Google Gemini")
        print("2. OpenAI")
        print("3. OpenRouter")
        
        provider_choice = input("Enter choice (1-3): ").strip()
        if provider_choice == "1":
            current.provider = "gemini"
            current.base_url = ""
        elif provider_choice == "2":
            current.provider = "openai"
            current.base_url = "https://api.openai.com/v1/chat/completions"
        elif provider_choice == "3":
            current.provider = "openrouter"
            current.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # API Key
        api_key = input("Enter API Key: ").strip()
        if api_key:
            current.api_key = api_key
        
        # Model
        if current.provider == "gemini":
            model = input(f"Enter model (default: gemini-pro): ").strip() or "gemini-pro"
        elif current.provider == "openai":
            model = input(f"Enter model (default: gpt-3.5-turbo): ").strip() or "gpt-3.5-turbo"
        else:  # openrouter
            model = input(f"Enter model (e.g., deepseek/deepseek-chat-v3-0324:free): ").strip()
        
        if model:
            current.model = model
        
        # Custom base URL
        if current.provider != "gemini":
            use_custom = input("Use custom base URL? (y/n): ").strip().lower()
            if use_custom == 'y':
                base_url = input("Enter base URL: ").strip()
                if base_url:
                    current.base_url = base_url
        
        # Save and test
        if self.config_manager.save_config():
            print("Configuration saved! Testing connection...")
            await self._test_ai_connection()
        else:
            print("Error saving configuration!")

    async def manage_channel_mappings(self) -> None:
        """Manage channel mappings submenu."""
        while True:
            self.display_mapping_menu()
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == "1":
                self.view_all_mappings()
            elif choice == "2":
                await self.add_new_mapping()
            elif choice == "3":
                await self.edit_mapping()
            elif choice == "4":
                self.delete_mapping()
            elif choice == "5":
                self.toggle_mapping_status()
            elif choice == "6":
                break
            else:
                print("Invalid choice. Please enter 1-6.")
            
            if choice != "6":
                input("\nPress Enter to continue...")

    async def list_all_chats(self) -> None:
        """List all available chats."""
        print("\n--- Fetching Available Chats ---")
        
        if not self.processor:
            await self._initialize_processor()
        
        if not self.processor:
            print("Error: Cannot initialize Telegram client. Please configure Telegram settings first.")
            return
        
        try:
            chats = await self.processor.telegram_client.get_all_chats()
            
            if not chats:
                print("No chats found or error fetching chats.")
                return
            
            print(f"\nFound {len(chats)} chats:")
            print("-" * 80)
            print(f"{'No.':<4} {'Name':<40} {'ID':<15} {'Type':<15}")
            print("-" * 80)
            
            for i, chat in enumerate(chats, 1):
                name = chat['name'][:35] + "..." if len(chat['name']) > 35 else chat['name']
                print(f"{i:<4} {name:<40} {chat['id']:<15} {chat['type']:<15}")
            
            # Save to database for future reference
            for chat in chats:
                self.db_manager.save_channel_info(chat['id'], chat['name'], chat['type'])
            
            print("\nChat information saved to database.")
            
        except Exception as e:
            logging.error(f"Error listing chats: {e}")
            print("Error fetching chats. Please check your Telegram configuration.")

    async def _initialize_processor(self) -> bool:
        """Initialize the processor if not already done."""
        try:
            tg_config = self.config_manager.telegram_config
            
            if not all([tg_config.api_id, tg_config.api_hash, tg_config.phone_number]):
                print("Telegram configuration is incomplete. Please configure Telegram settings first.")
                return False
            
            if not self.config_manager.ai_config.api_key:
                print("AI configuration is incomplete. Please configure AI settings first.")
                return False
            
            self.processor = MultiChannelProcessor(self.config_manager)
            
            if await self.processor.initialize():
                print("Processor initialized successfully!")
                return True
            else:
                print("Failed to initialize processor!")
                return False
                
        except Exception as e:
            logging.error(f"Error initializing processor: {e}")
            print(f"Error initializing processor: {e}")
            return False
    
    async def start_processing(self) -> None:
        """Start the message processing."""
        print("\n--- Starting Message Processing ---")
        
        if not self.processor:
            await self._initialize_processor()
        
        if not self.processor:
            print("Cannot start processing without proper initialization.")
            return
        
        active_mappings = self.config_manager.get_active_mappings()
        if not active_mappings:
            print("No active channel mappings found!")
            return
        
        print(f"Found {len(active_mappings)} active mappings:")
        for mapping in active_mappings:
            print(f"  - {mapping.id}: {mapping.source_channel_name} -> {mapping.target_channel_name}")
        
        # Ask user what to do
        print("\nProcessing options:")
        print("1. Process historical messages only (last 7 days)")
        print("2. Start real-time monitoring")
        print("3. Both (recommended for first run)")
        
        choice = input("Enter choice (1-3): ").strip()
        
        # AI Agent Configuration
        use_ai_agent = False
        ai_system_prompt = None
        custom_footer = None
        
        print("\n--- AI Agent Configuration ---")
        agent_choice = input("Do you want to use AI agent to edit text? (y/n): ").strip().lower()
        
        if agent_choice == 'y':
            # Check if AI is configured
            if not self.config_manager.ai_config.api_key:
                print("Error: AI API key not configured! Please configure AI settings first.")
                return
            
            # Test AI connection
            try:
                from ai_processor import UniversalMessageProcessor
                ai_config = self.config_manager.ai_config
                test_processor = UniversalMessageProcessor(
                    ai_config.api_key, ai_config.model, ai_config.provider, ai_config.base_url
                )
                test_result = await test_processor.process_message("تست", None)
                if not test_result:
                    print("Error: Cannot connect to AI API!")
                    return
            except Exception as e:
                print(f"Error connecting to AI: {e}")
                return
            
            use_ai_agent = True
            print("\nEnter system prompt for AI agent (what you want the agent to do with the text):")
            print("Example: 'Rewrite this text to be more professional and add trading insights'")
            ai_system_prompt = input("System prompt: ").strip()
            
            if not ai_system_prompt:
                ai_system_prompt = "Please rewrite this text to be more professional and suitable for a trading channel."
        
        # Footer Configuration
        print("\n--- Footer Configuration ---")
        print("Choose footer style:")
        print("1. Default footer (links + hashtags)")
        print("2. Custom footer")
        print("3. No footer")
        
        footer_choice = input("Enter choice (1-3): ").strip()
        
        if footer_choice == "2":
            print("\nEnter custom footer content:")
            print("You can use Telegram formatting:")
            print("- **bold text**")
            print("- *italic text*") 
            print("- [link text](URL)")
            print("- `code text`")
            print("- #hashtag")
            custom_footer = input("Custom footer: ").strip()
            
            if custom_footer:
                custom_footer = "\n\n" + custom_footer
        elif footer_choice == "3":
            custom_footer = ""
        
        # Store configuration for this session
        session_config = {
            'use_ai_agent': use_ai_agent,
            'ai_system_prompt': ai_system_prompt,
            'custom_footer': custom_footer
        }
        
        try:
            if choice in ['1', '3']:
                print("\nProcessing historical messages...")
                for mapping in active_mappings:
                    print(f"Processing {mapping.id}...")
                    
                    # Count messages before processing
                    since_date = datetime.now() - timedelta(days=7)
                    messages = await self.processor.telegram_client.get_channel_messages(
                        mapping.source_channel_id, since_date=since_date
                    )
                    
                    matching_count = 0
                    for msg_data in messages:
                        if self.processor._message_matches_criteria(msg_data['text'], mapping):
                            matching_count += 1
                    
                    print(f"  Found {len(messages)} total messages, {matching_count} matching criteria")
                    
                    # Process with session config
                    await self._process_mapping_with_config(mapping, session_config, historical=True)
                
                print("Historical processing completed!")
            
            if choice in ['2', '3']:
                print("\nStarting real-time monitoring...")
                print("Messages will be posted every 12 hours automatically.")
                print("Press Ctrl+C to stop monitoring.")
                
                # Store session config for real-time monitoring
                self.processor.session_config = session_config
                await self.processor.start_monitoring()
            
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            if self.processor:
                self.processor.stop_monitoring()
        except Exception as e:
            logging.error(f"Error during processing: {e}")
            print(f"Error during processing: {e}")

    async def _process_mapping_with_config(self, mapping, session_config, historical=False):
        """Process mapping with session configuration."""
        try:
            if historical:
                since_date = datetime.now() - timedelta(days=7)
                messages = await self.processor.telegram_client.get_channel_messages(
                    mapping.source_channel_id, since_date=since_date
                )
            else:
                last_id = self.processor.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
                messages = await self.processor.telegram_client.get_channel_messages(
                    mapping.source_channel_id, last_message_id=last_id
                )
            
            for msg_data in messages:
                if self.processor._message_matches_criteria(msg_data['text'], mapping):
                    await self._process_single_message_with_config(msg_data, mapping, session_config)
                    
        except Exception as e:
            logging.error(f"Error processing mapping {mapping.id} with config: {e}")

    async def _process_single_message_with_config(self, msg_data, mapping, session_config):
        """Process a single message with session configuration."""
        try:
            # Check if already processed
            last_id = self.processor.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            if last_id and msg_data['id'] <= last_id:
                return
            
            # Determine prompt to use
            prompt_to_use = None
            if session_config['use_ai_agent'] and session_config['ai_system_prompt']:
                prompt_to_use = f"{session_config['ai_system_prompt']}\n\nOriginal text: {{original_text}}\n\nPlease provide only the rewritten text."
            elif mapping.prompt_template:
                prompt_to_use = mapping.prompt_template
            
            # Process with AI
            processed_text = await self.processor.ai_processor.process_message(
                msg_data['text'], 
                prompt_to_use,
                session_config['custom_footer']
            )
            
            if processed_text:
                # Save to database
                from database import ProcessedMessage
                message = ProcessedMessage(
                    message_id=msg_data['id'],
                    source_channel_id=mapping.source_channel_id,
                    target_channel_id=mapping.target_channel_id,
                    mapping_id=mapping.id,
                    original_message=msg_data['text'],
                    processed_message=processed_text,
                    date=msg_data['date']
                )
                
                if self.processor.db_manager.save_processed_message(message):
                    logging.info(f"Processed and saved message {msg_data['id']} for mapping {mapping.id}")
                else:
                    logging.error(f"Failed to save message {msg_data['id']} for mapping {mapping.id}")
            
        except Exception as e:
            logging.error(f"Error processing message {msg_data['id']} for mapping {mapping.id}: {e}")

    def view_database_status(self) -> None:
        """View database status and statistics."""
        print("\n--- Database Status ---")
        
        try:
            channels = self.db_manager.get_all_channels()
            print(f"Stored Channels: {len(channels)}")
            
            # Get message counts for each mapping
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Total messages
                cursor.execute("SELECT COUNT(*) FROM processed_messages")
                total_messages = cursor.fetchone()[0]
                print(f"Total Processed Messages: {total_messages}")
                
                # Unposted messages
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 0")
                unposted_messages = cursor.fetchone()[0]
                print(f"Unposted Messages: {unposted_messages}")
                
                # Posted messages
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 1")
                posted_messages = cursor.fetchone()[0]
                print(f"Posted Messages: {posted_messages}")
                
                # Messages by mapping
                cursor.execute("""
                    SELECT mapping_id, COUNT(*) as count, 
                           SUM(CASE WHEN posted = 1 THEN 1 ELSE 0 END) as posted_count
                    FROM processed_messages 
                    GROUP BY mapping_id
                """)
                
                results = cursor.fetchall()
                if results:
                    print("\nMessages by Mapping:")
                    for mapping_id, total, posted in results:
                        unposted = total - posted
                        print(f"  {mapping_id}: {total} total, {posted} posted, {unposted} pending")
                
                # Recent activity
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM processed_messages 
                    WHERE created_at >= date('now', '-7 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                
                recent = cursor.fetchall()
                if recent:
                    print("\nRecent Activity (last 7 days):")
                    for date, count in recent:
                        print(f"  {date}: {count} messages")
        
        except Exception as e:
            logging.error(f"Error getting database status: {e}")
            print("Error retrieving database status.")

    def display_mapping_menu(self) -> None:
        """Display channel mapping management menu."""
        print("\n" + "="*50)
        print("CHANNEL MAPPING MANAGEMENT")
        print("="*50)
        print("1. View All Mappings")
        print("2. Add New Mapping")
        print("3. Edit Mapping")
        print("4. Delete Mapping")
        print("5. Toggle Mapping Active/Inactive")
        print("6. Back to Main Menu")
        print("="*50)
    
    async def _test_ai_connection(self) -> None:
        """Test AI connection."""
        try:
            from ai_processor import UniversalMessageProcessor
            ai_config = self.config_manager.ai_config
            
            processor = UniversalMessageProcessor(
                ai_config.api_key, 
                ai_config.model, 
                ai_config.provider, 
                ai_config.base_url
            )
            
            # Test with simple message
            test_result = await processor.process_message("تست اتصال", None)
            
            if test_result:
                print("✓ AI connection successful!")
                print("✓ Model responding correctly")
            else:
                print("✗ AI connection failed!")
                
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
    

    def view_all_mappings(self) -> None:
        """Display all channel mappings."""
        mappings = self.config_manager.channel_mappings
        
        if not mappings:
            print("No channel mappings configured.")
            return
        
        print("\n--- Current Channel Mappings ---")
        for mapping_id, mapping in mappings.items():
            status = "Active" if mapping.active else "Inactive"
            print(f"\nMapping ID: {mapping_id}")
            print(f"  Status: {status}")
            print(f"  Source: {mapping.source_channel_name} (ID: {mapping.source_channel_id})")
            print(f"  Target: {mapping.target_channel_name} (ID: {mapping.target_channel_id})")
            print(f"  Keywords: {', '.join(mapping.keywords) if mapping.keywords else 'None'}")
            print(f"  Signature: {mapping.signature}")
    
    async def add_new_mapping(self) -> None:
        """Add a new channel mapping."""
        print("\n--- Add New Channel Mapping ---")
        
        # Initialize processor to get chat list
        if not self.processor:
            await self._initialize_processor()
        
        if not self.processor:
            print("Error: Cannot initialize Telegram client. Please configure Telegram settings first.")
            return
        
        mapping_id = input("Enter mapping ID (unique identifier): ").strip()
        if mapping_id in self.config_manager.channel_mappings:
            print("Error: Mapping ID already exists!")
            return
        
        print("\nFetching available chats...")
        chats = await self.processor.telegram_client.get_all_chats()
        
        # Display available chats
        print("\nAvailable Chats:")
        for i, chat in enumerate(chats, 1):
            print(f"{i}. {chat['name']} (ID: {chat['id']}) - Type: {chat['type']}")
        
        # Get source channel
        try:
            source_idx = int(input("\nSelect source channel number: ")) - 1
            source_chat = chats[source_idx]
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        # Get target channel
        try:
            target_idx = int(input("Select target channel number: ")) - 1
            target_chat = chats[target_idx]
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        # Get other details
        keywords_input = input("Enter keywords (comma-separated, or press Enter for none): ").strip()
        keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []
        
        signature = input("Enter required signature (e.g., @Fundamental_View): ").strip()
        
        # Create mapping
        mapping = ChannelMapping(
            id=mapping_id,
            source_channel_id=source_chat['id'],
            source_channel_name=source_chat['name'],
            target_channel_id=target_chat['id'],
            target_channel_name=target_chat['name'],
            keywords=keywords,
            signature=signature,
            active=True
        )
        
        if self.config_manager.add_channel_mapping(mapping):
            print(f"Mapping '{mapping_id}' added successfully!")
            
            # Save channel info to database
            self.db_manager.save_channel_info(source_chat['id'], source_chat['name'], 'source')
            self.db_manager.save_channel_info(target_chat['id'], target_chat['name'], 'target')
        else:
            print("Error adding mapping!")
    
    async def edit_mapping(self) -> None:
        """Edit an existing channel mapping."""
        self.view_all_mappings()
        
        if not self.config_manager.channel_mappings:
            return
        
        mapping_id = input("\nEnter mapping ID to edit: ").strip()
        mapping = self.config_manager.channel_mappings.get(mapping_id)
        
        if not mapping:
            print("Mapping not found!")
            return
        
        print(f"\nEditing mapping: {mapping_id}")
        print("Press Enter to keep current values")
        
        # Edit keywords
        current_keywords = ', '.join(mapping.keywords) if mapping.keywords else ''
        keywords_input = input(f"Keywords (current: {current_keywords}): ").strip()
        if keywords_input:
            mapping.keywords = [k.strip() for k in keywords_input.split(",")]
        
        # Edit signature
        signature = input(f"Signature (current: {mapping.signature}): ").strip()
        if signature:
            mapping.signature = signature
        
        # Custom prompt template
        if mapping.prompt_template:
            print("Current custom prompt template is set.")
        use_custom = input("Do you want to set a custom prompt template? (y/n): ").strip().lower()
        if use_custom == 'y':
            print("Enter custom prompt template (use {original_text} as placeholder):")
            custom_prompt = input().strip()
            if custom_prompt:
                mapping.prompt_template = custom_prompt
        
        if self.config_manager.save_config():
            print("Mapping updated successfully!")
        else:
            print("Error updating mapping!")
    
    def delete_mapping(self) -> None:
        """Delete a channel mapping."""
        self.view_all_mappings()
        
        if not self.config_manager.channel_mappings:
            return
        
        mapping_id = input("\nEnter mapping ID to delete: ").strip()
        
        if mapping_id not in self.config_manager.channel_mappings:
            print("Mapping not found!")
            return
        
        confirm = input(f"Are you sure you want to delete mapping '{mapping_id}'? (y/n): ").strip().lower()
        if confirm == 'y':
            if self.config_manager.remove_channel_mapping(mapping_id):
                print("Mapping deleted successfully!")
            else:
                print("Error deleting mapping!")
    
    def toggle_mapping_status(self) -> None:
        """Toggle mapping active/inactive status."""
        self.view_all_mappings()
        
        if not self.config_manager.channel_mappings:
            return
        
        mapping_id = input("\nEnter mapping ID to toggle: ").strip()
        mapping = self.config_manager.channel_mappings.get(mapping_id)
        
        if not mapping:
            print("Mapping not found!")
            return
        
        mapping.active = not mapping.active
        status = "activated" if mapping.active else "deactivated"
        
        if self.config_manager.save_config():
            print(f"Mapping '{mapping_id}' {status} successfully!")
        else:
            print("Error updating mapping status!")
    