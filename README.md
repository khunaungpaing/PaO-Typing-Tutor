# Pa-O Typing Tutor

A desktop typing tutor for the **Pa-O Kham Dom Experimental** keyboard. It is
built with Python and PyQt6 and provides guided Pa-O practice with a virtual
keyboard, finger guidance, live typing metrics, and editable lesson content.

## Highlights

- Pa-O Kham Dom Base and Shift keyboard mapping, including official Pa-O
  digits and Pa-O punctuation.
- KhamThaton-Exp font with OpenType `ss01` enabled for Kham Dom shaping.
- On-screen keyboard with Shift state, target-key highlighting, and finger
  guidance.
- WPM, CPM, accuracy, elapsed time, error review, restart, and sound feedback.
- Built-in lessons plus custom lesson creation, editing, deletion, and
  JSON/CSV import.
- User-created keyboard layouts, Pa-O/Myanmar/English interface localization,
  and optional custom sounds.

## Requirements

- Python 3.11 or later
- A supported desktop platform: macOS, Windows, or Linux

Install the Python dependencies from `requirements.txt`.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

On Windows, activate the virtual environment and run `python main.py` using
the equivalent commands for your shell.

The optional global physical-key guidance listener uses `pynput`. On macOS it
may require Input Monitoring permission. Typing into the app itself works
without that permission.

## Pa-O font and shaping

The app loads [KhamThaton-Exp-Regular-0.1.ttf](assets/fonts/KhamThaton-Exp-Regular-0.1.ttf)
and enables the `ss01` OpenType feature. This is required for the intended
Kham Dom glyph forms, including temporary multi-codepoint encodings used by
the experimental keyboard.

The visible title inside the app uses KhamThaton-Exp with `ss01`. macOS renders
the native window title using its system font, so that title intentionally uses
the ASCII name `Pa-O Typing Tutor`.

## Lessons

Built-in lessons are stored in [assets/lessons.json](assets/lessons.json).
Create a lesson with the **+** button, or use the lesson manager to edit and
delete lessons you created. User lessons are stored locally in
`assets/custom_lessons.json` and are intentionally ignored by Git.

The lesson dialog imports UTF-8 JSON or CSV files. Downloadable samples are in
[assets/samples](assets/samples/).

JSON accepts one lesson object or an array of objects:

```json
[
  {
    "title": "အခန်ႋနမူ𑛦နာ𑛦",
    "text": "အ အာ အိ အီ"
  }
]
```

CSV requires `title` and `text` headers:

```csv
title,text
အခန်ႋနမူ𑛦နာ𑛦,အ အာ အိ အီ
```

## Keyboard layouts

The built-in layout is **Pa-O Kham Dom Experimental**. It follows the Base and
Shift mappings in `pa_o_kham_dom.kmn`; the application’s source mapping is in
[core/key_mapping.py](core/key_mapping.py).

Use the keyboard button in the app to choose a layout or save a custom one.
Custom layouts are JSON files in `assets/keyboards/`; see
[assets/keyboards/README.md](assets/keyboards/README.md) for the schema.
Runtime-created layouts are ignored by Git so personal mappings stay local.

## Localization and sounds

- Interface translations live in `assets/locales/`. Copy a locale JSON file,
  set its `code` and `name`, and translate the values while preserving keys.
- Optional sound files and the event manifest live in `assets/sounds/`. See
  [assets/sounds/README.md](assets/sounds/README.md) for `correct`,
  `incorrect`, and `complete` sound events. Missing files fall back to the
  built-in synthesized tones.

## App icons

The app loads platform icons from `assets/img/app.ico` (Windows) and
`assets/img/app.icns` (macOS). Replace them with production artwork when ready.
Use [make_icons.py](make_icons.py) to generate both files from
`assets/img/app.png`; it requires Pillow:

```bash
.venv/bin/pip install Pillow
.venv/bin/python make_icons.py
```

## Project layout

```text
assets/   lessons, fonts, icons, locale catalogs, samples, sounds
core/     typing engine, key mapping, persistence, localization, audio
gui/      PyQt6 screens, dialogs, virtual keyboard, hand guidance
main.py   application entry point
```

## Development notes

Run a quick syntax check after changes:

```bash
.venv/bin/python -m compileall -q main.py core gui
```

The project’s `.gitignore` excludes caches, virtual environments, IDE files,
and runtime-created personal lessons, layouts, and sound files.
