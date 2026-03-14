"""사운드 매니저 — numpy로 프로시저럴 사운드 생성"""
import math
from typing import Dict, Optional
import pygame

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class SoundManager:
    """프로시저럴 사운드 생성 및 재생"""

    def __init__(self) -> None:
        self.enabled = HAS_NUMPY
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.volume: float = 0.7

        if self.enabled:
            try:
                self._generate_sounds()
            except Exception:
                self.enabled = False

    def _generate_tone(self, frequency: float, duration_ms: int,
                       volume: float = 0.3, sample_rate: int = 22050) -> "np.ndarray":
        """사인파 톤 생성"""
        n_samples = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, False)
        wave = np.sin(2 * np.pi * frequency * t) * volume * 32767
        # fade in/out (5ms)
        fade_samples = min(int(sample_rate * 0.005), n_samples // 2)
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            wave[:fade_samples] *= fade_in
            wave[-fade_samples:] *= fade_out
        return wave.astype(np.int16)

    def _generate_sweep(self, freq_start: float, freq_end: float,
                        duration_ms: int, volume: float = 0.3,
                        sample_rate: int = 22050) -> "np.ndarray":
        """주파수 스윕 생성"""
        n_samples = int(sample_rate * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, n_samples, False)
        freqs = np.linspace(freq_start, freq_end, n_samples)
        phase = np.cumsum(2 * np.pi * freqs / sample_rate)
        wave = np.sin(phase) * volume * 32767
        # fade
        fade_samples = min(int(sample_rate * 0.005), n_samples // 2)
        if fade_samples > 0:
            wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
            wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        return wave.astype(np.int16)

    def _generate_multi_tone(self, freqs: list, tone_ms: int,
                             volume: float = 0.3,
                             sample_rate: int = 22050) -> "np.ndarray":
        """여러 음을 연결한 멜로디 생성"""
        waves = []
        for freq in freqs:
            waves.append(self._generate_tone(freq, tone_ms, volume, sample_rate))
        return np.concatenate(waves)

    def _generate_sounds(self) -> None:
        """모든 게임 사운드를 프로시저럴 생성"""
        # step: 짧은 고주파 탭
        self.sounds["step"] = pygame.sndarray.make_sound(
            self._generate_tone(800, 20, 0.15)
        )
        # push: 저주파 + 약간의 노이즈 느낌
        push_wave = self._generate_tone(200, 50, 0.2)
        noise = (np.random.randn(len(push_wave)) * 1000).astype(np.int16)
        push_wave = np.clip(push_wave + noise, -32767, 32767).astype(np.int16)
        self.sounds["push"] = pygame.sndarray.make_sound(push_wave)

        # goal: 도→미 상승 2음
        self.sounds["goal"] = pygame.sndarray.make_sound(
            self._generate_multi_tone([523, 659], 80, 0.25)
        )
        # clear: 도미솔도 아르페지오
        self.sounds["clear"] = pygame.sndarray.make_sound(
            self._generate_multi_tone([523, 659, 784, 1047], 100, 0.25)
        )
        # undo: 하강 스윕
        self.sounds["undo"] = pygame.sndarray.make_sound(
            self._generate_sweep(600, 300, 50, 0.2)
        )
        # bump: 짧은 저음
        self.sounds["bump"] = pygame.sndarray.make_sound(
            self._generate_tone(150, 30, 0.2)
        )
        # click: UI 클릭
        self.sounds["click"] = pygame.sndarray.make_sound(
            self._generate_tone(1000, 15, 0.15)
        )

    def play(self, name: str) -> None:
        """사운드 재생"""
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(self.volume)
            sound.play()

    def set_volume(self, vol: float) -> None:
        """볼륨 설정 (0.0~1.0)"""
        self.volume = max(0.0, min(1.0, vol))
