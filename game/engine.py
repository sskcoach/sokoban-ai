"""게임 엔진 — 이동, 충돌, 클리어 판정, undo/redo"""
from typing import Tuple, Optional, FrozenSet, List, Dict, Any
from game.level import Level
from game.constants import TILE_WALL


class GameEngine:
    """소코반 게임 로직 엔진"""

    def __init__(self, level_data: Dict[str, Any]) -> None:
        self.level_data = level_data
        self.level = Level.from_string(level_data["data"])
        self.initial_level = self.level.clone()
        self.move_count: int = 0
        self.elapsed_time: float = 0.0
        self.undo_stack: List[Tuple[Tuple[int, int], FrozenSet[Tuple[int, int]]]] = []
        self.redo_stack: List[Tuple[Tuple[int, int], FrozenSet[Tuple[int, int]]]] = []
        self.last_move_result: str = ""
        self.last_direction: Tuple[int, int] = (0, 1)  # 기본 아래
        self.box_just_placed_on_goal: Optional[Tuple[int, int]] = None

    def _save_state(self) -> Tuple[Tuple[int, int], FrozenSet[Tuple[int, int]]]:
        """현재 상태 스냅샷"""
        return (self.level.player, frozenset(self.level.boxes))

    def move(self, direction: Tuple[int, int]) -> str:
        """
        주어진 방향으로 이동 시도.
        반환: "moved" | "pushed" | "blocked"
        """
        self.last_direction = direction
        self.box_just_placed_on_goal = None
        dx, dy = direction
        px, py = self.level.player
        nx, ny = px + dx, py + dy

        # 벽이면 이동 불가
        if self.level.is_wall(nx, ny):
            self.last_move_result = "blocked"
            return "blocked"

        # 박스가 있는 경우
        if (nx, ny) in self.level.boxes:
            # 박스 뒤 확인
            bx, by = nx + dx, ny + dy
            if self.level.is_wall(bx, by) or (bx, by) in self.level.boxes:
                self.last_move_result = "blocked"
                return "blocked"

            # 상태 저장 (undo용)
            self.undo_stack.append(self._save_state())
            self.redo_stack.clear()

            # 박스 이동
            self.level.boxes.remove((nx, ny))
            self.level.boxes.add((bx, by))
            self.level.player = (nx, ny)
            self.move_count += 1

            # 박스가 목표 위에 놓였는지 확인
            if (bx, by) in self.level.goals:
                self.box_just_placed_on_goal = (bx, by)

            self.last_move_result = "pushed"
            return "pushed"

        # 빈 공간으로 이동
        self.undo_stack.append(self._save_state())
        self.redo_stack.clear()
        self.level.player = (nx, ny)
        self.move_count += 1
        self.last_move_result = "moved"
        return "moved"

    def undo(self) -> bool:
        """되돌리기. 성공 시 True 반환"""
        if not self.undo_stack:
            return False
        # 현재 상태를 redo 스택에 저장
        self.redo_stack.append(self._save_state())
        # 이전 상태 복원
        player, boxes = self.undo_stack.pop()
        self.level.player = player
        self.level.boxes = set(boxes)
        self.move_count -= 1
        return True

    def redo(self) -> bool:
        """다시 실행. 성공 시 True 반환"""
        if not self.redo_stack:
            return False
        self.undo_stack.append(self._save_state())
        player, boxes = self.redo_stack.pop()
        self.level.player = player
        self.level.boxes = set(boxes)
        self.move_count += 1
        return True

    def restart(self) -> None:
        """레벨을 초기 상태로 리셋"""
        self.level = self.initial_level.clone()
        self.move_count = 0
        self.elapsed_time = 0.0
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.box_just_placed_on_goal = None

    def is_deadlocked(self, x: int, y: int) -> bool:
        """
        코너 데드락 감지: 박스가 목표가 아닌 위치에서
        두 직교 방향 모두 벽이면 데드락
        """
        if (x, y) in self.level.goals:
            return False
        if (x, y) not in self.level.boxes:
            return False

        # 네 코너 방향 조합 확인
        wall_up = self.level.is_wall(x, y - 1)
        wall_down = self.level.is_wall(x, y + 1)
        wall_left = self.level.is_wall(x - 1, y)
        wall_right = self.level.is_wall(x + 1, y)

        if (wall_up and wall_left) or (wall_up and wall_right) or \
           (wall_down and wall_left) or (wall_down and wall_right):
            return True
        return False

    def update(self, dt: float) -> None:
        """경과 시간 업데이트"""
        self.elapsed_time += dt
