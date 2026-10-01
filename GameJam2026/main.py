import sys

import pygame

from entities import Platform, SpikeTrap
from levels import LEVELS


WIDTH = 960
HEIGHT = 600
FPS = 60
MOVE_SPEED = 245
JUMP_VELOCITY = -570
GRAVITY = 1450
MAX_FALL_SPEED = 850
JUMP_BUFFER_TIME = 0.12
COYOTE_TIME = 0.08

INK = (17, 22, 30)
WHITE = (237, 242, 232)
MUTED = (133, 151, 157)
ACID = (220, 246, 94)
CORAL = (255, 105, 91)


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
        self.level_index = 0
        self.checkpoint_index = 0
        self.load_level()
        self.reset_player()

    def load_level(self):
        self.level = LEVELS[self.level_index]
        self.world_width = self.level["width"]
        self.platforms = [Platform(*definition) for definition in self.level["platforms"]]
        self.traps = [SpikeTrap(**definition) for definition in self.level["traps"]]
        self.checkpoints = self.level["checkpoints"]

    def reset_player(self):
        spawn_x = self.level["spawn"] if self.checkpoint_index == 0 else self.checkpoints[self.checkpoint_index - 1]
        self.player = pygame.Rect(spawn_x, 500 - 48, 28, 42)
        self.velocity_y = 0.0
        self.on_ground = False
        self.jump_was_held = False
        self.jump_buffer_timer = 0.0
        self.coyote_timer = 0.0
        self.camera_x = max(0, spawn_x - WIDTH // 3)

    def reset_level(self):
        self.load_level()
        self.reset_player()

    def advance_level(self):
        if self.level_index + 1 == len(LEVELS):
            self.state = "won"
            return
        self.level_index += 1
        self.checkpoint_index = 0
        self.elapsed = 0.0
        self.load_level()
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

        self._update_playing(dt, keys)

    def _update_playing(self, dt, keys):
        self.elapsed += dt
        self._move_horizontally(dt, keys)
        jumped = self._handle_jump(dt, keys)
        landed = self._move_vertically(dt)
        self._update_traps(jumped, landed)
        if self.state != "playing":
            return
        self._update_progress()
        self._update_camera()

    def _move_horizontally(self, dt, keys):
        move = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.player.x += round(move * MOVE_SPEED * dt)
        self.player.x = max(0, min(self.world_width - self.player.width, self.player.x))

    def _handle_jump(self, dt, keys):
        jump_held = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        jump_pressed = jump_held and not self.jump_was_held
        if jump_pressed:
            self.jump_buffer_timer = JUMP_BUFFER_TIME
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)
        jumped = self.jump_buffer_timer > 0 and (self.on_ground or self.coyote_timer > 0)
        if jumped:
            self.velocity_y = JUMP_VELOCITY
            self.on_ground = False
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0
        self.jump_was_held = jump_held
        return jumped

    def _move_vertically(self, dt):
        for platform in self.platforms:
            platform.update(dt)
        previous_bottom = self.player.bottom
        self.velocity_y = min(MAX_FALL_SPEED, self.velocity_y + GRAVITY * dt)
        self.player.y += round(self.velocity_y * dt)
        self.on_ground = False
        landed = False
        for platform in self.platforms:
            if platform.gone or platform.kind == "fake":
                continue
            if self.player.colliderect(platform.rect) and self.velocity_y >= 0 and previous_bottom <= platform.rect.top + 8:
                self.player.bottom = platform.rect.top
                self.velocity_y = 0
                self.on_ground = True
                landed = True
                if platform.kind == "crumble" and platform.timer == 0:
                    platform.timer = 0.001
                if platform.kind == "moving":
                    self.player.x += platform.rect.x - platform.previous_x
        return landed

    def _update_traps(self, jumped, landed):
        for trap in self.traps:
            trap.update(self.elapsed, self.player, jumped, landed)
            if trap.collides(self.player, self.elapsed):
                self.die()
        if self.player.top > HEIGHT + 50:
            self.die()

    def _update_progress(self):
        while self.checkpoint_index < len(self.checkpoints) and self.player.centerx > self.checkpoints[self.checkpoint_index]:
            self.checkpoint_index += 1
        if self.player.centerx >= self.level["exit"]:
            self.advance_level()

    def _update_camera(self):
        target_camera = self.player.centerx - WIDTH * 0.38
        self.camera_x = max(0, min(self.world_width - WIDTH, int(target_camera)))

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
        self.screen.blit(self.font.render(f"FAULTLINE  /  {self.level_index + 1:02d} {self.level['name']}", True, WHITE), (24, 20))
        death_text = self.font.render(f"FAILURES {self.deaths:02d}", True, CORAL)
        self.screen.blit(death_text, (WIDTH - death_text.get_width() - 24, 20))
        progress = self.player.centerx / self.world_width
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
        pygame.draw.rect(self.screen, (43, 50, 52), (0, 522, WIDTH, HEIGHT - 522))
        for trap in self.traps:
            trap.draw(self.screen, self.camera_x, self.elapsed)

        for index, checkpoint in enumerate(self.checkpoints):
            x = checkpoint - self.camera_x
            if -20 < x < WIDTH + 20:
                pygame.draw.line(self.screen, MUTED, (x, 500), (x, 424), 2)
                flag_color = ACID if self.checkpoint_index > index else MUTED
                pygame.draw.polygon(self.screen, flag_color, [(x, 424), (x + 25, 433), (x, 442)])

        goal_x = self.level["exit"] - 20 - self.camera_x
        if -60 < goal_x < WIDTH + 60:
            pygame.draw.rect(self.screen, ACID, (goal_x, 412, 8, 88))
            pygame.draw.rect(self.screen, WHITE, (goal_x + 8, 412, 45, 28), 2)

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
            self.draw_overlay("YOU MADE IT", f"Three levels. {self.deaths} failures.", "PRESS R TO RUN IT BACK")

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
                        self.level_index = 0
                        self.checkpoint_index = 0
                        self.elapsed = 0
                        self.reset_level()
                        self.state = "title"
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
# This is a sample Python script.
