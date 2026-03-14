"""파티클 이펙트 시스템 — 스파클, 컨페티"""
import random
import math
from typing import List, Tuple, Optional
import pygame
from game.constants import PARTICLE_GRAVITY, COLOR_CONFETTI, COLOR_SPARKLE


class Particle:
    """단일 파티클"""
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'life', 'max_life', 'size')

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 color: Tuple[int, int, int], life: float, size: float) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size


class ParticleSystem:
    """파티클 매니저 — 방출, 업데이트, 렌더링"""

    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def emit(self, x: float, y: float, count: int,
             colors: List[Tuple[int, int, int]],
             speed_range: Tuple[float, float] = (20, 80),
             life_range: Tuple[float, float] = (0.5, 1.5),
             size_range: Tuple[float, float] = (2, 5),
             gravity: bool = True) -> None:
        """파티클을 방출"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(speed_range[0], speed_range[1])
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            if gravity:
                vy = -abs(vy)  # 위로 발사
            color = random.choice(colors)
            life = random.uniform(life_range[0], life_range[1])
            size = random.uniform(size_range[0], size_range[1])
            self.particles.append(Particle(x, y, vx, vy, color, life, size))

    def emit_sparkle(self, x: float, y: float) -> None:
        """목표 도착 시 금색 스파클"""
        self.emit(x, y, 6, [COLOR_SPARKLE, (255, 200, 50), (255, 255, 150)],
                  speed_range=(15, 50), life_range=(0.3, 0.6),
                  size_range=(2, 4), gravity=False)

    def emit_confetti(self, screen_width: int) -> None:
        """클리어 시 컨페티 — 화면 상단에서 떨어짐"""
        for _ in range(80):
            x = random.uniform(0, screen_width)
            y = random.uniform(-20, 0)
            vx = random.uniform(-30, 30)
            vy = random.uniform(50, 150)
            color = random.choice(COLOR_CONFETTI)
            life = random.uniform(1.5, 2.5)
            size = random.uniform(3, 6)
            self.particles.append(Particle(x, y, vx, vy, color, life, size))

    def update(self, dt: float) -> None:
        """파티클 물리 업데이트"""
        alive: List[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += PARTICLE_GRAVITY * dt  # 중력
            alive.append(p)
        self.particles = alive

    def draw(self, screen: pygame.Surface) -> None:
        """파티클 렌더링"""
        for p in self.particles:
            alpha = max(0, min(255, int((p.life / p.max_life) * 255)))
            r, g, b = p.color
            # alpha를 밝기로 근사 (pygame에서 개별 파티클 alpha는 비용이 크므로)
            color = (r * alpha // 255, g * alpha // 255, b * alpha // 255)
            size = max(1, int(p.size * (p.life / p.max_life)))
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), size)

    def clear(self) -> None:
        """모든 파티클 제거"""
        self.particles.clear()

    @property
    def active(self) -> bool:
        """활성 파티클이 있는지"""
        return len(self.particles) > 0
