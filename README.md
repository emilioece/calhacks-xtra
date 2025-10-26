# Quit Trigger Filter - MVP

A Chrome extension and LiveKit-powered vision agent for helping people in addiction recovery by filtering trigger content from TikTok and other short-form video platforms.

## Architecture

### Components

1. **Chrome Extension** (`extension/`)
   - Captures video frames from TikTok at 1-2 fps
   - Sends frames to ingestion service via background worker
   - Configurable capture rate and quality

2. **Ingestion Service** (`src/agent.py`)
   - FastAPI endpoint that receives frames
   - Integrated with LiveKit Agents for vision analysis
   - LLM-powered trigger detection

3. **Vision Agent** (in `src/agent.py`)
   - Processes frames through LLM vision model
   - Detects triggers from configurable list
   - Returns trigger detection results

## Setup

### Prerequisites

- Python 3.10+
- uv package manager (or use venv directly)
- Chrome browser
- OpenAI API key (for vision model)

### Installation

1. Install Python dependencies:
```bash
.\venv\Scripts\uv.exe sync
```

Or if you have uv in PATH:
```bash
uv sync
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Add your credentials to `.env`:
```env
# For LiveKit Cloud (optional for MVP)
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI API key (required for vision model)
OPENAI_API_KEY=your-openai-key

# Server config
INGEST_PORT=8000
ALLOWED_ORIGINS=*
```

4. Load Chrome Extension:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `extension/` directory

5. Configure extension:
   - Click the extension icon → Options
   - Set endpoint URL: `http://localhost:8000/ingest/frame`
   - Adjust capture interval (500ms = 2 fps)
   - Click "Save"

6. Start the server:
```bash
.\venv\Scripts\python.exe -m uvicorn src.agent:app --reload --port 8000
```

## Usage

1. Open TikTok in Chrome
2. Navigate to your feed
3. The extension automatically captures frames
4. Check the server logs for frame processing

## Testing

Run tests:
```bash
.\venv\Scripts\pytest.exe
```

Or:
```bash
.\venv\Scripts\uv.exe run pytest
```

## Current Status

✅ **Milestone 1: Frame Capture**
- Chrome extension captures TikTok frames
- Background worker forwards to FastAPI endpoint
- Endpoint validates and accepts frames

🔄 **Milestone 2: Vision Processing (In Progress)**
- Vision agent function implemented
- Uses LiveKit `ImageContent` with LLM vision
- Configurable trigger detection
- Currently commented out for MVP testing

## Trigger Detection

The system detects these triggers by default:
- Smoking
- Cigarettes
- Vaping
- Alcohol
- Drinking
- Drug paraphernalia
- Weapons
- Violence
- Harmful substances
- Inappropriate content

## Development

### Project Structure

```
├── extension/          # Chrome extension
│   ├── manifest.json   # MV3 manifest
│   ├── content.js      # Frame capture logic
│   ├── background.js   # Frame forwarding
│   └── options.html    # Configuration UI
├── src/
│   ├── agent.py        # FastAPI + LiveKit agent
│   └── config.py       # Configuration
├── tests/
│   └── test_ingest.py  # Unit tests
└── pyproject.toml      # Python dependencies
```

### Code Formatting

```bash
.\venv\Scripts\uv.exe run ruff format
.\venv\Scripts\uv.exe run ruff check
```

## Next Steps

1. Enable vision processing in production endpoint
2. Implement TikTok-specific actions (MCP handler)
3. Add Redis for action queue (if needed)
4. Deploy to production
5. Expand to Instagram Reels and YouTube Shorts

## License

MIT

## Acknowledgments

Built with:
- [LiveKit Agents](https://docs.livekit.io/agents/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pillow](https://pillow.readthedocs.io/)
- Chrome Extensions API
