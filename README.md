# Auto-Typer

A lightweight, global hotkey text typer for Windows. Paste your text, press F9, and watch it type itself out automatically. Perfect for repetitive text entry, form filling, or just showing off.

## Features

- 🚀 **Global Hotkeys** - Press F9 anywhere to start typing, F11 to stop
- 📋 **Clipboard Auto-Load** - Automatically grabs your clipboard content on startup
- 🖥️ **System Tray** - Minimizes to tray with quick actions
- 🖱️ **Mouse Click Stop** - Click anywhere to instantly stop typing
- ⚡ **Customizable Speed** - Adjust typing speed from 1ms to 1000ms per character
- 🔄 **Auto-Close Option** - Automatically closes after typing completes

## Installation

### Option 1: Download the EXE (Recommended)

1. Go to the [Releases](https://github.com/Lemalemo3/autotypeplus/releases) page
2. Download `autotypeplus.exe`
3. Run it - no installation required!

### Option 2: Run from Source

```bash
# Clone the repository
git clone https://github.com/Lemalemo3/autotypeplus.git
cd autotypeplus

# Install dependencies
pip install PyQt5 pynput

# Run the app
python autotypeplus.py
```

## Usage

1. **Copy** some text to your clipboard (Ctrl+C)
2. **Open** Auto-Typer - your clipboard content is automatically loaded
3. **Click** into the target window (Notepad, browser, form, etc.)
4. **Press F9** to start typing
5. **Press F11** or **click anywhere** to stop

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F9` | Start typing |
| `F11` | Stop typing |

## System Tray

When you close the window, Auto-Typer minimizes to the system tray. Right-click the tray icon for quick actions:

- Show Window
- Start Typing
- Stop Typing
- Quit

## Building from Source

To compile the EXE yourself:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=favicon.png --add-data "favicon.png;." autotypeplus.py
```

## Requirements

- Windows 10/11
- Python 3.7+ (for source installation)
- No additional dependencies for the EXE version

## License

MIT License - Free to use, modify, and distribute. See [LICENSE](LICENSE) for details.

## Contributing

Feel free to open issues or submit pull requests. All contributions welcome!
