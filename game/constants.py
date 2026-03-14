"""게임 전역 상수 정의"""
import pygame

# --- 화면 ---
WINDOW_TITLE = "Sokoban"
DEFAULT_WINDOW_SIZE = (1024, 768)
FPS = 60

# --- 타일 ---
TILE_SIZE = 48

# --- 색상 (RGB) ---
COLOR_WALL_BASE = (90, 70, 60)
COLOR_WALL_LIGHT = (120, 100, 85)
COLOR_WALL_DARK = (60, 45, 35)
COLOR_WALL_BRICK_LINE = (50, 35, 25)

COLOR_FLOOR = (210, 195, 170)
COLOR_FLOOR_LINE = (190, 175, 150)

COLOR_GOAL = (220, 60, 60)
COLOR_GOAL_GLOW = (255, 100, 100)

COLOR_BOX_BASE = (180, 130, 60)
COLOR_BOX_LIGHT = (220, 170, 90)
COLOR_BOX_DARK = (130, 90, 40)
COLOR_BOX_ON_GOAL = (100, 200, 100)
COLOR_BOX_DEADLOCK = (255, 60, 60)

COLOR_PLAYER_BODY = (50, 120, 220)
COLOR_PLAYER_LIGHT = (80, 150, 250)
COLOR_PLAYER_DARK = (30, 80, 170)
COLOR_PLAYER_EYE = (255, 255, 255)
COLOR_PLAYER_PUPIL = (30, 30, 30)

COLOR_BG = (40, 40, 50)
COLOR_HUD_BG = (30, 30, 40)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (150, 150, 160)
COLOR_TEXT_HIGHLIGHT = (255, 220, 80)
COLOR_MENU_SELECTED = (255, 200, 60)
COLOR_MENU_NORMAL = (200, 200, 210)
COLOR_BUTTON = (70, 70, 90)
COLOR_BUTTON_HOVER = (90, 90, 120)
COLOR_STAR_FILLED = (255, 200, 50)
COLOR_STAR_EMPTY = (80, 80, 90)
COLOR_LOCKED = (100, 100, 110)

COLOR_CONFETTI = [
    (255, 80, 80), (80, 255, 80), (80, 80, 255),
    (255, 255, 80), (255, 80, 255), (80, 255, 255),
    (255, 160, 50), (200, 100, 255),
]
COLOR_SPARKLE = (255, 230, 100)

# --- 애니메이션 ---
MOVE_DURATION = 0.12
FADE_DURATION = 0.2
PULSE_SPEED = 3.0
PARTICLE_GRAVITY = 300.0

# --- 게임 상태 ---
STATE_TITLE = "title"
STATE_LEVEL_SELECT = "level_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_CLEAR = "clear"
STATE_EDITOR = "editor"
STATE_SETTINGS = "settings"
STATE_QUIT = "quit"

# --- 타일 기호 ---
TILE_WALL = '#'
TILE_FLOOR = ' '
TILE_GOAL = '.'
TILE_BOX = '$'
TILE_BOX_ON_GOAL = '*'
TILE_PLAYER = '@'
TILE_PLAYER_ON_GOAL = '+'

# --- 방향 ---
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# --- 키 매핑 ---
KEY_MOVE = {
    pygame.K_UP: DIR_UP, pygame.K_w: DIR_UP,
    pygame.K_DOWN: DIR_DOWN, pygame.K_s: DIR_DOWN,
    pygame.K_LEFT: DIR_LEFT, pygame.K_a: DIR_LEFT,
    pygame.K_RIGHT: DIR_RIGHT, pygame.K_d: DIR_RIGHT,
}
KEY_UNDO = pygame.K_z
KEY_REDO = pygame.K_y
KEY_RESTART = pygame.K_r
KEY_PAUSE = pygame.K_ESCAPE


def calc_stars(moves: int, par: int) -> int:
    """이동 횟수와 par 기준으로 별점 계산 (1~3)"""
    if moves <= par:
        return 3
    elif moves <= int(par * 1.5):
        return 2
    else:
        return 1


# --- 에디터 ---
EDITOR_PALETTE_WIDTH = 80
EDITOR_TOOLBAR_HEIGHT = 40
EDITOR_STATUS_HEIGHT = 30
EDITOR_GRID_SIZES = {"Small": (8, 8), "Medium": (10, 10), "Large": (14, 14)}

# --- 세이브 파일 경로 ---
SAVE_FILE = "data/save.json"
CUSTOM_LEVELS_DIR = "data/custom_levels"
