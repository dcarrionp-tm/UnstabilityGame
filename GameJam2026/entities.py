import pygame


INK = (17, 22, 30)
WHITE = (237, 242, 232)
ACID = (220, 246, 94)
CORAL = (255, 105, 91)
TEAL = (77, 206, 185)
GROUND_Y = 500


class Platform:
    def __init__(self, x, y, width, kind="solid", end_x=None, speed=0):
        self.rect = pygame.Rect(x, y, width, 22)
        self.kind = kind
        self.timer = 0.0
        self.gone = False
        self.start_x = x
        self.end_x = end_x
        self.speed = speed
        self.direction = 1
        self.previous_x = x

    def update(self, dt):
        self.previous_x = self.rect.x
        if self.kind == "crumble" and self.timer > 0:
            self.timer += dt
            if self.timer >= 0.72:
                self.gone = True
        if self.kind == "moving" and self.end_x is not None:
            self.rect.x += round(self.speed * self.direction * dt)
            if self.rect.x >= self.end_x:
                self.rect.x = self.end_x
                self.direction = -1
            elif self.rect.x <= self.start_x:
                self.rect.x = self.start_x
                self.direction = 1

    def draw(self, surface, camera_x):
        if self.gone:
            return
        rect = self.rect.move(-camera_x, 0)
        color = TEAL if self.kind == "solid" else ACID
        if self.kind == "moving":
            color = (105, 179, 222)
        elif self.kind == "crumble":
            color = CORAL if self.timer > 0 else (215, 170, 96)
        elif self.kind == "fake":
            color = (118, 128, 130)
        pygame.draw.rect(surface, color, rect, border_radius=3)
        pygame.draw.line(surface, WHITE, (rect.left + 4, rect.top + 2), (rect.right - 4, rect.top + 2), 2)
        if self.kind in ("crumble", "fake"):
            for offset in range(10, rect.w, 24):
                pygame.draw.line(surface, INK, (rect.x + offset, rect.y + 5), (rect.x + offset - 5, rect.bottom - 3), 2)


class SpikeTrap:
    def __init__(self, x, count=4, kind="on_jump", trigger_x=None):
        self.x = x
        self.count = count
        self.kind = kind
        self.trigger_x = trigger_x
        self.activated_at = 0.0 if kind == "static" else None

    def update(self, now, player, jumped=False, landed=False):
        if self.activated_at is None:
            crossed_trigger = self.trigger_x is not None and player.centerx > self.trigger_x
            triggered = (
                (self.kind == "on_jump" and jumped)
                or (self.kind == "on_land" and landed)
                or (self.kind == "hidden" and crossed_trigger)
            )
            if triggered:
                self.activated_at = now

    def active(self, now):
        return self.kind == "static" or (self.activated_at is not None and now - self.activated_at > 0.28)

    def draw(self, surface, camera_x, now):
        if self.activated_at is None:
            return
        elapsed = now - self.activated_at
        height = 25 if self.kind == "static" else int(25 * min(1.0, elapsed / 0.28))
        color = CORAL if self.active(now) else (255, 181, 96)
        for index in range(self.count):
            x = self.x + index * 25 - camera_x
            pygame.draw.polygon(surface, color, [(x, GROUND_Y), (x + 12, GROUND_Y - height), (x + 24, GROUND_Y)])

    def collides(self, player, now):
        if not self.active(now):
            return False
        hitbox = pygame.Rect(round(self.x), GROUND_Y - 25, self.count * 25, 25)
        return player.colliderect(hitbox)