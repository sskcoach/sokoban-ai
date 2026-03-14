# 소코반(Sokoban) 게임 — 원샷 완전 구현 프롬프트 v2

> **v1 실패 교훈 반영:**
> - v1에서 AI가 만든 레벨 20개 중 9개가 풀 수 없었음 (박스/목표 불일치 3개 + 구조적 불가 6개)
> - v2에서는 BFS 솔버로 전수 검증 완료된 레벨만 수록
> - 레벨 검증을 위한 솔버 코드를 자율 수정 절차에 추가

Pygame 기반 소코반 게임을 처음부터 끝까지 완성해줘.
외부 에셋 파일 없이, 아래 명세대로 모든 코드를 한 번에 작성하고, `python main.py`로 즉시 실행 가능해야 한다.

---

## 1. 프로젝트 구조

```
sokoban/
├── main.py              # 엔트리포인트, 게임 루프, 상태 머신, --test 모드
├── game/
│   ├── __init__.py      # 빈 파일
│   ├── constants.py     # 상수 (타일 크기, 색상, 키 매핑, 상태명)
│   ├── assets.py        # 픽셀아트 스프라이트 생성 (pygame.draw 기반)
│   ├── level.py         # Level 클래스: 파싱, 상태 관리, 직렬화
│   ├── level_data.py    # 내장 레벨 20개 (섹션 5에 전문 수록 — 솔버 검증 완료)
│   ├── engine.py        # GameEngine: 이동, 충돌, 클리어, undo/redo
│   ├── renderer.py      # Renderer: 타일맵 렌더링, 애니메이션 보간
│   ├── editor.py        # LevelEditor: 레벨 제작 도구
│   ├── save_manager.py  # SaveManager: JSON 기반 진행/랭킹/설정 저장
│   ├── sound.py         # SoundManager: numpy로 프로시저럴 사운드 생성
│   ├── ui.py            # 각 화면 State 클래스들
│   └── particles.py     # ParticleSystem: 스파클, 컨페티
└── data/                # 자동 생성 디렉토리
    ├── save.json        # 게임 진행 저장
    ├── custom_levels/   # 사용자 제작 레벨
    └── screenshots/     # --test 모드 스크린샷
```

---

## 2. 모듈 간 인터페이스 (반드시 이 시그니처를 따를 것)

### constants.py 주요 상수
```
TILE_SIZE = 48
FPS = 60
MOVE_DURATION = 0.12  # 초
FADE_DURATION = 0.2
TILE_WALL='#', TILE_FLOOR=' ', TILE_GOAL='.', TILE_BOX='$',
TILE_BOX_ON_GOAL='*', TILE_PLAYER='@', TILE_PLAYER_ON_GOAL='+'
STATE_TITLE, STATE_LEVEL_SELECT, STATE_PLAYING, STATE_PAUSED,
STATE_CLEAR, STATE_EDITOR, STATE_SETTINGS, STATE_QUIT = 문자열 상수
DIR_UP=(0,-1), DIR_DOWN=(0,1), DIR_LEFT=(-1,0), DIR_RIGHT=(1,0)
KEY_MOVE = {pygame.K_UP: DIR_UP, K_w: DIR_UP, ...}  # 방향키+WASD
calc_stars(moves, par) -> int  # 1~3
```

### Level 클래스 (level.py)
```
class Level:
    width: int, height: int
    walls: set[tuple[int,int]]
    goals: set[tuple[int,int]]
    boxes: set[tuple[int,int]]
    player: tuple[int,int]

    @staticmethod
    from_string(data: str) -> Level       # 문자열 파싱
    def clone() -> Level                  # 깊은 복사
    def get_tile(x, y) -> str             # 해당 좌표의 타일 기호 반환
    def is_clear() -> bool                # 모든 박스가 목표 위인지
    def is_wall(x, y) -> bool
    def is_passable(x, y) -> bool         # 벽 아니고 박스도 없는 곳
```

### GameEngine (engine.py)
```
class GameEngine:
    level: Level
    initial_level: Level                  # 리스타트용 초기 상태
    move_count: int
    undo_stack: list, redo_stack: list
    elapsed_time: float
    last_direction: tuple                 # 플레이어 방향 (스프라이트용)
    box_just_placed_on_goal: tuple|None   # 파티클 트리거

    def __init__(level_data: dict)        # level_data.py의 레벨 dict
    def move(direction: tuple) -> str     # "moved"|"pushed"|"blocked"
    def undo() -> bool
    def redo() -> bool
    def restart()
    def is_deadlocked(x, y) -> bool       # 코너 데드락 감지
    def update(dt: float)                 # 시간 누적
```

### Assets (assets.py)
```
class Assets:
    tiles: dict[str, pygame.Surface]      # "wall","floor","goal","box","box_on_goal","box_deadlock"
    player: dict[str, list[Surface]]      # {"up":[idle,walk], "down":..., "left":..., "right":...}

    @staticmethod
    create() -> Assets                    # 모든 스프라이트를 생성하여 반환
```

### SoundManager (sound.py)
```
class SoundManager:
    enabled: bool                         # numpy import 실패 시 False
    def play(name: str)                   # "step","push","goal","clear","undo","bump","click"
    def set_volume(vol: float)            # 0.0~1.0
```

### SaveManager (save_manager.py)
```
class SaveManager:
    data: dict
    def load() -> dict                    # save.json 읽기 (없으면 기본값)
    def save(data: dict)                  # save.json 쓰기
    def get_unlocked() -> int             # 잠금 해제된 최고 레벨 (1-based)
    def unlock_next(current_level: int)
    def save_record(level_idx, moves, time, stars) -> bool  # 신기록이면 True
    def get_record(level_idx) -> dict
    def get_settings() -> dict
    def save_settings(settings: dict)
    def save_custom_level(name, level_string) -> str
    def load_custom_levels() -> list
```

### Renderer (renderer.py)
```
class AnimState:
    moving: bool, progress: float
    player_from, player_to: tuple
    box_from, box_to: tuple|None
    def start(player_from, player_to, direction, box_from=None, box_to=None)
    def update(dt)
    def get_lerp_pos(from_pos, to_pos) -> tuple  # 보간 픽셀 좌표

class Renderer:
    def __init__(assets: Assets)
    def update(dt)                        # tick 업데이트 (펄스 등)
    def render_level(screen, engine, anim: AnimState)
    def render_hud(screen, engine, level_info: dict)
```

### ParticleSystem (particles.py)
```
class Particle: x,y, vx,vy, color, life, max_life, size
class ParticleSystem:
    def emit(x, y, count, colors, speed_range, life_range, size_range, gravity=True)
    def emit_sparkle(x, y)               # 목표 도착 금색 스파클 6개
    def emit_confetti(screen_width)       # 클리어 다색 컨페티 80개
    def update(dt)
    def draw(screen)
    def clear()
    @property active -> bool
```

### 상태 머신 — 모든 State 클래스 (ui.py + editor.py)
```
class State:
    ctx: dict                             # 공유 컨텍스트
    def enter(context: dict)              # 상태 진입
    def exit()                            # 상태 퇴출
    def handle_event(event) -> str|None   # 반환값이 상태명이면 전환
    def update(dt: float) -> str|None     # 반환값이 상태명이면 전환 (클리어 감지 등)
    def draw(screen)

# ui.py에 구현: TitleState, LevelSelectState, PlayingState, PausedState, ClearState, SettingsState
# editor.py에 구현: EditorState
```

### main.py 게임 루프 골격
```
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # CWD를 스크립트 위치로 고정
pygame.mixer.pre_init(22050, -16, 1)  # mixer를 init 전에 설정
pygame.init()
screen = pygame.display.set_mode(DEFAULT_WINDOW_SIZE)
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()
assets = Assets.create()
sound = SoundManager()
save = SaveManager()
context = {"assets": assets, "sound": sound, "save": save, "current_level_idx": 0}
states = {STATE_TITLE: TitleState(), STATE_PLAYING: PlayingState(), ...}
current_state = states[STATE_TITLE]
current_state.enter(context)

running = True
while running:
    dt = clock.tick(FPS) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False; break
        result = current_state.handle_event(event)
        if result == STATE_QUIT: running = False; break
        if result and result in states:
            # PAUSED 진입 시 screen 스냅샷 저장
            if result == STATE_PAUSED: context["_screen_snapshot"] = screen.copy()
            current_state.exit()
            current_state = states[result]
            current_state.enter(context)
    if not running: break
    result = current_state.update(dt)
    if result and result in states:
        current_state.exit()
        current_state = states[result]
        current_state.enter(context)
    current_state.draw(screen)
    pygame.display.flip()
pygame.quit()
```

---

## 3. 핵심 게임 로직 상세

### 3.1 이동 규칙
- 방향키 / WASD로 4방향 이동
- 빈 바닥, 목표 지점으로 이동 가능
- 박스는 밀기만 가능 (당기기 불가)
- 박스 뒤에 벽이나 다른 박스가 있으면 밀 수 없음
- 모든 박스가 목표 위에 있으면 클리어

### 3.2 Undo / Redo
- Z키: Undo (무제한)
- Y키: Redo
- 스택에 (player_pos, frozenset(boxes)) 저장
- Undo 후 새 이동 시 redo_stack 초기화

### 3.3 데드락 감지 (코너만)
- 박스가 목표가 아닌 위치에서 두 직교 방향 모두 벽이면 데드락
- 예: 위+왼쪽 벽, 위+오른쪽 벽, 아래+왼쪽 벽, 아래+오른쪽 벽
- 데드락 박스는 빨간 테두리 하이라이트

---

## 4. 스프라이트 생성 규칙 (assets.py)

모든 스프라이트는 pygame.Surface(TILE_SIZE×TILE_SIZE)에 pygame.draw 함수(rect, circle, polygon, line)로 도형을 조합하여 그린다. set_at()으로 개별 픽셀 찍기 금지.

**벽**: 진갈색 배경 + 밝은 벽돌 라인 격자 + 상단/좌측 하이라이트 + 하단/우측 셰도우
**바닥**: 베이지 배경 + 연한 격자 라인
**목표**: 바닥 위에 빨간 다이아몬드 (tick 기반 펄스: alpha 변화)
**박스**: 갈색 사각형 + 상단 하이라이트 + 하단 셰도우 + 중앙에 X 무늬
**박스(목표 위)**: 박스와 같되 초록/금 테두리 글로우
**박스(데드락)**: 박스와 같되 빨간 테두리
**플레이어(4방향)**: 파란 둥근 사각형 몸체 + 흰 눈 + 검은 눈동자(방향에 따라 위치 이동)

걷기 프레임 = idle 프레임을 y축으로 ±2px 오프셋한 Surface (별도 그리기 불필요)

---

## 5. 내장 레벨 데이터 — BFS 솔버 전수 검증 완료

> **중요**: 아래 20개 레벨은 BFS 솔버로 풀 수 있음이 검증되었다.
> data 문자열을 **한 글자도 바꾸지 말고** 그대로 사용할 것.
> AI가 레벨을 임의로 만들거나 수정하면 풀 수 없는 퍼즐이 될 수 있으므로 절대 금지.

각 레벨은 `{"name": str, "difficulty": str, "par": int, "data": str}` 형식이다.
par 값은 BFS 최적해 기준이다.

### 튜토리얼 (1~5) — 박스 1개

**Level 1 — "First Steps" / Tutorial / par=5**
```
####
#. #
#  #
#$ #
#@ #
####
```

**Level 2 — "Turn" / Tutorial / par=8**
```
######
#    #
# #@ #
# $  #
# .  #
######
```

**Level 3 — "Easy Push" / Tutorial / par=6**
```
#####
#  .#
# $ #
#  @#
#####
```

**Level 4 — "Corridor" / Tutorial / par=10**
```
#######
#     #
#.$ @ #
#     #
#######
```

**Level 5 — "Two Rooms" / Tutorial / par=12**
```
######
#.   #
## # #
# $  #
# @  #
######
```

### 초급 (6~10) — 박스 2개

**Level 6 — "Side by Side" / Easy / par=15**
```
  ####
###  #
# $. #
# .$ #
# @  #
######
```

**Level 7 — "Squeeze" / Easy / par=20**
```
 #####
##   #
# $  #
# .#.#
# $  #
# @  #
######
```

**Level 8 — "Crossroads" / Easy / par=18**
```
#######
#  .  #
# #$# #
#  @  #
# #$# #
#  .  #
#######
```

**Level 9 — "U-Turn" / Easy / par=22**
```
 #####
 #   #
##$# #
#  . #
#  . #
##$# #
 # @ #
 #####
```

**Level 10 — "L-Shape" / Easy / par=9**
```
 #####
 #   #
## $ ##
#  .  #
# $.  #
#  @  #
#######
```

### 중급 (11~15) — 박스 3개

**Level 11 — "Three in Row" / Medium / par=17**
```
########
#   .  #
#  $   #
## # ###
#  $ . #
#  $   #
#  . @ #
########
```

**Level 12 — "Storage" / Medium / par=23**
```
#######
#  .  #
# $#$ #
#  .  #
# $#. #
#  @  #
#######
```

**Level 13 — "Zigzag" / Medium / par=16**
```
 ######
 #    #
## $  #
#  .$ #
# #.  #
# $.  #
# @ ###
#####
```

**Level 14 — "Warehouse" / Medium / par=28**
```
 ######
##    #
#  $  #
# .#. #
#  $  #
# .$ ##
# @###
####
```

**Level 15 — "Puzzle Box" / Medium / par=14**
```
#######
#     #
# $.$ #
# .#. #
#  $  #
#  @  #
#######
```

### 상급 (16~20) — 박스 4~6개

**Level 16 — "Tight Fit" / Hard / par=50**
```
 ######
 #    ##
##.$$  #
# .  # #
# .# $ #
# . $  #
##  ####
 #@ #
 ####
```

**Level 17 — "Double Cross" / Hard / par=39**
```
########
#   .  #
# $ $  #
##.##.##
#  $ $ #
#  .  @#
########
```

**Level 18 — "The Vault" / Hard / par=60**
```
########
#      #
# #### #
# #..# #
# #..# #
# $$$$ #
##    @#
 ######
```

**Level 19 — "Labyrinth" / Hard / par=18**
```
 ########
 #   .  #
## $  # #
#  .$ . #
# #  $  #
#  $  . #
#  @ ####
######
```

**Level 20 — "Grand Finale" / Hard / par=24**
```
#########
#       #
# .$ $. #
#  # #  #
# .$ $. #
#  . .  #
# $$    #
#   @   #
#########
```

---

## 6. 사운드 시스템 (sound.py)

numpy로 사운드 파형을 생성. numpy import 실패 시 enabled=False로 무음 동작 (try/except 한 줄).

사운드 생성법:
- sample_rate = 22050
- **중요**: `pygame.init()` 호출 전에 `pygame.mixer.pre_init(frequency=22050, size=-16, channels=1)` 호출
- numpy 배열(dtype=np.int16)로 파형 생성 → `pygame.sndarray.make_sound(array)` (mono: shape=(n_samples,))

| 이름 | 파형 | 주파수(Hz) | 길이(ms) | 비고 |
|------|------|-----------|---------|------|
| step | sin | 800 | 20 | 짧은 탭 |
| push | sin+noise | 200 | 50 | 무거운 느낌 |
| goal | sin 2음 | 523→659 | 160 | 도→미 |
| clear | sin 4음 | 523→659→784→1047 | 400 | 도미솔도 아르페지오 |
| undo | sin sweep | 600→300 | 50 | 하강 스윕 |
| bump | sin | 150 | 30 | 둔탁한 저음 |
| click | sin | 1000 | 15 | UI 클릭 |

각 사운드에 fade-in/out(5ms) 적용하여 클릭 노이즈 방지.

---

## 7. 레벨 에디터 (editor.py)

### 기능 (핵심만, 과도한 기능 금지)
- 진입 시 크기 선택: Small(8×8) / Medium(10×10) / Large(14×14)
- 좌클릭: 선택 타일 배치 / 우클릭: 바닥으로 제거
- 좌측 팔레트(80px): 벽/바닥/목표/박스/플레이어, 클릭 또는 1~5 숫자키 선택
- 플레이어는 1명만 허용 (새로 배치하면 기존 플레이어 제거)
- T키: 유효성 검증 후 테스트 플레이 (PlayingState로 전환, ESC로 에디터 복귀)
- Ctrl+S: data/custom_levels/ 에 JSON 저장
- Ctrl+L: 저장된 레벨 목록에서 선택 로드
- 유효성: 플레이어 정확히 1명, 박스 수 == 목표 수 ≥ 1
- 그리드 리사이즈 기능은 구현하지 않음

### 에디터 UI 레이아웃
- 상단 40px: 버튼 바 (Save, Load, Test, Clear, Back)
- 좌측 80px: 타일 팔레트 (세로 배열, 선택 상태 하이라이트)
- 중앙: 편집 캔버스 (그리드 + 마우스 호버 프리뷰)
- 하단 30px: 상태 텍스트 ("Player: 1  Boxes: 3  Goals: 3  [OK]")

---

## 8. UI / UX 상세

### 8.1 전체 규칙
- **모든 UI 텍스트는 영문** (pygame 기본 폰트 한글 미지원)
- 폰트: `pygame.font.SysFont(None, size)` — 시스템 기본 폰트 사용
- 한글 주석은 OK

### 8.2 화면별 상세

**TITLE**
- 상단: "SOKOBAN" 큰 텍스트 (폰트 크기 72, 노란색)
- 중앙: 메뉴 항목 5개 세로 배열 — Play, Level Select, Editor, Settings, Quit
- 선택 표시: 노란색 + 좌측 "> " 표시
- 조작: 상/하 방향키로 선택 이동, Enter로 진입
- Play 선택 시: unlocked 레벨 중 마지막 미클리어 레벨로 시작
- Quit 선택 시: STATE_QUIT 반환 → 메인 루프 종료

**LEVEL_SELECT**
- 4열 × 5행 그리드 레벨 버튼 (20개)
- 각 버튼: 레벨 번호, 잠금 시 자물쇠 아이콘, 클리어 시 별점(* 문자)
- 최고 기록 이동 횟수 표시
- 방향키 커서 이동, Enter 선택 (잠긴 레벨은 bump 사운드), ESC로 뒤로

**PLAYING**
- 중앙: 게임 필드 (화면 중앙에 자동 센터링)
- 상단 HUD(40px): "Level: {name}" / "Moves: {n}" / "Time: {MM:SS}" / "Par: {n}"
- 하단(30px): "Arrows/WASD=Move  Z=Undo  Y=Redo  R=Restart  ESC=Pause"
- 이동 시 lerp 보간 애니메이션 (MOVE_DURATION초, ease-out)
  - 보간 중 입력은 무시
  - AnimState로 관리: moving, progress, player_from/to, box_from/to
- move() 결과에 따라 사운드: "moved"→step, "pushed"→push, "blocked"→bump
- 박스가 목표에 놓이면 → goal 사운드 + 스파클 파티클
- 클리어 감지 시 → update()에서 STATE_CLEAR 반환
- ESC → STATE_PAUSED (에디터 테스트 모드면 STATE_EDITOR로 복귀)

**PAUSED**
- 진입 시 저장된 screen 스냅샷을 배경으로 사용
- 반투명 검은 오버레이 (alpha 150)
- 중앙에 메뉴: Resume, Restart, Level Select, Main Menu
- 조작: 상/하 + Enter, ESC로 Resume

**CLEAR**
- "Level Clear!" 큰 텍스트 (노란색)
- Moves: {n} / Time: {MM:SS} / Stars: ***
- 신기록이면 "New Record!" 텍스트 깜빡임 (blink_timer 기반)
- 컨페티 파티클 이펙트 (emit_confetti)
- clear 사운드 재생
- 메뉴: "Next Level" (마지막이면 "Congratulations!") / "Level Select"

**EDITOR** — 섹션 7 참고

**SETTINGS**
- SFX Volume: 좌우 방향키로 0~100% (10% 단위)
- 현재 볼륨 바 시각화 (채워진 사각형)
- ESC로 뒤로 (설정은 자동 저장)

### 8.3 화면 전환
- 페이드 아웃(검은색, 200ms) → 페이드 인(200ms) 적용
- main.py에서 fade 상태 관리: fading, fade_alpha, fade_in, fade_target_state

---

## 9. 세이브 시스템 (save_manager.py)

`data/save.json` 단일 파일:
```json
{
  "unlocked": 1,
  "records": {},
  "settings": {"sfx_volume": 0.7}
}
```
- 첫 실행 시 data/, data/custom_levels/, data/screenshots/ 자동 생성 (os.makedirs)
- main.py에서 `os.chdir(os.path.dirname(os.path.abspath(__file__)))` 로 CWD 고정
- 레벨 클리어 시 자동 저장 (기존 기록보다 좋을 때만 갱신)
- unlocked: 잠금 해제된 최고 레벨 (1-based), 레벨 1은 항상 해제
- records 키는 레벨 인덱스(문자열), 값은 {moves, time, stars, date}

---

## 10. 파티클 시스템 (particles.py)

```
class Particle:
    x, y, vx, vy: float
    color: tuple
    life, max_life, size: float

class ParticleSystem:
    particles: list[Particle]
    def emit(x, y, count, colors, speed_range, life_range, size_range, gravity=True)
    def emit_sparkle(x, y)  # 목표 도착: 금색 6개, 느린 속도, 0.5초
    def emit_confetti(screen_width)  # 클리어: 다색 80개, 상단에서 낙하, 2초
    def update(dt)  # 위치 += 속도*dt, vy += PARTICLE_GRAVITY*dt, life -= dt
    def draw(screen)  # alpha = life/max_life * 255 근사 (밝기로), pygame.draw.circle
    def clear()
```

---

## 11. 기술 요구사항

```bash
pip install pygame numpy
python main.py
```
- Python 3.8+, pygame 2.0+, numpy
- 60 FPS (pygame.time.Clock)
- 게임 루프: event → update(dt) → draw(screen) → flip()
- 창 제목: "Sokoban", 기본 크기: 1024×768
- 타입 힌트 사용
- 순환 import 금지 (의존 방향: constants ← level ← engine ← renderer ← ui ← main)
- 한글 주석

---

## 절대 규칙 (위반 시 실격)

1. **스텁/플레이스홀더 절대 금지**. "TODO", "pass", "implement later", "..." 등 미완성 코드가 한 줄이라도 있으면 실패. 모든 함수를 완전히 구현할 것.
2. **외부 파일 금지**. 이미지, 사운드, 폰트 파일 사용 금지. 모든 것을 코드로 생성.
3. **레벨 데이터 변조 절대 금지**. 섹션 5의 레벨 문자열을 한 글자도 바꾸지 말 것. 이 레벨들은 BFS 솔버로 풀 수 있음이 검증되었으며, 한 글자라도 변경하면 풀 수 없게 될 수 있다.
4. **레벨을 새로 만들지 말 것**. AI가 즉석에서 만든 소코반 퍼즐은 높은 확률로 풀 수 없다. 섹션 5에 수록된 검증 완료 레벨만 사용할 것.
5. **set_at() 금지**. 스프라이트는 pygame.draw 함수로만 그릴 것.
6. **실행 즉시 동작**. python main.py로 에러 없이 즉시 타이틀 화면이 나와야 함.
7. **영문 UI만**. 화면에 표시되는 모든 텍스트는 영문. 주석만 한글 허용.
8. **각 파일을 빠짐없이 완전하게 작성**. 총 13개 파일.

---

## 자동 테스트 모드 (필수 구현)

main.py에 `--test` CLI 인수를 추가하여, AI가 자율적으로 게임을 조작하고 스크린샷을 찍어 검증할 수 있게 한다.

```bash
python main.py --test
```

### 동작 방식
`--test` 모드 진입 시, 실제 게임 윈도우를 띄우고 아래 시나리오를 **자동으로 수행**한다.
저장 경로: `data/screenshots/` (자동 생성)

### 테스트 시나리오 (Level 1: "First Steps" 자동 클리어)

Level 1 맵 (좌표 분석):
```
####
#. #   ← row 1: 목표(.) at (1,1)
#  #   ← row 2: 빈 바닥
#$ #   ← row 3: 박스($) at (1,3)
#@ #   ← row 4: 플레이어(@) at (1,4)
####
```
풀이: UP, UP (2수만에 클리어)
- UP 1회: 플레이어(1,4)→(1,3), 박스(1,3)→(1,2) 밀림
- UP 2회: 플레이어(1,3)→(1,2), 박스(1,2)→(1,1)=목표 → 클리어!

구현 방식: 상태 머신을 직접 조작하고, 키 이벤트를 주입하고, 프레임을 tick하고, 스크린샷을 저장.
```python
test_actions = [
    ("screenshot", "01_title.png"),       # 타이틀 화면
    ("key", pygame.K_RETURN),             # Play → 게임 시작
    ("wait", 0.5),
    ("screenshot", "02_level_start.png"), # 레벨 시작
    ("key", pygame.K_UP),                 # UP 1: 박스 밀기
    ("wait", 0.3),
    ("screenshot", "03_box_pushed.png"),  # 박스 밀린 상태
    ("key", pygame.K_UP),                 # UP 2: 클리어!
    ("wait", 0.5),
    ("screenshot", "04_level_clear.png"), # 클리어 직후
    ("wait", 1.0),
    ("screenshot", "05_clear_screen.png"),# 결과 + 파티클
]
```

### 구현 요구사항
- 실제 윈도우가 열리고 모든 렌더링이 보여야 함 (headless 금지)
- 키 입력은 pygame.event.post()로 주입하거나 handle_event를 직접 호출
- 대기 시간 동안 게임 루프 정상 동작 (애니메이션, 파티클)
- 모든 스크린샷 저장 후 자동 종료
- update()의 반환값도 처리하여 상태 전환 (클리어 감지 등)

---

## 실행 및 자율 수정 절차

코드 작성 완료 후, 아래 절차를 자율적으로 수행하라.

### Step 1: 의존성 설치 & 첫 실행
```bash
pip install pygame numpy
python main.py --test
```

### Step 2: 에러 발생 시 자율 수정 루프
- 에러 발생 → 트레이스백 분석 → 해당 파일 수정 → 다시 실행
- 에러 없을 때까지 반복 (최대 10회)
- 수정 시 다른 모듈과의 인터페이스 정합성 확인

### Step 3: 스크린샷 시각 검증
`--test` 성공 후 스크린샷을 직접 열어서 확인:
```
data/screenshots/01_title.png       → "SOKOBAN" 텍스트 + 메뉴 5개 보이는가?
data/screenshots/02_level_start.png → 벽/바닥/박스/플레이어/목표가 렌더링되는가?
data/screenshots/03_box_pushed.png  → 박스가 위로 한 칸 밀렸는가?
data/screenshots/04_level_clear.png → 클리어 감지되었는가?
data/screenshots/05_clear_screen.png → 클리어 화면 + 파티클 보이는가?
```
문제 발견 시 수정 후 `--test` 재실행.

### Step 4: 레벨 데이터 검증 (v2 신규 — 가장 중요)
레벨 데이터가 프롬프트에 수록된 것과 정확히 일치하는지 확인:
- 각 레벨의 박스 수 == 목표 수인지 코드로 검증
- 플레이어가 정확히 1명인지 검증
- 검증 실패 시 → 프롬프트의 원본 레벨 데이터로 교체

### Step 5: 기능 검증 체크리스트
- [ ] 타이틀 메뉴 5개 키보드 선택
- [ ] Z Undo, Y Redo, R Restart
- [ ] ESC 일시정지 메뉴
- [ ] 레벨 선택 잠금/해제
- [ ] 클리어 시 save.json 저장 + 다음 레벨 해제
- [ ] 에디터 타일 배치 + 테스트 플레이
- [ ] 설정 볼륨 조절
- [ ] lerp 보간 애니메이션
- [ ] 사운드 재생

### Step 6: 최종 실행
```bash
python main.py
```
정상 실행 확인 후 종료.

### 최종 목표 (이것이 달성되면 완료)
> **`python main.py --test` 실행 시 5장의 스크린샷이 정상 생성되고, 각 스크린샷에서 타이틀 화면, 레벨 렌더링, 박스 밀기, 클리어 판정, 클리어 결과 화면이 시각적으로 확인되며, `python main.py`로 일반 실행 시 에러 없이 게임이 동작한다.**

이 목표가 달성될 때까지 멈추지 말 것.
