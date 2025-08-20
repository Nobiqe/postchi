# gui_launcher.py
"""
GUI Launcher and Integration Script
Replaces the command-line main.py with a modern GUI interface
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        "telethon",
        "google-generativeai",
        "sqlite3",
        "tkinter"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "tkinter":
                import tkinter
            elif package == "telethon":
                import telethon
            elif package == "google-generativeai":
                import google.generativeai
            elif package == "sqlite3":
                import sqlite3
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages and try again.")
        return False
    
    return True

def setup_environment():
    """Setup environment for GUI application"""
    # Create necessary directories
    directories = ["media", "logs", "backups"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Setup logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/telegram_gui.log'),
            logging.StreamHandler()
        ]
    )
    
    return True

def main():
    """Main entry point"""
    print("Telegram Multi-Channel Processor GUI")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    # Setup environment
    if not setup_environment():
        print("Failed to setup environment")
        input("Press Enter to exit...")
        return
    
    try:
        # Import and start GUI
        from gui_telegram_bot import ModernTelegramBotGUI
        
        print("Starting GUI application...")
        app = ModernTelegramBotGUI()
        app.run()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure gui_telegram_bot.py is in the same directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()