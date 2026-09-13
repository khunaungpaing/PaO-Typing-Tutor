"""Small generated UI sounds with volume and mute controls."""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path

from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QUrl
from PyQt6.QtMultimedia import (
    QAudioFormat, QAudioOutput, QAudioSink, QMediaDevices, QMediaPlayer, QtAudio,
)


class SoundManager:
    """Play short synthesized sounds without requiring external audio assets."""

    def __init__(self, sounds_directory: Path | None = None) -> None:
        self.volume = 0.45
        self.muted = False
        self._active: list[tuple[QAudioSink, QBuffer]] = []
        self._media: list[tuple[QMediaPlayer, QAudioOutput]] = []
        self.sounds_directory = sounds_directory
        self.custom_sounds = self._load_manifest()

    def _load_manifest(self) -> dict[str, Path]:
        if self.sounds_directory is None:
            return {}
        manifest = self.sounds_directory / "sounds.json"
        try:
            entries = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        sounds: dict[str, Path] = {}
        for event in ("correct", "incorrect", "complete"):
            filename = entries.get(event)
            if isinstance(filename, str):
                path = self.sounds_directory / filename
                if path.is_file():
                    sounds[event] = path
        return sounds

    def set_volume(self, value: int) -> None:
        self.volume = max(0.0, min(1.0, value / 100.0))

    def set_muted(self, muted: bool) -> None:
        self.muted = muted

    def play_key(self, correct: bool) -> None:
        event = "correct" if correct else "incorrect"
        if not self._play_file(event):
            self._play(720 if correct else 190, 35 if correct else 90)

    def play_complete(self) -> None:
        if not self._play_file("complete"):
            self._play(990, 180)

    def _play_file(self, event: str) -> bool:
        path = self.custom_sounds.get(event)
        if path is None:
            return False
        if self.muted or self.volume <= 0:
            return True
        output = QAudioOutput()
        output.setVolume(self.volume)
        player = QMediaPlayer()
        player.setAudioOutput(output)
        player.setSource(QUrl.fromLocalFile(str(path)))
        pair = (player, output)
        self._media.append(pair)
        player.mediaStatusChanged.connect(
            lambda status, item=pair: self._release_media(status, item)
        )
        player.play()
        return True

    def _release_media(self, status: QMediaPlayer.MediaStatus,
                       pair: tuple[QMediaPlayer, QAudioOutput]) -> None:
        if status in (QMediaPlayer.MediaStatus.EndOfMedia,
                      QMediaPlayer.MediaStatus.InvalidMedia) and pair in self._media:
            self._media.remove(pair)

    def _play(self, frequency: int, duration_ms: int) -> None:
        if self.muted or self.volume <= 0:
            return
        rate = 22050
        samples = int(rate * duration_ms / 1000)
        pcm = bytearray()
        for index in range(samples):
            fade = 1.0 - index / samples
            value = int(10000 * fade * math.sin(2 * math.pi * frequency * index / rate))
            pcm.extend(struct.pack("<h", value))
        audio_format = QAudioFormat()
        audio_format.setSampleRate(rate)
        audio_format.setChannelCount(1)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        sink = QAudioSink(QMediaDevices.defaultAudioOutput(), audio_format)
        sink.setVolume(self.volume)
        buffer = QBuffer()
        buffer.setData(QByteArray(bytes(pcm)))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self._active.append((sink, buffer))
        sink.stateChanged.connect(lambda _state, pair=(sink, buffer): self._release(pair))
        sink.start(buffer)

    def _release(self, pair: tuple[QAudioSink, QBuffer]) -> None:
        if pair[0].state() == QtAudio.State.IdleState and pair in self._active:
            self._active.remove(pair)
