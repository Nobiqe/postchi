import asyncio
from menu import MenuSystem


async def main():
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