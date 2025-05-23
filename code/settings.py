# Game window settings
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 800
FRAMERATE = 120
FULLSCREEN = False # Set to True for fullscreen, False for windowed

# Game settings
GRAVITY = 600
JUMP_STRENGTH = 400

# Difficulty settings
DIFFICULTY_LEVELS = {
    1: {"name": "Tutorial", "speed": 200, "interval": 3000, "gap": 150, "color": (100, 255, 100)},
    2: {"name": "Easy", "speed": 220, "interval": 2800, "gap": 140, "color": (150, 255, 150)},
    3: {"name": "Beginner", "speed": 240, "interval": 2600, "gap": 130, "color": (200, 255, 100)},
    4: {"name": "Casual", "speed": 260, "interval": 2400, "gap": 120, "color": (255, 255, 100)},
    5: {"name": "Normal", "speed": 280, "interval": 2200, "gap": 110, "color": (255, 200, 100)},
    6: {"name": "Moderate", "speed": 300, "interval": 2000, "gap": 100, "color": (255, 150, 100)},
    7: {"name": "Challenging", "speed": 320, "interval": 1800, "gap": 90, "color": (255, 100, 100)},
    8: {"name": "Hard", "speed": 340, "interval": 1600, "gap": 80, "color": (255, 50, 50)},
    9: {"name": "Expert", "speed": 360, "interval": 1400, "gap": 70, "color": (200, 50, 50)},
    10: {"name": "Master", "speed": 380, "interval": 1200, "gap": 60, "color": (150, 0, 0)},
    11: {"name": "Insane", "speed": 400, "interval": 1000, "gap": 50, "color": (100, 0, 0)},
    12: {"name": "Nightmare", "speed": 450, "interval": 800, "gap": 40, "color": (50, 0, 0)},
}

# Maximum difficulty level
MAX_DIFFICULTY = 12
