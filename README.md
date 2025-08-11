# Telegram Multi-Channel Processor

A powerful Python application that automatically processes and forwards messages between Telegram channels using AI text processing. The system monitors source channels, processes messages with AI providers (Gemini, OpenAI, OpenRouter), and schedules posts to target channels.

## Features

### 🤖 AI-Powered Message Processing
- **Multiple AI Providers**: Support for Google Gemini, OpenAI, and OpenRouter
- **Automatic Text Processing**: Converts messages to formal Persian text suitable for Telegram channels
- **Custom Prompts**: Configure custom processing templates for each channel mapping
- **Smart Filtering**: Only processes messages matching specific keywords and signatures

### 📱 Multi-Channel Management
- **Channel Mapping**: Configure multiple source-to-target channel pairs
- **Real-time Monitoring**: Continuous monitoring of source channels for new messages
- **Historical Processing**: Process messages from the last 7 days on startup
- **Scheduled Posting**: Automatic posting with configurable intervals (default: 12 hours)

### 🗄️ Database Management
- **SQLite Database**: Stores processed messages, channel information, and posting schedules
- **Duplicate Prevention**: Prevents reprocessing of already handled messages
- **Status Tracking**: Tracks posted/unposted messages for each mapping
- **Statistics**: View processing statistics and recent activity

### 🎯 Smart Content Filtering
- **Keyword Matching**: Filter messages based on specified keywords
- **Signature Detection**: Only process messages containing required signatures
- **Content Validation**: Ensures messages meet criteria before processing

## Installation

### Prerequisites
- Python 3.7 or higher
- Telegram API credentials (API ID and API Hash)
- AI API key (Gemini, OpenAI, or OpenRouter)

### Required Packages
```bash
pip install telethon google-generativeai requests
```

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-multi-channel-processor.git
cd telegram-multi-channel-processor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Get Telegram API credentials**
   - Visit https://my.telegram.org/apps
   - Create a new application
   - Note down your `api_id` and `api_hash`

4. **Get AI API key**
   - **Gemini**: Get from Google AI Studio
   - **OpenAI**: Get from OpenAI platform
   - **OpenRouter**: Get from OpenRouter.ai

5. **Run the application**
```bash
python main.py
```

## Configuration

### First Run Setup

1. **Configure Telegram Settings**
   - Enter your API ID and API Hash
   - Provide your phone number
   - Complete authentication process

2. **Configure AI Settings**
   - Select your AI provider (Gemini/OpenAI/OpenRouter)
   - Enter your API key
   - Choose the model to use
   - Test the connection

3. **Set Up Channel Mappings**
   - Add source and target channels
   - Configure keywords and signatures
   - Set custom processing templates (optional)

### Configuration Files

The application creates a `config.json` file with your settings:

```json
{
  "telegram": {
    "api_id": "your_api_id",
    "api_hash": "your_api_hash",
    "phone_number": "your_phone"
  },
  "ai": {
    "api_key": "your_api_key",
    "model": "gemini-pro",
    "provider": "gemini",
    "base_url": ""
  },
  "channel_mappings": [
    {
      "id": "mapping_1",
      "source_channel_id": -1001234567890,
      "source_channel_name": "Source Channel",
      "target_channel_id": -1001234567891,
      "target_channel_name": "Target Channel",
      "keywords": ["keyword1", "keyword2"],
      "signature": "@YourSignature",
      "active": true
    }
  ]
}
```

## Usage

### Interactive Menu System

The application provides an interactive menu with the following options:

1. **Configure Telegram Settings** - Set up API credentials
2. **Configure AI Settings** - Configure AI provider and test connection
3. **Manage Channel Mappings** - Add, edit, delete channel mappings
4. **List All Chats** - View available channels and groups
5. **Start Processing** - Begin monitoring and processing
6. **View Database Status** - Check processing statistics
7. **Exit** - Close the application

### Processing Options

When starting processing, you can choose:
- **Historical Processing**: Process messages from the last 7 days
- **Real-time Monitoring**: Monitor for new messages continuously  
- **Both**: Recommended for first run

### Message Processing Flow

1. **Monitor** source channels for new messages
2. **Filter** messages based on keywords and signatures
3. **Process** with AI to convert to formal Persian text
4. **Store** processed messages in database
5. **Schedule** posting based on configured intervals
6. **Post** messages to target channels automatically

## AI Processing

### Default Prompt Template

The system uses this template for processing messages:

```
لطفاً متن زیر را به صورت رسمی و حرفه‌ای در زبان فارسی بازنویسی کنید. متن باید واضح، دقیق و مناسب برای انتشار در کانال تلگرام باشد:

متن اصلی: {original_text}

لطفاً فقط متن بازنویسی شده را ارائه دهید.
```

### Automatic Footer Addition

All processed messages automatically include:
- Hashtags: #Fundamental #AskBid #اسک_بید
- Links to registration, website, social media
- Academy and YouTube links

## Database Schema

### Tables

- **processed_messages**: Stores all processed messages with status tracking
- **posting_schedule**: Manages posting intervals for each mapping
- **channels**: Stores channel information and metadata

### Key Features

- **Duplicate Prevention**: Unique constraints prevent reprocessing
- **Status Tracking**: Tracks posted/unposted status
- **Scheduling**: Manages posting intervals and timing
- **Statistics**: Provides detailed processing statistics

## Error Handling

### Robust Error Management
- **Flood Control**: Handles Telegram rate limiting
- **Connection Recovery**: Automatic reconnection on failures  
- **Graceful Degradation**: Continues processing even if individual operations fail
- **Detailed Logging**: Comprehensive logging for debugging

### Common Issues

1. **Authentication Errors**: Check API credentials and phone number format
2. **Channel Access**: Ensure bot has access to both source and target channels
3. **AI API Errors**: Verify API key and model availability
4. **Rate Limiting**: System automatically handles Telegram flood controls

## File Structure

```
telegram-multi-channel-processor/
├── main.py                 # Application entry point
├── menu.py                # Interactive menu system
├── main_processor.py      # Core processing logic
├── telegram_client.py     # Telegram API wrapper
├── ai_processor.py        # AI processing with multiple providers
├── config.py              # Configuration management
├── database.py            # Database operations
├── config.json            # Configuration file (auto-generated)
├── telegram_messages.db   # SQLite database (auto-generated)
├── telegram_processor.log # Application log file
└── session_files/         # Telegram session files
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

- This tool is for educational and legitimate business purposes only
- Ensure compliance with Telegram's Terms of Service
- Respect channel privacy and permissions
- Use responsibly and ethically

## Support

If you encounter any issues or have questions:

1. Check the application logs in `telegram_processor.log`
2. Review the database status in the menu
3. Verify your configuration settings
4. Open an issue on GitHub with detailed information

## Changelog

### Version 1.0.0
- Initial release with multi-channel support
- AI processing with Gemini, OpenAI, and OpenRouter
- Interactive menu system
- Database management and statistics
- Automated scheduling and posting