import asyncio
from typing import Optional
from config import ConfigManager, ChannelMapping, TelegramConfig, AIConfig
from main_processor import MultiChannelProcessor
from database import DatabaseManager
import logging
from datetime import datetime, timedelta
from typing import Optional
from datetime import datetime
from config import SavedFooter  # Add this import

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
        """Start the message processing with media support options."""
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
        
        # Processing type selection
        print("\nProcessing options:")
        print("1. Process historical messages only (last 7 days)")
        print("2. Start real-time monitoring (immediate forwarding)")
        print("3. Both (recommended for first run)")
        
        processing_choice = input("Enter choice (1-3): ").strip()
        
        # Media handling configuration
        print("\n--- Media Configuration ---")
        include_media = input("Do you want to download and forward media files? (y/n): ").strip().lower() == 'y'
        
        # AI Agent Configuration
        print("\n--- AI Agent Configuration ---")
        use_ai_agent = input("Do you want to use AI agent to edit text? (y/n): ").strip().lower() == 'y'

        ai_system_prompt = None
        if use_ai_agent:
            if not self.config_manager.ai_config.api_key:
                print("Error: AI API key not configured! Please configure AI settings first.")
                return
            
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
            
            print("\nEnter system prompt for AI agent:")
            print("Example: 'Rewrite this text to be more professional and add trading insights'")
            ai_system_prompt = input("System prompt: ").strip()
            
            if not ai_system_prompt:
                ai_system_prompt = "Please rewrite this text to be more professional and suitable for a trading channel."

        # Footer Configuration
        custom_footer = None
        while True:
            print("\n--- Footer Configuration ---")
            print("Choose footer style:")
            print("1. Saved footers")
            print("2. Create Custom footer")
            print("3. No footer")
            
            footer_choice = input("Enter choice (1-3): ").strip()
            
            if footer_choice == "1":
                selected_footer = self.show_saved_footers_menu()
                if selected_footer is not None:
                    custom_footer = selected_footer
                    break
            elif footer_choice == "2":
                custom_footer = self.create_custom_footer()
                break
            elif footer_choice == "3":
                custom_footer = ""
                break
            else:
                print("Invalid choice. Please enter 1-3.")

        # Mode calculation with media support (now 36 modes total)
        mode_base = 0
        if processing_choice == "1":  # Historical
            mode_base = 0
        elif processing_choice == "2":  # Real-time
            mode_base = 12
        elif processing_choice == "3":  # Both
            mode_base = 24

        media_offset = 0 if include_media else 6
        ai_offset = 0 if use_ai_agent else 3
        footer_offset = int(footer_choice) - 1
        current_mode = mode_base + media_offset + ai_offset + footer_offset + 1

        print(f"\nMode {current_mode}/36:")
        print(f"   Processing: {['Historical', 'Real-time', 'Both'][int(processing_choice)-1]}")
        print(f"   Media: {'Enabled' if include_media else 'Disabled'}")
        print(f"   AI Agent: {'Enabled' if use_ai_agent else 'Disabled'}")
        print(f"   Footer: {['Saved', 'Custom', 'None'][int(footer_choice)-1]}")
        
        # Create session configuration
        session_config = {
            'use_ai_agent': use_ai_agent,
            'ai_system_prompt': ai_system_prompt,
            'custom_footer': custom_footer,
            'include_media': include_media,
            'mode': current_mode
        }
        
        try:
            if processing_choice in ['1', '3']:  # Historical processing
                print(f"\nProcessing historical messages (Mode {current_mode})...")
                for mapping in active_mappings:
                    print(f"Processing {mapping.id}...")
                    
                    since_date = datetime.now() - timedelta(days=7)
                    messages = await self.processor.telegram_client.get_channel_messages(
                        mapping.source_channel_id, since_date=since_date
                    )
                    
                    matching_count = 0
                    for msg_data in messages:
                        if self.processor._message_matches_criteria(msg_data['text'], mapping):
                            matching_count += 1
                    
                    print(f"  Found {len(messages)} total messages, {matching_count} matching criteria")
                    
                    await self._process_mapping_with_config(mapping, session_config, historical=True)
                
                print("Historical processing completed!")
            
            if processing_choice in ['2', '3']:  # Real-time monitoring
                print(f"\nStarting real-time monitoring (Mode {current_mode})...")
                print("Messages will be forwarded immediately when detected.")
                print("\n" + "="*60)
                print("MONITORING ACTIVE - Choose an option:")
                print("  Press '5' + Enter: Stop and return to main menu")
                print("  Press Ctrl+C: Force stop")
                print("="*60)
                
                self.processor.session_config = session_config
                await self._start_monitoring_with_exit()
            
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            if self.processor:
                self.processor.stop_monitoring()
        except Exception as e:
            logging.error(f"Error during processing (Mode {current_mode}): {e}")
            print(f"Error during processing: {e}")

    async def _start_monitoring_with_exit(self) -> None:
        """Start monitoring with option to exit gracefully."""
        import threading
        import sys
        
        # Flag to control monitoring
        monitoring_active = True
        
        def input_thread():
            """Thread to handle user input."""
            nonlocal monitoring_active
            while monitoring_active:
                try:
                    user_input = input().strip()
                    if user_input == '5':
                        print("\n⏹️  Stopping monitoring and returning to main menu...")
                        monitoring_active = False
                        if self.processor:
                            self.processor.stop_monitoring()
                        break
                except EOFError:
                    # Handle Ctrl+D
                    break
                except KeyboardInterrupt:
                    # Handle Ctrl+C in input thread
                    break
        
        # Start input thread
        input_thread_obj = threading.Thread(target=input_thread, daemon=True)
        input_thread_obj.start()
        
        # Start monitoring
        self.processor.is_running = True
        logging.info("Starting multi-channel monitoring...")
        
        try:
            while self.processor.is_running and monitoring_active:
                try:
                    active_mappings = self.config_manager.get_active_mappings()
                    
                    for mapping in active_mappings:
                        if not monitoring_active:
                            break
                        # Only use the immediate processing method
                        await self.processor._process_and_post_immediately(mapping)
                    
                    # Wait before next check
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(5)
                    
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user.")
        finally:
            monitoring_active = False
            if self.processor:
                self.processor.stop_monitoring()
            print("✅ Returned to main menu.")

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
        """Process a single message with session configuration including media."""
        try:
            last_id = self.processor.db_manager.get_last_message_id(mapping.source_channel_id, mapping.id)
            if last_id and msg_data['id'] <= last_id:
                return
            
            # Handle media download if enabled
            media_path = None
            if session_config['include_media'] and msg_data.get('has_media'):
                media_path = await self.processor.telegram_client.download_media(
                    msg_data['id'], mapping.source_channel_id, msg_data.get('media_file_id')
                )
            
            # Process text with AI if enabled
            processed_text = msg_data['text']
            if session_config['use_ai_agent'] and session_config['ai_system_prompt']:
                prompt_to_use = f"{session_config['ai_system_prompt']}\n\nOriginal text: {{original_text}}\n\nPlease provide only the rewritten text."
                processed_text = await self.processor.ai_processor.process_message(
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
            
            if self.processor.db_manager.save_processed_message(message):
                logging.info(f"Processed and saved message {msg_data['id']} for mapping {mapping.id}")
            else:
                logging.error(f"Failed to save message {msg_data['id']} for mapping {mapping.id}")
        
        except Exception as e:
            logging.error(f"Error processing message {msg_data['id']} for mapping {mapping.id}: {e}")

    def view_database_status(self) -> None:
        """View database status and manage data."""
        while True:
            self.display_database_menu()
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                self.show_database_statistics()
            elif choice == "2":
                self.manage_unposted_messages()
            elif choice == "3":
                self.view_recent_activity()
            elif choice == "4":
                self.manage_processed_messages()
            elif choice == "5":
                self.view_media_messages()  # New option
            elif choice == "6":
                self.database_cleanup()
            elif choice == "7":
                break
            else:
                print("Invalid choice. Please enter 1-7.")
            
            if choice != "7":
                input("\nPress Enter to continue...")

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

    def show_saved_footers_menu(self):
        """Show saved footers menu and return selected footer content."""
        while True:
            if not self.config_manager.saved_footers:
                print("No saved footers found.")
                return ""
            
            print("\n--- Saved Footers ---")
            print("Select a number to preview footer, type 5 to return to footer menu")
            
            # Sort by date (newest first)
            sorted_footers = sorted(self.config_manager.saved_footers, 
                                key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), 
                                reverse=True)
            
            for i, footer in enumerate(sorted_footers, 1):
                date_str = footer.created_at.strftime('%Y-%m-%d') if hasattr(footer, 'created_at') else 'Unknown'
                print(f"{i}. {footer.name} ({date_str})")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == "5":
                return None  # Return to footer menu
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(sorted_footers):
                    return self.show_footer_preview(sorted_footers[idx])
                else:
                    print("Invalid selection!")
            except ValueError:
                print("Please enter a number!")

    def show_footer_preview(self, footer):
        """Show footer preview with options."""
        while True:
            print(f"\n--- Footer Preview: {footer.name} ---")
            print("Content:")
            print("-" * 40)
            print(footer.content)
            print("-" * 40)
            print("\nGuidelines:")
            print("- Press Enter: Select this footer")
            print("- Type 0: Delete this footer")
            print("- Type 5: Return to footer list")
            print("- Leave blank + Enter: Continue without footer")
            
            choice = input("\nYour choice: ").strip()
            
            if choice == "":
                return "\n\n" + footer.content
            elif choice == "0":
                confirm = input(f"Delete '{footer.name}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    self.config_manager.saved_footers.remove(footer)
                    self.config_manager.save_config()
                    print("Footer deleted!")
                    return None  # Return to list
            elif choice == "5":
                return None  # Return to list
            else:
                print("Invalid choice!")

    def create_custom_footer(self):
        """Create a new custom footer using system editor."""
        import tempfile
        import os
        import subprocess
        
        print("\nCreate Custom Footer:")
        print("Opening text editor...")
        
        # Create temporary file with instructions
        instructions = """## Telegram Footer Template
    ## Delete these instruction lines and write your footer below
    ## 
    ## Telegram Formatting Guide:
    ## **bold text**
    ## *italic text*
    ## [link text](URL)
    ## `code text`
    ## #hashtag
    ## 
    ## Example:
    ## Visit: https://example.com
    ## Follow: @username
    ## 
    ## Write your footer content below:

    """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(instructions)
            temp_file_path = temp_file.name
        
        try:
            # Open editor based on OS
            if os.name == 'nt':  # Windows
                os.startfile(temp_file_path)
            elif os.name == 'posix':  # Linux/Mac
                editor = os.environ.get('EDITOR', 'nano')  # Default to nano
                subprocess.run([editor, temp_file_path])
            
            input("Press Enter after you've finished editing and saved the file...")
            
            # Read the content
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            # Remove instruction lines (lines starting with #)
            lines = content.split('\n')
            footer_lines = [line for line in lines if not line.strip().startswith('##')]
            custom_footer = '\n'.join(footer_lines).strip()
            
            if custom_footer:
                # Get footer name
                footer_name = input("\nEnter name for this footer: ").strip()
                if not footer_name:
                    footer_name = f"Footer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Check for duplicate names
                existing_names = [f.name for f in self.config_manager.saved_footers]
                if footer_name in existing_names:
                    counter = 1
                    while f"{footer_name}_{counter}" in existing_names:
                        counter += 1
                    footer_name = f"{footer_name}_{counter}"
                
                # Save footer
                new_footer = SavedFooter(
                    name=footer_name,
                    content=custom_footer,
                    created_at=datetime.now()
                )
                
                self.config_manager.saved_footers.append(new_footer)
                self.config_manager.save_config()
                print(f"Footer saved as '{footer_name}'")
                
                return "\n\n" + custom_footer
            else:
                print("No content entered.")
                return ""
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return ""
    
    def view_database_status(self) -> None:
        """View database status and manage data."""
        while True:
            self.display_database_menu()
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == "1":
                self.show_database_statistics()
            elif choice == "2":
                self.manage_unposted_messages()
            elif choice == "3":
                self.view_recent_activity()
            elif choice == "4":
                self.manage_processed_messages()
            elif choice == "5":
                self.database_cleanup()
            elif choice == "6":
                break
            else:
                print("Invalid choice. Please enter 1-6.")
            
            if choice != "6":
                input("\nPress Enter to continue...")

    def display_database_menu(self) -> None:
        """Display database management menu."""
        print("\n" + "="*50)
        print("DATABASE MANAGEMENT")
        print("="*50)
        print("1. View Statistics")
        print("2. Manage Unposted Messages")
        print("3. View Recent Activity")
        print("4. Manage Processed Messages")
        print("5. View Media Messages")  # New option
        print("6. Database Cleanup")
        print("7. Back to Main Menu")
        print("="*50)

    def show_database_statistics(self) -> None:
        """Show database statistics."""
        print("\n--- Database Statistics ---")
        
        try:
            channels = self.db_manager.get_all_channels()
            print(f"Stored Channels: {len(channels)}")
            
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages")
                total_messages = cursor.fetchone()[0]
                print(f"Total Processed Messages: {total_messages}")
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 0")
                unposted_messages = cursor.fetchone()[0]
                print(f"Unposted Messages: {unposted_messages}")
                
                cursor.execute("SELECT COUNT(*) FROM processed_messages WHERE posted = 1")
                posted_messages = cursor.fetchone()[0]
                print(f"Posted Messages: {posted_messages}")
                
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
        
        except Exception as e:
            logging.error(f"Error getting database statistics: {e}")
            print("Error retrieving database statistics.")

    def manage_unposted_messages(self) -> None:
        """Manage unposted messages."""
        print("\n--- Unposted Messages Management ---")
        
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, mapping_id, message_id, original_message, processed_message, date_received
                    FROM processed_messages WHERE posted = 0
                    ORDER BY date_received DESC
                """)
                
                unposted = cursor.fetchall()
                
                if not unposted:
                    print("No unposted messages found.")
                    return
                
                print(f"Found {len(unposted)} unposted messages:")
                
                for i, (db_id, mapping_id, msg_id, original, processed, date) in enumerate(unposted[:10], 1):
                    print(f"\n{i}. Mapping: {mapping_id} | Message ID: {msg_id}")
                    print(f"   Date: {date}")
                    print(f"   Original: {original[:50]}...")
                    print(f"   Processed: {processed[:50]}...")
                
                if len(unposted) > 10:
                    print(f"\n... and {len(unposted) - 10} more messages")
                
                print("\nOptions:")
                print("1. Mark specific message as posted")
                print("2. Delete specific message")
                print("3. Mark all as posted for a mapping")
                print("4. Clear all unposted messages")
                
                sub_choice = input("Enter choice (1-4): ").strip()
                
                if sub_choice == "1":
                    msg_id = input("Enter message ID to mark as posted: ").strip()
                    mapping_id = input("Enter mapping ID: ").strip()
                    if self.db_manager.mark_as_posted(int(msg_id), mapping_id):
                        print("Message marked as posted.")
                    else:
                        print("Error marking message as posted.")
                
                elif sub_choice == "2":
                    db_id = input("Enter database ID to delete: ").strip()
                    cursor.execute("DELETE FROM processed_messages WHERE id = ?", (db_id,))
                    conn.commit()
                    print("Message deleted.")
                
                elif sub_choice == "3":
                    mapping_id = input("Enter mapping ID: ").strip()
                    cursor.execute("UPDATE processed_messages SET posted = 1, date_posted = ? WHERE mapping_id = ? AND posted = 0", 
                                (datetime.now(), mapping_id))
                    conn.commit()
                    print(f"All messages for mapping '{mapping_id}' marked as posted.")
                
                elif sub_choice == "4":
                    confirm = input("Delete all unposted messages? (y/n): ").strip().lower()
                    if confirm == 'y':
                        cursor.execute("DELETE FROM processed_messages WHERE posted = 0")
                        conn.commit()
                        print("All unposted messages cleared.")
        
        except Exception as e:
            logging.error(f"Error managing unposted messages: {e}")
            print("Error managing unposted messages.")

    def view_recent_activity(self) -> None:
        """View recent database activity."""
        print("\n--- Recent Activity ---")
        
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM processed_messages 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                
                recent = cursor.fetchall()
                if recent:
                    print("Activity (last 30 days):")
                    for date, count in recent:
                        print(f"  {date}: {count} messages")
                else:
                    print("No recent activity found.")
                
                # Show latest messages
                cursor.execute("""
                    SELECT mapping_id, message_id, date_received, posted
                    FROM processed_messages 
                    ORDER BY date_received DESC 
                    LIMIT 10
                """)
                
                latest = cursor.fetchall()
                if latest:
                    print("\nLatest 10 messages:")
                    for mapping_id, msg_id, date, posted in latest:
                        status = "Posted" if posted else "Pending"
                        print(f"  {mapping_id} | ID: {msg_id} | {date} | {status}")
        
        except Exception as e:
            logging.error(f"Error viewing recent activity: {e}")
            print("Error viewing recent activity.")

    def manage_processed_messages(self) -> None:
        """Manage all processed messages."""
        print("\n--- Processed Messages Management ---")
        
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                print("Search options:")
                print("1. By mapping ID")
                print("2. By date range")
                print("3. By message content")
                print("4. Show all recent")
                
                search_choice = input("Enter choice (1-4): ").strip()
                
                if search_choice == "1":
                    mapping_id = input("Enter mapping ID: ").strip()
                    cursor.execute("""
                        SELECT id, message_id, original_message, processed_message, date_received, posted
                        FROM processed_messages WHERE mapping_id = ?
                        ORDER BY date_received DESC LIMIT 20
                    """, (mapping_id,))
                
                elif search_choice == "2":
                    days = input("Enter number of days back: ").strip()
                    cursor.execute("""
                        SELECT id, message_id, original_message, processed_message, date_received, posted
                        FROM processed_messages 
                        WHERE date_received >= date('now', '-{} days')
                        ORDER BY date_received DESC LIMIT 20
                    """.format(days))
                
                elif search_choice == "3":
                    keyword = input("Enter keyword to search in messages: ").strip()
                    cursor.execute("""
                        SELECT id, message_id, original_message, processed_message, date_received, posted
                        FROM processed_messages 
                        WHERE original_message LIKE ? OR processed_message LIKE ?
                        ORDER BY date_received DESC LIMIT 20
                    """, (f'%{keyword}%', f'%{keyword}%'))
                
                else:  # Show all recent
                    cursor.execute("""
                        SELECT id, message_id, original_message, processed_message, date_received, posted
                        FROM processed_messages 
                        ORDER BY date_received DESC LIMIT 20
                    """)
                
                results = cursor.fetchall()
                
                if results:
                    for db_id, msg_id, original, processed, date, posted in results:
                        status = "Posted" if posted else "Pending"
                        print(f"\nDB ID: {db_id} | Msg ID: {msg_id} | {date} | {status}")
                        print(f"Original: {original[:100]}...")
                        print(f"Processed: {processed[:100]}...")
                    
                    print("\nActions:")
                    print("1. Delete message by DB ID")
                    print("2. Edit processed message")
                    print("3. Toggle posted status")
                    
                    action = input("Enter action (1-3): ").strip()
                    
                    if action == "1":
                        db_id = input("Enter DB ID to delete: ").strip()
                        cursor.execute("DELETE FROM processed_messages WHERE id = ?", (db_id,))
                        conn.commit()
                        print("Message deleted.")
                    
                    elif action == "2":
                        db_id = input("Enter DB ID to edit: ").strip()
                        new_text = input("Enter new processed text: ").strip()
                        cursor.execute("UPDATE processed_messages SET processed_message = ? WHERE id = ?", (new_text, db_id))
                        conn.commit()
                        print("Message updated.")
                    
                    elif action == "3":
                        db_id = input("Enter DB ID to toggle status: ").strip()
                        cursor.execute("UPDATE processed_messages SET posted = NOT posted WHERE id = ?", (db_id,))
                        conn.commit()
                        print("Status toggled.")
                
                else:
                    print("No messages found.")
        
        except Exception as e:
            logging.error(f"Error managing processed messages: {e}")
            print("Error managing processed messages.")

    def database_cleanup(self) -> None:
        """Database cleanup options."""
        print("\n--- Database Cleanup ---")
        
        try:
            import sqlite3
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                print("Cleanup options:")
                print("1. Delete old posted messages (older than X days)")
                print("2. Delete messages from specific mapping")
                print("3. Clear posting schedule")
                print("4. Vacuum database")
                print("5. Reset all message statuses to unposted")
                
                cleanup_choice = input("Enter choice (1-5): ").strip()
                
                if cleanup_choice == "1":
                    days = input("Delete posted messages older than how many days? ").strip()
                    confirm = input(f"Delete all posted messages older than {days} days? (y/n): ").strip().lower()
                    if confirm == 'y':
                        cursor.execute("""
                            DELETE FROM processed_messages 
                            WHERE posted = 1 AND date_posted < date('now', '-{} days')
                        """.format(days))
                        deleted = cursor.rowcount
                        conn.commit()
                        print(f"Deleted {deleted} old messages.")
                
                elif cleanup_choice == "2":
                    mapping_id = input("Enter mapping ID to delete all messages: ").strip()
                    confirm = input(f"Delete ALL messages for mapping '{mapping_id}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        cursor.execute("DELETE FROM processed_messages WHERE mapping_id = ?", (mapping_id,))
                        deleted = cursor.rowcount
                        conn.commit()
                        print(f"Deleted {deleted} messages.")
                
                elif cleanup_choice == "3":
                    confirm = input("Clear all posting schedules? (y/n): ").strip().lower()
                    if confirm == 'y':
                        cursor.execute("DELETE FROM posting_schedule")
                        conn.commit()
                        print("Posting schedules cleared.")
                
                elif cleanup_choice == "4":
                    print("Optimizing database...")
                    cursor.execute("VACUUM")
                    conn.commit()
                    print("Database optimized.")
                
                elif cleanup_choice == "5":
                    confirm = input("Reset ALL messages to unposted status? (y/n): ").strip().lower()
                    if confirm == 'y':
                        cursor.execute("UPDATE processed_messages SET posted = 0, date_posted = NULL")
                        updated = cursor.rowcount
                        conn.commit()
                        print(f"Reset {updated} messages to unposted.")
        
        except Exception as e:
            logging.error(f"Error in database cleanup: {e}")
            print("Error performing cleanup.")

    def view_media_messages(self) -> None:
        """View messages with media attachments."""
        print("\n--- Messages with Media ---")
        
        try:
            import sqlite3
            import subprocess
            import platform
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Get messages with media
                cursor.execute("""
                    SELECT id, mapping_id, message_id, original_message, processed_message, 
                        media_type, media_path, date_received, posted
                    FROM processed_messages 
                    WHERE has_media = 1 
                    ORDER BY date_received DESC 
                    LIMIT 20
                """)
                
                media_messages = cursor.fetchall()
                
                if not media_messages:
                    print("No messages with media found.")
                    return
                
                print(f"Found {len(media_messages)} messages with media:")
                
                for i, (db_id, mapping_id, msg_id, original, processed, media_type, media_path, date, posted) in enumerate(media_messages, 1):
                    status = "Posted" if posted else "Pending"
                    media_exists = "✓" if media_path and Path(media_path).exists() else "✗"
                    
                    print(f"\n{i}. ID: {db_id} | Msg: {msg_id} | {mapping_id}")
                    print(f"   Date: {date} | Status: {status}")
                    print(f"   Media: {media_type or 'Unknown'} | File: {media_exists}")
                    print(f"   Text: {(original or '')[:60]}...")
                    if media_path:
                        print(f"   Path: {media_path}")
                
                # Media actions
                print("\nMedia Actions:")
                print("1. View specific media file")
                print("2. Show media statistics")
                print("3. Clean up missing media files")
                print("4. Export media list")
                
                choice = input("Enter choice (1-4): ").strip()
                
                if choice == "1":
                    db_id = input("Enter DB ID to view media: ").strip()
                    cursor.execute("SELECT media_path, media_type FROM processed_messages WHERE id = ?", (db_id,))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        media_path = Path(result[0])
                        if media_path.exists():
                            print(f"Opening: {media_path}")
                            self._open_media_file(str(media_path))
                        else:
                            print("Media file not found on disk.")
                    else:
                        print("No media path found for this message.")
                
                elif choice == "2":
                    # Media statistics
                    cursor.execute("""
                        SELECT media_type, COUNT(*) as count
                        FROM processed_messages 
                        WHERE has_media = 1 
                        GROUP BY media_type
                    """)
                    stats = cursor.fetchall()
                    
                    print("\nMedia Statistics:")
                    for media_type, count in stats:
                        print(f"  {media_type or 'Unknown'}: {count} files")
                    
                    # File size info
                    total_size = 0
                    missing_files = 0
                    cursor.execute("SELECT media_path FROM processed_messages WHERE has_media = 1")
                    for (media_path,) in cursor.fetchall():
                        if media_path and Path(media_path).exists():
                            total_size += Path(media_path).stat().st_size
                        else:
                            missing_files += 1
                    
                    print(f"\nTotal size: {total_size / (1024*1024):.2f} MB")
                    print(f"Missing files: {missing_files}")
                
                elif choice == "3":
                    # Clean up missing files
                    cursor.execute("SELECT id, media_path FROM processed_messages WHERE has_media = 1")
                    missing_count = 0
                    
                    for db_id, media_path in cursor.fetchall():
                        if media_path and not Path(media_path).exists():
                            cursor.execute("UPDATE processed_messages SET media_path = NULL WHERE id = ?", (db_id,))
                            missing_count += 1
                    
                    conn.commit()
                    print(f"Cleaned up {missing_count} missing media references.")
                
                elif choice == "4":
                    # Export media list
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    export_file = f"media_list_{timestamp}.txt"
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        f.write("Media Files Export\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for db_id, mapping_id, msg_id, original, processed, media_type, media_path, date, posted in media_messages:
                            f.write(f"ID: {db_id} | Message: {msg_id} | Mapping: {mapping_id}\n")
                            f.write(f"Date: {date} | Posted: {posted}\n")
                            f.write(f"Media: {media_type} | Path: {media_path}\n")
                            f.write(f"Text: {original}\n")
                            f.write("-" * 50 + "\n")
                    
                    print(f"Media list exported to: {export_file}")
        
        except Exception as e:
            logging.error(f"Error viewing media messages: {e}")
            print("Error viewing media messages.")

    def _open_media_file(self, file_path: str) -> None:
        """Open media file with system default application."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(['start', '', file_path], shell=True, check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', file_path], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=True)
            
            print("Media file opened successfully.")
            
        except subprocess.CalledProcessError:
            print("Could not open media file with system default application.")
        except Exception as e:
            print(f"Error opening media file: {e}")

