import random
from pathlib import Path

import pygame


GROUND_Y = 500
POPUP_TELL = 0.5          # seconds a pop-up spike flickers before it rises
POPUP_RISE = 0.15
VANISH_RANGE = 90         # solid-looking platforms start to shimmer when the player is this close
VANISH_TELL = 0.35        # seconds of shimmer before they vanish
GHOST_ALPHA = 85          # how see-through the platforms that actually hold are
FAKE_SHADOW_TIME = 1.4    # a shadow that grows, waits, then fades with no rock
ROCK_TELL = 0.55          # the real rock's faint shadow, easy to miss
ROCK_GRAVITY = 2000
LUCKY_WOBBLE = 0.4        # the block shakes this long before the bad outcome
WIN_CHANCE = 0.5

WHITE = (237, 242, 232)
GOLD = (246, 196, 64)
CORAL = (255, 105, 91)
INK = (17, 22, 30)
COIN_PATH = Path(__file__).resolve().parent / "Assets" / "Level_Sprites" / "PNG" / "Collectable Object" / "Plague_Town_2D_Platformer_Tileset_Collectable Object - Coin 01.png"

_cache = {}


def _font(size):
    if size not in _cache:
        _cache[size] = pygame.font.SysFont("consolas", size, bold=True)
    return _cache[size]


def _draw_texture(surface, texture, rect):
    """Same tiling the team's Platform.draw uses, so tricks look like real platforms."""
    for offset in range(0, rect.w, texture.get_width()):
        tile_width = min(texture.get_width(), rect.w - offset)
        surface.blit(texture, (rect.x + offset, rect.y - 8), pygame.Rect(0, 0, tile_width, texture.get_height()))


class TrickPlatform:
    """Behaves like an entities.Platform, so the existing collision loop can stand on it."""

    def __init__(self, x, y, width):
        self.rect = pygame.Rect(x, y, width, 22)
        self.timer = 0.0
        self.gone = False
        self.previous_x = x

    def update(self, dt):
        pass

    def think(self, dt, game):
        pass

    def hits(self, player):
        return False


class GhostPlatform(TrickPlatform):
    """Looks see-through, is solid. Tell: a glint sweeps across it."""
    kind = "ghost"

    def draw(self, surface, camera_x, sprites):
        if "ghost" not in _cache:
            _cache["ghost"] = sprites["solid"].copy()
            _cache["ghost"].set_alpha(GHOST_ALPHA)
        rect = self.rect.move(-camera_x, 0)
        _draw_texture(surface, _cache["ghost"], rect)
        sweep = (pygame.time.get_ticks() / 1000 * 140) % (rect.w + 120) - 60
        if 0 <= sweep <= rect.w:
            pygame.draw.line(surface, WHITE, (rect.x + sweep, rect.y - 4), (rect.x + sweep + 8, rect.y + 10), 2)


class VanishPlatform(TrickPlatform):
    """Looks solid, vanishes as you come close. Tell: it shimmers first."""
    kind = "vanish"

    def think(self, dt, game):
        if self.gone:
            return
        if self.timer == 0 and abs(game.player.centerx - self.rect.centerx) < self.rect.w / 2 + VANISH_RANGE:
            self.timer = 0.001
        if self.timer > 0:
            self.timer += dt
            if self.timer >= VANISH_TELL:
                self.gone = True

    def draw(self, surface, camera_x, sprites):
        if self.gone:
            return
        rect = self.rect.move(-camera_x, 0)
        texture = sprites["solid"]
        if self.timer > 0:
            texture = texture.copy()
            texture.set_alpha(255 if pygame.time.get_ticks() // 50 % 2 else 110)
            rect.x += random.randint(-2, 2)
        _draw_texture(surface, texture, rect)


class PopupSpike:
    """Normal-looking ground until the player crosses trigger_x. Tell: tips flicker, then rise."""

    def __init__(self, x, count, trigger_x):
        self.x = x
        self.count = count
        self.trigger_x = trigger_x
        self.time = None

    def think(self, dt, game):
        if self.time is None and game.player.centerx >= self.trigger_x:
            self.time = 0.0
        elif self.time is not None:
            self.time += dt

    def height(self):
        if self.time is None or self.time < POPUP_TELL:
            return 0
        return round(25 * min(1.0, (self.time - POPUP_TELL) / POPUP_RISE))

    def hits(self, player):
        if self.height() < 25:
            return False
        return player.colliderect(pygame.Rect(self.x + 4, GROUND_Y - 18, self.count * 25 - 8, 18))

    def draw(self, surface, camera_x, assets):
        if self.time is None:
            return
        width = self.count * 25
        height = self.height()
        if height == 0:
            if pygame.time.get_ticks() // 80 % 2:
                tips = pygame.transform.smoothscale(assets["spike"], (width, 10))
                surface.blit(tips, (self.x - camera_x, GROUND_Y - 6))
            return
        rendered = pygame.transform.smoothscale(assets["spike"], (width, height + 12))
        surface.blit(rendered, (self.x - camera_x, GROUND_Y - rendered.get_height()))


class ShadowRock:
    """A shadow on the ground. fake=True: it grows and fades, no rock. Real: faint shadow, then a rock."""

    def __init__(self, x, trigger_x, fake=False):
        self.x = x
        self.trigger_x = trigger_x
        self.fake = fake
        self.time = None
        self.y = -40.0
        self.velocity_y = 400.0
        self.landed = False

    def think(self, dt, game):
        if self.time is None:
            if game.player.centerx >= self.trigger_x:
                self.time = 0.0
            return
        self.time += dt
        if not self.fake and self.time > ROCK_TELL and not self.landed:
            self.velocity_y += ROCK_GRAVITY * dt
            self.y += self.velocity_y * dt
            if self.y >= GROUND_Y - 30:
                self.y = GROUND_Y - 30
                self.landed = True

    def hits(self, player):
        if self.fake or self.time is None or self.time <= ROCK_TELL or self.landed:
            return False
        return player.colliderect(pygame.Rect(round(self.x - 18), round(self.y), 36, 28))

    def draw(self, surface, camera_x, assets):
        if self.time is None:
            return
        screen_x = self.x - camera_x
        if self.fake:
            grow = min(1.0, self.time / 0.8)
            fade = max(0.0, 1 - max(0.0, self.time - 1.0) / (FAKE_SHADOW_TIME - 1.0))
            self._shadow(surface, screen_x, round(30 + 50 * grow), round(150 * fade))
            return
        if not self.landed:
            grow = min(1.0, self.time / (ROCK_TELL + 0.4))
            self._shadow(surface, screen_x, round(16 + 20 * grow), 60)
        if self.time > ROCK_TELL:
            rock = assets["falling_rock"]
            surface.blit(rock, rock.get_rect(midtop=(screen_x, round(self.y))))

    def _shadow(self, surface, screen_x, width, alpha):
        if alpha <= 0:
            return
        shadow = pygame.Surface((width, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, alpha), shadow.get_rect())
        surface.blit(shadow, (screen_x - width // 2, GROUND_Y - 5))


class LuckyBlock:
    """Jump into it from below. Win: coins. Lose: it wobbles, then spikes pop up just ahead."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.outcome = None
        self.time = 0.0
        self.coins = []
        self.trap = PopupSpike(x + 55, 3, -1)

    def think(self, dt, game):
        player = game.player
        if self.outcome is None and player.colliderect(self.rect):
            self.outcome = "win" if random.random() < WIN_CHANCE else "lose"
            if game.velocity_y < 0:
                player.top = self.rect.bottom
                game.velocity_y = 0
            if self.outcome == "win":
                self.coins = [[self.rect.centerx, self.rect.top, random.uniform(-120, 120), random.uniform(-420, -260)] for _ in range(7)]
        if self.outcome is None:
            return
        self.time += dt
        for coin in self.coins:
            coin[2] *= 0.99
            coin[3] += 900 * dt
            coin[0] += coin[2] * dt
            coin[1] += coin[3] * dt
        if self.outcome == "lose" and self.time > LUCKY_WOBBLE:
            self.trap.think(dt, game)

    def hits(self, player):
        return self.trap.hits(player)

    def draw(self, surface, camera_x, assets):
        rect = self.rect.move(-camera_x, 0)
        if self.outcome is None:
            rect.y += round(3 * pygame.math.Vector2(0, 1).rotate(pygame.time.get_ticks() * 0.2).y)
            color = GOLD
        else:
            color = (120, 96, 62)
            if self.outcome == "lose" and self.time < LUCKY_WOBBLE:
                rect.x += random.randint(-3, 3)
                color = CORAL
        pygame.draw.rect(surface, color, rect, border_radius=5)
        pygame.draw.rect(surface, INK, rect, 3, border_radius=5)
        if self.outcome is None:
            mark = _font(26).render("?", True, WHITE)
            surface.blit(mark, mark.get_rect(center=rect.center))
        if "coin" not in _cache:
            _cache["coin"] = pygame.transform.smoothscale(pygame.image.load(str(COIN_PATH)).convert_alpha(), (22, 22))
        for x, y, _, _ in self.coins:
            if y < GROUND_Y:
                surface.blit(_cache["coin"], (round(x - camera_x - 11), round(y - 11)))
        self.trap.draw(surface, camera_x, assets)


TRICKS = {
    "ghost": GhostPlatform,
    "vanish": VanishPlatform,
    "popup": PopupSpike,
    "rock": ShadowRock,
    "fake_shadow": lambda x, trigger_x: ShadowRock(x, trigger_x, fake=True),
    "lucky": LuckyBlock,
}


class TrickManager:
    """Builds a level's "tricks" list and runs them. Levels without tricks are untouched."""

    def __init__(self, level):
        self.items = [TRICKS[name](*args) for name, *args in level.get("tricks", [])]
        self.banner = level.get("banner")
        self.exit_x = level["exit"]
        self.time = 0.0

    def platforms(self):
        return [item for item in self.items if isinstance(item, TrickPlatform)]

    def exit_open(self):
        return all(item.outcome is not None for item in self.items if isinstance(item, LuckyBlock))

    def update(self, dt, game):
        self.time += dt
        for item in self.items:
            item.think(dt, game)
            if item.hits(game.player):
                game.die()

    def draw(self, surface, camera_x, assets):
        for item in self.items:
            if not isinstance(item, TrickPlatform):
                item.draw(surface, camera_x, assets)
        if not self.exit_open():
            x = self.exit_x - 2 - camera_x
            pygame.draw.rect(surface, CORAL, (x - 11, 462, 22, 18), border_radius=3)
            pygame.draw.arc(surface, CORAL, (x - 8, 450, 16, 20), 0, 3.14, 3)

    def draw_banner(self, surface):
        if not self.banner:
            return
        text = _font(22).render(self.banner, True, WHITE)
        text.set_alpha(round(255 * min(1.0, self.time / 1.2)))
        center = (surface.get_width() // 2, 92)
        if self.time > 1.5 and self.time % 3.0 < 0.08:
            ghost = _font(22).render(self.banner, True, CORAL)
            surface.blit(ghost, ghost.get_rect(center=(center[0] + 3, center[1])))
        surface.blit(text, text.get_rect(center=center))
