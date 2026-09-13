"""Forms for user-created typing content and Pa-O keyboard layouts."""

from __future__ import annotations

import shutil
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QMessageBox, QPlainTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.content_store import delete_user_lesson, load_user_lessons, update_user_lesson
from core.key_mapping import PHYSICAL_LABELS
from core.keyboard_layouts import KeyboardLayout


class ImportResourcesPanel(QWidget):
    """Let end users download a ready-to-edit lesson sample."""

    import_requested = pyqtSignal()

    def __init__(self, resource_directory: Path, strings: dict[str, str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.resource_directory = resource_directory
        self.strings = strings
        self.setObjectName("resourcePanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(9)
        label = QLabel(strings["resources"])
        label.setObjectName("resourceLabel")
        self.format_picker = QComboBox()
        self.format_picker.addItem("JSON", "json")
        self.format_picker.addItem("CSV", "csv")
        sample = QPushButton(strings["sample"])
        import_button = QPushButton(strings["import"])
        sample.clicked.connect(self._download_sample)
        import_button.clicked.connect(self.import_requested.emit)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self.format_picker)
        layout.addWidget(sample)
        layout.addWidget(import_button)

    def _download_sample(self) -> None:
        suffix = str(self.format_picker.currentData())
        stem = "lesson-sample"
        self._download(self.resource_directory / f"{stem}.{suffix}",
                       f"{stem}.{suffix}", f"{suffix.upper()} (*.{suffix})")

    def _download(self, source: Path, suggested_name: str, file_filter: str) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self, self.strings["save_as"], suggested_name, file_filter)
        if not destination:
            return
        try:
            shutil.copyfile(source, destination)
        except OSError as exc:
            QMessageBox.warning(self, self.strings["failed"], str(exc))
            return
        QMessageBox.information(self, self.strings["downloaded"], destination)


class LessonEditorDialog(QDialog):
    """Collect a lesson title and Pa-O practice text."""

    def __init__(self, strings: dict[str, str], resource_directory: Path,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.strings = strings
        self.import_requested = False
        self.setObjectName("contentDialog")
        self.setWindowTitle(strings["title"])
        self.setMinimumSize(760, 560)
        self.resize(820, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)
        heading = QLabel(strings["heading"])
        heading.setObjectName("dialogHeading")
        description = QLabel(strings["description"])
        description.setObjectName("dialogDescription")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)
        resources = ImportResourcesPanel(resource_directory, strings, self)
        resources.import_requested.connect(self._request_import)
        layout.addWidget(resources)
        form = QFormLayout()
        form.setSpacing(12)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(strings["title_placeholder"])
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(strings["text_placeholder"])
        form.addRow(strings["name"], self.title_edit)
        form.addRow(strings["text"], self.text_edit)
        layout.addLayout(form, 1)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.title_edit.setFocus()

    def _request_import(self) -> None:
        self.import_requested = True
        self.accept()

    @property
    def lesson_title(self) -> str:
        return self.title_edit.text().strip()

    @property
    def lesson_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def _validate(self) -> None:
        if not self.lesson_title or not self.lesson_text:
            QMessageBox.warning(self, self.strings["invalid"], self.strings["required"])
            return
        self.accept()


class KeyboardLayoutDialog(QDialog):
    """Select an existing layout or build a new Pa-O mapping in a table."""

    def __init__(self, layouts: list[KeyboardLayout], current_index: int,
                 strings: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.layouts = layouts
        self.strings = strings
        self.save_requested = False
        self.selected_index = max(0, current_index)
        self.setObjectName("contentDialog")
        self.setWindowTitle(strings["title"])
        self.setMinimumSize(920, 740)
        self.resize(980, 800)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)
        heading = QLabel(strings["heading"])
        heading.setObjectName("dialogHeading")
        description = QLabel(strings["description"])
        description.setObjectName("dialogDescription")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel(strings["existing"]))
        self.layout_picker = QComboBox()
        self.layout_picker.addItems([item.name for item in layouts])
        self.layout_picker.setCurrentIndex(self.selected_index)
        self.layout_picker.currentIndexChanged.connect(self._populate)
        selector_row.addWidget(self.layout_picker, 1)
        layout.addLayout(selector_row)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(strings["name_placeholder"])
        layout.addWidget(self.name_edit)
        self.table = QTableWidget(len(PHYSICAL_LABELS), 3)
        self.table.setHorizontalHeaderLabels(
            [strings["physical"], strings["normal"], strings["shift"]])
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        cancel = QPushButton(strings["cancel"])
        use = QPushButton(strings["use"])
        save = QPushButton(strings["save"])
        use.setObjectName("secondaryButton")
        save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject)
        use.clicked.connect(self._use_selected)
        save.clicked.connect(self._save_new)
        actions.addWidget(cancel)
        actions.addStretch()
        actions.addWidget(use)
        actions.addWidget(save)
        layout.addLayout(actions)
        self._populate(self.selected_index)

    def _populate(self, index: int) -> None:
        if not 0 <= index < len(self.layouts):
            return
        self.selected_index = index
        mapping = self.layouts[index].mapping
        for row, (key, label) in enumerate(PHYSICAL_LABELS.items()):
            physical = QTableWidgetItem(label)
            physical.setFlags(physical.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, physical)
            self.table.setItem(row, 1, QTableWidgetItem(mapping[key]["normal"]))
            self.table.setItem(row, 2, QTableWidgetItem(mapping[key]["shift"]))

    def bindings(self) -> dict[str, dict[str, str]]:
        return {
            self.table.item(row, 0).text(): {
                "normal": self.table.item(row, 1).text(),
                "shift": self.table.item(row, 2).text(),
            }
            for row in range(self.table.rowCount())
        }

    def _use_selected(self) -> None:
        self.save_requested = False
        self.selected_index = self.layout_picker.currentIndex()
        self.accept()

    def _save_new(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, self.strings["invalid"], self.strings["name_required"])
            return
        self.save_requested = True
        self.accept()


class ManageLessonsDialog(QDialog):
    """Edit and delete persisted custom lessons while protecting built-ins."""

    def __init__(self, lessons_path: Path, strings: dict[str, str],
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.lessons_path = lessons_path
        self.strings = strings
        self.lessons = load_user_lessons(lessons_path)
        self.changed = False
        self.setObjectName("contentDialog")
        self.setWindowTitle(strings["title"])
        self.setMinimumSize(860, 600)
        self.resize(920, 680)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)
        heading = QLabel(strings["heading"])
        heading.setObjectName("dialogHeading")
        description = QLabel(strings["description"])
        description.setObjectName("dialogDescription")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)

        content = QHBoxLayout()
        content.setSpacing(14)
        self.lesson_list = QListWidget()
        self.lesson_list.setObjectName("customLessonList")
        self.lesson_list.setMinimumWidth(290)
        self.lesson_list.addItems([lesson["title"] for lesson in self.lessons])
        self.lesson_list.currentRowChanged.connect(self._select_lesson)
        content.addWidget(self.lesson_list, 1)
        editor = QVBoxLayout()
        form = QFormLayout()
        form.setSpacing(12)
        self.title_edit = QLineEdit()
        self.text_edit = QPlainTextEdit()
        self.title_edit.setPlaceholderText(strings["title_placeholder"])
        self.text_edit.setPlaceholderText(strings["text_placeholder"])
        form.addRow(strings["name"], self.title_edit)
        form.addRow(strings["text"], self.text_edit)
        editor.addLayout(form, 1)
        content.addLayout(editor, 2)
        layout.addLayout(content, 1)

        actions = QHBoxLayout()
        self.delete_button = QPushButton(strings["delete"])
        self.delete_button.setObjectName("dangerButton")
        close_button = QPushButton(strings["close"])
        self.save_button = QPushButton(strings["save"])
        self.save_button.setObjectName("primaryButton")
        self.delete_button.clicked.connect(self._delete)
        close_button.clicked.connect(self.accept)
        self.save_button.clicked.connect(self._save)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        actions.addWidget(close_button)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)
        if self.lessons:
            self.lesson_list.setCurrentRow(0)
        else:
            self._set_editor_enabled(False)

    def _select_lesson(self, index: int) -> None:
        if not 0 <= index < len(self.lessons):
            self.title_edit.clear()
            self.text_edit.clear()
            self._set_editor_enabled(False)
            return
        self._set_editor_enabled(True)
        self.title_edit.setText(self.lessons[index]["title"])
        self.text_edit.setPlainText(self.lessons[index]["text"])

    def _set_editor_enabled(self, enabled: bool) -> None:
        self.title_edit.setEnabled(enabled)
        self.text_edit.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def _save(self) -> None:
        index = self.lesson_list.currentRow()
        try:
            lesson = update_user_lesson(
                self.lessons_path, index, self.title_edit.text(),
                self.text_edit.toPlainText())
        except (IndexError, OSError, ValueError) as exc:
            QMessageBox.warning(self, self.strings["invalid"], str(exc))
            return
        self.lessons[index] = lesson
        self.lesson_list.item(index).setText(lesson["title"])
        self.changed = True

    def _delete(self) -> None:
        index = self.lesson_list.currentRow()
        if not 0 <= index < len(self.lessons):
            return
        answer = QMessageBox.question(
            self, self.strings["delete"],
            self.strings["confirm"].format(title=self.lessons[index]["title"]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_user_lesson(self.lessons_path, index)
        except (IndexError, OSError) as exc:
            QMessageBox.warning(self, self.strings["invalid"], str(exc))
            return
        self.lessons.pop(index)
        self.lesson_list.takeItem(index)
        self.changed = True
        if self.lessons:
            next_index = min(index, len(self.lessons) - 1)
            self.lesson_list.setCurrentRow(-1)
            self.lesson_list.setCurrentRow(next_index)
            self._select_lesson(next_index)
        else:
            self._select_lesson(-1)
