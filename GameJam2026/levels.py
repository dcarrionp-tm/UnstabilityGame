LEVELS = [
    {
        "name": "THE FRIENDLY FLOOR",
        "width": 1900,
        "spawn": 50,
        "exit": 1800,
        "platforms": [
            (0, 500, 300, "solid"), (360, 500, 250, "solid"),
            (610, 500, 145, "fake"), (805, 500, 300, "solid"),
            (1160, 500, 245, "solid"), (1450, 500, 450, "solid"),
            (430, 414, 105, "solid"), (855, 410, 110, "crumble"),
            (1220, 415, 110, "crumble"),
        ],
        "traps": [
            {"x": 445, "count": 4, "kind": "on_jump"},
            {"x": 1060, "count": 4, "kind": "hidden", "trigger_x": 970},
            {"x": 1225, "count": 4, "kind": "static"},
        ],
        "falling_rocks": [
            {"x": 930, "trigger_x": 835}, {"x": 1320, "trigger_x": 1225},
        ],
        "fake_game_over": 1035,
        "decorations": [
            ("headstone", 115), ("bird", 265), ("fence", 370), ("rock", 555),
            ("headstone", 1165), ("bird", 1460), ("fence", 1685), ("rock", 1860),
        ],
    },
    {
        "name": "NOTHING IS STATIONARY",
        "width": 2050,
        "spawn": 50,
        "exit": 1950,
        "platforms": [
            (0, 500, 275, "solid"), (350, 500, 205, "solid"),
            (785, 500, 205, "solid"), (1080, 500, 220, "solid"),
            (1395, 500, 250, "solid"), (1710, 500, 340, "solid"),
            (360, 410, 95, "moving", 625, 130),
            (620, 500, 165, "fake"), (865, 405, 100, "moving", 1035, 105),
            (1140, 410, 95, "crumble"), (1465, 395, 100, "moving", 1650, 125),
        ],
        "traps": [
            {"x": 805, "count": 5, "kind": "hidden", "trigger_x": 740},
            {"x": 1450, "count": 4, "kind": "on_land"},
        ],
        "falling_rocks": [
            {"x": 875, "trigger_x": 780}, {"x": 1220, "trigger_x": 1125},
            {"x": 1840, "trigger_x": 1745},
        ],
        "fake_game_over": 1330,
        "decorations": [
            ("bird", 135), ("rock", 360), ("headstone", 480), ("fence", 790),
            ("rock", 1080), ("headstone", 1395), ("bird", 1850), ("rock", 1990),
        ],
    },
    {
        "name": "THE EXIT IS A LIAR",
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
            {"x": 275, "y": 430, "outcome": "random"},
            {"x": 590, "y": 430, "outcome": "random"},
            {"x": 925, "y": 430, "outcome": "random"},
            {"x": 1260, "y": 430, "outcome": "random"},
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