# Bingody Music Agent

A Minecraft/Voxel-styled CLI music agent with a pet companion named Bingody.

## Features

- **Voxel Art TUI** - Pixel-style terminal interface with ASCII Bingody mascot
- **Multi-state Pet** - Bingody responds with different expressions: idle, playing, searching, error, chill
- **Music Playback** - Search and play music from NetEase Cloud Music
- **Interactive Commands** - Rich command system with `/bingo` prefix
- **Music Agent** - AI-powered conversational music assistant

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml with your API keys

# Run
python -m cli
```

## Commands

| Command | Description |
|---------|-------------|
| `/bingo play <song>` | Play a song |
| `/bingo search <keyword>` | Search for songs |
| `/bingo feed` | Feed Bingody (increases affinity) |
| `/bingo mood` | Switch mood mode |
| `/bingo queue` | Show play queue |

## Keyboard Shortcuts

- `Space` - Play/Pause
- `N` / `P` - Next/Previous track
- `F` - Feed Bingody
- `Q` - Quit

## Design

- **Gold** `#d8b83a` - Bingody body, accents
- **Cyan** `#2ad2d2` - Highlights, commands
- **Deep Slate** `#0f172a` - Background

## License

MIT