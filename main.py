"""Application entry point for the Pa-O Typing Tutor."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.font_features import pao_font
from core.lesson_loader import LessonLoader
from gui.main_window import MainWindow

# --- System Path Mappings ---
BASE_DIR = Path(__file__).resolve().parent
FONT_PATH = BASE_DIR / "assets" / "fonts" / "KhamThaton-Exp-Regular-0.1.ttf"
KEYBOARD_FONT_PATH = FONT_PATH
FONT_FALLBACKS = (
    BASE_DIR / "assets" / "fonts" / "Thuwana-Regular.otf",
    BASE_DIR / "assets" / "fonts" / "kothupaoh1.ttf",
)
LESSONS_PATH = BASE_DIR / "assets" / "lessons.json"

# Cross-platform application icons
APP_ICON_WIN_PATH = BASE_DIR / "assets" / "img" / "app.ico"
APP_ICON_MAC_PATH = BASE_DIR / "assets" / "img" / "app.icns"


def init_mac_dock_runtime() -> None:
    """Ensure PyQt6 window icons render natively inside the macOS Dock ecosystem."""
    if sys.platform == "darwin":
        try:
            from ctypes import c_void_p, cdll
            # Fetch the running App instance from the Apple runtime layers
            shared_app = cdll.LoadLibrary(None).NSApplication_sharedApplication
            shared_app.restype = c_void_p
            app_instance = shared_app()

            # Dynamically register the foreground activation policy selector
            set_policy_sel = cdll.LoadLibrary(None).sel_registerName(b"setActivationPolicy:")
            # Force activation policy state to 0 (Regular UI Application)
            cdll.LoadLibrary(None).objc_msgSend(app_instance, set_policy_sel, 0)
        except Exception:
            # Fallback quietly if runtime ctypes bindings are restricted
            pass


def load_application_font(app: QApplication) -> tuple[str, str | None]:
    """Load the bundled font and return its family plus an optional warning."""
    selected_path = FONT_PATH
    warning: str | None = None

    if not selected_path.is_file():
        selected_path = next((path for path in FONT_FALLBACKS if path.is_file()), FONT_PATH)
        if selected_path == FONT_PATH:
            return app.font().family(), f"Custom font not found: {FONT_PATH}"
        warning = f"{FONT_PATH.name} was not found; using {selected_path.name} instead."

    font_id = QFontDatabase.addApplicationFont(str(selected_path))
    if font_id < 0:
        return app.font().family(), f"Could not load custom font: {selected_path}"

    families = QFontDatabase.applicationFontFamilies(font_id)
    if not families:
        return app.font().family(), "The custom font contains no readable family."
    return families[0], warning


def load_application_icon(app: QApplication) -> str | None:
    """Use the platform-appropriate native bundled asset as the application icon."""
    # Prioritize icon asset matching the system environment
    target_path = APP_ICON_MAC_PATH if sys.platform == "darwin" else APP_ICON_WIN_PATH

    # Fallback to alternative system extension if the primary choice is missing
    if not target_path.is_file():
        target_path = APP_ICON_WIN_PATH if target_path == APP_ICON_MAC_PATH else APP_ICON_MAC_PATH

    if not target_path.is_file():
        return f"App icon asset missing framework target: {target_path.name}"

    icon = QIcon(str(target_path))
    if icon.isNull():
        return f"Could not parse graphic data structure: {target_path}"

    app.setWindowIcon(icon)
    return None


def main() -> int:
    """Create and run the Qt application context loop."""
    # Initialize the macOS specific runtime fixes before application construction
    init_mac_dock_runtime()

    app = QApplication(sys.argv)
    app.setApplicationName("Pa-O Typing Tutor")
    app.setStyle("Fusion")

    # Handle engine initialization configurations
    font_family, font_warning = load_application_font(app)
    icon_warning = load_application_icon(app)
    app.setFont(pao_font(font_family, 12))

    # Initialize backend components
    loader = LessonLoader(LESSONS_PATH)
    lessons = loader.load()

    keyboard_font = next(
        (path for path in (KEYBOARD_FONT_PATH, *FONT_FALLBACKS) if path.is_file()),
        KEYBOARD_FONT_PATH,
    )

    # Render Application Viewports
    window = MainWindow(lessons, font_family, str(keyboard_font), BASE_DIR / "assets")
    window.setWindowIcon(app.windowIcon())
    window.show()

    # Process and display boot diagnostic alerts if validation errors occur
    warnings = [message for message in (font_warning, icon_warning, loader.last_warning) if message]
    if warnings:
        QMessageBox.warning(window, "Startup warning", "\n\n".join(warnings))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
