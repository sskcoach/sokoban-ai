"""픽셀아트 스프라이트 생성 — pygame.draw 기반, 외부 파일 없음"""
import math
from typing import Dict, List, Tuple
import pygame
from game.constants import (
    TILE_SIZE,
    COLOR_WALL_BASE, COLOR_WALL_LIGHT, COLOR_WALL_DARK, COLOR_WALL_BRICK_LINE,
    COLOR_FLOOR, COLOR_FLOOR_LINE,
    COLOR_GOAL, COLOR_GOAL_GLOW,
    COLOR_BOX_BASE, COLOR_BOX_LIGHT, COLOR_BOX_DARK, COLOR_BOX_ON_GOAL, COLOR_BOX_DEADLOCK,
    COLOR_PLAYER_BODY, COLOR_PLAYER_LIGHT, COLOR_PLAYER_DARK,
    COLOR_PLAYER_EYE, COLOR_PLAYER_PUPIL,
)

T = TILE_SIZE  # 축약


class Assets:
    """게임 스프라이트 모음"""

    def __init__(self) -> None:
        self.tiles: Dict[str, pygame.Surface] = {}
        self.player: Dict[str, List[pygame.Surface]] = {}

    @staticmethod
    def create() -> "Assets":
        """모든 스프라이트를 생성하여 반환"""
        assets = Assets()
        assets.tiles["wall"] = Assets._make_wall()
        assets.tiles["floor"] = Assets._make_floor()
        assets.tiles["goal"] = Assets._make_goal()
        assets.tiles["box"] = Assets._make_box(COLOR_BOX_BASE, COLOR_BOX_LIGHT, COLOR_BOX_DARK)
        assets.tiles["box_on_goal"] = Assets._make_box_on_goal()
        assets.tiles["box_deadlock"] = Assets._make_box_deadlock()

        # 플레이어: 4방향 × [idle, walk]
        for direction in ["up", "down", "left", "right"]:
            idle = Assets._make_player(direction)
            # walk = idle을 y축으로 2px 오프셋
            walk = pygame.Surface((T, T), pygame.SRCALPHA)
            walk.blit(idle, (0, -2))
            assets.player[direction] = [idle, walk]

        return assets

    @staticmethod
    def _make_wall() -> pygame.Surface:
        """벽 타일: 벽돌 패턴 + 3D 느낌"""
        surf = pygame.Surface((T, T))
        surf.fill(COLOR_WALL_BASE)

        # 벽돌 패턴 (2행 × 3열)
        brick_h = T // 3
        brick_w = T // 2
        for row in range(3):
            offset = brick_w // 2 if row % 2 == 1 else 0
            y = row * brick_h
            for col in range(-1, 3):
                x = col * brick_w + offset
                # 벽돌 라인
                pygame.draw.rect(surf, COLOR_WALL_BRICK_LINE,
                                 (x, y, brick_w, brick_h), 1)
                # 벽돌 내부 밝은 부분
                pygame.draw.line(surf, COLOR_WALL_LIGHT,
                                 (x + 2, y + 1), (x + brick_w - 3, y + 1))
                pygame.draw.line(surf, COLOR_WALL_LIGHT,
                                 (x + 1, y + 2), (x + 1, y + brick_h - 3))

        # 상단/좌측 하이라이트
        pygame.draw.line(surf, COLOR_WALL_LIGHT, (0, 0), (T - 1, 0), 2)
        pygame.draw.line(surf, COLOR_WALL_LIGHT, (0, 0), (0, T - 1), 2)
        # 하단/우측 셰도우
        pygame.draw.line(surf, COLOR_WALL_DARK, (0, T - 1), (T - 1, T - 1), 2)
        pygame.draw.line(surf, COLOR_WALL_DARK, (T - 1, 0), (T - 1, T - 1), 2)

        return surf

    @staticmethod
    def _make_floor() -> pygame.Surface:
        """바닥 타일: 베이지 + 그리드"""
        surf = pygame.Surface((T, T))
        surf.fill(COLOR_FLOOR)
        # 격자 라인
        pygame.draw.line(surf, COLOR_FLOOR_LINE, (0, 0), (T, 0))
        pygame.draw.line(surf, COLOR_FLOOR_LINE, (0, 0), (0, T))
        return surf

    @staticmethod
    def _make_goal() -> pygame.Surface:
        """목표 지점: 바닥 위에 빨간 다이아몬드"""
        surf = Assets._make_floor().copy()
        center = T // 2
        size = T // 5
        # 다이아몬드 모양
        points = [
            (center, center - size),
            (center + size, center),
            (center, center + size),
            (center - size, center),
        ]
        pygame.draw.polygon(surf, COLOR_GOAL, points)
        pygame.draw.polygon(surf, COLOR_GOAL_GLOW, points, 2)
        return surf

    @staticmethod
    def _make_box(base: Tuple, light: Tuple, dark: Tuple) -> pygame.Surface:
        """박스: 나무 상자 느낌"""
        surf = pygame.Surface((T, T), pygame.SRCALPHA)
        # 바닥 먼저
        floor = Assets._make_floor()
        surf.blit(floor, (0, 0))

        margin = 3
        box_rect = pygame.Rect(margin, margin, T - margin * 2, T - margin * 2)

        # 본체
        pygame.draw.rect(surf, base, box_rect)
        # 상단 하이라이트
        pygame.draw.rect(surf, light,
                         (margin, margin, box_rect.width, 4))
        # 좌측 하이라이트
        pygame.draw.rect(surf, light,
                         (margin, margin, 4, box_rect.height))
        # 하단 셰도우
        pygame.draw.rect(surf, dark,
                         (margin, T - margin - 4, box_rect.width, 4))
        # 우측 셰도우
        pygame.draw.rect(surf, dark,
                         (T - margin - 4, margin, 4, box_rect.height))
        # 중앙 X 무늬
        cx, cy = T // 2, T // 2
        d = T // 5
        pygame.draw.line(surf, dark, (cx - d, cy - d), (cx + d, cy + d), 2)
        pygame.draw.line(surf, dark, (cx + d, cy - d), (cx - d, cy + d), 2)
        # 테두리
        pygame.draw.rect(surf, dark, box_rect, 2)

        return surf

    @staticmethod
    def _make_box_on_goal() -> pygame.Surface:
        """목표 위의 박스: 초록/금 글로우"""
        surf = Assets._make_box(COLOR_BOX_BASE, COLOR_BOX_LIGHT, COLOR_BOX_DARK)
        margin = 2
        pygame.draw.rect(surf, COLOR_BOX_ON_GOAL,
                         (margin, margin, T - margin * 2, T - margin * 2), 3)
        return surf

    @staticmethod
    def _make_box_deadlock() -> pygame.Surface:
        """데드락 박스: 빨간 테두리"""
        surf = Assets._make_box(COLOR_BOX_BASE, COLOR_BOX_LIGHT, COLOR_BOX_DARK)
        margin = 2
        pygame.draw.rect(surf, COLOR_BOX_DEADLOCK,
                         (margin, margin, T - margin * 2, T - margin * 2), 3)
        return surf

    @staticmethod
    def _make_player(direction: str) -> pygame.Surface:
        """플레이어 캐릭터: 둥근 몸체 + 눈"""
        surf = pygame.Surface((T, T), pygame.SRCALPHA)
        cx, cy = T // 2, T // 2

        # 몸체 (둥근 사각형 근사: 원 + 사각형)
        body_size = T // 2 - 2
        body_rect = pygame.Rect(cx - body_size, cy - body_size,
                                body_size * 2, body_size * 2)
        pygame.draw.rect(surf, COLOR_PLAYER_BODY, body_rect, border_radius=8)

        # 하이라이트
        hl_rect = pygame.Rect(cx - body_size + 2, cy - body_size + 2,
                              body_size * 2 - 8, body_size - 2)
        pygame.draw.rect(surf, COLOR_PLAYER_LIGHT, hl_rect, border_radius=6)

        # 눈 (방향에 따라 위치 변경)
        eye_r = 5
        pupil_r = 2
        eye_offset_x = 6
        eye_y = cy - 3

        if direction == "down":
            eye_y = cy + 1
            pupil_dy = 2
            pupil_dx = 0
        elif direction == "up":
            eye_y = cy - 7
            pupil_dy = -2
            pupil_dx = 0
        elif direction == "left":
            pupil_dx = -2
            pupil_dy = 0
        else:  # right
            pupil_dx = 2
            pupil_dy = 0

        # 왼쪽 눈
        left_eye_x = cx - eye_offset_x
        pygame.draw.circle(surf, COLOR_PLAYER_EYE, (left_eye_x, eye_y), eye_r)
        pygame.draw.circle(surf, COLOR_PLAYER_PUPIL,
                           (left_eye_x + pupil_dx, eye_y + pupil_dy), pupil_r)

        # 오른쪽 눈
        right_eye_x = cx + eye_offset_x
        pygame.draw.circle(surf, COLOR_PLAYER_EYE, (right_eye_x, eye_y), eye_r)
        pygame.draw.circle(surf, COLOR_PLAYER_PUPIL,
                           (right_eye_x + pupil_dx, eye_y + pupil_dy), pupil_r)

        return surf
