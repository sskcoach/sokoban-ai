"""
내장 레벨 데이터 — 20개, 난이도순 정렬.
모든 레벨은 박스 수 == 목표 수, 플레이어 1명이 검증된 퍼즐.
"""

LEVELS = [
    # ===== 튜토리얼 (1~5) =====
    {
        "name": "First Steps",
        "difficulty": "Tutorial",
        "par": 5,
        "data": "####\n#. #\n#  #\n#$ #\n#@ #\n####",
    },
    {
        "name": "Turn",
        "difficulty": "Tutorial",
        "par": 8,
        "data": "######\n#    #\n# #@ #\n# $  #\n# .  #\n######",
    },
    {
        "name": "Easy Push",
        "difficulty": "Tutorial",
        "par": 6,
        "data": "#####\n#  .#\n# $ #\n#  @#\n#####",
    },
    {
        "name": "Corridor",
        "difficulty": "Tutorial",
        "par": 10,
        "data": "#######\n#     #\n#.$ @ #\n#     #\n#######",
    },
    {
        "name": "Two Rooms",
        "difficulty": "Tutorial",
        "par": 12,
        "data": "######\n#.   #\n## # #\n# $  #\n# @  #\n######",
    },
    # ===== 초급 (6~10) =====
    {
        "name": "Side by Side",
        "difficulty": "Easy",
        "par": 15,
        "data": "  ####\n###  #\n# $. #\n# .$ #\n# @  #\n######",
    },
    {
        "name": "Squeeze",
        "difficulty": "Easy",
        "par": 20,
        "data": " #####\n##   #\n# $  #\n# .#.#\n# $  #\n# @  #\n######",
    },
    {
        "name": "Crossroads",
        "difficulty": "Easy",
        "par": 18,
        "data": "#######\n#  .  #\n# #$# #\n#  @  #\n# #$# #\n#  .  #\n#######",
    },
    {
        "name": "U-Turn",
        "difficulty": "Easy",
        "par": 22,
        "data": " #####\n #   #\n##$# #\n#  . #\n#  . #\n##$# #\n # @ #\n #####",
    },
    {
        "name": "L-Shape",
        "difficulty": "Easy",
        "par": 9,
        "data": " #####\n #   #\n## $ ##\n#  .  #\n# $.  #\n#  @  #\n#######",
    },
    # ===== 중급 (11~15) =====
    {
        "name": "Three in Row",
        "difficulty": "Medium",
        "par": 17,
        "data": "########\n#   .  #\n#  $   #\n## # ###\n#  $ . #\n#  $   #\n#  . @ #\n########",
    },
    {
        "name": "Storage",
        "difficulty": "Medium",
        "par": 23,
        "data": "#######\n#  .  #\n# $#$ #\n#  .  #\n# $#. #\n#  @  #\n#######",
    },
    {
        "name": "Zigzag",
        "difficulty": "Medium",
        "par": 16,
        "data": " ######\n #    #\n## $  #\n#  .$ #\n# #.  #\n# $.  #\n# @ ###\n#####",
    },
    {
        "name": "Warehouse",
        "difficulty": "Medium",
        "par": 28,
        "data": " ######\n##    #\n#  $  #\n# .#. #\n#  $  #\n# .$ ##\n# @###\n####",
    },
    {
        "name": "Puzzle Box",
        "difficulty": "Medium",
        "par": 14,
        "data": "#######\n#     #\n# $.$ #\n# .#. #\n#  $  #\n#  @  #\n#######",
    },
    # ===== 상급 (16~20) =====
    {
        "name": "Tight Fit",
        "difficulty": "Hard",
        "par": 50,
        "data": " ######\n #    ##\n##.$$  #\n# .  # #\n# .# $ #\n# . $  #\n##  ####\n #@ #\n ####",
    },
    {
        "name": "Double Cross",
        "difficulty": "Hard",
        "par": 39,
        "data": "########\n#   .  #\n# $ $  #\n##.##.##\n#  $ $ #\n#  .  @#\n########",
    },
    {
        "name": "The Vault",
        "difficulty": "Hard",
        "par": 60,
        "data": "########\n#      #\n# #### #\n# #..# #\n# #..# #\n# $$$$ #\n##    @#\n ######",
    },
    {
        "name": "Labyrinth",
        "difficulty": "Hard",
        "par": 18,
        "data": " ########\n #   .  #\n## $  # #\n#  .$ . #\n# #  $  #\n#  $  . #\n#  @ ####\n######",
    },
    {
        "name": "Grand Finale",
        "difficulty": "Hard",
        "par": 24,
        "data": "#########\n#       #\n# .$ $. #\n#  # #  #\n# .$ $. #\n#  . .  #\n# $$    #\n#   @   #\n#########",
    },
]

TOTAL_LEVELS = len(LEVELS)
