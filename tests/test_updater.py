"""Unit tests for the updater logic, version parsing, asset matching, and GitHub API integration."""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from core.updater import (
    ReleaseAsset,
    ReleaseInfo,
    fetch_latest_release,
    find_platform_asset,
    get_default_download_path,
    is_newer_version,
    parse_version,
)


class TestVersionParsing(unittest.TestCase):
    """Test semver parsing across diverse version string formats."""

    def test_standard_versions(self) -> None:
        self.assertEqual(parse_version("v1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("2.10.5"), (2, 10, 5))

    def test_short_versions(self) -> None:
        self.assertEqual(parse_version("v2.1"), (2, 1, 0))
        self.assertEqual(parse_version("3"), (3, 0, 0))

    def test_prerelease_and_metadata(self) -> None:
        self.assertEqual(parse_version("1.0.0-rc1"), (1, 0, 0))
        self.assertEqual(parse_version("v2.1.0-beta.2"), (2, 1, 0))
        self.assertEqual(parse_version("1.4.2+build.99"), (1, 4, 2))

    def test_edge_cases(self) -> None:
        self.assertEqual(parse_version(""), (0, 0, 0))
        self.assertEqual(parse_version("invalid"), (0, 0, 0))
        self.assertEqual(parse_version("  v1.5.0  "), (1, 5, 0))


class TestVersionComparison(unittest.TestCase):
    """Test strict semver comparison for determining if an update is available."""

    def test_newer_versions(self) -> None:
        self.assertTrue(is_newer_version("v1.0.1", "1.0.0"))
        self.assertTrue(is_newer_version("1.1.0", "v1.0.9"))
        self.assertTrue(is_newer_version("v2.0.0", "1.99.99"))
        self.assertTrue(is_newer_version("v2.1", "2.0.5"))

    def test_same_or_older_versions(self) -> None:
        self.assertFalse(is_newer_version("v1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "v1.0.1"))
        self.assertFalse(is_newer_version("0.9.9", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0-rc1", "1.0.0"))


class TestPlatformAssetMatching(unittest.TestCase):
    """Test matching the appropriate binary asset based on operating system."""

    def setUp(self) -> None:
        self.sample_assets = [
            {
                "name": "Pa-O-Typing-Tutor-v1.1.0-macos.dmg",
                "browser_download_url": "https://example.com/macos.dmg",
                "size": 52428800,
                "content_type": "application/x-apple-diskimage",
            },
            {
                "name": "Pa-O-Typing-Tutor-v1.1.0-windows-setup.exe",
                "browser_download_url": "https://example.com/setup.exe",
                "size": 48234496,
                "content_type": "application/vnd.microsoft.portable-executable",
            },
            {
                "name": "Pa-O-Typing-Tutor-v1.1.0-linux.AppImage",
                "browser_download_url": "https://example.com/linux.AppImage",
                "size": 62914560,
                "content_type": "application/x-executable",
            },
            {
                "name": "SHA256SUMS.txt",
                "browser_download_url": "https://example.com/sha256.txt",
                "size": 512,
                "content_type": "text/plain",
            },
        ]

    def test_macos_match(self) -> None:
        asset = find_platform_asset(self.sample_assets, platform="darwin")
        self.assertIsNotNone(asset)
        assert asset is not None
        self.assertTrue(asset.name.endswith(".dmg"))
        self.assertEqual(asset.download_url, "https://example.com/macos.dmg")
        self.assertAlmostEqual(asset.size_mb, 50.0, places=1)

    def test_windows_match(self) -> None:
        asset = find_platform_asset(self.sample_assets, platform="win32")
        self.assertIsNotNone(asset)
        assert asset is not None
        self.assertTrue(asset.name.endswith(".exe"))
        self.assertEqual(asset.download_url, "https://example.com/setup.exe")

    def test_linux_match(self) -> None:
        asset = find_platform_asset(self.sample_assets, platform="linux")
        self.assertIsNotNone(asset)
        assert asset is not None
        self.assertTrue(asset.name.endswith(".AppImage"))
        self.assertEqual(asset.download_url, "https://example.com/linux.AppImage")

    def test_empty_or_no_match(self) -> None:
        self.assertIsNone(find_platform_asset([], platform="darwin"))
        checksum_only = [{"name": "checksums.txt", "browser_download_url": "url", "size": 10}]
        self.assertIsNone(find_platform_asset(checksum_only, platform="win32"))


class TestFetchLatestRelease(unittest.TestCase):
    """Test GitHub API release query handling and error modes."""

    @patch("urllib.request.urlopen")
    def test_fetch_success_update_available(self, mock_urlopen: MagicMock) -> None:
        mock_payload = {
            "tag_name": "v1.1.0",
            "body": "## What's Changed\n* Added audio effects\n* Fixed UI layout",
            "html_url": "https://github.com/khunaungpaing/PaO-Typing-Tutor/releases/tag/v1.1.0",
            "assets": [
                {
                    "name": "Pa-O-Typing-Tutor-v1.1.0-macos.dmg",
                    "browser_download_url": "https://example.com/macos.dmg",
                    "size": 52428800,
                }
            ],
            "published_at": "2026-09-28T12:00:00Z",
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = fetch_latest_release(
            repo="khunaungpaing/PaO-Typing-Tutor",
            current_version="1.0.0",
            timeout=5.0,
        )

        self.assertEqual(info.tag_name, "v1.1.0")
        self.assertEqual(info.version, "1.1.0")
        self.assertTrue(info.is_newer)
        self.assertIn("Added audio effects", info.body)

    @patch("urllib.request.urlopen")
    def test_fetch_success_up_to_date(self, mock_urlopen: MagicMock) -> None:
        mock_payload = {
            "tag_name": "v1.0.0",
            "body": "Initial release",
            "html_url": "https://github.com/khunaungpaing/PaO-Typing-Tutor/releases/tag/v1.0.0",
            "assets": [],
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = fetch_latest_release(
            repo="khunaungpaing/PaO-Typing-Tutor",
            current_version="1.0.0",
            timeout=5.0,
        )

        self.assertFalse(info.is_newer)

    @patch("urllib.request.urlopen")
    def test_fetch_http_404_no_releases(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/repos/dummy/repo/releases/latest",
            code=404,
            msg="Not Found",
            hdrs=None,  # type: ignore
            fp=io.BytesIO(b""),
        )

        with self.assertRaises(RuntimeError) as ctx:
            fetch_latest_release("dummy/repo", "1.0.0")
        self.assertIn("No published releases found", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_fetch_http_403_rate_limit(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.github.com/repos/dummy/repo/releases/latest",
            code=403,
            msg="Forbidden",
            hdrs=None,  # type: ignore
            fp=io.BytesIO(b""),
        )

        with self.assertRaises(RuntimeError) as ctx:
            fetch_latest_release("dummy/repo", "1.0.0")
        self.assertIn("rate limit exceeded", str(ctx.exception))


class TestDownloadPath(unittest.TestCase):
    """Test resolution of default download destination path."""

    def test_download_path(self) -> None:
        path = get_default_download_path("Pa-O-Typing-Tutor-v1.0.0.dmg")
        self.assertEqual(path.name, "Pa-O-Typing-Tutor-v1.0.0.dmg")
        self.assertTrue(path.parent.is_dir())


if __name__ == "__main__":
    unittest.main()
