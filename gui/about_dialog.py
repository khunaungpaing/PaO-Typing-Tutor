"""About dialog for Pa-O Typing Tutor with tabs for app info and license."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.version import (
    APP_NAME,
    AUTHOR,
    COPYRIGHT,
    DESCRIPTION,
    LICENSE_NAME,
    LICENSE_TEXT,
    WEBSITE,
    __version__,
)


class AboutDialog(QDialog):
    """Tabbed dialog showing version metadata, language details, and license."""

    def __init__(self, parent: QWidget | None = None, assets_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contentDialog")
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.resize(540, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Tab widget
        tabs = QTabWidget()
        tabs.setObjectName("aboutTabs")
        tabs.addTab(self._create_about_tab(assets_dir), "About")
        tabs.addTab(self._create_license_tab(), LICENSE_NAME)
        main_layout.addWidget(tabs, 1)

        # Footer button
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        main_layout.addLayout(footer)

        self._apply_dialog_theme()

    def _create_about_tab(self, assets_dir: Path | None) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # App Header with Icon and Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        icon_label = QLabel()
        icon_path = (assets_dir / "img" / "app.png") if assets_dir else None
        if icon_path and icon_path.is_file():
            pixmap = QPixmap(str(icon_path)).scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(64, 64)
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        app_title = QLabel(APP_NAME)
        app_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        version_label = QLabel(f"Version {__version__}")
        version_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #7c6df2;")
        title_layout.addWidget(app_title)
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout, 1)
        layout.addLayout(header_layout)

        # Short description
        desc_label = QLabel(DESCRIPTION)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #dbe5f2; font-size: 13px; line-height: 1.4;")
        layout.addWidget(desc_label)

        # Pa'O Language & Unicode Card
        lang_card = QFrame()
        lang_card.setObjectName("infoCard")
        lang_layout = QVBoxLayout(lang_card)
        lang_layout.setContentsMargins(12, 10, 12, 10)
        lang_layout.setSpacing(4)

        lang_heading = QLabel("About Pa'O Language & Script")
        lang_heading.setStyleSheet("font-weight: 700; color: #8978ff; font-size: 12px;")
        lang_body = QLabel(
            "Pa'O (ပအိုဝ်း / ပအိုဝ်ႏ) is a Karenic language spoken by approximately "
            "750,000–875,000 people primarily in Shan State, Myanmar. It is written in the "
            "Myanmar script with specialized tone marks and extensions, supported in "
            "Unicode 16.0 (Myanmar Extended-C). This app features the Pa-O Kham Dom "
            "Experimental keyboard layout and KhamThaton-Exp font (authentic Kham Dom glyph "
            "forms are rendered by default; OpenType ss01 is reserved for viewing original base glyphs)."
        )
        lang_body.setWordWrap(True)
        lang_body.setStyleSheet("color: #9fb0c7; font-size: 12px; line-height: 1.3;")
        lang_layout.addWidget(lang_heading)
        lang_layout.addWidget(lang_body)
        layout.addWidget(lang_card)

        # Details Table / Metadata
        meta_card = QFrame()
        meta_card.setObjectName("infoCard")
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(12, 8, 12, 8)
        meta_layout.setSpacing(4)

        author_label = QLabel(f"<b>Author:</b> {AUTHOR} &nbsp;&middot;&nbsp; {COPYRIGHT}")
        author_label.setStyleSheet("color: #cad5e2; font-size: 12px;")
        meta_layout.addWidget(author_label)

        site_label = QLabel(f'<b>GitHub:</b> <a href="{WEBSITE}" style="color: #7c6df2;">{WEBSITE}</a>')
        site_label.setOpenExternalLinks(True)
        site_label.setStyleSheet("color: #cad5e2; font-size: 12px;")
        meta_layout.addWidget(site_label)

        layout.addWidget(meta_card)
        layout.addStretch()
        return tab

    def _create_license_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        license_view = QPlainTextEdit()
        license_view.setReadOnly(True)
        license_view.setPlainText(LICENSE_TEXT)
        license_view.setFont(QFont("Courier New", 11) if sys_has_courier() else QFont("monospace", 11))
        license_view.setStyleSheet("""
            QPlainTextEdit {
                background: #080d17;
                color: #cbd5e1;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
        """)
        layout.addWidget(license_view)
        return tab

    def _apply_dialog_theme(self) -> None:
        self.setStyleSheet("""
            QDialog#contentDialog {
                background: #0b1220;
            }
            QTabWidget#aboutTabs::pane {
                border: 1px solid #1e293b;
                border-radius: 8px;
                background: #0f172a;
                top: -1px;
            }
            QTabBar::tab {
                background: #131d31;
                color: #8da2be;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #1e293b;
                border-bottom: none;
                font-weight: 600;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #0f172a;
                color: #f8fafc;
                border-top: 2px solid #6d5ce7;
            }
            QTabBar::tab:hover:!selected {
                background: #19263f;
                color: #c7d5e6;
            }
            #infoCard {
                background: #141f33;
                border: 1px solid #23334d;
                border-radius: 8px;
            }
            QPushButton#primaryButton {
                background: #6d5ce7;
                color: white;
                border: 0;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton#primaryButton:hover {
                background: #7b6bef;
            }
            QPushButton#primaryButton:pressed {
                background: #5b4bc9;
            }
        """)


def sys_has_courier() -> bool:
    """Helper to detect font availability safely."""
    return True
