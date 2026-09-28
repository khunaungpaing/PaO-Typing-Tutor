"""Background QThread workers for non-blocking update checking and file streaming."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.updater import ReleaseInfo, fetch_latest_release

CHUNK_SIZE = 65536  # 64 KB streaming chunk size


class CheckUpdateWorker(QThread):
    """Fetches the latest GitHub Release in the background without freezing the UI."""

    finished = pyqtSignal(object)  # Emits ReleaseInfo
    error = pyqtSignal(str)        # Emits error message

    def __init__(self, repo: str, current_version: str, timeout: float = 10.0, parent=None) -> None:
        super().__init__(parent)
        self.repo = repo
        self.current_version = current_version
        self.timeout = timeout

    def run(self) -> None:
        try:
            info = fetch_latest_release(self.repo, self.current_version, self.timeout)
            self.finished.emit(info)
        except Exception as exc:
            self.error.emit(str(exc))


class DownloadUpdateWorker(QThread):
    """Streams asset download in 64 KB chunks with cancel and progress reporting."""

    progress = pyqtSignal(int, int, float)  # downloaded_bytes, total_bytes, percent
    finished = pyqtSignal(str)              # downloaded file path
    error = pyqtSignal(str)                 # error message
    cancelled = pyqtSignal()                # emitted on cooperative cancel

    def __init__(
        self,
        url: str,
        destination: Path,
        user_agent: str = "Pa-O-Typing-Tutor-Updater",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.url = url
        self.destination = Path(destination)
        self.user_agent = user_agent
        self._is_cancelled = False

    def cancel(self) -> None:
        """Cooperatively request thread cancellation."""
        self._is_cancelled = True

    def run(self) -> None:
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        part_path = self.destination.with_suffix(self.destination.suffix + ".part")

        req = urllib.request.Request(
            self.url,
            headers={"User-Agent": self.user_agent},
        )

        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                total_bytes = int(response.headers.get("Content-Length", 0))
                downloaded = 0

                with open(part_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if part_path.exists():
                                try:
                                    part_path.unlink()
                                except OSError:
                                    pass
                            self.cancelled.emit()
                            return

                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        percent = (downloaded / total_bytes * 100.0) if total_bytes > 0 else -1.0
                        self.progress.emit(downloaded, total_bytes, percent)

            # Atomic rename from .part to target filename upon success
            if part_path.exists():
                os.replace(part_path, self.destination)
                self.finished.emit(str(self.destination))
            else:
                self.error.emit("Downloaded file was unexpectedly removed.")

        except urllib.error.URLError as exc:
            self._cleanup_part(part_path)
            if not self._is_cancelled:
                self.error.emit(f"Download connection error: {exc.reason}")
        except Exception as exc:
            self._cleanup_part(part_path)
            if not self._is_cancelled:
                self.error.emit(f"Download failed: {exc}")

    def _cleanup_part(self, part_path: Path) -> None:
        if part_path.exists():
            try:
                part_path.unlink()
            except OSError:
                pass
