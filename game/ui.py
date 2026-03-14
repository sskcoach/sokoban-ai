"""UI 상태 클래스들 — 타이틀, 레벨 선택, 플레이, 일시정지, 클리어, 설정"""
import math
from typing import Optional, Dict, Any, List
import pygame
from game.constants import (
    STATE_TITLE, STATE_LEVEL_SELECT, STATE_PLAYING, STATE_PAUSED,
    STATE_CLEAR, STATE_EDITOR, STATE_SETTINGS, STATE_QUIT,
    COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_HIGHLIGHT,
    COLOR_MENU_SELECTED, COLOR_MENU_NORMAL, COLOR_HUD_BG,
    COLOR_STAR_FILLED, COLOR_STAR_EMPTY, COLOR_LOCKED,
    COLOR_BUTTON, COLOR_BUTTON_HOVER,
    KEY_MOVE, KEY_UNDO, KEY_REDO, KEY_RESTART, KEY_PAUSE,
    TILE_SIZE, MOVE_DURATION, FADE_DURATION,
    calc_stars,
)
from game.engine import GameEngine
from game.renderer import Renderer, AnimState
from game.particles import ParticleSystem
from game.level_data import LEVELS, TOTAL_LEVELS


class State:
    """상태 기본 클래스"""
    def enter(self, context: Dict[str, Any]) -> None:
        self.ctx = context

    def exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        return None

    def update(self, dt: float) -> Optional[str]:
        return None

    def draw(self, screen: pygame.Surface) -> None:
        pass


class TitleState(State):
    """타이틀 화면"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        self.menu_items = ["Play", "Level Select", "Editor", "Settings", "Quit"]
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RETURN:
                self.ctx["sound"].play("click")
                item = self.menu_items[self.selected]
                if item == "Play":
                    # 마지막 미클리어 레벨 또는 레벨 1
                    unlocked = self.ctx["save"].get_unlocked()
                    level_idx = min(unlocked, TOTAL_LEVELS) - 1
                    self.ctx["current_level_idx"] = level_idx
                    return STATE_PLAYING
                elif item == "Level Select":
                    return STATE_LEVEL_SELECT
                elif item == "Editor":
                    return STATE_EDITOR
                elif item == "Settings":
                    return STATE_SETTINGS
                elif item == "Quit":
                    return STATE_QUIT
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()

        # 타이틀
        title_font = pygame.font.SysFont(None, 72)
        title_surf = title_font.render("SOKOBAN", True, COLOR_TEXT_HIGHLIGHT)
        title_rect = title_surf.get_rect(center=(screen_w // 2, screen_h // 4))
        screen.blit(title_surf, title_rect)

        # 메뉴
        menu_font = pygame.font.SysFont(None, 36)
        start_y = screen_h // 2 - 40
        for i, item in enumerate(self.menu_items):
            color = COLOR_MENU_SELECTED if i == self.selected else COLOR_MENU_NORMAL
            prefix = "> " if i == self.selected else "  "
            text = menu_font.render(prefix + item, True, color)
            rect = text.get_rect(center=(screen_w // 2, start_y + i * 50))
            screen.blit(text, rect)


class LevelSelectState(State):
    """레벨 선택 화면"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        self.cursor = 0
        self.cols = 4
        self.rows = 5

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return STATE_TITLE
            elif event.key == pygame.K_UP:
                self.cursor = max(0, self.cursor - self.cols)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_DOWN:
                self.cursor = min(TOTAL_LEVELS - 1, self.cursor + self.cols)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RIGHT:
                self.cursor = min(TOTAL_LEVELS - 1, self.cursor + 1)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RETURN:
                unlocked = self.ctx["save"].get_unlocked()
                if self.cursor < unlocked:
                    self.ctx["current_level_idx"] = self.cursor
                    self.ctx["sound"].play("click")
                    return STATE_PLAYING
                else:
                    self.ctx["sound"].play("bump")
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()

        # 타이틀
        font_title = pygame.font.SysFont(None, 42)
        title = font_title.render("Level Select", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(screen_w // 2, 40)))

        unlocked = self.ctx["save"].get_unlocked()
        font = pygame.font.SysFont(None, 24)
        font_small = pygame.font.SysFont(None, 18)

        btn_w, btn_h = 120, 100
        margin_x = 20
        margin_y = 15
        total_w = self.cols * btn_w + (self.cols - 1) * margin_x
        start_x = (screen_w - total_w) // 2
        start_y = 80

        for i in range(TOTAL_LEVELS):
            row = i // self.cols
            col = i % self.cols
            x = start_x + col * (btn_w + margin_x)
            y = start_y + row * (btn_h + margin_y)

            is_selected = i == self.cursor
            is_unlocked = i < unlocked
            rect = pygame.Rect(x, y, btn_w, btn_h)

            # 배경
            bg_color = COLOR_BUTTON_HOVER if is_selected else COLOR_BUTTON
            if not is_unlocked:
                bg_color = (50, 50, 55)
            pygame.draw.rect(screen, bg_color, rect, border_radius=6)

            if is_selected:
                pygame.draw.rect(screen, COLOR_TEXT_HIGHLIGHT, rect, 2, border_radius=6)

            # 레벨 번호
            num_text = font.render(str(i + 1), True,
                                   COLOR_TEXT if is_unlocked else COLOR_LOCKED)
            screen.blit(num_text, num_text.get_rect(center=(x + btn_w // 2, y + 20)))

            if is_unlocked:
                # 이름
                name = LEVELS[i]["name"]
                name_text = font_small.render(name, True, COLOR_TEXT_DIM)
                screen.blit(name_text, name_text.get_rect(center=(x + btn_w // 2, y + 40)))

                # 별점 / 기록
                record = self.ctx["save"].get_record(i)
                if record:
                    stars = record.get("stars", 0)
                    star_str = "*" * stars + "-" * (3 - stars)
                    star_text = font_small.render(star_str, True, COLOR_STAR_FILLED)
                    screen.blit(star_text, star_text.get_rect(center=(x + btn_w // 2, y + 60)))
                    moves_text = font_small.render(f"{record['moves']} moves", True, COLOR_TEXT_DIM)
                    screen.blit(moves_text, moves_text.get_rect(center=(x + btn_w // 2, y + 80)))
            else:
                # 자물쇠 아이콘
                lock_x, lock_y = x + btn_w // 2, y + 55
                pygame.draw.rect(screen, COLOR_LOCKED,
                                 (lock_x - 8, lock_y, 16, 12), border_radius=2)
                pygame.draw.arc(screen, COLOR_LOCKED,
                                (lock_x - 6, lock_y - 10, 12, 14),
                                3.14, 0, 2)

        # ESC 안내
        esc_text = font_small.render("ESC = Back", True, COLOR_TEXT_DIM)
        screen.blit(esc_text, (10, screen_h - 25))


class PlayingState(State):
    """게임 플레이 화면"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        level_idx = self.ctx.get("current_level_idx", 0)
        self.level_idx = level_idx
        self.level_info = LEVELS[level_idx]
        self.engine = GameEngine(self.level_info)
        self.renderer = Renderer(self.ctx["assets"])
        self.anim = AnimState()
        self.particles = ParticleSystem()
        self.is_editor_test = self.ctx.get("editor_test", False)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_PAUSE:
                if self.is_editor_test:
                    self.ctx["editor_test"] = False
                    return STATE_EDITOR
                return STATE_PAUSED

            # 애니메이션 중이면 입력 무시
            if self.anim.moving:
                return None

            if event.key in KEY_MOVE:
                direction = KEY_MOVE[event.key]
                old_player = self.engine.level.player
                old_boxes = set(self.engine.level.boxes)
                result = self.engine.move(direction)

                if result == "blocked":
                    self.ctx["sound"].play("bump")
                elif result == "moved":
                    self.ctx["sound"].play("step")
                    self.anim.start(old_player, self.engine.level.player, direction)
                elif result == "pushed":
                    self.ctx["sound"].play("push")
                    new_boxes = self.engine.level.boxes
                    moved_box_to = new_boxes - old_boxes
                    moved_box_from = old_boxes - new_boxes
                    box_from = moved_box_from.pop() if moved_box_from else None
                    box_to = moved_box_to.pop() if moved_box_to else None
                    self.anim.start(old_player, self.engine.level.player,
                                    direction, box_from, box_to)

                    # 박스가 목표에 놓이면 파티클
                    if self.engine.box_just_placed_on_goal:
                        bx, by = self.engine.box_just_placed_on_goal
                        screen_w, screen_h = pygame.display.get_surface().get_size()
                        ox, oy = self.renderer._calc_offset(self.engine, screen_w, screen_h)
                        self.particles.emit_sparkle(
                            ox + bx * TILE_SIZE + TILE_SIZE // 2,
                            oy + by * TILE_SIZE + TILE_SIZE // 2)
                        self.ctx["sound"].play("goal")

            elif event.key == KEY_UNDO:
                if self.engine.undo():
                    self.ctx["sound"].play("undo")
            elif event.key == KEY_REDO:
                if self.engine.redo():
                    self.ctx["sound"].play("click")
            elif event.key == KEY_RESTART:
                self.engine.restart()
                self.anim = AnimState()
                self.particles.clear()
        return None

    def update(self, dt: float) -> Optional[str]:
        if not self.anim.moving:
            self.engine.update(dt)
        self.anim.update(dt)
        self.renderer.update(dt)
        self.particles.update(dt)

        # 클리어 체크 (애니메이션 끝난 후)
        if not self.anim.moving and self.engine.level.is_clear():
            if not self.is_editor_test:
                # 기록 저장
                stars = calc_stars(self.engine.move_count, self.level_info["par"])
                is_new = self.ctx["save"].save_record(
                    self.level_idx, self.engine.move_count,
                    self.engine.elapsed_time, stars)
                self.ctx["save"].unlock_next(self.level_idx + 1)
                self.ctx["clear_data"] = {
                    "moves": self.engine.move_count,
                    "time": self.engine.elapsed_time,
                    "stars": stars,
                    "is_new_record": is_new,
                    "level_idx": self.level_idx,
                }
                return STATE_CLEAR
            else:
                self.ctx["editor_test"] = False
                return STATE_EDITOR
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        self.renderer.render_level(screen, self.engine, self.anim)
        self.renderer.render_hud(screen, self.engine, self.level_info)
        self.particles.draw(screen)


class PausedState(State):
    """일시정지 메뉴"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        self.menu_items = ["Resume", "Restart", "Level Select", "Main Menu"]
        self.selected = 0
        # 배경 스냅샷 저장
        self.bg_snapshot = context.get("_screen_snapshot", None)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return STATE_PLAYING
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RETURN:
                self.ctx["sound"].play("click")
                item = self.menu_items[self.selected]
                if item == "Resume":
                    return STATE_PLAYING
                elif item == "Restart":
                    return STATE_PLAYING  # enter에서 재시작
                elif item == "Level Select":
                    return STATE_LEVEL_SELECT
                elif item == "Main Menu":
                    return STATE_TITLE
        return None

    def draw(self, screen: pygame.Surface) -> None:
        # 반투명 오버레이
        if self.bg_snapshot:
            screen.blit(self.bg_snapshot, (0, 0))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        screen_w, screen_h = screen.get_size()
        font = pygame.font.SysFont(None, 42)
        title = font.render("PAUSED", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(screen_w // 2, screen_h // 3)))

        menu_font = pygame.font.SysFont(None, 32)
        for i, item in enumerate(self.menu_items):
            color = COLOR_MENU_SELECTED if i == self.selected else COLOR_MENU_NORMAL
            prefix = "> " if i == self.selected else "  "
            text = menu_font.render(prefix + item, True, color)
            rect = text.get_rect(center=(screen_w // 2, screen_h // 2 + i * 45))
            screen.blit(text, rect)


class ClearState(State):
    """클리어 결과 화면"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        self.clear_data = context.get("clear_data", {})
        self.particles = ParticleSystem()
        self.particles.emit_confetti(pygame.display.get_surface().get_width())
        self.ctx["sound"].play("clear")
        self.menu_items = []
        level_idx = self.clear_data.get("level_idx", 0)
        if level_idx + 1 < TOTAL_LEVELS:
            self.menu_items.append("Next Level")
        else:
            self.menu_items.append("Congratulations!")
        self.menu_items.append("Level Select")
        self.selected = 0
        self.blink_timer: float = 0.0

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RETURN:
                self.ctx["sound"].play("click")
                item = self.menu_items[self.selected]
                if item == "Next Level":
                    level_idx = self.clear_data.get("level_idx", 0)
                    self.ctx["current_level_idx"] = level_idx + 1
                    return STATE_PLAYING
                elif item == "Level Select":
                    return STATE_LEVEL_SELECT
                elif item == "Congratulations!":
                    return STATE_TITLE
        return None

    def update(self, dt: float) -> Optional[str]:
        self.particles.update(dt)
        self.blink_timer += dt
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()

        # 클리어 텍스트
        font_big = pygame.font.SysFont(None, 60)
        clear_text = font_big.render("Level Clear!", True, COLOR_TEXT_HIGHLIGHT)
        screen.blit(clear_text, clear_text.get_rect(center=(screen_w // 2, screen_h // 4)))

        # 결과
        font = pygame.font.SysFont(None, 32)
        moves = self.clear_data.get("moves", 0)
        time_val = self.clear_data.get("time", 0.0)
        stars = self.clear_data.get("stars", 1)
        is_new = self.clear_data.get("is_new_record", False)

        mins = int(time_val) // 60
        secs = int(time_val) % 60

        texts = [
            f"Moves: {moves}",
            f"Time: {mins:02d}:{secs:02d}",
            f"Stars: {'*' * stars}{'.' * (3 - stars)}",
        ]

        y = screen_h // 3 + 20
        for t in texts:
            text_surf = font.render(t, True, COLOR_TEXT)
            screen.blit(text_surf, text_surf.get_rect(center=(screen_w // 2, y)))
            y += 40

        # 신기록
        if is_new:
            show = int(self.blink_timer * 3) % 2 == 0
            if show:
                nr_text = font.render("New Record!", True, (255, 100, 100))
                screen.blit(nr_text, nr_text.get_rect(center=(screen_w // 2, y + 10)))

        # 메뉴
        menu_font = pygame.font.SysFont(None, 30)
        menu_y = screen_h * 2 // 3
        for i, item in enumerate(self.menu_items):
            color = COLOR_MENU_SELECTED if i == self.selected else COLOR_MENU_NORMAL
            prefix = "> " if i == self.selected else "  "
            text = menu_font.render(prefix + item, True, color)
            rect = text.get_rect(center=(screen_w // 2, menu_y + i * 40))
            screen.blit(text, rect)

        # 파티클
        self.particles.draw(screen)


class SettingsState(State):
    """설정 화면"""

    def enter(self, context: Dict[str, Any]) -> None:
        super().enter(context)
        settings = self.ctx["save"].get_settings()
        self.sfx_volume = int(settings.get("sfx_volume", 0.7) * 100)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # 설정 저장
                self.ctx["save"].save_settings({
                    "sfx_volume": self.sfx_volume / 100.0,
                })
                self.ctx["sound"].set_volume(self.sfx_volume / 100.0)
                return STATE_TITLE
            elif event.key == pygame.K_LEFT:
                self.sfx_volume = max(0, self.sfx_volume - 10)
                self.ctx["sound"].set_volume(self.sfx_volume / 100.0)
                self.ctx["sound"].play("click")
            elif event.key == pygame.K_RIGHT:
                self.sfx_volume = min(100, self.sfx_volume + 10)
                self.ctx["sound"].set_volume(self.sfx_volume / 100.0)
                self.ctx["sound"].play("click")
        return None

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        screen_w, screen_h = screen.get_size()

        # 타이틀
        font_title = pygame.font.SysFont(None, 42)
        title = font_title.render("Settings", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(screen_w // 2, 60)))

        # 볼륨
        font = pygame.font.SysFont(None, 30)
        vol_text = font.render(f"SFX Volume: {self.sfx_volume}%", True, COLOR_TEXT)
        screen.blit(vol_text, vol_text.get_rect(center=(screen_w // 2, screen_h // 2 - 30)))

        # 볼륨 바
        bar_w = 300
        bar_h = 20
        bar_x = (screen_w - bar_w) // 2
        bar_y = screen_h // 2 + 10
        pygame.draw.rect(screen, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        filled = int(bar_w * self.sfx_volume / 100)
        if filled > 0:
            pygame.draw.rect(screen, COLOR_TEXT_HIGHLIGHT,
                             (bar_x, bar_y, filled, bar_h), border_radius=4)

        # 안내
        help_font = pygame.font.SysFont(None, 22)
        help_text = help_font.render("Left/Right = Adjust   ESC = Back", True, COLOR_TEXT_DIM)
        screen.blit(help_text, help_text.get_rect(center=(screen_w // 2, screen_h // 2 + 60)))
