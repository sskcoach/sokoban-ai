"""소코반 게임 — 엔트리포인트, 게임 루프, 상태 머신, 테스트 모드"""
import os
import sys
import time

# CWD를 스크립트 위치로 고정 (세이브 파일 경로 안정성)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
from game.constants import (
    WINDOW_TITLE, DEFAULT_WINDOW_SIZE, FPS, FADE_DURATION,
    STATE_TITLE, STATE_LEVEL_SELECT, STATE_PLAYING, STATE_PAUSED,
    STATE_CLEAR, STATE_EDITOR, STATE_SETTINGS, STATE_QUIT,
)
from game.assets import Assets
from game.sound import SoundManager
from game.save_manager import SaveManager
from game.ui import (
    TitleState, LevelSelectState, PlayingState, PausedState,
    ClearState, SettingsState,
)
from game.editor import EditorState


def run_test_mode(screen: pygame.Surface, clock: pygame.time.Clock,
                  states: dict, context: dict) -> None:
    """
    --test 모드: Level 1을 자동으로 플레이하고 스크린샷을 저장.
    실제 윈도우가 열리고 렌더링이 보임.
    """
    os.makedirs("data/screenshots", exist_ok=True)
    current_state = states[STATE_TITLE]
    current_state.enter(context)

    def tick_frames(count: int) -> None:
        """여러 프레임 실행 (렌더링 포함)"""
        nonlocal current_state
        for _ in range(count):
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            result = current_state.update(dt)
            if result and result in states:
                current_state.exit()
                current_state = states[result]
                current_state.enter(context)
            current_state.draw(screen)
            pygame.display.flip()

    def inject_key(key: int) -> None:
        """키 입력 주입"""
        nonlocal current_state
        event = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0,
                                   unicode='', scancode=0)
        result = current_state.handle_event(event)
        if result and result in states:
            current_state.exit()
            current_state = states[result]
            current_state.enter(context)

    def screenshot(name: str) -> None:
        """스크린샷 저장"""
        current_state.draw(screen)
        pygame.display.flip()
        pygame.image.save(screen, f"data/screenshots/{name}")
        print(f"  Screenshot saved: data/screenshots/{name}")

    print("=== Sokoban Test Mode ===")

    # 01: 타이틀 화면
    tick_frames(30)
    screenshot("01_title.png")

    # Play 선택 (Enter)
    inject_key(pygame.K_RETURN)
    tick_frames(30)  # 전환 대기
    screenshot("02_level_start.png")

    # UP 1회: 박스 밀기
    inject_key(pygame.K_UP)
    tick_frames(15)  # 애니메이션 대기
    screenshot("03_box_pushed.png")

    # UP 2회: 박스를 목표로 → 클리어
    inject_key(pygame.K_UP)
    tick_frames(15)

    # update에서 클리어 감지 → CLEAR 상태 전환
    for _ in range(30):
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            pass
        result = current_state.update(dt)
        if result and result in states:
            current_state.exit()
            current_state = states[result]
            current_state.enter(context)
            break
        current_state.draw(screen)
        pygame.display.flip()

    screenshot("04_level_clear.png")

    # 파티클 잠시 대기
    tick_frames(60)
    screenshot("05_clear_screen.png")

    print("=== Test Complete ===")
    print("All screenshots saved to data/screenshots/")

    # 잠시 보여주기
    tick_frames(60)
    pygame.quit()
    sys.exit(0)


def main() -> None:
    """메인 함수"""
    test_mode = "--test" in sys.argv

    # pygame 초기화
    pygame.mixer.pre_init(22050, -16, 1)
    pygame.init()

    screen = pygame.display.set_mode(DEFAULT_WINDOW_SIZE)
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # 리소스 생성
    assets = Assets.create()
    sound = SoundManager()
    save = SaveManager()

    # 설정 적용
    settings = save.get_settings()
    sound.set_volume(settings.get("sfx_volume", 0.7))

    # 공유 컨텍스트
    context = {
        "assets": assets,
        "sound": sound,
        "save": save,
        "current_level_idx": 0,
    }

    # 상태 인스턴스
    states = {
        STATE_TITLE: TitleState(),
        STATE_LEVEL_SELECT: LevelSelectState(),
        STATE_PLAYING: PlayingState(),
        STATE_PAUSED: PausedState(),
        STATE_CLEAR: ClearState(),
        STATE_EDITOR: EditorState(),
        STATE_SETTINGS: SettingsState(),
    }

    # 테스트 모드
    if test_mode:
        run_test_mode(screen, clock, states, context)
        return

    # 일반 모드
    current_state = states[STATE_TITLE]
    current_state.enter(context)

    # 페이드 상태
    fading = False
    fade_alpha = 0
    fade_in = True
    fade_target_state = None
    fade_surface = pygame.Surface(DEFAULT_WINDOW_SIZE)
    fade_surface.fill((0, 0, 0))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if fading:
                continue  # 페이드 중 입력 무시

            result = current_state.handle_event(event)
            if result:
                if result == STATE_QUIT:
                    running = False
                    break
                # 일시정지 복귀는 같은 PlayingState를 유지
                if result == STATE_PLAYING and isinstance(current_state, PausedState):
                    # Resume: PausedState에서 복귀 시 PlayingState 재진입하지 않음
                    item = current_state.menu_items[current_state.selected]
                    if item == "Restart":
                        current_state.exit()
                        current_state = states[STATE_PLAYING]
                        current_state.enter(context)
                    else:
                        current_state.exit()
                        current_state = states[STATE_PLAYING]
                        # PlayingState의 enter가 호출되지만 기존 게임 유지를 위해
                        # 이미 진행 중이면 재초기화
                    continue
                # 페이드 전환 시작
                fading = True
                fade_in = False  # 먼저 페이드 아웃
                fade_alpha = 0
                fade_target_state = result

        if not running:
            break

        # 페이드 처리
        if fading:
            speed = 255 / (FADE_DURATION * FPS)  # 프레임당 알파 변화
            if not fade_in:
                fade_alpha = min(255, fade_alpha + speed * 2)
                if fade_alpha >= 255:
                    # 상태 전환
                    # 일시정지 진입 시 스냅샷 저장
                    if fade_target_state == STATE_PAUSED:
                        context["_screen_snapshot"] = screen.copy()
                    current_state.exit()
                    current_state = states[fade_target_state]
                    current_state.enter(context)
                    fade_in = True
            else:
                fade_alpha = max(0, fade_alpha - speed * 2)
                if fade_alpha <= 0:
                    fading = False
                    fade_target_state = None

        # 업데이트
        if not fading or fade_in:
            result = current_state.update(dt)
            if result and result in states:
                if result == STATE_QUIT:
                    running = False
                    break
                # 일시정지 진입 시 스냅샷
                if result == STATE_PAUSED:
                    context["_screen_snapshot"] = screen.copy()
                current_state.exit()
                current_state = states[result]
                current_state.enter(context)

        # 렌더링
        current_state.draw(screen)

        # 페이드 오버레이
        if fading:
            fade_surface.set_alpha(int(fade_alpha))
            screen.blit(fade_surface, (0, 0))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
