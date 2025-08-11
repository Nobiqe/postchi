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













