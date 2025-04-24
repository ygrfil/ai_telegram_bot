# AI Telegram Bot

A customizable Telegram bot that integrates with multiple AI providers, allowing users to chat with different AI models, generate images, and more.

## Features

- 🤖 Multiple AI model support (Anthropic Claude, OpenAI, Google Gemini, Perplexity)
- 🎨 Image generation capabilities
- 📊 Usage statistics and tracking
- 🔒 User access control
- 📱 Responsive and intuitive interface
- 📡 Web search capabilities

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ai_telegram_bot.git
   cd ai_telegram_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your own API keys and settings:
   - Get a Telegram Bot token from [BotFather](https://t.me/botfather)
   - Add your Telegram user ID as ADMIN_ID and in ALLOWED_USER_IDS
   - Add your API keys for OpenRouter, Fal.ai, and Google Gemini

## Usage

1. Start the bot:
   ```bash
   python -m bot
   ```

2. Start a chat with your bot on Telegram

3. Use the menu buttons to:
   - Switch between AI models
   - Generate images
   - Clear conversation history
   - Access admin features (if you're an admin)

## AI Provider Setup

### OpenRouter
Sign up at [OpenRouter](https://openrouter.ai/) to get API access to multiple AI models including OpenAI, Anthropic Claude, and more.

### Google Gemini
Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### Fal.ai
Sign up at [Fal.ai](https://fal.ai/) to get an API key for image generation.

## Adding New Providers

To add a new AI provider:

1. Create a new file in `bot/services/ai_providers/` that implements the `BaseAIProvider` interface
2. Update `providers.py` to include your new model configuration
3. Register your provider in `__init__.py`'s `get_provider` function

## Environment Variables

| Variable | Description |
|----------|-------------|
| BOT_TOKEN | Telegram Bot API token |
| ADMIN_ID | Telegram user ID for admin access |
| ALLOWED_USER_IDS | Comma-separated list of allowed user IDs |
| OPENROUTER_API_KEY | API key for OpenRouter |
| FAL_API_KEY | API key for Fal.ai image generation |
| GEMINI_API_KEY | API key for Google Gemini |
| MAX_TOKENS | Maximum tokens for AI responses (default: 4096) |

## License

MIT