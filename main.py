import asyncio
from menu import MenuSystem
import os
import sys


async def main():

    """session_files = [f for f in os.listdir('.') if f.startswith('session_') and f.endswith('.session')]
    if session_files:
        print("Found existing session files. Cleaning up...")
        for session_file in session_files:
            try:
                os.remove(session_file)
                print(f"Removed {session_file}")
            except:
                pass"""
            
    """ Main entry point of the application """
    menu = MenuSystem()
    await menu.run()


if __name__ == "__main__":
    
    required_packages = [
        "telethon",
        "google_generativeai",
        "asynico",
        "sqlite3"
    ]    

    try:
        import telethon
        import google.generativeai
        print("starting telegram multi-channel processor...\n")

        asyncio.run(main())

    except ImportError as e :
        print(f"missing required package: {e}")