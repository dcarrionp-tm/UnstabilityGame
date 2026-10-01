LEVELS = [
    {
        "name": "Friendly Beginings",
        "width": 2220,
        "spawn": 50,
        "exit": 2160,
        "platforms": [
            (0, 500, 150, "solid"),
            (210, 410, 150, "solid"),
            (390, 500, 300, "solid"),
            (760, 460, 100, "fake"),
            (840, 410, 200, "solid"),
            (1100, 500, 200, "solid"),
            (1410, 500, 200, "solid"),
            (1770, 500, 450, "solid"),
        ],
        "traps": [
            {"x": 390, "count": 4, "kind": "hidden", "trigger_x": 370, "base_y": 500},
            {"x": 1100, "count": 8, "kind": "fake", "base_y": 500},
        ],
        "falling_rocks": [
            {"x": 550, "trigger_x": 420, "warning_duration": 0.1, "fall_acceleration": 10000, "max_fall_speed": 1800},
            {"x": 1480, "trigger_x": 1430, "warning_duration": 0.12, "fall_acceleration": 5500, "max_fall_speed": 1900},
            {"x": 1540, "trigger_x": 1430, "warning_duration": 0.12, "fall_acceleration": 5500, "max_fall_speed": 1900},
            {"x": 1600, "trigger_x": 1430, "warning_duration": 0.12, "fall_acceleration": 5500, "max_fall_speed": 1900},
        ],
        "fake_game_over": 1190,
        "decorations": [
            ("headstone", 90), ("bird", 420), ("rock", 600), ("fence", 660),
            ("headstone", 1130), ("bird", 1280), ("rock", 1440),
            ("fence", 1780), ("rock", 1980), ("bird", 2160),
        ],
    },
    {
        "name": "Give Up",
        "width": 2100,
        "spawn": 50,
        "exit": 2000,
        "platforms": [
            (0, 500, 275, "solid"), (350, 500, 205, "solid"),
            (785, 500, 205, "solid"), (1080, 500, 220, "solid"),
            (1395, 500, 250, "solid"), (1710, 500, 340, "solid"),
            (360, 410, 95, "moving", 625, 130),
            (620, 500, 165, "fake"), (865, 405, 110, "moving", 1035, 105),
            (1140, 410, 100, "crumble"), (1465, 395, 105, "moving", 1650, 125),
        ],
        "bonus_platforms": [
            {"x": 260, "y": 430, "outcome": "safe"},
            {"x": 550, "y": 430, "outcome": "random"},
            {"x": 930, "y": 430, "outcome": "safe"},
            {"x": 1470, "y": 420, "outcome": "random"},
        ],
        "traps": [
            {"x": 805, "count": 5, "kind": "hidden", "trigger_x": 740},
            {"x": 1450, "count": 4, "kind": "on_land"},
        ],
        "falling_rocks": [
            {"x": 650, "trigger_x": 540, "warning_duration": 0.8, "fake": True},
            {"x": 875, "trigger_x": 780}, {"x": 1220, "trigger_x": 1125},
            {"x": 1840, "trigger_x": 1745},
        ],
        "fake_game_over": 1330,
        "decorations": [
            ("bird", 135), ("rock", 360), ("headstone", 480), ("fence", 790),
            ("rock", 1080), ("headstone", 1395), ("bird", 1850), ("rock", 1990),
        ],
        "helicopters": [
            {"x": 320, "y": 110, "speed": 0.55, "amplitude": 20, "drift": 40, "phase": 0.5, "scale": 0.8},
            {"x": 920, "y": 150, "speed": 0.46, "amplitude": 24, "drift": 50, "phase": 1.5, "scale": 1.0},
            {"x": 1500, "y": 130, "speed": 0.52, "amplitude": 18, "drift": 45, "phase": 2.7, "scale": 0.9},
        ],
    },
    {
        "name": "Stop Trying",

        "width": 2200,

        "spawn": 50,

        "exit": 2100,

        "platforms": [

            (0, 500, 260, "solid"), (355, 500, 180, "solid"),

            (700, 500, 180, "solid"), (1030, 500, 190, "solid"),

            (1370, 500, 185, "solid"), (1705, 500, 495, "solid"),

            (370, 405, 90, "moving", 550, 115),

            (620, 500, 155, "fake"), (820, 395, 105, "crumble"),

            (1060, 405, 95, "moving", 1260, 140),

            (1420, 390, 95, "moving", 1630, 125),

            (1780, 415, 105, "fake"),

        ],

        "traps": [

            {"x": 390, "count": 4, "kind": "on_jump"},

            {"x": 1060, "count": 5, "kind": "hidden", "trigger_x": 980},

            {"x": 1740, "count": 4, "kind": "static"},

        ],

        "bonus_platforms": [

            {"x": 275, "y": 430, "outcome": "safe"},

            {"x": 590, "y": 430, "outcome": "spikes"},

            {"x": 925, "y": 430, "outcome": "false"},

            {"x": 1260, "y": 430, "outcome": "temporary"},

        ],

        "falling_rocks": [

            {"x": 775, "trigger_x": 680}, {"x": 1150, "trigger_x": 1055},

            {"x": 1880, "trigger_x": 1785},

        ],

        "fake_game_over": 875,

        "decorations": [

            ("headstone", 170), ("rock", 520), ("bird", 760), ("fence", 1030),

            ("headstone", 1370), ("rock", 1540), ("fence", 1705), ("bird", 2050),

        ],

    },
]