# Telegram Multi-Channel Processor

A powerful Python application that automatically processes and forwards messages between Telegram channels using AI text processing. The system monitors source channels, processes messages with AI providers (Gemini, OpenAI, OpenRouter), and forwards them to target channels with smart content optimization.

## Features

### 🤖 AI-Powered Message Processing
- **Always-On AI Agent**: Automatically summarizes captions to 600-800 characters for Telegram limits
- **Smart Processing**: Captions always processed; regular text messages optionally processed
- **Multiple AI Providers**: Support for Google Gemini, OpenAI, and OpenRouter
- **Intelligent Length Management**: Prevents Telegram caption limit issues (1024 chars)
- **Custom Prompts**: Configure custom AI system prompts for text rewriting

### 📱 Multi-Channel Management
- **Channel Mapping**: Configure multiple source-to-target channel pairs
- **36 Different Processing Modes**: Combinations of historical/real-time, media handling, AI scope, and footer options
- **Real-time Monitoring**: Immediate forwarding of new messages (no scheduling delays)
- **Historical Processing**: Process messages from the last 7 days on startup
- **Media Support**: Download and forward images, videos, documents with captions

### 🏷️ Flexible Footer System
- **Saved Footers**: Create and manage reusable footer templates
- **Custom Footers**: Create new footers using system text editor
- **No Footer Option**: Forward messages without any additional content
- **Footer Preview**: Preview and manage saved footers before use

### 🗄️ Database Management
- **SQLite Database**: Stores processed messages, channel information, and processing history
- **Media Tracking**: Tracks downloaded media files and paths
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
- AI API key (Gemini, OpenAI, or OpenRouter) - **Required for caption processing**

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

4. **Get AI API key** (Required for caption processing)
   - **Gemini**: Get from Google AI Studio
   - **OpenAI**: Get from OpenAI platform
   - **OpenRouter**: Get from OpenRouter.ai

5. **Run the application**
```bash
python main.py
```

## AI Processing Logic

### Always-On AI Agent
The AI agent is now **always active** with smart processing rules:

#### Captions (Media Messages)
- **Always processed** by AI to ensure Telegram compatibility
- Summarized to 600-800 characters to prevent truncation
- Aggressive summarization if content exceeds limits

#### Regular Text Messages
- **User choice**: Apply AI processing or send unchanged
- Only processed if user opts for "Apply AI to all messages"
- Original text preserved when AI processing is disabled

#### Processing Flow
```
Message → Has Media? 
    ├─ Yes (Caption) → Always AI Process → Summarize to 600-800 chars
    └─ No (Text) → User Choice?
        ├─ Apply to All → AI Process
        └─ Captions Only → Send Original
```

## 36 Processing Modes

The application offers 36 different processing modes based on combinations of:

### Processing Type (3 options):
- **Historical Only**: Process messages from last 7 days
- **Real-time Only**: Monitor for new messages continuously
- **Both**: Process historical + real-time monitoring

### Media Handling (2 options):
- **Media Enabled**: Download and forward media files
- **Media Disabled**: Forward text only

### AI Scope (2 options):
- **Captions Only**: AI processes only media captions (default behavior)
- **All Messages**: AI processes both captions and regular text messages

### Footer Options (3 options):
- **Saved Footers**: Use pre-saved footer templates
- **Custom Footers**: Create new footer on-the-fly
- **No Footer**: Forward without additional content

### Mode Examples:
- **Mode 1**: Historical + Media + Captions Only + Saved Footer
- **Mode 13**: Real-time + Media + All Messages + Saved Footer
- **Mode 25**: Both + No Media + Captions Only + Saved Footer
- **Mode 36**: Both + No Media + All Messages + No Footer

## Configuration

### First Run Setup

1. **Configure Telegram Settings**
   - Enter your API ID and API Hash
   - Provide your phone number
   - Complete authentication process

2. **Configure AI Settings** (**Required**)
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
6. **View Database Status** - Check processing statistics and media files
7. **Exit** - Close the application

### Processing Flow

When you start processing, the system will:

1. **Media Configuration**: Enable/disable media download and forwarding
2. **AI Scope Selection**: Choose whether to apply AI to all messages or captions only
3. **Configure Footer**: Choose saved footer, create custom, or use no footer
4. **Select Processing Type**: Historical, real-time, or both
5. **Display Current Mode**: Shows which of the 36 modes is running

### Message Processing Flow

1. **Monitor** source channels for new messages (real-time mode)
2. **Filter** messages based on keywords and signatures  
3. **Smart AI Processing**:
   - Captions: Always processed and summarized (600-800 chars)
   - Regular text: Processed only if user selected "Apply to All"
4. **Media Handling** (if enabled): Download and prepare media files
5. **Add Footer** (if configured)
6. **Store** processed messages in database with media info
7. **Forward Immediately** to target channels with media attachments

## AI Processing Features

### Automatic Caption Optimization
- **Length Management**: Ensures captions fit Telegram's 1024 character limit
- **Smart Summarization**: Preserves key information while reducing length
- **Aggressive Fallback**: Additional summarization if content still too long
- **Quality Preservation**: Maintains message meaning and important details

### Configurable System Prompts
Users can set custom system prompts like:
- "Rewrite this text to be more professional"
- "Translate to formal Persian and add trading insights" 
- "Summarize the key points maintaining crypto focus"

### AI Processing Options
- **Smart Processing**: Automatic AI application based on content type
- **Custom Prompts**: Set different prompts per session
- **Multiple Providers**: Switch between Gemini, OpenAI, OpenRouter
- **Fallback System**: Uses original text if AI processing fails

## Media Support

### Supported Media Types
- **Images**: JPG, PNG, GIF
- **Videos**: MP4, WebM
- **Audio**: MP3, voice messages
- **Documents**: All file types supported by Telegram

### Media Processing
- **Automatic Download**: Downloads media to local storage
- **Path Tracking**: Stores media file paths in database
- **Caption Processing**: Always processes media captions with AI
- **Single Post Format**: Combines media with processed caption

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

- **processed_messages**: Stores all processed messages with media info and status tracking
- **posting_schedule**: Manages posting intervals for each mapping (legacy)  
- **channels**: Stores channel information and metadata

### Media Support Features

- **Media Tracking**: Stores media file paths, types, and IDs
- **File Management**: Tracks downloaded files and cleanup
- **Media Statistics**: Shows media usage and storage info
- **Missing File Detection**: Identifies and cleans up missing media references

### Key Features

- **Duplicate Prevention**: Unique constraints prevent reprocessing
- **Immediate Forwarding**: No scheduling delays, instant message forwarding
- **Status Tracking**: Tracks forwarded/pending status
- **Statistics**: Provides detailed processing and media statistics

## Real-time Monitoring

### Immediate Forwarding
- Messages are forwarded immediately upon detection
- No artificial delays or scheduling
- Continuous monitoring every 5 seconds
- Live status updates with processing details

### Monitoring Controls
- Press `5` + Enter to stop and return to menu
- Ctrl+C for emergency stop
- Live processing feedback
- Mode information display
- Media download progress

## Error Handling

### Robust Error Management
- **Flood Control**: Handles Telegram rate limiting
- **Connection Recovery**: Automatic reconnection on failures
- **AI Fallback**: Uses original text if AI processing fails
- **Media Error Handling**: Continues processing if media download fails
- **Graceful Degradation**: Continues processing even if individual operations fail
- **Detailed Logging**: Comprehensive logging for debugging

### Common Issues

1. **Authentication Errors**: Check API credentials and phone number format
2. **Channel Access**: Ensure account has access to both source and target channels
3. **AI API Errors**: Verify API key and model availability (**Required** for captions)
4. **Rate Limiting**: System automatically handles Telegram flood controls
5. **Media Issues**: Check storage space and file permissions

## File Structure

```
telegram-multi-channel-processor/
├── main.py                 # Application entry point
├── menu.py                # Interactive menu system with 36 modes
├── main_processor.py      # Core processing logic with smart AI handling
├── telegram_client.py     # Telegram API wrapper with media support
├── ai_processor.py        # AI processing with smart caption optimization
├── config.py              # Configuration management with footer support
├── database.py            # Database operations with media tracking
├── config.json            # Configuration file (auto-generated)
├── telegram_messages.db   # SQLite database (auto-generated)
├── telegram_processor.log # Application log file
├── media/                 # Downloaded media files directory
└── session_files/         # Telegram session files
```

## Key Changes from Original

### AI Processing Revolution
- **Always-On AI**: AI agent always active for caption optimization
- **Smart Scope Control**: User controls AI application to regular messages
- **Caption Optimization**: Automatic summarization to prevent Telegram truncation
- **36 Mode System**: Enhanced from 18 to 36 modes with AI scope options

### Enhanced Media Support
- **Full Media Pipeline**: Download, store, and forward all media types
- **Media Database**: Complete tracking of media files and metadata
- **Caption-Media Sync**: Processed captions properly paired with media
- **Storage Management**: Media file organization and cleanup tools

### Processing Improvements
- **Smart Processing Logic**: Different rules for captions vs regular text
- **Immediate Forwarding**: No scheduling delays, instant message forwarding  
- **Length Management**: Intelligent handling of Telegram character limits
- **Session-based Configuration**: Different settings per processing session

### User Experience  
- **Clear AI Scope**: Users understand exactly what gets processed
- **Live Monitoring**: Real-time feedback during processing with processing details
- **Media Progress**: Shows media download and processing status
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
- AI processing is required for proper caption handling
- Configure your own content - no default company information included

## Support

If you encounter any issues or have questions:

1. Check the application logs in `telegram_processor.log`
2. Review the database status and media files in the menu
3. Verify your AI configuration (required for captions)
4. Ensure proper channel access permissions
5. Check media storage space and permissions
6. Open an issue on GitHub with detailed information