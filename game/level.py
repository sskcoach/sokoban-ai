"""레벨 파싱 및 상태 관리"""
from typing import Set, Tuple, Optional
from game.constants import (
    TILE_WALL, TILE_FLOOR, TILE_GOAL, TILE_BOX,
    TILE_BOX_ON_GOAL, TILE_PLAYER, TILE_PLAYER_ON_GOAL,
)


class Level:
    """소코반 레벨 상태를 관리하는 클래스"""

    def __init__(self) -> None:
        self.width: int = 0
        self.height: int = 0
        self.walls: Set[Tuple[int, int]] = set()
        self.goals: Set[Tuple[int, int]] = set()
        self.boxes: Set[Tuple[int, int]] = set()
        self.player: Tuple[int, int] = (0, 0)
        self._floor: Set[Tuple[int, int]] = set()

    @staticmethod
    def from_string(data: str) -> "Level":
        """문자열에서 레벨을 파싱하여 Level 객체 반환"""
        level = Level()
        lines = data.split('\n')
        level.height = len(lines)
        level.width = max(len(line) for line in lines) if lines else 0

        for y, line in enumerate(lines):
            for x, ch in enumerate(line):
                pos = (x, y)
                if ch == TILE_WALL:
                    level.walls.add(pos)
                elif ch == TILE_FLOOR:
                    level._floor.add(pos)
                elif ch == TILE_GOAL:
                    level.goals.add(pos)
                    level._floor.add(pos)
                elif ch == TILE_BOX:
                    level.boxes.add(pos)
                    level._floor.add(pos)
                elif ch == TILE_BOX_ON_GOAL:
                    level.boxes.add(pos)
                    level.goals.add(pos)
                    level._floor.add(pos)
                elif ch == TILE_PLAYER:
                    level.player = pos
                    level._floor.add(pos)
                elif ch == TILE_PLAYER_ON_GOAL:
                    level.player = pos
                    level.goals.add(pos)
                    level._floor.add(pos)
        return level

    def clone(self) -> "Level":
        """깊은 복사본 반환"""
        new_level = Level()
        new_level.width = self.width
        new_level.height = self.height
        new_level.walls = set(self.walls)
        new_level.goals = set(self.goals)
        new_level.boxes = set(self.boxes)
        new_level.player = self.player
        new_level._floor = set(self._floor)
        return new_level

    def get_tile(self, x: int, y: int) -> str:
        """해당 좌표의 타일 기호를 반환"""
        pos = (x, y)
        is_goal = pos in self.goals
        is_box = pos in self.boxes
        is_player = pos == self.player

        if pos in self.walls:
            return TILE_WALL
        if is_player and is_goal:
            return TILE_PLAYER_ON_GOAL
        if is_player:
            return TILE_PLAYER
        if is_box and is_goal:
            return TILE_BOX_ON_GOAL
        if is_box:
            return TILE_BOX
        if is_goal:
            return TILE_GOAL
        if pos in self._floor:
            return TILE_FLOOR
        return TILE_FLOOR

    def is_clear(self) -> bool:
        """모든 박스가 목표 위에 있는지 확인"""
        return self.boxes == self.goals if self.goals else False

    def is_wall(self, x: int, y: int) -> bool:
        """벽인지 확인"""
        return (x, y) in self.walls

    def is_passable(self, x: int, y: int) -> bool:
        """이동 가능한 위치인지 확인 (벽이 아니고 박스도 없는 곳)"""
        pos = (x, y)
        return pos not in self.walls and pos not in self.boxes

    def to_string(self) -> str:
        """레벨을 문자열로 직렬화"""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                line += self.get_tile(x, y)
            lines.append(line.rstrip())
        return '\n'.join(lines)
