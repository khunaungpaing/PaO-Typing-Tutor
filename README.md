# Pa-O Typing Tutor

[![Latest Release](https://img.shields.io/github/v/release/khunaungpaing/PaO-Typing-Tutor?include_prereleases&color=6d5ce7&label=Release)](https://github.com/khunaungpaing/PaO-Typing-Tutor/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-4ade80.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-38bdf8.svg)](#download--install)
[![Python Version](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)

> **⚠️ IMPORTANT**: This application is specifically designed for the **Pa-O Kham Dom Experimental Version** (`ပအိုဝ်းခမ်းဒွမ် စမ်းသပ်ဗားရှင်း`) keyboard layout and typography.

**Pa-O Typing Tutor** is a modern, cross-platform desktop application designed to help users learn, practice, and master touch typing in the Pa-O language using the **Pa-O Kham Dom Experimental** keyboard layout. Built with Python and PyQt6, it provides an interactive virtual on-screen keyboard, real-time typing metrics, audio feedback, structured lessons, and custom lesson management.

---

## ✨ Features

- **Pa-O Kham Dom Experimental Layout**: Specially tailored keyboard mapping and typing rules built exclusively for the Kham Dom Experimental layout.
- **Virtual On-Screen Keyboard**: Responsive, flexible keyboard layout that scales cleanly across small and widescreen displays, featuring live target key highlights, active pressed keys, and Shift state synchronization.
- **Native Pa-O Font Display**: Bundles `KhamThaton-Exp` (`KhamThaton-Exp-Regular`), rendering authentic Pa-O Kham Dom glyphs and complex ligatures natively by default.
- **28 Structured Lessons**: Built-in lesson catalog covering basic vowels, consonants, tone marks, vocabulary, and full practice sentences.
- **Live Typing Performance Metrics**: Real-time Words Per Minute (WPM), Accuracy percentage, Character count, and session duration.
- **Custom Lesson Manager**: Create, edit, and organize personal practice materials, with easy import of custom lessons from UTF-8 JSON and CSV files.
- **In-App Auto-Updates**: One-click check for updates with in-app background downloader and platform installer launch directly through GitHub Releases.
- **Localized Interface**: Full user interface localization in **Pa'O** (ပအိုဝ်း), **Burmese** (မြန်မာ), and **English**.
- **Audio Feedback**: Pleasant auditory cues for keystrokes, errors, and lesson completion, with synthesized tone fallbacks.
- **Modern Dark Theme**: Eye-friendly, accessible dark aesthetic designed for comfortable, extended practice sessions.
- **100% Offline & Private**: Operates entirely offline with zero telemetry, analytics, or background data collection.

---

## 📦 Download & Install

Pre-compiled binary packages are available for macOS and Windows on the [Releases page](https://github.com/khunaungpaing/PaO-Typing-Tutor/releases/latest).

| Platform | Download Package | Requirements |
| :--- | :--- | :--- |
| **macOS** | [`Pa-O-Typing-Tutor-v1.0.0-macos.dmg`](https://github.com/khunaungpaing/PaO-Typing-Tutor/releases/latest) | macOS 11.0 (Big Sur) or later (Apple Silicon & Intel) |
| **Windows** | [`Pa-O-Typing-Tutor-v1.0.0-windows-setup.exe`](https://github.com/khunaungpaing/PaO-Typing-Tutor/releases/latest) | Windows 10 or Windows 11 (64-bit) |
| **Linux** | Run from source | Python 3.9+ |

> **🔏 Code Signing Notice**:
> Free code signing provided by [SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).
>
> **🔒 Privacy Policy**:
> Pa-O Typing Tutor is 100% offline and collects zero telemetry or personal data. See our [Privacy Policy](PRIVACY.md).

---

## 🛡️ First-Launch Security Warnings & Workarounds

Because this open-source application is community-developed and not signed with expensive corporate developer certificates, your operating system will show a standard one-time security warning when first opened.

### macOS ("App is damaged" or "Unidentified Developer")

macOS Gatekeeper automatically places quarantine flags on applications downloaded outside the App Store.

#### Recommended Fix (Terminal command):
1. Copy or drag **Pa-O Typing Tutor** into your `/Applications` folder.
2. Open **Terminal** (press `Cmd + Space`, type `Terminal`, and hit `Enter`).
3. Run the following command:
   ```bash
   xattr -cr "/Applications/Pa-O Typing Tutor.app"
   ```
4. Launch the application normally from Applications or Launchpad.

#### Alternative GUI Method:
1. In **Finder**, locate the app in your Applications folder.
2. **Right-click** (or `Control + click`) on **Pa-O Typing Tutor.app** and select **Open**.
3. In the confirmation dialog, click **Open**. (You only need to do this once).

---

### Windows ("Windows protected your PC" / Microsoft Defender SmartScreen)

Windows SmartScreen displays a warning for newly published software that has not yet accumulated download reputation.

1. When the blue **"Windows protected your PC"** dialog appears, click **More info**.
2. Click the **Run anyway** button that appears at the bottom.
3. The setup wizard will start and install Pa-O Typing Tutor cleanly.

---

## 🚀 Run from Source

If you prefer to run from source or are on Linux:

### 1. Prerequisites
- **Python 3.9 or later**
- `git`

### 2. Clone the repository
```bash
git clone https://github.com/khunaungpaing/PaO-Typing-Tutor.git
cd PaO-Typing-Tutor
```

### 3. Create a virtual environment and install dependencies
**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

---

## 🏛️ Codebase Architecture

```text
PaO-Typing-Tutor/
├── assets/                  # Application resources
│   ├── fonts/               # KhamThaton font files (native Kham Dom glyphs)
│   ├── img/                 # App icons (PNG, ICNS, ICO)
│   ├── keyboards/           # Keyboard layout definitions
│   ├── locales/             # Translations (en.json, my.json, pao.json)
│   ├── samples/             # Sample lesson files (JSON, CSV)
│   ├── sounds/              # Audio feedback files
│   └── lessons.json         # Built-in course lessons
├── core/                    # Core business logic (no GUI dependencies)
│   ├── content_store.py     # User lesson and layout storage
│   ├── font_features.py     # Font styling configuration
│   ├── key_mapping.py       # Key mapping algorithms and defaults
│   ├── keyboard_layouts.py  # Layout discovery and parsing
│   ├── lesson_loader.py     # Lesson catalog loading and validation
│   ├── localization.py      # Multi-language string resolver
│   ├── metrics.py           # WPM, CPM, and accuracy calculations
│   ├── sound_manager.py     # Audio player with synthesized tone fallback
│   ├── typing_engine.py     # Typing state machine and character evaluator
│   └── version.py           # Single source of truth for version and metadata
├── gui/                     # PyQt6 user interface components
│   ├── about_dialog.py      # Tabbed About and License dialog
│   ├── content_dialogs.py   # Lesson editor, lesson manager, keyboard editor
│   ├── hand_panel.py        # Hand placement and finger guides
│   ├── icons.py             # Vector icon helper (FontAwesome + Qt fallback)
│   ├── main_window.py       # Main application window & event orchestrator
│   ├── metrics_bar.py       # Real-time metrics display
│   ├── typing_area.py       # Target prompt and input area
│   └── virtual_keyboard.py  # Rendered keyboard with key highlighting
├── scripts/                 # Build and packaging automation
│   ├── build_macos.sh       # macOS PyInstaller + codesign + DMG script
│   ├── build_windows.ps1    # Windows PyInstaller + Inno Setup script
│   └── build_windows.bat    # Windows batch wrapper
├── .github/workflows/       # GitHub Actions CI/CD
│   └── build-release.yml    # Automated multi-platform release builder
├── installer.iss            # Inno Setup Windows installer script
├── pao-typing-tutor.spec    # Cross-platform PyInstaller specification
├── make_icons.py            # Multi-resolution icon generation script
├── requirements.txt         # Runtime Python dependencies
├── LICENSE                  # MIT License
└── main.py                  # Application entry point
```

| Component | Responsibility |
| :--- | :--- |
| `core/version.py` | Single source of truth for versioning, app IDs, author, and license information |
| `core/typing_engine.py` | State machine processing key strokes, comparing targets, recording error positions |
| `core/font_features.py` | Font styling and typography configuration |
| `gui/about_dialog.py` | Displays version, Pa'O language background, and MIT License |
| `gui/virtual_keyboard.py` | Draws virtual keyboard, handles key shift transformations and active highlights |
| `installer.iss` | Windows Inno Setup compiler script with persistent AppId |

---

## 🛠️ Building Standalone Binaries

### macOS (.app & .dmg)
Requires macOS with Python 3.9+ and PyInstaller:
```bash
./scripts/build_macos.sh
```
The output disk image is saved to `dist/Pa-O-Typing-Tutor-v{version}-macos.dmg`.

### Windows (.exe & Setup Installer)
Requires Windows, Python 3.9+, and [Inno Setup 6](https://jrsoftware.org/isdl.php):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```
The output installer is saved to `dist\Pa-O-Typing-Tutor-v{version}-windows-setup.exe`.

---

## 🤝 Contributing

Contributions to improve Pa-O Typing Tutor are warmly welcomed!

- **Report Bugs**: Open an issue on GitHub describing the bug and your operating system.
- **Add Lessons**: Suggest or create new practice passages in Pa'O.
- **Improve Translations**: Review or enhance language files in `assets/locales/`.
- **Keyboard Layouts**: Submit standard or regional keyboard layouts for the Pa'O community.

### Pull Request Process
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/new-feature`).
3. Verify syntax and tests (`python3 -m compileall -q main.py core gui`).
4. Commit your changes with descriptive messages.
5. Push to your branch and submit a Pull Request.

---

## 📄 License & Author

This project is open-source software licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.

**Author**: Khun Aung Paing  
**GitHub**: [@khunaungpaing](https://github.com/khunaungpaing)  
**Email**: [khunaungpang.it.tumlm@gmail.com](mailto:khunaungpang.it.tumlm@gmail.com)  
**Copyright**: © 2026 Khun Aung Paing
