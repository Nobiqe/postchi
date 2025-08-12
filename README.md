# Telegram Multi-Channel Processor

A powerful Python application that automatically processes and forwards messages between Telegram channels using AI text processing. The system monitors source channels, processes messages with AI providers (Gemini, OpenAI, OpenRouter), and forwards them to target channels with flexible processing modes.

## Features

### 🤖 AI-Powered Message Processing
- **Multiple AI Providers**: Support for Google Gemini, OpenAI, and OpenRouter
- **Flexible AI Processing**: Choose to enable/disable AI text processing per session
- **Custom Prompts**: Configure custom AI system prompts for text rewriting
- **Smart Filtering**: Only processes messages matching specific keywords and signatures

### 📱 Multi-Channel Management
- **Channel Mapping**: Configure multiple source-to-target channel pairs
- **18 Different Processing Modes**: Combinations of historical/real-time, AI on/off, and footer options
- **Real-time Monitoring**: Immediate forwarding of new messages (no scheduling delays)
- **Historical Processing**: Process messages from the last 7 days on startup

### 📝 Flexible Footer System
- **Saved Footers**: Create and manage reusable footer templates
- **Custom Footers**: Create new footers using system text editor
- **No Footer Option**: Forward messages without any additional content
- **Footer Preview**: Preview and manage saved footers before use

### 🗄️ Database Management
- **SQLite Database**: Stores processed messages, channel information, and processing history
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
- AI API key (Gemini, OpenAI, or OpenRouter) - Optional if not using AI processing

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
pip install telethon google-generativeai requests
```

3. **Get Telegram API credentials**
   - Visit https://my.telegram.org/apps
   - Create a new application
   - Note down your `api_id` and `api_hash`

4. **Get AI API key** (Optional - only if using AI processing)
   - **Gemini**: Get from Google AI Studio
   - **OpenAI**: Get from OpenAI platform
   - **OpenRouter**: Get from OpenRouter.ai

5. **Run the application**
```bash
python main.py
```

## 18 Processing Modes

The application offers 18 different processing modes based on combinations of:

### Processing Type:
- **Historical Only**: Process messages from last 7 days
- **Real-time Only**: Monitor for new messages continuously
- **Both**: Process historical + real-time monitoring

### AI Processing:
- **AI Enabled**: Use AI to rewrite/process text
- **AI Disabled**: Forward original messages without AI processing

### Footer Options:
- **Saved Footers**: Use pre-saved footer templates
- **Custom Footers**: Create new footer on-the-fly
- **No Footer**: Forward without additional content

### Mode Examples:
- **Mode 1**: Historical + AI Enabled + Saved Footer
- **Mode 7**: Real-time + AI Enabled + Saved Footer
- **Mode 13**: Both + AI Enabled + Saved Footer
- **Mode 6**: Historical + AI Disabled + No Footer
- **Mode 18**: Both + AI Disabled + No Footer

## Configuration

### First Run Setup

1. **Configure Telegram Settings**
   - Enter your API ID and API Hash
   - Provide your phone number
   - Complete authentication process

2. **Configure AI Settings** (Optional)
   - Select your AI provider (Gemini/OpenAI/OpenRouter)
   - Enter your API key
   - Choose the model to use
   - Test the connection

3. **Set Up Channel Mappings**
   - List all available chats/channels
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
  ],
  "saved_footers": [
    {
      "name": "Default Footer",
      "content": "Your custom footer content here",
      "created_at": "2024-01-01T00:00:00"
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
5. **Start Processing** - Begin monitoring and processing with mode selection
6. **View Database Status** - Check processing statistics
7. **Exit** - Close the application

### Processing Flow

When you start processing, the system will:

1. **Ask about AI Processing**: Enable/disable AI text processing
2. **Configure AI Prompt** (if enabled): Set custom system prompt for text rewriting
3. **Configure Footer**: Choose saved footer, create custom, or use no footer
4. **Select Processing Type**: Historical, real-time, or both
5. **Display Current Mode**: Shows which of the 18 modes is running

### Message Processing Flow

1. **Monitor** source channels for new messages (real-time mode)
2. **Filter** messages based on keywords and signatures  
3. **Process** with AI (if enabled) to rewrite text
4. **Add Footer** (if configured)
5. **Store** processed messages in database
6. **Forward Immediately** to target channels (no scheduling delays)

## AI Processing

### Configurable System Prompts

Instead of fixed templates, users can set custom system prompts like:
- "Rewrite this text to be more professional"
- "Translate to formal Persian and add trading insights" 
- "Summarize the key points in bullet format"

### AI Processing Options

- **Skip AI Processing**: Forward original messages unchanged
- **Custom Prompts**: Set different prompts per session
- **Multiple Providers**: Switch between Gemini, OpenAI, OpenRouter

## Footer Management

### Saved Footers
- Create reusable footer templates
- Preview before selection
- Date-based organization
- Edit and delete options

### Custom Footers  
- Opens system text editor (notepad, nano, etc.)
- Supports Telegram formatting
- Auto-saves for future use
- Instant preview

### Footer Options
- **Telegram Formatting**: Bold, italic, links, hashtags
- **Multi-line Support**: Complex footer layouts
- **Link Integration**: Social media, websites, registration links
- **Hashtag Support**: Automatic hashtag inclusion

## Database Schema

### Tables

- **processed_messages**: Stores all processed messages with status tracking
- **posting_schedule**: Manages posting intervals for each mapping (legacy)  
- **channels**: Stores channel information and metadata

### Key Features

- **Duplicate Prevention**: Unique constraints prevent reprocessing
- **Immediate Forwarding**: No scheduling delays, instant message forwarding
- **Status Tracking**: Tracks forwarded/pending status
- **Statistics**: Provides detailed processing statistics

## Real-time Monitoring

### Immediate Forwarding
- Messages are forwarded immediately upon detection
- No artificial delays or scheduling
- Continuous monitoring every 5 seconds
- Live status updates

### Monitoring Controls
- Press `5` + Enter to stop and return to menu
- Ctrl+C for emergency stop
- Live processing feedback
- Mode information display

## Error Handling

### Robust Error Management
- **Flood Control**: Handles Telegram rate limiting
- **Connection Recovery**: Automatic reconnection on failures
- **Graceful Degradation**: Continues processing even if individual operations fail
- **Detailed Logging**: Comprehensive logging for debugging

### Common Issues

1. **Authentication Errors**: Check API credentials and phone number format
2. **Channel Access**: Ensure account has access to both source and target channels
3. **AI API Errors**: Verify API key and model availability (only if using AI)
4. **Rate Limiting**: System automatically handles Telegram flood controls

## File Structure

```
telegram-multi-channel-processor/
├── main.py                 # Application entry point
├── menu.py                # Interactive menu system with 18 modes
├── main_processor.py      # Core processing logic with immediate forwarding
├── telegram_client.py     # Telegram API wrapper
├── ai_processor.py        # AI processing with multiple providers
├── config.py              # Configuration management with footer support
├── database.py            # Database operations
├── config.json            # Configuration file (auto-generated)
├── telegram_messages.db   # SQLite database (auto-generated)
├── telegram_processor.log # Application log file
└── session_files/         # Telegram session files
```

## Key Changes from Original

### Processing Improvements
- **18 Mode System**: Flexible combinations of processing options
- **Immediate Forwarding**: No scheduling delays, instant message forwarding  
- **AI Optional**: Can run without AI processing for simple forwarding
- **Session-based Configuration**: Different settings per processing session

### Footer System
- **Saved Footer Management**: Create, edit, delete reusable footers
- **Custom Footer Creation**: Use system editor for complex footers
- **No Default Footers**: No hardcoded company-specific content
- **Preview System**: See footer before applying

### User Experience  
- **No Hardcoded Defaults**: Users must configure their own content
- **Live Monitoring**: Real-time feedback during processing
- **Flexible Configuration**: Each session can have different settings
- **Better Error Handling**: More informative error messages

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
- Configure your own content - no default company information included

## Support

If you encounter any issues or have questions:

1. Check the application logs in `telegram_processor.log`
2. Review the database status in the menu
3. Verify your configuration settings
4. Ensure proper channel access permissions
5. Open an issue on GitHub with detailed information
