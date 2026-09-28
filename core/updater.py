"""Core update checking and release asset resolution for GitHub Releases."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ReleaseAsset:
    """Represents a downloadable binary package attached to a GitHub Release."""
    name: str
    download_url: str
    size: int  # in bytes
    content_type: str = ""

    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)

    @property
    def formatted_size(self) -> str:
        if self.size <= 0:
            return "Unknown size"
        if self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size_mb:.1f} MB"


@dataclass
class ReleaseInfo:
    """Information about the latest remote release queried from GitHub."""
    tag_name: str
    version: str
    body: str
    html_url: str
    asset: Optional[ReleaseAsset]
    is_newer: bool
    published_at: str = ""


def parse_version(v: str) -> tuple[int, ...]:
    """Parse version string into a tuple of integers for semver comparison.

    Handles 'v1.0.0', '1.2.3', 'v2.1', '1.0.0-rc1', etc.
    """
    if not v:
        return (0, 0, 0)
    clean = str(v).strip().lstrip("vV")
    # Take the portion before any prerelease/build metadata separated by '-' or '+'
    main_part = re.split(r"[-+]", clean)[0]
    digits = re.findall(r"\d+", main_part)
    if not digits:
        return (0, 0, 0)
    nums = [int(d) for d in digits]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def is_newer_version(remote: str, local: str) -> bool:
    """Strict semver comparison returning True if remote > local."""
    r_parts = list(parse_version(remote))
    l_parts = list(parse_version(local))
    max_len = max(len(r_parts), len(l_parts), 3)
    r_parts.extend([0] * (max_len - len(r_parts)))
    l_parts.extend([0] * (max_len - len(l_parts)))
    return tuple(r_parts) > tuple(l_parts)


def find_platform_asset(assets: list[dict], platform: str = sys.platform) -> ReleaseAsset | None:
    """Match the most appropriate binary package for the current OS platform."""
    if not assets:
        return None

    best_score = -1
    best_asset: dict | None = None

    for item in assets:
        name = str(item.get("name", "")).strip()
        lower_name = name.lower()
        score = -1

        if platform == "darwin":
            if lower_name.endswith(".dmg"):
                score = 100 if any(k in lower_name for k in ("macos", "mac", "darwin", "apple")) else 80
            elif lower_name.endswith(".zip") and any(k in lower_name for k in ("macos", "mac", "darwin")):
                score = 60
            elif lower_name.endswith(".pkg"):
                score = 50
        elif platform == "win32":
            if lower_name.endswith(".exe"):
                if any(k in lower_name for k in ("setup", "installer")):
                    score = 100
                elif any(k in lower_name for k in ("windows", "win")):
                    score = 90
                else:
                    score = 80
            elif lower_name.endswith(".msi"):
                score = 70
            elif lower_name.endswith(".zip") and any(k in lower_name for k in ("windows", "win")):
                score = 60
        else:  # Linux and other POSIX
            if lower_name.endswith(".appimage"):
                score = 100
            elif lower_name.endswith(".deb"):
                score = 90
            elif lower_name.endswith(".rpm"):
                score = 85
            elif lower_name.endswith(".tar.gz") or lower_name.endswith(".tgz"):
                score = 80 if "linux" in lower_name else 60
            elif lower_name.endswith(".zip") and "linux" in lower_name:
                score = 50

        if score > best_score:
            best_score = score
            best_asset = item

    if best_asset and best_score > 0:
        return ReleaseAsset(
            name=str(best_asset.get("name", "")),
            download_url=str(best_asset.get("browser_download_url", "")),
            size=int(best_asset.get("size", 0)),
            content_type=str(best_asset.get("content_type", "")),
        )
    return None


def fetch_latest_release(repo: str, current_version: str, timeout: float = 10.0) -> ReleaseInfo:
    """Query the GitHub Releases API for the latest release."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"Pa-O-Typing-Tutor/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            data = json.loads(payload)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError(f"No published releases found for repository '{repo}'.") from exc
        if exc.code == 403:
            raise RuntimeError("GitHub API rate limit exceeded. Please try again later.") from exc
        raise RuntimeError(f"GitHub API returned error HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network connection failed: {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to check for updates: {exc}") from exc

    tag_name = str(data.get("tag_name", "")).strip()
    version = tag_name.lstrip("vV")
    body = str(data.get("body", "")).strip() or "No release notes provided."
    html_url = str(data.get("html_url", f"https://github.com/{repo}/releases/latest"))
    raw_assets = data.get("assets", [])
    matched_asset = find_platform_asset(raw_assets, sys.platform)
    is_newer = is_newer_version(tag_name, current_version)
    published_at = str(data.get("published_at", ""))

    return ReleaseInfo(
        tag_name=tag_name,
        version=version,
        body=body,
        html_url=html_url,
        asset=matched_asset,
        is_newer=is_newer,
        published_at=published_at,
    )


def get_default_download_path(filename: str) -> Path:
    """Save to user's ~/Downloads folder by default, fallback to temp directory."""
    try:
        downloads = Path.home() / "Downloads"
        if downloads.is_dir() and os.access(downloads, os.W_OK):
            return downloads / filename
    except Exception:
        pass
    return Path(tempfile.gettempdir()) / filename
