"""Modern update dialog with in-app check, download progress, and 1-click install."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.updater import ReleaseInfo, get_default_download_path
from core.version import APP_NAME, GITHUB_REPO, __version__
from workers.update_worker import CheckUpdateWorker, DownloadUpdateWorker


class UpdateDialog(QDialog):
    """Adaptive, non-blocking software update dialog for checking and downloading updates."""

    PAGE_CHECKING = 0
    PAGE_UP_TO_DATE = 1
    PAGE_UPDATE_AVAILABLE = 2
    PAGE_DOWNLOADING = 3
    PAGE_READY = 4
    PAGE_ERROR = 5

    def __init__(
        self,
        current_version: str = __version__,
        repo: str = GITHUB_REPO,
        silent_mode: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.repo = repo
        self.silent_mode = silent_mode

        self.current_release_info: Optional[ReleaseInfo] = None
        self.downloaded_file_path: Optional[str] = None

        self._check_worker: Optional[CheckUpdateWorker] = None
        self._download_worker: Optional[DownloadUpdateWorker] = None

        self.setWindowTitle(f"Software Update - {APP_NAME}")
        self.setMinimumSize(540, 480)
        self.resize(580, 520)

        self._build_ui()
        self._apply_dialog_theme()

        # Start update check immediately
        self.start_check()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 20)
        main_layout.setSpacing(16)

        # Multi-page Stacked Widget
        self.stack = QStackedWidget(self)

        # ---------------- Page 0: Checking ----------------
        self.page_checking = QWidget()
        chk_layout = QVBoxLayout(self.page_checking)
        chk_layout.setContentsMargins(12, 40, 12, 40)
        chk_layout.setSpacing(16)
        chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chk_title = QLabel("Checking for Updates…")
        self.chk_title.setObjectName("dialogTitle")
        self.chk_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chk_subtitle = QLabel(f"Connecting to GitHub repository ({self.repo})…")
        self.chk_subtitle.setObjectName("subText")
        self.chk_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.chk_progress = QProgressBar()
        self.chk_progress.setRange(0, 0)  # Animated indeterminate progress bar
        self.chk_progress.setFixedHeight(6)
        self.chk_progress.setTextVisible(False)
        self.chk_progress.setFixedWidth(320)

        chk_layout.addStretch()
        chk_layout.addWidget(self.chk_title)
        chk_layout.addWidget(self.chk_subtitle)
        chk_layout.addSpacing(8)
        chk_layout.addWidget(self.chk_progress, 0, Qt.AlignmentFlag.AlignCenter)
        chk_layout.addStretch()
        self.stack.addWidget(self.page_checking)

        # ---------------- Page 1: Up to Date ----------------
        self.page_uptodate = QWidget()
        utd_layout = QVBoxLayout(self.page_uptodate)
        utd_layout.setContentsMargins(12, 30, 12, 30)
        utd_layout.setSpacing(16)
        utd_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        utd_badge = QLabel("✓ UP TO DATE")
        utd_badge.setObjectName("successBadge")
        utd_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        utd_card = QFrame()
        utd_card.setObjectName("upToDateCard")
        utd_card_layout = QVBoxLayout(utd_card)
        utd_card_layout.setContentsMargins(20, 20, 20, 20)
        utd_card_layout.setSpacing(10)
        utd_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        utd_title = QLabel("You are running the latest version!")
        utd_title.setObjectName("dialogTitle")
        utd_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.utd_desc = QLabel(
            f"{APP_NAME} v{self.current_version} is currently the newest available release."
        )
        self.utd_desc.setObjectName("subText")
        self.utd_desc.setWordWrap(True)
        self.utd_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        utd_card_layout.addWidget(utd_title)
        utd_card_layout.addWidget(self.utd_desc)

        utd_layout.addStretch()
        utd_layout.addWidget(utd_badge, 0, Qt.AlignmentFlag.AlignCenter)
        utd_layout.addWidget(utd_card)
        utd_layout.addStretch()
        self.stack.addWidget(self.page_uptodate)

        # ---------------- Page 2: Update Available ----------------
        self.page_available = QWidget()
        avail_layout = QVBoxLayout(self.page_available)
        avail_layout.setContentsMargins(0, 0, 0, 0)
        avail_layout.setSpacing(12)

        avail_header = QHBoxLayout()
        avail_title_box = QVBoxLayout()
        avail_title_box.setSpacing(2)

        avail_badge = QLabel("UPDATE AVAILABLE")
        avail_badge.setObjectName("accentBadge")

        avail_title = QLabel("A new version is available!")
        avail_title.setObjectName("dialogTitle")

        avail_title_box.addWidget(avail_badge)
        avail_title_box.addWidget(avail_title)
        avail_header.addLayout(avail_title_box, 1)
        avail_layout.addLayout(avail_header)

        # Version Comparison Card
        self.version_card = QFrame()
        self.version_card.setObjectName("versionCard")
        vcard_layout = QVBoxLayout(self.version_card)
        vcard_layout.setContentsMargins(16, 12, 16, 12)
        vcard_layout.setSpacing(6)

        self.v_compare_label = QLabel()
        self.v_compare_label.setObjectName("compareLabel")

        self.asset_info_label = QLabel()
        self.asset_info_label.setObjectName("assetInfoLabel")

        vcard_layout.addWidget(self.v_compare_label)
        vcard_layout.addWidget(self.asset_info_label)
        avail_layout.addWidget(self.version_card)

        # Changelog / Release Notes
        notes_hdr = QLabel("Release Notes:")
        notes_hdr.setObjectName("sectionHeader")
        avail_layout.addWidget(notes_hdr)

        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setObjectName("changelogBrowser")
        self.changelog_browser.setOpenExternalLinks(True)
        avail_layout.addWidget(self.changelog_browser, 1)

        self.stack.addWidget(self.page_available)

        # ---------------- Page 3: Downloading ----------------
        self.page_downloading = QWidget()
        dl_layout = QVBoxLayout(self.page_downloading)
        dl_layout.setContentsMargins(12, 40, 12, 40)
        dl_layout.setSpacing(16)
        dl_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dl_title = QLabel("Downloading Update…")
        dl_title.setObjectName("dialogTitle")
        dl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dl_status_label = QLabel("Connecting to server…")
        self.dl_status_label.setObjectName("subText")
        self.dl_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dl_progress = QProgressBar()
        self.dl_progress.setRange(0, 100)
        self.dl_progress.setValue(0)
        self.dl_progress.setFixedHeight(10)
        self.dl_progress.setTextVisible(False)
        self.dl_progress.setFixedWidth(400)

        self.dl_stats_label = QLabel("0.0 MB / 0.0 MB (0%)")
        self.dl_stats_label.setObjectName("dlStatsLabel")
        self.dl_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dl_layout.addStretch()
        dl_layout.addWidget(dl_title)
        dl_layout.addWidget(self.dl_status_label)
        dl_layout.addSpacing(6)
        dl_layout.addWidget(self.dl_progress, 0, Qt.AlignmentFlag.AlignCenter)
        dl_layout.addWidget(self.dl_stats_label)
        dl_layout.addStretch()
        self.stack.addWidget(self.page_downloading)

        # ---------------- Page 4: Ready to Install ----------------
        self.page_ready = QWidget()
        rdy_layout = QVBoxLayout(self.page_ready)
        rdy_layout.setContentsMargins(12, 30, 12, 30)
        rdy_layout.setSpacing(16)
        rdy_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rdy_badge = QLabel("✓ READY TO INSTALL")
        rdy_badge.setObjectName("successBadge")
        rdy_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rdy_card = QFrame()
        rdy_card.setObjectName("readyCard")
        rdy_card_layout = QVBoxLayout(rdy_card)
        rdy_card_layout.setContentsMargins(20, 20, 20, 20)
        rdy_card_layout.setSpacing(8)
        rdy_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rdy_title = QLabel("Download Complete!")
        rdy_title.setObjectName("dialogTitle")
        rdy_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rdy_subtitle = QLabel(
            "The update package has been downloaded and is ready to install."
        )
        rdy_subtitle.setObjectName("subText")
        rdy_subtitle.setWordWrap(True)
        rdy_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rdy_path_label = QLabel()
        self.rdy_path_label.setObjectName("readyPathLabel")
        self.rdy_path_label.setWordWrap(True)
        self.rdy_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rdy_card_layout.addWidget(rdy_title)
        rdy_card_layout.addWidget(rdy_subtitle)
        rdy_card_layout.addWidget(self.rdy_path_label)

        rdy_layout.addStretch()
        rdy_layout.addWidget(rdy_badge, 0, Qt.AlignmentFlag.AlignCenter)
        rdy_layout.addWidget(rdy_card)
        rdy_layout.addStretch()
        self.stack.addWidget(self.page_ready)

        # ---------------- Page 5: Error ----------------
        self.page_error = QWidget()
        err_layout = QVBoxLayout(self.page_error)
        err_layout.setContentsMargins(12, 30, 12, 30)
        err_layout.setSpacing(16)
        err_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        err_badge = QLabel("⚠️ UPDATE ERROR")
        err_badge.setObjectName("errorBadge")
        err_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        err_card = QFrame()
        err_card.setObjectName("errorCard")
        err_card_layout = QVBoxLayout(err_card)
        err_card_layout.setContentsMargins(20, 20, 20, 20)
        err_card_layout.setSpacing(8)
        err_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        err_title = QLabel("Check for Updates Failed")
        err_title.setObjectName("dialogTitle")
        err_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.err_message_label = QLabel(
            "Unable to communicate with the GitHub Releases API."
        )
        self.err_message_label.setObjectName("subText")
        self.err_message_label.setWordWrap(True)
        self.err_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        err_card_layout.addWidget(err_title)
        err_card_layout.addWidget(self.err_message_label)

        err_layout.addStretch()
        err_layout.addWidget(err_badge, 0, Qt.AlignmentFlag.AlignCenter)
        err_layout.addWidget(err_card)
        err_layout.addStretch()
        self.stack.addWidget(self.page_error)

        main_layout.addWidget(self.stack, 1)

        # ---------------- Bottom Action Bar ----------------
        # CRITICAL: Pre-construct all buttons once to prevent layout blank-canvas bug!
        self.button_bar = QHBoxLayout()
        self.button_bar.setSpacing(10)

        # Pre-constructed buttons
        self.btn_releases = QPushButton("Open GitHub Releases")
        self.btn_releases.setObjectName("secondaryButton")
        self.btn_releases.clicked.connect(self._open_github_releases)

        self.btn_show_folder = QPushButton("Show in Folder")
        self.btn_show_folder.setObjectName("secondaryButton")
        self.btn_show_folder.clicked.connect(self._show_download_folder)

        self.btn_retry = QPushButton("Check Again")
        self.btn_retry.setObjectName("secondaryButton")
        self.btn_retry.clicked.connect(self.start_check)

        self.btn_cancel_download = QPushButton("Cancel")
        self.btn_cancel_download.setObjectName("secondaryButton")
        self.btn_cancel_download.clicked.connect(self._cancel_download)

        # Primary action buttons (Escaped ampersands for clean text)
        self.btn_download = QPushButton("Download && Update")
        self.btn_download.setObjectName("primaryButton")
        self.btn_download.clicked.connect(self._start_download)

        install_text = "Install && Restart" if sys.platform.startswith("win") else (
            "Open Disk Image" if sys.platform == "darwin" else "Open Package"
        )
        self.btn_install = QPushButton(install_text)
        self.btn_install.setObjectName("primaryButton")
        self.btn_install.clicked.connect(self._launch_installer)

        self.btn_close = QPushButton("Close")
        self.btn_close.setObjectName("secondaryButton")
        self.btn_close.clicked.connect(self.close)

        self.button_bar.addWidget(self.btn_releases)
        self.button_bar.addWidget(self.btn_show_folder)
        self.button_bar.addStretch()
        self.button_bar.addWidget(self.btn_retry)
        self.button_bar.addWidget(self.btn_cancel_download)
        self.button_bar.addWidget(self.btn_close)
        self.button_bar.addWidget(self.btn_download)
        self.button_bar.addWidget(self.btn_install)

        main_layout.addLayout(self.button_bar)

        self._set_page(self.PAGE_CHECKING)

    def _set_page(self, page_index: int) -> None:
        """Switch stacked page and toggle button visibility cleanly without takeAt()."""
        self.stack.setCurrentIndex(page_index)

        # Reset all button visibilities
        self.btn_releases.hide()
        self.btn_show_folder.hide()
        self.btn_retry.hide()
        self.btn_cancel_download.hide()
        self.btn_download.hide()
        self.btn_install.hide()
        self.btn_close.hide()

        if page_index == self.PAGE_CHECKING:
            self.btn_close.setText("Cancel")
            self.btn_close.show()

        elif page_index == self.PAGE_UP_TO_DATE:
            self.btn_releases.show()
            self.btn_close.setText("OK")
            self.btn_close.show()
            self.btn_close.setFocus()

        elif page_index == self.PAGE_UPDATE_AVAILABLE:
            if self.current_release_info and self.current_release_info.asset:
                self.btn_download.show()
                self.btn_download.setFocus()
            else:
                self.btn_releases.show()
                self.btn_releases.setFocus()
            self.btn_close.setText("Later")
            self.btn_close.show()

        elif page_index == self.PAGE_DOWNLOADING:
            self.btn_cancel_download.show()

        elif page_index == self.PAGE_READY:
            self.btn_show_folder.show()
            self.btn_install.show()
            self.btn_install.setFocus()
            self.btn_close.setText("Close")
            self.btn_close.show()

        elif page_index == self.PAGE_ERROR:
            self.btn_releases.show()
            self.btn_retry.show()
            self.btn_close.setText("Close")
            self.btn_close.show()

    def start_check(self) -> None:
        """Trigger background update check."""
        self._set_page(self.PAGE_CHECKING)

        if self._check_worker is not None and self._check_worker.isRunning():
            return

        self._check_worker = CheckUpdateWorker(self.repo, self.current_version, parent=self)
        self._check_worker.finished.connect(self._on_check_finished)
        self._check_worker.error.connect(self._on_check_error)
        self._check_worker.start()

    def _on_check_finished(self, info: ReleaseInfo) -> None:
        self.current_release_info = info

        if info.is_newer:
            # Update is available!
            self.v_compare_label.setText(
                f"Current: <b>v{self.current_version}</b>  ➔  New: <b style='color:#a78bfa;'>v{info.version}</b>"
            )

            if info.asset:
                self.asset_info_label.setText(
                    f"📦 Package: <b>{info.asset.name}</b> ({info.asset.formatted_size})"
                )
            else:
                self.asset_info_label.setText(
                    "⚠️ Direct download package not matched for this platform. Please download from GitHub Releases."
                )

            # Rich Markdown rendering for release notes
            self.changelog_browser.setMarkdown(info.body)
            self._set_page(self.PAGE_UPDATE_AVAILABLE)

            # In silent mode, show dialog now that an actual update is found
            if self.silent_mode:
                self.show()
                self.raise_()
                self.activateWindow()

        else:
            # Up to date
            self.utd_desc.setText(
                f"{APP_NAME} v{self.current_version} is currently the newest available release."
            )
            self._set_page(self.PAGE_UP_TO_DATE)
            if self.silent_mode:
                # Stay completely quiet if silent mode and up to date
                self.close()

    def _on_check_error(self, err_msg: str) -> None:
        self.err_message_label.setText(err_msg)
        self._set_page(self.PAGE_ERROR)
        if self.silent_mode:
            # Stay completely quiet on error during background check
            self.close()

    def _start_download(self) -> None:
        if not self.current_release_info or not self.current_release_info.asset:
            return

        asset = self.current_release_info.asset
        dest_path = get_default_download_path(asset.name)

        self.dl_status_label.setText(f"Downloading {asset.name}…")
        self.dl_progress.setValue(0)
        self.dl_stats_label.setText("Starting download…")
        self._set_page(self.PAGE_DOWNLOADING)

        self._download_worker = DownloadUpdateWorker(asset.download_url, dest_path, parent=self)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)
        self._download_worker.cancelled.connect(self._on_download_cancelled)
        self._download_worker.start()

    def _on_download_progress(self, downloaded: int, total: int, percent: float) -> None:
        if total > 0:
            self.dl_progress.setValue(int(percent))
            dl_mb = downloaded / (1024 * 1024)
            tot_mb = total / (1024 * 1024)
            self.dl_stats_label.setText(f"{dl_mb:.1f} MB / {tot_mb:.1f} MB ({percent:.1f}%)")
        else:
            self.dl_progress.setRange(0, 0)
            dl_mb = downloaded / (1024 * 1024)
            self.dl_stats_label.setText(f"{dl_mb:.1f} MB downloaded")

    def _on_download_finished(self, file_path: str) -> None:
        self.downloaded_file_path = file_path
        self.rdy_path_label.setText(f"Saved to: <br><code>{file_path}</code>")
        self._set_page(self.PAGE_READY)

    def _on_download_error(self, err_msg: str) -> None:
        self.err_message_label.setText(f"Download failed: {err_msg}")
        self._set_page(self.PAGE_ERROR)

    def _cancel_download(self) -> None:
        if self._download_worker is not None and self._download_worker.isRunning():
            self._download_worker.cancel()
        else:
            self._set_page(self.PAGE_UPDATE_AVAILABLE)

    def _on_download_cancelled(self) -> None:
        self._set_page(self.PAGE_UPDATE_AVAILABLE)

    def _launch_installer(self) -> None:
        """1-Click launch of downloaded installer package."""
        if not self.downloaded_file_path:
            return

        path = self.downloaded_file_path

        try:
            if sys.platform.startswith("win"):
                # Run the Windows setup wizard and quit app
                subprocess.Popen([path], shell=True)
                app = QApplication.instance()
                if app:
                    app.quit()
            elif sys.platform == "darwin":
                # Mount the DMG
                subprocess.Popen(["open", path])
                self.accept()
            else:
                subprocess.Popen(["xdg-open", path])
                self.accept()
        except Exception as exc:
            self.err_message_label.setText(f"Failed to launch installer: {exc}")
            self._set_page(self.PAGE_ERROR)

    def _show_download_folder(self) -> None:
        """Reveal downloaded file in system file manager."""
        if not self.downloaded_file_path:
            return

        target = Path(self.downloaded_file_path).resolve()
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(target)])
            elif sys.platform.startswith("win"):
                subprocess.Popen(f'explorer /select,"{target}"', shell=True)
            else:
                subprocess.Popen(["xdg-open", str(target.parent)])
        except Exception as exc:
            print(f"Error opening folder: {exc}", file=sys.stderr)

    def _open_github_releases(self) -> None:
        url = (
            self.current_release_info.html_url
            if self.current_release_info
            else f"https://github.com/{self.repo}/releases"
        )
        QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event) -> None:
        """Cancel ongoing workers when the dialog is closed."""
        if self._download_worker is not None and self._download_worker.isRunning():
            self._download_worker.cancel()
            self._download_worker.wait(1000)
        if self._check_worker is not None and self._check_worker.isRunning():
            self._check_worker.wait(1000)
        super().closeEvent(event)

    def _apply_dialog_theme(self) -> None:
        """Apply modern, cohesive theme matching Pa-O Typing Tutor aesthetics."""
        self.setStyleSheet("""
            QDialog {
                background: #090f1d;
                color: #e6edf7;
            }
            QLabel {
                color: #e6edf7;
                background: transparent;
            }
            #dialogTitle {
                font-size: 19px;
                font-weight: 800;
                color: #f8fafc;
            }
            #subText {
                font-size: 13px;
                color: #94a3b8;
                line-height: 1.4;
            }
            #sectionHeader {
                font-size: 13px;
                font-weight: 700;
                color: #c4b5fd;
            }
            #compareLabel {
                font-size: 15px;
                color: #e2e8f0;
            }
            #assetInfoLabel {
                font-size: 13px;
                color: #94a3b8;
            }
            #dlStatsLabel {
                font-size: 12px;
                font-weight: 600;
                color: #94a3b8;
            }
            #readyPathLabel {
                font-size: 12px;
                color: #94a3b8;
            }
            #readyPathLabel code {
                color: #a78bfa;
            }

            /* Badges */
            #successBadge {
                background: #064e3b;
                color: #34d399;
                border: 1px solid #059669;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            #accentBadge {
                background: #2e1065;
                color: #c084fc;
                border: 1px solid #7c3aed;
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.8px;
            }
            #errorBadge {
                background: #450a0a;
                color: #f87171;
                border: 1px solid #dc2626;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 800;
            }

            /* Cards with specific IDs to prevent child label inheritance */
            QFrame#upToDateCard, QFrame#versionCard, QFrame#readyCard, QFrame#errorCard {
                background: #111a2b;
                border: 1px solid #1d2b42;
                border-radius: 12px;
            }
            QFrame#errorCard {
                border-color: #3b1822;
                background: #181119;
            }

            /* Rich Markdown changelog */
            #changelogBrowser {
                background: #0c1424;
                border: 1px solid #1d2b42;
                border-radius: 10px;
                padding: 12px;
                color: #cbd5e1;
                font-size: 13px;
                line-height: 1.5;
            }

            /* Progress Bar */
            QProgressBar {
                background: #131d2e;
                border: 1px solid #23334d;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 3px;
            }

            /* Buttons */
            #primaryButton {
                background: #6d5ce7;
                color: #ffffff;
                border: 0;
                border-radius: 10px;
                padding: 9px 18px;
                font-weight: 700;
                font-size: 13px;
                min-height: 20px;
            }
            #primaryButton:hover {
                background: #7c6df2;
            }
            #primaryButton:pressed {
                background: #5b4bc9;
            }
            #secondaryButton {
                background: #151f31;
                color: #d9e2ef;
                border: 1px solid #2b3a52;
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                min-height: 20px;
            }
            #secondaryButton:hover {
                background: #1c2940;
                border-color: #647d9f;
            }

            /* Clean Scrollbar styling */
            QScrollBar:vertical {
                background: #090f1d;
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2a3a52;
                border-radius: 4px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a5e7b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
