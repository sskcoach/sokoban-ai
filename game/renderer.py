"""렌더러 — 타일맵 렌더링, 애니메이션 보간"""
import math
from typing import Tuple, Optional, Dict, Any
import pygame
from game.constants import (
    TILE_SIZE, MOVE_DURATION, PULSE_SPEED,
    COLOR_BG, COLOR_HUD_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_GOAL, COLOR_GOAL_GLOW,
    DEFAULT_WINDOW_SIZE,
)
from game.assets import Assets
from game.engine import GameEngine


class AnimState:
    """이동 애니메이션 상태"""

    def __init__(self) -> None:
        self.moving: bool = False
        self.progress: float = 0.0
        self.player_from: Tuple[int, int] = (0, 0)
        self.player_to: Tuple[int, int] = (0, 0)
        self.box_from: Optional[Tuple[int, int]] = None
        self.box_to: Optional[Tuple[int, int]] = None
        self.direction: Tuple[int, int] = (0, 1)

    def start(self, player_from: Tuple[int, int], player_to: Tuple[int, int],
              direction: Tuple[int, int],
              box_from: Optional[Tuple[int, int]] = None,
              box_to: Optional[Tuple[int, int]] = None) -> None:
        """애니메이션 시작"""
        self.moving = True
        self.progress = 0.0
        self.player_from = player_from
        self.player_to = player_to
        self.direction = direction
        self.box_from = box_from
        self.box_to = box_to

    def update(self, dt: float) -> None:
        """애니메이션 진행"""
        if not self.moving:
            return
        self.progress += dt / MOVE_DURATION
        if self.progress >= 1.0:
            self.progress = 1.0
            self.moving = False

    def get_lerp_pos(self, from_pos: Tuple[int, int],
                     to_pos: Tuple[int, int]) -> Tuple[float, float]:
        """보간된 픽셀 위치 반환"""
        t = self.progress
        # ease out quad
        t = t * (2 - t)
        fx, fy = from_pos
        tx, ty = to_pos
        x = fx + (tx - fx) * t
        y = fy + (ty - fy) * t
        return (x * TILE_SIZE, y * TILE_SIZE)


class Renderer:
    """게임 화면 렌더러"""

    def __init__(self, assets: Assets) -> None:
        self.assets = assets
        self.tick: float = 0.0

    def update(self, dt: float) -> None:
        """틱 업데이트 (펄스 등)"""
        self.tick += dt

    def _calc_offset(self, engine: GameEngine,
                     screen_w: int, screen_h: int,
                     hud_top: int = 40, hud_bottom: int = 30) -> Tuple[int, int]:
        """레벨을 화면 중앙에 배치하기 위한 오프셋 계산"""
        level_w = engine.level.width * TILE_SIZE
        level_h = engine.level.height * TILE_SIZE
        available_h = screen_h - hud_top - hud_bottom
        ox = (screen_w - level_w) // 2
        oy = hud_top + (available_h - level_h) // 2
        return (ox, oy)

    def render_level(self, screen: pygame.Surface, engine: GameEngine,
                     anim: AnimState) -> None:
        """타일맵 + 플레이어 + 박스 렌더링"""
        screen_w, screen_h = screen.get_size()
        ox, oy = self._calc_offset(engine, screen_w, screen_h)
        level = engine.level

        # 바닥과 벽 렌더링
        for y in range(level.height):
            for x in range(level.width):
                px, py_pos = ox + x * TILE_SIZE, oy + y * TILE_SIZE
                pos = (x, y)

                if pos in level.walls:
                    screen.blit(self.assets.tiles["wall"], (px, py_pos))
                else:
                    # 바닥은 항상 그림
                    screen.blit(self.assets.tiles["floor"], (px, py_pos))

                    # 목표 지점 (펄스 효과)
                    if pos in level.goals and pos not in level.boxes:
                        goal_surf = self.assets.tiles["goal"].copy()
                        # 펄스: 밝기 변화
                        pulse = (math.sin(self.tick * PULSE_SPEED) + 1) / 2
                        alpha = int(150 + 105 * pulse)
                        goal_surf.set_alpha(alpha)
                        screen.blit(goal_surf, (px, py_pos))

        # 박스 렌더링 (애니메이션 중인 박스 제외)
        for bx, by in level.boxes:
            # 애니메이션 중인 박스는 별도 처리
            if anim.moving and anim.box_to == (bx, by):
                continue

            px, py_pos = ox + bx * TILE_SIZE, oy + by * TILE_SIZE
            if (bx, by) in level.goals:
                screen.blit(self.assets.tiles["box_on_goal"], (px, py_pos))
            elif engine.is_deadlocked(bx, by):
                screen.blit(self.assets.tiles["box_deadlock"], (px, py_pos))
            else:
                screen.blit(self.assets.tiles["box"], (px, py_pos))

        # 애니메이션 중인 박스
        if anim.moving and anim.box_from is not None and anim.box_to is not None:
            bpx, bpy = anim.get_lerp_pos(anim.box_from, anim.box_to)
            bx_dest, by_dest = anim.box_to
            if (bx_dest, by_dest) in level.goals:
                screen.blit(self.assets.tiles["box_on_goal"],
                            (ox + bpx, oy + bpy))
            else:
                screen.blit(self.assets.tiles["box"], (ox + bpx, oy + bpy))

        # 플레이어 렌더링
        direction = engine.last_direction
        dir_name = {(0, -1): "up", (0, 1): "down",
                    (-1, 0): "left", (1, 0): "right"}.get(direction, "down")

        if anim.moving:
            ppx, ppy = anim.get_lerp_pos(anim.player_from, anim.player_to)
            # 걷기 프레임 (애니메이션 중)
            frame_idx = 1 if anim.progress < 0.5 else 0
            player_surf = self.assets.player[dir_name][frame_idx]
            screen.blit(player_surf, (ox + ppx, oy + ppy))
        else:
            ppx = level.player[0] * TILE_SIZE
            ppy = level.player[1] * TILE_SIZE
            player_surf = self.assets.player[dir_name][0]
            screen.blit(player_surf, (ox + ppx, oy + ppy))

    def render_hud(self, screen: pygame.Surface, engine: GameEngine,
                   level_info: dict) -> None:
        """상단 HUD 렌더링"""
        screen_w = screen.get_width()
        font = pygame.font.SysFont(None, 28)

        # 상단 배경
        pygame.draw.rect(screen, COLOR_HUD_BG, (0, 0, screen_w, 40))

        # 레벨 이름
        name_text = font.render(f"Level: {level_info.get('name', '?')}", True, COLOR_TEXT)
        screen.blit(name_text, (10, 8))

        # 이동 횟수
        moves_text = font.render(f"Moves: {engine.move_count}", True, COLOR_TEXT)
        screen.blit(moves_text, (screen_w // 4, 8))

        # 경과 시간
        mins = int(engine.elapsed_time) // 60
        secs = int(engine.elapsed_time) % 60
        time_text = font.render(f"Time: {mins:02d}:{secs:02d}", True, COLOR_TEXT)
        screen.blit(time_text, (screen_w // 2, 8))

        # Par
        par_text = font.render(f"Par: {level_info.get('par', '?')}", True, COLOR_TEXT_DIM)
        screen.blit(par_text, (screen_w * 3 // 4, 8))

        # 하단 조작 안내
        screen_h = screen.get_height()
        pygame.draw.rect(screen, COLOR_HUD_BG, (0, screen_h - 30, screen_w, 30))
        help_font = pygame.font.SysFont(None, 22)
        help_text = help_font.render(
            "Arrows/WASD=Move  Z=Undo  Y=Redo  R=Restart  ESC=Pause",
            True, COLOR_TEXT_DIM
        )
        help_rect = help_text.get_rect(center=(screen_w // 2, screen_h - 15))
        screen.blit(help_text, help_rect)
