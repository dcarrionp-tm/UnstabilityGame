import sys

import pygame


WIDTH = 960
HEIGHT = 600
FPS = 60
WORLD_WIDTH = 2760
GROUND_Y = 500

INK = (17, 22, 30)
WHITE = (237, 242, 232)
MUTED = (133, 151, 157)
ACID = (220, 246, 94)
CORAL = (255, 105, 91)
TEAL = (77, 206, 185)


class Platform:
    def __init__(self, x, y, width, kind="solid"):
        self.rect = pygame.Rect(x, y, width, 22)
        self.kind = kind
        self.timer = 0.0
        self.gone = False

    def update(self, dt, player):
        if self.kind == "crumble" and self.timer > 0:
            self.timer += dt
            if self.timer >= 0.72:
                self.gone = True
        if self.kind == "fake" and self.timer > 0:
            self.timer += dt
            if self.timer >= 0.24:
                self.gone = True

    def draw(self, surface, camera_x):
        if self.gone:
            return
        rect = self.rect.move(-camera_x, 0)
        color = TEAL if self.kind == "solid" else ACID
        if self.kind == "crumble":
            color = CORAL if self.timer > 0 else (215, 170, 96)
        if self.kind == "fake":
            color = (118, 128, 130)
        pygame.draw.rect(surface, color, rect, border_radius=3)
        pygame.draw.line(surface, WHITE, (rect.left + 4, rect.top + 2), (rect.right - 4, rect.top + 2), 2)
        if self.kind in ("crumble", "fake"):
            for offset in range(10, rect.w, 24):
                pygame.draw.line(surface, INK, (rect.x + offset, rect.y + 5), (rect.x + offset - 5, rect.bottom - 3), 2)


class SpikeTrap:
    def __init__(self, trigger_x, x, count=4):
        self.trigger_x = trigger_x
        self.x = x
        self.count = count
        self.activated_at = None

    def update(self, now, player):
        if self.activated_at is None and player.centerx > self.trigger_x:
            self.activated_at = now

    def active(self, now):
        return self.activated_at is not None and now - self.activated_at > 0.48

    def draw(self, surface, camera_x, now):
        if self.activated_at is None:
            return
        elapsed = now - self.activated_at
        height = int(25 * min(1.0, elapsed / 0.48))
        color = CORAL if self.active(now) else (255, 181, 96)
        for index in range(self.count):
            x = int(self.x + index * 25 - camera_x)
            pygame.draw.polygon(surface, color, [(x, GROUND_Y), (x + 12, GROUND_Y - height), (x + 24, GROUND_Y)])

    def collides(self, player, now):
        if not self.active(now):
            return False
        hitbox = pygame.Rect(self.x, GROUND_Y - 25, self.count * 25, 25)
        return player.colliderect(hitbox)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("FAULTLINE // an unstable platformer")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.big_font = pygame.font.SysFont("consolas", 56, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 14)
        self.state = "title"
        self.deaths = 0
        self.elapsed = 0.0
        self.camera_x = 0
        self.make_level()
        self.reset_player()

    def make_level(self):
        ground_sections = [
            (0, 350, "solid"), (410, 250, "solid"), (660, 150, "fake"),
            (900, 290, "solid"), (1190, 160, "crumble"), (1440, 260, "solid"),
            (1700, 150, "fake"), (1940, 270, "solid"), (2210, 180, "crumble"),
            (2470, WORLD_WIDTH - 2470, "solid"),
        ]
        self.platforms = [Platform(x, GROUND_Y, width, kind) for x, width, kind in ground_sections]
        self.platforms.extend([
            Platform(460, 414, 100, "crumble"), Platform(735, 420, 100),
            Platform(1020, 405, 110, "crumble"), Platform(1280, 390, 100),
            Platform(1530, 415, 100, "fake"), Platform(1805, 405, 100, "crumble"),
            Platform(2050, 400, 120), Platform(2290, 390, 110, "crumble"),
        ])
        self.traps = [SpikeTrap(540, 605), SpikeTrap(1050, 1095), SpikeTrap(1570, 1620), SpikeTrap(2070, 2140)]
        self.checkpoints = [980, 1900]
        self.checkpoint_index = 0

    def reset_player(self):
        spawn_x = 50 if self.checkpoint_index == 0 else self.checkpoints[self.checkpoint_index - 1]
        self.player = pygame.Rect(spawn_x, GROUND_Y - 48, 28, 42)
        self.velocity_y = 0.0
        self.on_ground = False
        self.camera_x = max(0, spawn_x - WIDTH // 3)

    def reset_level(self):
        checkpoint_index = self.checkpoint_index
        self.make_level()
        self.checkpoint_index = checkpoint_index
        self.reset_player()

    def die(self):
        if self.state == "playing":
            self.deaths += 1
            self.state = "dead"
            self.state_timer = 0.55

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if self.state == "title":
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                self.state = "playing"
            return
        if self.state == "dead":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.reset_level()
                self.state = "playing"
            return
        if self.state == "won":
            return

        self.elapsed += dt
        move = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.player.x += round(move * 290 * dt)
        self.player.x = max(0, min(WORLD_WIDTH - self.player.width, self.player.x))
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.velocity_y = -570
            self.on_ground = False

        previous_bottom = self.player.bottom
        self.velocity_y = min(850, self.velocity_y + 1450 * dt)
        self.player.y += round(self.velocity_y * dt)
        self.on_ground = False
        for platform in self.platforms:
            if not platform.gone and self.player.colliderect(platform.rect) and self.velocity_y >= 0 and previous_bottom <= platform.rect.top + 8:
                self.player.bottom = platform.rect.top
                self.velocity_y = 0
                self.on_ground = True
                if platform.kind in ("crumble", "fake") and platform.timer == 0:
                    platform.timer = 0.001
        for platform in self.platforms:
            platform.update(dt, self.player)

        for trap in self.traps:
            trap.update(self.elapsed, self.player)
            if trap.collides(self.player, self.elapsed):
                self.die()
        if self.player.top > HEIGHT + 50:
            self.die()

        while self.checkpoint_index < len(self.checkpoints) and self.player.centerx > self.checkpoints[self.checkpoint_index]:
            self.checkpoint_index += 1
        if self.player.centerx >= WORLD_WIDTH - 90:
            self.state = "won"
        target_camera = self.player.centerx - WIDTH * 0.38
        self.camera_x = max(0, min(WORLD_WIDTH - WIDTH, int(target_camera)))

    def draw_background(self):
        self.screen.fill(INK)
        for y in range(0, HEIGHT, 4):
            shade = int(24 + y * 0.025)
            pygame.draw.line(self.screen, (shade, shade + 8, shade + 12), (0, y), (WIDTH, y))
        drift = int((self.camera_x * 0.22) % 80)
        for x in range(-80, WIDTH + 80, 80):
            pygame.draw.line(self.screen, (37, 47, 54), (x - drift, 0), (x - drift + 180, HEIGHT), 1)
        for index in range(7):
            x = (index * 191 - self.camera_x // 3) % (WIDTH + 100)
            y = 105 + (index * 67) % 260
            pygame.draw.circle(self.screen, (54, 67, 67), (x, y), 2)

    def draw_hud(self):
        self.screen.blit(self.font.render("FAULTLINE  /  SECTOR 01", True, WHITE), (24, 20))
        death_text = self.font.render(f"FAILURES {self.deaths:02d}", True, CORAL)
        self.screen.blit(death_text, (WIDTH - death_text.get_width() - 24, 20))
        progress = self.player.centerx / WORLD_WIDTH
        pygame.draw.rect(self.screen, (55, 67, 69), (24, 52, WIDTH - 48, 3))
        pygame.draw.rect(self.screen, ACID, (24, 52, int((WIDTH - 48) * progress), 3))

    def draw_overlay(self, title, subtitle, prompt="", controls=""):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((8, 12, 17, 190))
        self.screen.blit(shade, (0, 0))
        title_surface = self.big_font.render(title, True, CORAL if self.state == "dead" else ACID)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 235)))
        subtitle_surface = self.font.render(subtitle, True, WHITE)
        self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WIDTH // 2, 292)))
        if prompt:
            prompt_surface = self.font.render(prompt, True, ACID)
            self.screen.blit(prompt_surface, prompt_surface.get_rect(center=(WIDTH // 2, 365)))
        if controls:
            controls_surface = self.small_font.render(controls, True, MUTED)
            self.screen.blit(controls_surface, controls_surface.get_rect(center=(WIDTH // 2, 404)))

    def draw(self):
        self.draw_background()
        for platform in self.platforms:
            platform.draw(self.screen, self.camera_x)
        pygame.draw.rect(self.screen, (43, 50, 52), (0, GROUND_Y + 22, WIDTH, HEIGHT - GROUND_Y))
        for trap in self.traps:
            trap.draw(self.screen, self.camera_x, self.elapsed)

        for index, checkpoint in enumerate(self.checkpoints):
            x = checkpoint - self.camera_x
            if -20 < x < WIDTH + 20:
                pygame.draw.line(self.screen, MUTED, (x, GROUND_Y), (x, GROUND_Y - 76), 2)
                flag_color = ACID if self.checkpoint_index > index else MUTED
                pygame.draw.polygon(self.screen, flag_color, [(x, GROUND_Y - 76), (x + 25, GROUND_Y - 67), (x, GROUND_Y - 58)])

        goal_x = WORLD_WIDTH - 76 - self.camera_x
        if -60 < goal_x < WIDTH + 60:
            pygame.draw.rect(self.screen, ACID, (goal_x, GROUND_Y - 88, 8, 88))
            pygame.draw.rect(self.screen, WHITE, (goal_x + 8, GROUND_Y - 88, 45, 28), 2)

        player_screen = self.player.move(-self.camera_x, 0)
        pygame.draw.rect(self.screen, (0, 0, 0), player_screen.move(4, 5), border_radius=5)
        pygame.draw.rect(self.screen, WHITE, player_screen, border_radius=5)
        pygame.draw.circle(self.screen, INK, (player_screen.centerx + 5, player_screen.y + 13), 3)
        pygame.draw.rect(self.screen, ACID, (player_screen.x + 5, player_screen.bottom - 8, player_screen.w - 10, 4), border_radius=2)

        self.draw_hud()
        if self.state == "title":
            self.draw_overlay("FAULTLINE", "THE GROUND IS LYING", "PRESS SPACE TO DROP IN", "A / D or arrows to move   |   Space to jump")
        elif self.state == "dead":
            self.draw_overlay("UNSTABLE", "That platform was a little too honest.")
        elif self.state == "won":
            self.draw_overlay("YOU MADE IT", f"Deaths: {self.deaths}", "PRESS R TO RUN IT BACK")

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.033)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.state == "won":
                        self.deaths = 0
                        self.checkpoint_index = 0
                        self.reset_level()
                        self.elapsed = 0
                        self.state = "title"
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
