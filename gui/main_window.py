"""Main application window and presentation coordination."""

from __future__ import annotations

import html
import time
from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import QEvent, QObject, QSettings, Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from core.content_store import (
    add_user_lesson, add_user_lessons, import_lessons, load_user_lessons,
    save_keyboard_layout,
)
from core.font_features import pao_font
from core.key_mapping import mapped_character
from core.keyboard_listener import PhysicalKeyboardListener
from core.keyboard_layouts import activate_layout, discover_layouts
from core.localization import Localizer
from core.metrics import MetricsCalculator
from core.sound_manager import SoundManager
from core.typing_engine import CharacterResult, TypingEngine
from gui.metrics_bar import MetricsBar
from gui.content_dialogs import KeyboardLayoutDialog, LessonEditorDialog
from gui.content_dialogs import ManageLessonsDialog
from gui.icons import icon
from gui.typing_area import TypingArea
from gui.virtual_keyboard import VirtualKeyboard


NATIVE_WINDOW_TITLE = "Pa-O Typing Tutor"


class MainWindow(QMainWindow):
    """Top-level typing tutor window."""

    def __init__(self, lessons: List[Dict[str, str]], font_family: str,
                 keyboard_font_path: str, assets_directory: Path) -> None:
        super().__init__()
        self.assets_directory = assets_directory
        self.custom_lessons_path = assets_directory / "custom_lessons.json"
        self.keyboard_directory = assets_directory / "keyboards"
        self.built_in_lessons = [lesson.copy() for lesson in lessons]
        self.lessons = [*self.built_in_lessons, *load_user_lessons(self.custom_lessons_path)]
        self.font_family = font_family
        self.keyboard_font_path = keyboard_font_path
        self.keyboard_layouts, self.keyboard_warnings = discover_layouts(
            self.keyboard_directory
        )
        self.current_layout_index = 0
        activate_layout(self.keyboard_layouts[0])
        self.localizer = Localizer(assets_directory / "locales")
        self.settings = QSettings("Pa-O", "Typing Tutor")
        self.localizer.set_language(str(self.settings.value("language", "pao")))
        self.sound = SoundManager(assets_directory / "sounds")
        self.physical_keyboard = PhysicalKeyboardListener(self)
        self.physical_keyboard.key_pressed.connect(self._physical_key_pressed)
        self.physical_keyboard.key_released.connect(self._physical_key_released)
        self.engine = TypingEngine()
        self.started_at: float | None = None
        self.finished = False
        self.error_history: List[CharacterResult] = []
        self.setWindowTitle(NATIVE_WINDOW_TITLE)
        self.setMinimumSize(900, 760)
        self.resize(1180, 1050)
        self._build_ui()
        self._translate_ui()
        self._apply_theme()
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._refresh_metrics)
        self._load_lesson(0)
        self.physical_keyboard.start()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("centralRoot")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 22, 28, 10)
        layout.setSpacing(14)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        header = QHBoxLayout(top_bar)
        header.setContentsMargins(18, 12, 18, 12)
        header.setSpacing(10)
        self.title_label = QLabel()
        self.title_label.setObjectName("appTitle")
        self.title_label.setMaximumWidth(520)
        self.lesson_picker = QComboBox()
        self.lesson_picker.addItems([lesson["title"] for lesson in self.lessons])
        self.lesson_picker.currentIndexChanged.connect(self._load_lesson)
        self.previous_button = QPushButton()
        self.previous_button.setObjectName("secondaryButton")
        self.previous_button.setFixedSize(42, 42)
        self.previous_button.clicked.connect(self._previous_lesson)
        self.next_button = QPushButton()
        self.next_button.setObjectName("secondaryButton")
        self.next_button.setFixedSize(42, 42)
        self.next_button.clicked.connect(self._next_lesson)
        self.language_picker = QComboBox()
        self.language_picker.setObjectName("languagePicker")
        for code, name in self.localizer.names.items():
            self.language_picker.addItem(name, code)
        selected_language = self.language_picker.findData(self.localizer.current)
        self.language_picker.setCurrentIndex(max(0, selected_language))
        self.language_picker.currentIndexChanged.connect(self._change_language)
        self.interface_icon = QLabel()
        self.interface_icon.setObjectName("contextIcon")
        self.interface_label = QLabel()
        self.interface_label.setObjectName("contextLabel")
        self.add_lesson_button = QPushButton()
        self.add_lesson_button.setObjectName("iconButton")
        self.add_lesson_button.setFixedSize(42, 42)
        self.add_lesson_button.clicked.connect(self._open_lesson_editor)
        self.manage_lessons_button = QPushButton()
        self.manage_lessons_button.setObjectName("iconButton")
        self.manage_lessons_button.setFixedSize(42, 42)
        self.manage_lessons_button.clicked.connect(self._open_manage_lessons)
        self.keyboard_layout_button = QPushButton()
        self.keyboard_layout_button.setObjectName("iconButton")
        self.keyboard_layout_button.setFixedSize(42, 42)
        self.keyboard_layout_button.clicked.connect(self._open_keyboard_layouts)
        header.addWidget(self.title_label, 1)
        header.addStretch()
        header.addWidget(self.interface_icon)
        header.addWidget(self.interface_label)
        header.addWidget(self.language_picker)
        header.addWidget(self.add_lesson_button)
        header.addWidget(self.manage_lessons_button)
        header.addWidget(self.keyboard_layout_button)
        layout.addWidget(top_bar)

        lesson_bar = QFrame()
        lesson_bar.setObjectName("lessonBar")
        lesson_layout = QHBoxLayout(lesson_bar)
        lesson_layout.setContentsMargins(12, 10, 12, 10)
        lesson_layout.setSpacing(10)
        lesson_layout.addWidget(self.previous_button)
        lesson_layout.addWidget(self.lesson_picker, 1)
        lesson_layout.addWidget(self.next_button)
        layout.addWidget(lesson_bar)

        self.metrics = MetricsBar()
        layout.addWidget(self.metrics)
        self.typing_area = TypingArea()
        self.target_label = self.typing_area.target_label
        self.input_edit = self.typing_area.input_edit
        self.hint_label = self.typing_area.hint_label
        self.restart_button = self.typing_area.restart_button
        self.sound_button = self.typing_area.sound_button
        self.input_edit.textChanged.connect(self._on_text_changed)
        self.input_edit.installEventFilter(self)
        self.restart_button.clicked.connect(self._restart)
        self.sound_button.toggled.connect(self._toggle_sound)
        layout.addWidget(self.typing_area, 2)

        keyboard_card = QFrame()
        keyboard_card.setObjectName("keyboardCard")
        keyboard_layout = QVBoxLayout(keyboard_card)
        keyboard_layout.setContentsMargins(14, 14, 14, 10)
        self.keyboard = VirtualKeyboard(Path(self.keyboard_font_path), self.font_family)
        keyboard_layout.addWidget(self.keyboard)
        layout.addWidget(keyboard_card, 1)
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        self._refresh_icons()

    def _apply_theme(self) -> None:
        self.setFont(pao_font(self.font_family, 12))
        self.setStyleSheet(f"""
            * {{ font-family: '{self.font_family}'; color: #e6edf7; }}
            QMainWindow, #centralRoot {{ background: #090f1d; }}
            #mainScroll {{ background: #090f1d; border: 0; }}
            QScrollBar:vertical {{ background: #090f1d; width: 9px; margin: 2px; }}
            QScrollBar::handle:vertical {{ background: #31425d; border-radius: 4px; min-height: 36px; }}
            QScrollBar::handle:vertical:hover {{ background: #4d6282; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
            QLabel {{ background: transparent; }}
            #topBar {{ background: #111a2b; border: 1px solid #1d2b42; border-radius: 12px; }}
            #appTitle {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
            #contextLabel {{ color: #91a2b9; font-size: 11px; font-weight: 600; }}
            #contextIcon {{ min-width: 16px; max-width: 16px; }}
            #lessonBar {{ background: transparent; }}
            QComboBox {{ background: #172235; border: 1px solid #2b3a52;
                border-radius: 12px; padding: 8px 34px 8px 12px; color: #edf2f9; min-height: 24px; }}
            QComboBox:hover {{ border-color: #4a5e7a; }}
            QComboBox:focus {{ border: 1px solid #7c6df2; }}
            QComboBox::drop-down {{ border: 0; width: 30px; }}
            QComboBox QAbstractItemView {{ background: #172235; border: 1px solid #344661;
                border-radius: 12px; padding: 6px; selection-background-color: #6d5ce7; }}
            QComboBox#languagePicker {{ min-width: 110px; max-width: 145px; }}
            #practiceCard {{ background: #111a2b; border: 1px solid #1d2b42; border-radius: 12px; }}
            #typingInput {{ background: #0c1424; border: 1px solid #2a3951;
                border-radius: 12px; padding: 11px 15px; color: #f8fafc;
                font-size: 19px; min-height: 32px; selection-background-color: #6757df; }}
            #typingInput:focus {{ border: 2px solid #7565e8; padding: 10px 14px; }}
            #metricsBar {{ background: transparent; }}
            #metricCard {{ background: #111a2b; border: 1px solid #1d2b42; border-radius: 12px; }}
            #metricHeading {{ color: #7f91ab; font-size: 10px; font-weight: 700; }}
            #metricValue {{ color: #f5f7fb; font-size: 23px; font-weight: 700; }}
            #targetText {{ background: #0c1424; border: 1px solid #17243a; border-radius: 12px;
                padding: 28px; font-size: 28px; line-height: 1.5; }}
            #hintText {{ color: #93a4bc; font-size: 12px; }}
            #primaryButton {{ background: #6d5ce7; color: white; border: 0; border-radius: 12px;
                padding: 9px 18px; font-weight: 700; }}
            #primaryButton:hover {{ background: #7b6bef; }}
            #primaryButton:pressed {{ background: #5b4bc9; }}
            #secondaryButton, #iconButton {{ background: #151f31; color: #d9e2ef;
                border: 1px solid #2b3a52; border-radius: 12px; padding: 8px; font-weight: 600; }}
            #secondaryButton:hover, #iconButton:hover {{ background: #1c2940; border-color: #647d9f; }}
            #iconButton:checked {{ background: #352e66; border-color: #7867ff; }}
            #secondaryButton:disabled {{ color: #4c5b70; border-color: #1b293d; background: #101827; }}
            #keyboardCard {{ background: #0e1727; border: 1px solid #1d2b42; border-radius: 12px; }}
            #keyboardKey {{ background: #1b2940; color: #c8d3e2; border: 1px solid #2e405b;
                border-radius: 12px; padding: 2px; font-family: '{self.keyboard.font_family}';
                font-size: 18px; font-weight: 600; }}
            #keyboardKey[target="true"] {{ background: #26224d; color: white; border: 3px solid #8978ff; }}
            #keyboardKey[targetShift="true"] {{ background: #25264c; border: 3px solid #4cc9f0; }}
            #keyboardKey[pressed="true"] {{ background: #dc8b1e; color: #0b1120; border: 2px solid #ffc45c; }}
            #modifierKey {{ background: #151f31; color: #8fa1ba; border: 1px solid #2b3a52;
                border-radius: 12px; font-size: 11px; font-weight: 700; }}
            #modifierKey[active="true"] {{ background: #6d5ce7; color: white; border: 2px solid #a99cff; }}
            #resultDialog {{ background: #0f172a; }}
            #resultHero {{ background: #172554; border: 1px solid #3730a3; border-radius: 18px; }}
            #resultBadge {{ color: #c4b5fd; font-size: 12px; font-weight: 700; }}
            #resultTitle {{ color: white; font-size: 30px; font-weight: 800; }}
            #resultSubtitle {{ color: #bfdbfe; font-size: 13px; }}
            #resultMetric {{ background: #172033; border: 1px solid #2b3a51; border-radius: 14px; }}
            #resultMetricLabel {{ color: #94a3b8; font-size: 11px; font-weight: 700; }}
            #resultMetricValue {{ color: #f8fafc; font-size: 25px; font-weight: 800; }}
            #resultErrors {{ background: #131d2e; border: 1px solid #26354a; border-radius: 12px; }}
            #resultErrorsTitle {{ color: #cbd5e1; font-size: 12px; font-weight: 700; }}
            #resultErrorsText {{ color: #94a3b8; background: transparent; }}
            #resultSuccess {{ color: #4ade80; font-size: 13px; font-weight: 700; }}
            #contentDialog {{ background: #0b1220; }}
            #dialogHeading {{ color: #f8fafc; font-size: 22px; font-weight: 800; }}
            #dialogDescription {{ color: #91a2b9; font-size: 12px; }}
            #resourcePanel {{ background: #111f35; border: 1px solid #263b5a;
                border-radius: 12px; }}
            #resourceLabel {{ color: #b7c7da; font-size: 11px; font-weight: 700; }}
            #contentDialog QLineEdit, #contentDialog QPlainTextEdit, #contentDialog QTableWidget,
            #contentDialog QListWidget {{
                background: #111a2b; border: 1px solid #2b3a52; border-radius: 12px;
                padding: 10px; selection-background-color: #6d5ce7; }}
            #contentDialog QListWidget::item {{ padding: 10px; border-radius: 8px; }}
            #contentDialog QListWidget::item:selected {{ background: #352e66; color: white; }}
            #contentDialog QTableWidget {{ gridline-color: #25344b; padding: 0; }}
            #contentDialog QHeaderView::section {{ background: #172235; color: #9fb0c7;
                border: 0; border-right: 1px solid #2b3a52; padding: 8px; }}
            #contentDialog QPushButton {{ background: #172235; color: #dbe5f2;
                border: 1px solid #30425e; border-radius: 12px; padding: 9px 16px; }}
            #contentDialog QPushButton:hover {{ background: #21304a; border-color: #5b7395; }}
            #contentDialog #primaryButton {{ background: #6d5ce7; color: white; border: 0; }}
            #contentDialog #primaryButton:hover {{ background: #7b6bef; }}
            #contentDialog #dangerButton {{ background: #3a1d2a; color: #fecdd3;
                border: 1px solid #713246; }}
            #contentDialog #dangerButton:hover {{ background: #562437; border-color: #a34460; }}
        """)
        title_font = pao_font(self.font_family, 22)
        title_font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(title_font)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Translate physical QWERTY events into Pa-O Unicode input."""
        if watched is self.input_edit and isinstance(event, QKeyEvent):
            key = event.key()
            if event.type() == QEvent.Type.KeyRelease:
                self.keyboard.set_pressed_key(None)
                if key == Qt.Key.Key_Shift.value:
                    self.keyboard.set_shifted(False)
                    return True
                self.keyboard.set_shifted(bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier))
            if event.type() == QEvent.Type.KeyPress:
                if key == Qt.Key.Key_Shift.value:
                    self.keyboard.set_shifted(True)
                    return True
                shifted = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                self.keyboard.set_shifted(shifted)
                shortcut_modifiers = (Qt.KeyboardModifier.ControlModifier
                                      | Qt.KeyboardModifier.AltModifier
                                      | Qt.KeyboardModifier.MetaModifier)
                if event.modifiers() & shortcut_modifiers:
                    return super().eventFilter(watched, event)
                character = mapped_character(key, shifted)
                if character is not None:
                    self.keyboard.set_pressed_key(key)
                    self.input_edit.insert(character)
                    return True
        return super().eventFilter(watched, event)

    def _physical_key_pressed(self, key: int, shifted: bool, character: str) -> None:
        """Mirror pynput events visually; Qt owns text entry to avoid duplication."""
        if self.isActiveWindow() and self.input_edit.hasFocus():
            self.keyboard.set_shifted(shifted)
            self.keyboard.set_pressed_key(key)

    def _physical_key_released(self, key: int) -> None:
        if self.isActiveWindow():
            self.keyboard.set_pressed_key(None)

    def _load_lesson(self, index: int) -> None:
        if not 0 <= index < len(self.lessons):
            return
        self.engine.reset(self.lessons[index]["text"])
        self.started_at = None
        self.finished = False
        self.error_history = []
        self.timer.stop()
        self.input_edit.clear()
        # Do not cap this to len(target): OpenType glyphs can contain multiple
        # Unicode code points and a mapped key can emit a multi-codepoint string.
        self.input_edit.setMaxLength(32767)
        self.input_edit.setEnabled(True)
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.lessons) - 1)
        self.metrics.update_metrics(0, 0, 0, 100)
        self._render_target()
        self._update_key_hint()
        self.input_edit.setFocus()

    def _restart(self) -> None:
        self._load_lesson(self.lesson_picker.currentIndex())

    def _previous_lesson(self) -> None:
        """Open the previous lesson when available."""
        self.lesson_picker.setCurrentIndex(max(0, self.lesson_picker.currentIndex() - 1))

    def _next_lesson(self) -> None:
        """Open the next lesson when available."""
        self.lesson_picker.setCurrentIndex(min(len(self.lessons) - 1,
                                               self.lesson_picker.currentIndex() + 1))

    def _change_keyboard_layout(self, index: int) -> None:
        """Activate a discovered JSON keyboard layout."""
        if 0 <= index < len(self.keyboard_layouts):
            self.current_layout_index = index
            activate_layout(self.keyboard_layouts[index])
            self.keyboard.reload_layout()
            self._update_key_hint()
            self.input_edit.setFocus()

    def _open_lesson_editor(self) -> None:
        t = self.localizer.text
        dialog = LessonEditorDialog({
            "title": t("lesson_editor.title"), "heading": t("lesson_editor.heading"),
            "description": t("lesson_editor.description"), "name": t("lesson_editor.name"),
            "text": t("lesson_editor.text"), "title_placeholder": t("lesson_editor.title_placeholder"),
            "text_placeholder": t("lesson_editor.text_placeholder"),
            "invalid": t("common.invalid"), "required": t("lesson_editor.required"),
            "import": t("common.import"), "resources": t("common.resources"),
            "sample": t("common.download_sample"),
            "save_as": t("common.save_as"), "failed": t("common.download_failed"),
            "downloaded": t("common.downloaded"),
        }, self.assets_directory / "samples", self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if dialog.import_requested:
                filename, _ = QFileDialog.getOpenFileName(
                    self, t("lesson_editor.import"), "",
                    "Lesson files (*.json *.csv);;JSON (*.json);;CSV (*.csv)")
                if not filename:
                    return
                added = add_user_lessons(
                    self.custom_lessons_path, import_lessons(Path(filename)))
            else:
                added = [add_user_lesson(
                    self.custom_lessons_path, dialog.lesson_title, dialog.lesson_text)]
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(self, t("common.invalid"), str(exc))
            return
        self.lessons.extend(added)
        self.lesson_picker.addItems([lesson["title"] for lesson in added])
        self.lesson_picker.setCurrentIndex(len(self.lessons) - 1)

    def _open_manage_lessons(self) -> None:
        t = self.localizer.text
        dialog = ManageLessonsDialog(self.custom_lessons_path, {
            "title": t("lesson_manager.title"), "heading": t("lesson_manager.heading"),
            "description": t("lesson_manager.description"),
            "name": t("lesson_editor.name"), "text": t("lesson_editor.text"),
            "title_placeholder": t("lesson_editor.title_placeholder"),
            "text_placeholder": t("lesson_editor.text_placeholder"),
            "save": t("lesson_manager.save"), "delete": t("lesson_manager.delete"),
            "close": t("lesson_manager.close"), "confirm": t("lesson_manager.confirm"),
            "invalid": t("common.invalid"),
        }, self)
        dialog.exec()
        if dialog.changed:
            self._reload_lessons()

    def _reload_lessons(self) -> None:
        custom_lessons = load_user_lessons(self.custom_lessons_path)
        self.lessons = [*self.built_in_lessons, *custom_lessons]
        index = max(0, min(self.lesson_picker.currentIndex(), len(self.lessons) - 1))
        self.lesson_picker.blockSignals(True)
        self.lesson_picker.clear()
        self.lesson_picker.addItems([lesson["title"] for lesson in self.lessons])
        self.lesson_picker.setCurrentIndex(index)
        self.lesson_picker.blockSignals(False)
        self._load_lesson(index)

    def _open_keyboard_layouts(self) -> None:
        t = self.localizer.text
        dialog = KeyboardLayoutDialog(self.keyboard_layouts, self.current_layout_index, {
            "title": t("keyboard_editor.title"), "heading": t("keyboard_editor.heading"),
            "description": t("keyboard_editor.description"),
            "existing": t("keyboard_editor.existing"),
            "name_placeholder": t("keyboard_editor.name_placeholder"),
            "physical": t("keyboard_editor.physical"), "normal": t("keyboard_editor.normal"),
            "shift": t("keyboard_editor.shift"), "cancel": t("common.cancel"),
            "use": t("keyboard_editor.use"), "save": t("keyboard_editor.save"),
            "invalid": t("common.invalid"), "name_required": t("keyboard_editor.name_required"),
        }, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.save_requested:
            try:
                name = dialog.name_edit.text().strip()
                save_keyboard_layout(self.keyboard_directory, name, dialog.bindings())
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, t("common.invalid"), str(exc))
                return
            index = self._reload_keyboard_layouts(name)
        else:
            index = dialog.selected_index
        self._change_keyboard_layout(index)

    def _reload_keyboard_layouts(self, selected_name: str) -> int:
        self.keyboard_layouts, self.keyboard_warnings = discover_layouts(
            self.keyboard_directory)
        matching = [
            i for i, item in enumerate(self.keyboard_layouts) if item.name == selected_name
        ]
        return matching[-1] if matching else 0

    def _change_language(self, index: int) -> None:
        code = self.language_picker.itemData(index)
        if not isinstance(code, str):
            return
        self.localizer.set_language(code)
        self.settings.setValue("language", code)
        self._translate_ui()
        self._update_key_hint()

    def _toggle_sound(self, muted: bool) -> None:
        self.sound.set_muted(muted)
        self._refresh_icons()
        self.sound_button.setToolTip(self.localizer.text(
            "controls.sound_on" if muted else "controls.sound_off"))

    def _refresh_icons(self) -> None:
        self.previous_button.setIcon(icon(self, "chevron-left"))
        self.next_button.setIcon(icon(self, "chevron-right"))
        self.restart_button.setIcon(icon(self, "undo"))
        self.sound_button.setIcon(icon(
            self, "volume-off" if self.sound_button.isChecked() else "volume-high"))
        self.interface_icon.setPixmap(icon(self, "globe").pixmap(15, 15))
        self.add_lesson_button.setIcon(icon(self, "plus"))
        self.manage_lessons_button.setIcon(icon(self, "list"))
        self.keyboard_layout_button.setIcon(icon(self, "keyboard"))

    def _translate_ui(self) -> None:
        t = self.localizer.text
        # macOS renders this native title with its system font and does not
        # expose OpenType features. The styled Pa-O title is the in-app label.
        self.setWindowTitle(NATIVE_WINDOW_TITLE)
        self.title_label.setText(t("app.title"))
        self.previous_button.setText("")
        self.next_button.setText("")
        self.restart_button.setText("")
        self.sound_button.setText("")
        self.interface_label.setText(t("controls.interface_language"))
        self.previous_button.setToolTip(t("controls.previous"))
        self.next_button.setToolTip(t("controls.next"))
        self.restart_button.setToolTip(t("controls.restart"))
        self.sound_button.setToolTip(t(
            "controls.sound_on" if self.sound_button.isChecked() else "controls.sound_off"))
        self.add_lesson_button.setToolTip(t("controls.add_lesson"))
        self.manage_lessons_button.setToolTip(t("controls.manage_lessons"))
        self.keyboard_layout_button.setToolTip(t("controls.keyboard_layouts"))
        self.language_picker.setToolTip(t("controls.language"))
        self.input_edit.setPlaceholderText(t("typing.placeholder"))
        self.metrics.set_titles({key: t(f"metrics.{key}") for key in self.metrics.headings})

    def _on_text_changed(self, text: str) -> None:
        if self.finished:
            return
        if text and self.started_at is None:
            self.started_at = time.monotonic()
            self.timer.start()
        previous_length = len(self.engine.typed)
        results = self.engine.update(text)
        if len(text) > previous_length:
            new_results = results[previous_length:]
            self.error_history.extend(result for result in new_results if not result.correct)
            if new_results:
                self.sound.play_key(all(result.correct for result in new_results))
        self._render_target()
        self._refresh_metrics()
        self._update_key_hint()
        if self.engine.complete:
            self._finish_lesson()

    def _render_target(self) -> None:
        parts: List[str] = []
        for index, character in enumerate(self.engine.target):
            escaped = html.escape(character)
            if index < len(self.engine.typed):
                color = "#4ade80" if self.engine.typed[index] == character else "#f87171"
                parts.append(f'<span style="color:{color};">{escaped}</span>')
            elif index == len(self.engine.typed):
                parts.append(f'<span style="background-color:#4c1d95;color:#fff;">{escaped}</span>')
            else:
                parts.append(f'<span style="color:#d1d5db;">{escaped}</span>')
        self.target_label.setText("".join(parts))

    def _elapsed(self) -> float:
        return time.monotonic() - self.started_at if self.started_at is not None else 0.0

    def _refresh_metrics(self) -> None:
        elapsed = self._elapsed()
        correct = self.engine.correct_count
        total = len(self.engine.typed)
        self.metrics.update_metrics(
            int(elapsed), MetricsCalculator.wpm(correct, elapsed),
            MetricsCalculator.cpm(correct, elapsed), MetricsCalculator.accuracy(correct, total),
        )

    def _update_key_hint(self) -> None:
        character = self.engine.next_character
        remaining = self.engine.target[len(self.engine.typed):]
        key_character = self.keyboard.highlight_target(remaining)
        if character is None:
            self.hint_label.setText(self.localizer.text("typing.complete"))
        elif key_character:
            self.hint_label.setText(self.localizer.text(
                "typing.next_key", character=character, key=key_character))
        else:
            self.hint_label.setText(self.localizer.text("typing.next", character=character))

    def _finish_lesson(self) -> None:
        self.finished = True
        self.timer.stop()
        self.sound.play_complete()
        self.input_edit.setEnabled(False)
        self._refresh_metrics()
        elapsed = max(self._elapsed(), 0.001)
        correct = self.engine.correct_count
        accuracy = MetricsCalculator.accuracy(correct, len(self.engine.typed))
        wpm = MetricsCalculator.wpm(correct, elapsed)
        error_lines = [
            self.localizer.text("result.error", position=error.index + 1,
                                expected=repr(error.expected), actual=repr(error.actual))
            for error in self.error_history
        ]
        dialog = QDialog(self)
        dialog.setObjectName("resultDialog")
        dialog.setWindowTitle(self.localizer.text("result.window"))
        dialog.setModal(True)
        dialog.setMinimumWidth(620)
        body = QVBoxLayout(dialog)
        body.setContentsMargins(24, 24, 24, 24)
        body.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("resultHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 18, 24, 20)
        badge = QLabel(self.localizer.text("result.badge"))
        badge.setObjectName("resultBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel(self.localizer.text("result.heading"))
        heading.setObjectName("resultTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel(self.localizer.text("result.subtitle"))
        subtitle.setObjectName("resultSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(badge)
        hero_layout.addWidget(heading)
        hero_layout.addWidget(subtitle)
        body.addWidget(hero)

        metrics_grid = QGridLayout()
        metrics_grid.setHorizontalSpacing(10)
        metric_values = (
            (self.localizer.text("metrics.speed"), f"{wpm:.1f} WPM"),
            (self.localizer.text("metrics.accuracy"), f"{accuracy:.1f}%"),
            (self.localizer.text("metrics.time"), f"{int(elapsed) // 60:02d}:{int(elapsed) % 60:02d}"),
        )
        for column, (label_text, value_text) in enumerate(metric_values):
            card = QFrame()
            card.setObjectName("resultMetric")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            label = QLabel(label_text)
            label.setObjectName("resultMetricLabel")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value = QLabel(value_text)
            value.setObjectName("resultMetricValue")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(label)
            card_layout.addWidget(value)
            metrics_grid.addWidget(card, 0, column)
        body.addLayout(metrics_grid)

        detail = QFrame()
        detail.setObjectName("resultErrors")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(16, 12, 16, 12)
        detail_title = QLabel(self.localizer.text("result.review", count=len(self.error_history)))
        detail_title.setObjectName("resultErrorsTitle")
        detail_layout.addWidget(detail_title)
        if error_lines:
            scroll = QScrollArea()
            scroll.setObjectName("resultErrorsText")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setMaximumHeight(105)
            error_text = QLabel("\n".join(error_lines))
            error_text.setObjectName("resultErrorsText")
            error_text.setWordWrap(True)
            scroll.setWidget(error_text)
            detail_layout.addWidget(scroll)
        else:
            success = QLabel(self.localizer.text("result.perfect"))
            success.setObjectName("resultSuccess")
            detail_layout.addWidget(success)
        body.addWidget(detail)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        practice_again = QPushButton(self.localizer.text("result.again"))
        practice_again.setIcon(icon(self, "undo"))
        practice_again.setObjectName("secondaryButton")
        practice_again.setMinimumHeight(44)
        practice_again.clicked.connect(lambda: dialog.done(2))
        next_lesson = QPushButton(self.localizer.text("result.next"))
        next_lesson.setIcon(icon(self, "chevron-right"))
        next_lesson.setObjectName("primaryButton")
        next_lesson.setMinimumHeight(44)
        has_next = self.lesson_picker.currentIndex() < len(self.lessons) - 1
        next_lesson.setEnabled(has_next)
        next_lesson.setText(self.localizer.text(
            "result.course_complete" if not has_next else "result.next"))
        next_lesson.clicked.connect(lambda: dialog.done(3))
        actions.addWidget(practice_again)
        actions.addStretch()
        actions.addWidget(next_lesson)
        body.addLayout(actions)
        result = dialog.exec()
        if result == 2:
            self._restart()
        elif result == 3:
            self._next_lesson()

    def closeEvent(self, event: object) -> None:
        """Stop background timer before closing."""
        self.timer.stop()
        self.physical_keyboard.stop()
        super().closeEvent(event)  # type: ignore[arg-type]
