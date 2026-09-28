"""Unit tests for background QThread workers."""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QCoreApplication

from core.updater import ReleaseInfo
from workers.update_worker import CheckUpdateWorker, DownloadUpdateWorker


class TestUpdateWorkers(unittest.TestCase):
    """Test background QThread worker behavior and signal emissions."""

    @classmethod
    def setUpClass(cls) -> None:
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    @patch("workers.update_worker.fetch_latest_release")
    def test_check_worker_success(self, mock_fetch: MagicMock) -> None:
        mock_info = ReleaseInfo(
            tag_name="v1.1.0",
            version="1.1.0",
            body="Changelog",
            html_url="https://example.com",
            asset=None,
            is_newer=True,
        )
        mock_fetch.return_value = mock_info

        worker = CheckUpdateWorker("khunaungpaing/PaO-Typing-Tutor", "1.0.0")

        results = []
        errors = []
        worker.finished.connect(results.append)
        worker.error.connect(errors.append)

        # Run synchronously for test
        worker.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].tag_name, "v1.1.0")
        self.assertEqual(len(errors), 0)

    @patch("workers.update_worker.fetch_latest_release")
    def test_check_worker_error(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = RuntimeError("Network timeout")

        worker = CheckUpdateWorker("khunaungpaing/PaO-Typing-Tutor", "1.0.0")

        results = []
        errors = []
        worker.finished.connect(results.append)
        worker.error.connect(errors.append)

        worker.run()

        self.assertEqual(len(results), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("Network timeout", errors[0])

    @patch("urllib.request.urlopen")
    def test_download_worker_success(self, mock_urlopen: MagicMock) -> None:
        content = b"Mock installer payload data 12345"
        mock_resp = MagicMock()
        mock_resp.read.side_effect = [content, b""]
        mock_resp.headers = {"Content-Length": str(len(content))}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "test_installer.dmg"
            worker = DownloadUpdateWorker("https://example.com/asset.dmg", dest)

            progress_reports = []
            finished_paths = []
            worker.progress.connect(lambda d, t, p: progress_reports.append((d, t, p)))
            worker.finished.connect(finished_paths.append)

            worker.run()

            self.assertEqual(len(finished_paths), 1)
            self.assertEqual(finished_paths[0], str(dest))
            self.assertTrue(dest.exists())
            self.assertEqual(dest.read_bytes(), content)
            self.assertTrue(len(progress_reports) >= 1)

    @patch("urllib.request.urlopen")
    def test_download_worker_cancel(self, mock_urlopen: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.read.side_effect = [b"Chunk1", b"Chunk2", b"Chunk3"]
        mock_resp.headers = {"Content-Length": "100"}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "cancelled_installer.dmg"
            worker = DownloadUpdateWorker("https://example.com/asset.dmg", dest)

            cancelled_events = []
            worker.cancelled.connect(lambda: cancelled_events.append(True))

            # Simulate cancellation immediately
            worker.cancel()
            worker.run()

            self.assertEqual(len(cancelled_events), 1)
            # Ensure partial file was cleaned up
            self.assertFalse(dest.exists())
            part_path = dest.with_suffix(dest.suffix + ".part")
            self.assertFalse(part_path.exists())


if __name__ == "__main__":
    unittest.main()
