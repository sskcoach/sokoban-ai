"""레벨 에디터 — 마우스 기반 타일 배치, 유효성 검증, 테스트 플레이"""
from typing import Optional, Dict, Any, List, Tuple
import pygame
from game.constants import (
    TILE_SIZE, STATE_TITLE, STATE_PLAYING, STATE_EDITOR,
    COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_HIGHLIGHT,
    COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_FLOOR, COLOR_FLOOR_LINE,
    EDITOR_PALETTE_WIDTH, EDITOR_TOOLBAR_HEIGHT, EDITOR_STATUS_HEIGHT,
    EDITOR_GRID_SIZES,
    TILE_WALL, TILE_FLOOR, TILE_GOAL, TILE_BOX, TILE_PLAYER,
)
from game.level import Level
from game.assets import Assets


PALETTE_TILES = [
    (TILE_WALL, "Wall", (90, 70, 60)),
    (TILE_FLOOR, "Floor", (210, 195, 170)),
    (TILE_GOAL, "Goal", (220, 60, 60)),
    (TILE_BOX, "Box", (180, 130, 60)),
    (TILE_PLAYER, "Player", (50, 120, 220)),
]


class EditorState:
    """레벨 에디터 상태"""

    def __init__(self) -> None:
        self.grid_w = 10
        self.grid_h = 10
        self.grid: List[List[str]] = []
        self.selected_tile = 0
        self.choosing_size = True
        self.size_options = list(EDITOR_GRID_SIZES.keys())
        self.size_cursor = 1  # Medium 기본
        self.message = ""
        self.message_timer = 0.0
        self.ctx: Dict[str, Any] = {}
        self.custom_levels_list: list = []
        self.showing_load_menu = False
        self.load_cursor = 0

    def _init_grid(self) -> None:
        """빈 그리드 초기화"""
        self.grid = [[TILE_FLOOR for _ in range(self.grid_w)]
                     for _ in range(self.grid_h)]

    def enter(self, context: Dict[str, Any]) -> None:
        self.ctx = context
        if not self.ctx.get("editor_returning", False):
            self.choosing_size = True
            self.size_cursor = 1
        else:
            self.ctx["editor_returning"] = False
            self.choosing_size = False

    def exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        # 로드 메뉴 표시 중
        if self.showing_load_menu:
            return self._handle_load_menu(event)

        # 크기 선택 중
        if self.choosing_size:
            return self._handle_size_select(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return STATE_TITLE

            # 숫자키로 타일 선택 (1~5)
            if pygame.K_1 <= event.key <= pygame.K_5:
                idx = event.key - pygame.K_1
                if idx < len(PALETTE_TILES):
                    self.selected_tile = idx

            # T키: 테스트 플레이
            if event.key == pygame.K_t:
                return self._test_play()

            # Ctrl+S: 저장
            if event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self._save_level()

            # Ctrl+L: 불러오기
            if event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self._show_load_menu()

        elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEMOTION:
            if event.type == pygame.MOUSEMOTION and not any(pygame.mouse.get_pressed()):
                return None
            buttons = pygame.mouse.get_pressed()
            if buttons[0] or buttons[2]:  # 좌/우 클릭
                mx, my = pygame.mouse.get_pos()
                self._handle_canvas_click(mx, my, buttons[0])

            # 팔레트 클릭
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                self._handle_palette_click(mx, my)
                self._handle_toolbar_click(mx, my)

        return None

    def _handle_size_select(self, event: pygame.event.Event) -> Optional[str]:
        """크기 선택 화면 이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return STATE_TITLE
            elif event.key == pygame.K_UP:
                self.size_cursor = (self.size_cursor - 1) % len(self.size_options)
            elif event.key == pygame.K_DOWN:
                self.size_cursor = (self.size_cursor + 1) % len(self.size_options)
            elif event.key == pygame.K_RETURN:
                name = self.size_options[self.size_cursor]
                self.grid_w, self.grid_h = EDITOR_GRID_SIZES[name]
                self._init_grid()
                self.choosing_size = False
        return None

    def _handle_load_menu(self, event: pygame.event.Event) -> Optional[str]:
        """로드 메뉴 이벤트 처리"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.showing_load_menu = False
            elif event.key == pygame.K_UP:
                self.load_cursor = max(0, self.load_cursor - 1)
            elif event.key == pygame.K_DOWN:
                self.load_cursor = min(len(self.custom_levels_list) - 1,
                                       self.load_cursor + 1)
            elif event.key == pygame.K_RETURN:
                if self.custom_levels_list:
                    self._load_level(self.custom_levels_list[self.load_cursor])
                    self.showing_load_menu = False
        return None

    def _handle_canvas_click(self, mx: int, my: int, left_button: bool) -> None:
        """캔버스 클릭 처리"""
        screen = pygame.display.get_surface()
        screen_w, screen_h = screen.get_size()
        canvas_x = EDITOR_PALETTE_WIDTH
        canvas_y = EDITOR_TOOLBAR_HEIGHT
        canvas_w = screen_w - EDITOR_PALETTE_WIDTH
        canvas_h = screen_h - EDITOR_TOOLBAR_HEIGHT - EDITOR_STATUS_HEIGHT

        # 그리드 영역 계산
        grid_pixel_w = self.grid_w * TILE_SIZE
        grid_pixel_h = self.grid_h * TILE_SIZE
        offset_x = canvas_x + (canvas_w - grid_pixel_w) // 2
        offset_y = canvas_y + (canvas_h - grid_pixel_h) // 2

        gx = (mx - offset_x) // TILE_SIZE
        gy = (my - offset_y) // TILE_SIZE

        if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
            if left_button:
                tile = PALETTE_TILES[self.selected_tile][0]
                # 플레이어는 1명만
                if tile == TILE_PLAYER:
                    for r in range(self.grid_h):
                        for c in range(self.grid_w):
                            if self.grid[r][c] == TILE_PLAYER:
                                self.grid[r][c] = TILE_FLOOR
                self.grid[gy][gx] = tile
            else:
                self.grid[gy][gx] = TILE_FLOOR

    def _handle_palette_click(self, mx: int, my: int) -> None:
        """팔레트 클릭 처리"""
        if mx >= EDITOR_PALETTE_WIDTH:
            return
        py = EDITOR_TOOLBAR_HEIGHT + 10
        for i in range(len(PALETTE_TILES)):
            item_y = py + i * 55
            if item_y <= my <= item_y + 48:
                self.selected_tile = i
                break

    def _handle_toolbar_click(self, mx: int, my: int) -> None:
        """툴바 버튼 클릭 처리"""
        if my > EDITOR_TOOLBAR_HEIGHT:
            return
        screen_w = pygame.display.get_surface().get_width()
        btn_w = 80
        btn_h = 30
        btn_y = 5
        buttons = ["Save", "Load", "Test", "Clear", "Back"]
        start_x = EDITOR_PALETTE_WIDTH + 10

        for i, name in enumerate(buttons):
            bx = start_x + i * (btn_w + 10)
            if bx <= mx <= bx + btn_w and btn_y <= my <= btn_y + btn_h:
                if name == "Save":
                    self._save_level()
                elif name == "Load":
                    self._show_load_menu()
                elif name == "Test":
                    self._test_play()
                elif name == "Clear":
                    self._init_grid()
                elif name == "Back":
                    pass  # ESC로 처리

    def _validate(self) -> Tuple[bool, str]:
        """레벨 유효성 검증"""
        players = 0
        boxes = 0
        goals = 0
        for row in self.grid:
            for cell in row:
                if cell == TILE_PLAYER:
                    players += 1
                elif cell == TILE_BOX:
                    boxes += 1
                elif cell == TILE_GOAL:
                    goals += 1

        if players != 1:
            return False, f"Need exactly 1 player (found {players})"
        if boxes == 0:
            return False, "Need at least 1 box"
        if boxes != goals:
            return False, f"Boxes ({boxes}) != Goals ({goals})"
        return True, "Valid!"

    def _to_string(self) -> str:
        """그리드를 문자열로 변환"""
        lines = []
        for row in self.grid:
            lines.append("".join(row))
        return "\n".join(lines)

    def _test_play(self) -> Optional[str]:
        """테스트 플레이"""
        valid, msg = self._validate()
        if not valid:
            self.message = msg
            self.message_timer = 3.0
            return None

        level_str = self._to_string()
        self.ctx["current_level_idx"] = 0
        # 임시 레벨 데이터로 교체
        from game.level_data import LEVELS
        self.ctx["_editor_level_backup"] = LEVELS[0].copy()
        LEVELS[0] = {
            "name": "Editor Test",
            "difficulty": "Custom",
            "par": 99,
            "data": level_str,
        }
        self.ctx["editor_test"] = True
        self.ctx["editor_returning"] = True
        return STATE_PLAYING

    def _save_level(self) -> None:
        """레벨 저장"""
        valid, msg = self._validate()
        if not valid:
            self.message = msg
            self.message_timer = 3.0
            return
        level_str = self._to_string()
        import time
        name = f"custom_{int(time.time())}"
        self.ctx["save"].save_custom_level(name, level_str)
        self.message = f"Saved: {name}"
        self.message_timer = 2.0

    def _show_load_menu(self) -> None:
        """로드 메뉴 표시"""
        self.custom_levels_list = self.ctx["save"].load_custom_levels()
        if not self.custom_levels_list:
            self.message = "No custom levels found"
            self.message_timer = 2.0
            return
        self.load_cursor = 0
        self.showing_load_menu = True

    def _load_level(self, level_data: dict) -> None:
        """레벨 로드"""
        data_str = level_data.get("data", "")
        lines = data_str.split('\n')
        self.grid_h = len(lines)
        self.grid_w = max(len(line) for line in lines) if lines else 1
        self.grid = []
        for line in lines:
            row = list(line.ljust(self.grid_w))
            self.grid.append(row)
        self.message = f"Loaded: {level_data.get('name', '?')}"
        self.message_timer = 2.0

    def update(self, dt: float) -> Optional[str]:
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""
        # 에디터 복귀 시 원래 레벨 복원
        if "_editor_level_backup" in self.ctx:
            from game.level_data import LEVELS
            LEVELS[0] = self.ctx.pop("_editor_level_backup")
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()

        if self.choosing_size:
            self._draw_size_select(screen, screen_w, screen_h)
            return

        if self.showing_load_menu:
            self._draw_load_menu(screen, screen_w, screen_h)
            return

        # 툴바
        self._draw_toolbar(screen, screen_w)

        # 팔레트
        self._draw_palette(screen, screen_h)

        # 캔버스
        self._draw_canvas(screen, screen_w, screen_h)

        # 상태 바
        self._draw_status(screen, screen_w, screen_h)

    def _draw_size_select(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        """크기 선택 화면"""
        font_title = pygame.font.SysFont(None, 42)
        title = font_title.render("Select Grid Size", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(sw // 2, sh // 3)))

        font = pygame.font.SysFont(None, 32)
        for i, name in enumerate(self.size_options):
            w, h = EDITOR_GRID_SIZES[name]
            color = COLOR_TEXT_HIGHLIGHT if i == self.size_cursor else COLOR_TEXT
            prefix = "> " if i == self.size_cursor else "  "
            text = font.render(f"{prefix}{name} ({w}x{h})", True, color)
            rect = text.get_rect(center=(sw // 2, sh // 2 + i * 45))
            screen.blit(text, rect)

    def _draw_load_menu(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        """로드 메뉴"""
        font_title = pygame.font.SysFont(None, 36)
        title = font_title.render("Load Level", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(sw // 2, 60)))

        font = pygame.font.SysFont(None, 26)
        for i, lv in enumerate(self.custom_levels_list):
            color = COLOR_TEXT_HIGHLIGHT if i == self.load_cursor else COLOR_TEXT
            text = font.render(f"{'> ' if i == self.load_cursor else '  '}{lv.get('name', '?')}",
                               True, color)
            screen.blit(text, (sw // 4, 100 + i * 30))

        help_font = pygame.font.SysFont(None, 20)
        help_text = help_font.render("Up/Down = Select  Enter = Load  ESC = Cancel",
                                     True, COLOR_TEXT_DIM)
        screen.blit(help_text, help_text.get_rect(center=(sw // 2, sh - 30)))

    def _draw_toolbar(self, screen: pygame.Surface, sw: int) -> None:
        """툴바 렌더링"""
        pygame.draw.rect(screen, (50, 50, 60), (0, 0, sw, EDITOR_TOOLBAR_HEIGHT))

        font = pygame.font.SysFont(None, 22)
        buttons = ["Save", "Load", "Test", "Clear", "Back"]
        btn_w = 80
        btn_h = 30
        btn_y = 5
        start_x = EDITOR_PALETTE_WIDTH + 10

        mx, my = pygame.mouse.get_pos()
        for i, name in enumerate(buttons):
            bx = start_x + i * (btn_w + 10)
            hovered = bx <= mx <= bx + btn_w and btn_y <= my <= btn_y + btn_h
            color = COLOR_BUTTON_HOVER if hovered else COLOR_BUTTON
            pygame.draw.rect(screen, color, (bx, btn_y, btn_w, btn_h), border_radius=4)
            text = font.render(name, True, COLOR_TEXT)
            screen.blit(text, text.get_rect(center=(bx + btn_w // 2, btn_y + btn_h // 2)))

    def _draw_palette(self, screen: pygame.Surface, sh: int) -> None:
        """팔레트 렌더링"""
        pygame.draw.rect(screen, (50, 50, 60),
                         (0, EDITOR_TOOLBAR_HEIGHT, EDITOR_PALETTE_WIDTH,
                          sh - EDITOR_TOOLBAR_HEIGHT))

        py = EDITOR_TOOLBAR_HEIGHT + 10
        font = pygame.font.SysFont(None, 16)
        for i, (tile, name, color) in enumerate(PALETTE_TILES):
            item_y = py + i * 55
            # 선택 하이라이트
            if i == self.selected_tile:
                pygame.draw.rect(screen, COLOR_TEXT_HIGHLIGHT,
                                 (2, item_y - 2, EDITOR_PALETTE_WIDTH - 4, 52), 2)
            # 타일 미리보기
            pygame.draw.rect(screen, color,
                             (10, item_y, 30, 30), border_radius=3)
            # 이름
            text = font.render(name, True, COLOR_TEXT_DIM)
            screen.blit(text, (10, item_y + 34))

    def _draw_canvas(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        """편집 캔버스 렌더링"""
        canvas_x = EDITOR_PALETTE_WIDTH
        canvas_y = EDITOR_TOOLBAR_HEIGHT
        canvas_w = sw - EDITOR_PALETTE_WIDTH
        canvas_h = sh - EDITOR_TOOLBAR_HEIGHT - EDITOR_STATUS_HEIGHT

        grid_pixel_w = self.grid_w * TILE_SIZE
        grid_pixel_h = self.grid_h * TILE_SIZE
        offset_x = canvas_x + (canvas_w - grid_pixel_w) // 2
        offset_y = canvas_y + (canvas_h - grid_pixel_h) // 2

        assets: Assets = self.ctx["assets"]
        mx, my = pygame.mouse.get_pos()

        for gy in range(self.grid_h):
            for gx in range(self.grid_w):
                px = offset_x + gx * TILE_SIZE
                py = offset_y + gy * TILE_SIZE
                cell = self.grid[gy][gx]

                # 바닥
                screen.blit(assets.tiles["floor"], (px, py))

                if cell == TILE_WALL:
                    screen.blit(assets.tiles["wall"], (px, py))
                elif cell == TILE_GOAL:
                    screen.blit(assets.tiles["goal"], (px, py))
                elif cell == TILE_BOX:
                    screen.blit(assets.tiles["box"], (px, py))
                elif cell == TILE_PLAYER:
                    screen.blit(assets.tiles["floor"], (px, py))
                    screen.blit(assets.player["down"][0], (px, py))

                # 그리드 라인
                pygame.draw.rect(screen, (80, 80, 90),
                                 (px, py, TILE_SIZE, TILE_SIZE), 1)

        # 마우스 호버 프리뷰
        hgx = (mx - offset_x) // TILE_SIZE
        hgy = (my - offset_y) // TILE_SIZE
        if 0 <= hgx < self.grid_w and 0 <= hgy < self.grid_h:
            hx = offset_x + hgx * TILE_SIZE
            hy = offset_y + hgy * TILE_SIZE
            pygame.draw.rect(screen, COLOR_TEXT_HIGHLIGHT,
                             (hx, hy, TILE_SIZE, TILE_SIZE), 2)

    def _draw_status(self, screen: pygame.Surface, sw: int, sh: int) -> None:
        """상태 바 렌더링"""
        y = sh - EDITOR_STATUS_HEIGHT
        pygame.draw.rect(screen, (50, 50, 60), (0, y, sw, EDITOR_STATUS_HEIGHT))

        # 박스/목표 카운트
        boxes = sum(row.count(TILE_BOX) for row in self.grid)
        goals = sum(row.count(TILE_GOAL) for row in self.grid)
        players = sum(row.count(TILE_PLAYER) for row in self.grid)
        valid = boxes == goals and boxes >= 1 and players == 1
        check = "OK" if valid else "!"

        font = pygame.font.SysFont(None, 22)
        status = f"Player: {players}  Boxes: {boxes}  Goals: {goals}  [{check}]"
        text = font.render(status, True,
                           COLOR_TEXT if valid else (255, 100, 100))
        screen.blit(text, (10, y + 6))

        # 메시지
        if self.message:
            msg_text = font.render(self.message, True, COLOR_TEXT_HIGHLIGHT)
            screen.blit(msg_text, (sw // 2, y + 6))
