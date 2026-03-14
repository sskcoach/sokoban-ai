"""BFS Sokoban solver – checks all 20 levels for solvability."""

import sys
import os
from collections import deque

sys.path.insert(0, os.path.dirname(__file__))
from game.level_data import LEVELS

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # up, down, left, right

STATE_LIMIT = 2_000_000


def parse_level(data: str):
    """Return walls (set), goals (frozenset), boxes (frozenset), player (tuple)."""
    walls = set()
    goals = set()
    boxes = set()
    player = None
    for r, line in enumerate(data.split("\n")):
        for c, ch in enumerate(line):
            if ch == "#":
                walls.add((r, c))
            elif ch == ".":
                goals.add((r, c))
            elif ch == "$":
                boxes.add((r, c))
            elif ch == "@":
                player = (r, c)
            elif ch == "+":  # player on goal
                player = (r, c)
                goals.add((r, c))
            elif ch == "*":  # box on goal
                boxes.add((r, c))
                goals.add((r, c))
    return walls, frozenset(goals), frozenset(boxes), player


def count_pieces(data: str):
    """Count boxes and goals in raw level string."""
    boxes = data.count("$") + data.count("*")
    goals = data.count(".") + data.count("+") + data.count("*")
    return boxes, goals


def is_corner_deadlock(box, walls, goals):
    """Box in a wall corner and not on a goal => dead."""
    if box in goals:
        return False
    r, c = box
    wu = (r - 1, c) in walls
    wd = (r + 1, c) in walls
    wl = (r, c - 1) in walls
    wr = (r, c + 1) in walls
    return (wu or wd) and (wl or wr)


def solve_bfs(data: str):
    """BFS solver. Returns (result, moves, states_explored).
    result: True=solved, False=no solution, None=state limit hit."""
    walls, goals, boxes, player = parse_level(data)

    if boxes == goals:
        return True, 0, 1

    initial_state = (player, boxes)
    visited = {initial_state}
    queue = deque()
    queue.append((player, boxes, 0))

    while queue:
        if len(visited) >= STATE_LIMIT:
            return None, len(visited), len(visited)

        pr, boxes_state, moves = queue.popleft()

        for dr, dc in DIRS:
            nr, nc = pr[0] + dr, pr[1] + dc
            new_pos = (nr, nc)

            if new_pos in walls:
                continue

            new_boxes = boxes_state
            if new_pos in boxes_state:
                br, bc = nr + dr, nc + dc
                box_dest = (br, bc)
                if box_dest in walls or box_dest in boxes_state:
                    continue
                if is_corner_deadlock(box_dest, walls, goals):
                    continue
                new_boxes = frozenset((boxes_state - {new_pos}) | {box_dest})

            state = (new_pos, new_boxes)
            if state in visited:
                continue
            visited.add(state)

            if new_boxes == goals:
                return True, moves + 1, len(visited)

            queue.append((new_pos, new_boxes, moves + 1))

    return False, 0, len(visited)


def main():
    header = (
        f"{'#':>3}  {'Name':<20} {'Diff':<10} {'Par':>4}  "
        f"{'B':>2} {'G':>2}  {'Solvable':<12} {'Moves':>6}  {'States':>12}  {'Notes'}"
    )
    print(header)
    print("-" * 100)

    for i, lvl in enumerate(LEVELS, 1):
        name = lvl["name"]
        diff = lvl["difficulty"]
        par = lvl["par"]
        b_count, g_count = count_pieces(lvl["data"])
        notes = ""

        if b_count != g_count:
            notes = f"box/goal mismatch!"

        result, val, states = solve_bfs(lvl["data"])

        if result is True:
            status = "YES"
            moves_str = str(val)
        elif result is False:
            status = "NO"
            moves_str = "-"
        else:
            status = "LIMIT HIT"
            moves_str = "?"

        print(
            f"{i:>3}  {name:<20} {diff:<10} {par:>4}  "
            f"{b_count:>2} {g_count:>2}  {status:<12} {moves_str:>6}  {states:>12,}  {notes}"
        )


if __name__ == "__main__":
    main()
