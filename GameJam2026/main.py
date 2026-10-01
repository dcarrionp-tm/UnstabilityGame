import math
import random
import sys
from pathlib import Path

import pygame

from entities import BonusPlatform, FallingRock, Platform, SpikeTrap
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
        pygame.mixer.init()
        pygame.display.set_caption("FAULTLINE // an unstable platformer")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets = self.load_assets()
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.big_font = pygame.font.SysFont("consolas", 56, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 14)
        self.music_volume = 0.18
        self.sound_volume = 0.9
        self.sounds = self.load_sounds()
        self.start_music()
        self.state = "title"
        self.deaths = 0
        self.elapsed = 0.0
        self.level_index = 0
        self.shake_duration = 0.0
        self.shake_strength = 0.0
        self.load_level()
        self.reset_player()

    def load_assets(self):
        asset_root = Path(__file__).resolve().parent / "Assets"
        levels = asset_root / "Level_Sprites" / "PNG"
        character_frames = asset_root / "Character_Sprites" / "PNG" / "PNG Sequences"

        def load_image(path):
            return pygame.image.load(str(path)).convert_alpha()

        def load_sequence(folder, size=(84, 84)):
            frames = sorted((character_frames / folder).glob("*.png"))
            return [pygame.transform.smoothscale(load_image(frame), size) for frame in frames]

        def load_decoration(filename, size):
            sprite = pygame.transform.smoothscale(load_image(environment / filename), size)
            sprite.set_alpha(155)
            return sprite

        background = levels / "Background"
        platformer = levels / "Platfromer"
        environment = levels / "Environment"
        ground_tile = load_image(platformer / "Plague_Town_2D_Platformer_Tileset_Platformer - Ground 02.png")
        solid_platform = pygame.transform.smoothscale(ground_tile, (96, 32))
        fake_platform = solid_platform.copy()
        tint = pygame.Surface(fake_platform.get_size(), pygame.SRCALPHA)
        tint.fill((235, 195, 145, 34))
        fake_platform.blit(tint, (0, 0))
        crumble_platform = pygame.transform.smoothscale(
            load_image(platformer / "Plague_Town_2D_Platformer_Tileset_Platformer - Bridge Part 02.png"),
            (96, 32),
        )
        crumble_platform.fill((32, 20, 0), special_flags=pygame.BLEND_RGB_ADD)
        bonus_sprite = pygame.transform.smoothscale(
            load_image(platformer / "Plague_Town_2D_Platformer_Tileset_Platformer - Bonus.png"),
            (64, 48),
        )
        return {
            "background_far": pygame.transform.scale(load_image(background / "Plague_Town_2D_Platformer_Tileset_Background - Layer 00.png"), (WIDTH, HEIGHT)),
            "background_near": pygame.transform.scale(load_image(background / "Plague_Town_2D_Platformer_Tileset_Background - Layer 01.png"), (WIDTH, HEIGHT)),
            "ground": pygame.transform.smoothscale(ground_tile, (96, 96)),
            "platforms": {
                "solid": solid_platform,
                "fake": fake_platform,
                "moving": pygame.transform.smoothscale(load_image(platformer / "Plague_Town_2D_Platformer_Tileset_Platformer - Bridge Part 01.png"), (96, 32)),
                "crumble": crumble_platform,
                "fallthrough_sign": pygame.transform.smoothscale(load_image(levels / "Environment" / "Plague_Town_2D_Platformer_Tileset_Environment - Signpost 04.png"), (48, 60)),
            },
            "bonus": bonus_sprite,
            "bonus_outcomes": {
                "safe": pygame.transform.smoothscale(solid_platform, (64, 48)),
                "false": pygame.transform.smoothscale(fake_platform, (64, 48)),
                "temporary": pygame.transform.smoothscale(crumble_platform, (64, 48)),
            },
            "spike": load_image(platformer / "Plague_Town_2D_Platformer_Tileset_Platformer - Spike.png"),
            "falling_rock": pygame.transform.smoothscale(load_image(environment / "Plague_Town_2D_Platformer_Tileset_Environment - Rock 01.png"), (40, 30)),
            "fall_warning": pygame.transform.smoothscale(load_image(environment / "Plague_Town_2D_Platformer_Tileset_Environment - Signpost 05.png"), (38, 52)),
            "decorations": {
                "rock": load_decoration("Plague_Town_2D_Platformer_Tileset_Environment - Rock 02.png", (38, 25)),
                "bird": load_decoration("Plague_Town_2D_Platformer_Tileset_Environment - Bird.png", (28, 28)),
                "headstone": load_decoration("Plague_Town_2D_Platformer_Tileset_Environment - Headstone.png", (34, 48)),
                "fence": load_decoration("Plague_Town_2D_Platformer_Tileset_Environment - Fence 01.png", (68, 39)),
            },
            "goal": pygame.transform.smoothscale(load_image(levels / "Collectable Object" / "Plague_Town_2D_Platformer_Tileset_Collectable Object - Golden Key.png"), (56, 56)),
            "player": {
                "idle": load_sequence("Idle"),
                "run": load_sequence("Running"),
                "jump": load_sequence("Jump Loop"),
                "hurt": load_sequence("Hurt"),
            },
        }

    def load_sounds(self):
        sound_root = Path(__file__).resolve().parent / "sounds"
        sound_map = {
            "start": sound_root / "start.mp3",
            "action": sound_root / "action.mp3",
            "pass": sound_root / "pass.mp3",
            "leveldone": sound_root / "leveldone.mp3",
            "gameover": sound_root / "gameover.mp3",
            "fail": sound_root / "fail.mp3",
            "fall": sound_root / "fall.mp3",
        }
        loaded = {}
        for key, path in sound_map.items():
            if path.exists():
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(2.6 if key == "fall" else self.sound_volume)
                loaded[key] = sound
        return loaded

    def start_music(self):
        music_path = Path(__file__).resolve().parent / "sounds" / "play.mp3"
        if music_path.exists():
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)

    def play_sound(self, key, maxtime=None):
        if not pygame.mixer.get_init():
            return
        sound = self.sounds.get(key)
        if sound is None:
            return
        if key == "fall":
            sound.set_volume(2.6)
        elif key == "gameover":
            sound.set_volume(1.2)
        else:
            sound.set_volume(self.sound_volume)
        if maxtime is not None:
            sound.play(maxtime=maxtime)
        else:
            sound.play()

    def load_level(self):
        self.level = LEVELS[self.level_index]
        self.world_width = self.level["width"]
        self.platforms = [Platform(*definition) for definition in self.level["platforms"]]
        self.bonus_platforms = BonusPlatform.create_all(self.level.get("bonus_platforms", []))
        self.traps = [SpikeTrap(**definition) for definition in self.level["traps"]]
        self.falling_rocks = [FallingRock(**definition) for definition in self.level.get("falling_rocks", [])]
        self.fake_game_over_timer = 0.0
        self.fake_game_over_triggered = False

    def trigger_fake_prank(self):
        if self.fake_game_over_triggered:
            return
        self.fake_game_over_triggered = True
        self.fake_game_over_timer = 1.1
        self.shake_duration = 0.28
        self.shake_strength = 14.0
        self.play_sound("gameover")

    def reset_player(self):
        spawn_x = self.level["spawn"]
        self.player = pygame.Rect(spawn_x, 500 - 48, 28, 42)
        self.facing = 1
        self.moving = False
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
            self.play_sound("leveldone")
            return
        self.play_sound("pass")
        self.level_index += 1
        self.elapsed = 0.0
        self.load_level()
        self.reset_player()

    def die(self):
        if self.state == "playing":
            self.deaths += 1
            self.state = "dead"
            self.state_timer = 0.55
            self.play_sound("fail")

    def update(self, dt):
        if self.shake_duration > 0:
            self.shake_duration = max(0.0, self.shake_duration - dt)
            self.shake_strength = max(0.0, self.shake_strength * 0.82)
        else:
            self.shake_strength = 0.0

        keys = pygame.key.get_pressed()
        if self.state == "title":
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                self.state = "playing"
                self.play_sound("start")
            return
        if self.state == "dead":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.reset_level()
                self.state = "playing"
            return
        if self.state == "won":
            return
        if self.fake_game_over_timer > 0:
            self.fake_game_over_timer = max(0.0, self.fake_game_over_timer - dt)
            return

        self._update_playing(dt, keys)

    def _update_playing(self, dt, keys):
        self.elapsed += dt
        jumped = self._update_player_input(dt, keys)
        landed = self._update_world(dt)
        self._update_hazards(jumped, landed)
        self._update_progress()
        self._update_camera()

    def _update_player_input(self, dt, keys):
        move = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.moving = move != 0
        if move:
            self.facing = move
        self.player.x += round(move * MOVE_SPEED * dt)
        self.player.x = max(0, min(self.world_width - self.player.width, self.player.x))
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
            self.play_sound("action")
        self.jump_was_held = jump_held
        return jumped

    def _update_world(self, dt):
        for platform in self.platforms:
            platform.update(dt)
        for platform in self.bonus_platforms:
            platform.update(dt)
        for hazard in self.falling_rocks:
            hazard.update(dt, self.player)
            if hazard.warning_timer is not None and hazard.warning_timer <= 0 and not getattr(hazard, "fall_sound_played", False):
                hazard.fall_sound_played = True
                fall_distance = 500 - 30 - (-36.0)
                fall_duration_ms = int(1000 * math.sqrt((2 * fall_distance) / hazard.fall_acceleration))
                self.play_sound("fall", maxtime=max(150, fall_duration_ms))
        previous_bottom = self.player.bottom
        self.velocity_y = min(MAX_FALL_SPEED, self.velocity_y + GRAVITY * dt)
        self.player.y += round(self.velocity_y * dt)
        self.on_ground = False
        landed = False
        for platform in self.platforms:
            if platform.gone or platform.kind == "fake":
                continue
            overlaps_horizontally = self.player.right > platform.rect.left and self.player.left < platform.rect.right
            reached_platform_top = previous_bottom <= platform.rect.top + 8 and self.player.bottom >= platform.rect.top
            if overlaps_horizontally and self.velocity_y >= 0 and reached_platform_top:
                self.player.bottom = platform.rect.top
                self.velocity_y = 0
                self.on_ground = True
                landed = True
                if platform.kind == "crumble" and platform.timer == 0:
                    platform.timer = 0.001
                if platform.kind == "moving":
                    self.player.x += platform.rect.x - platform.previous_x
        for platform in self.bonus_platforms:
            if platform.gone:
                continue
            overlaps_horizontally = self.player.right > platform.rect.left and self.player.left < platform.rect.right
            reached_platform_top = previous_bottom <= platform.rect.top + 8 and self.player.bottom >= platform.rect.top
            if not overlaps_horizontally or self.velocity_y < 0 or not reached_platform_top:
                continue
            outcome = platform.land()
            if outcome == "spikes":
                trap = SpikeTrap(
                    platform.rect.left,
                    count=max(2, round(platform.rect.width / 25)),
                    kind="on_jump",
                    base_y=platform.rect.top,
                )
                trap.activated_at = self.elapsed
                self.traps.append(trap)
                continue
            self.player.bottom = platform.rect.top
            self.velocity_y = 0
            self.on_ground = True
            landed = True
        return landed

    def _update_hazards(self, jumped, landed):
        for trap in self.traps:
            trap.update(self.elapsed, self.player, jumped, landed)
            if trap.collides(self.player, self.elapsed, self.assets["spike"]):
                self.die()
        for hazard in self.falling_rocks:
            if hazard.collides(self.player):
                if getattr(hazard, "fake", False):
                    self.trigger_fake_prank()
                    continue
                self.die()
        if self.player.top > HEIGHT + 50:
            self.die()

    def _update_progress(self):
        fake_spikes_popped = any(
            trap.kind == "fake" and trap.activated_at is not None
            for trap in self.traps
        )
        if self.level.get("fake_game_over") and fake_spikes_popped and not self.fake_game_over_triggered:
            self.trigger_fake_prank()
        if self.player.centerx >= self.level["exit"]:
            self.advance_level()

    def _update_camera(self):
        target_camera = self.player.centerx - WIDTH * 0.38
        self.camera_x = max(0, min(self.world_width - WIDTH, int(target_camera)))

    def draw_background(self):
        self.screen.fill(INK)
        for key, parallax, vertical_offset in (("background_far", 0.16, 0), ("background_near", 0.62, 54)):
            image = self.assets[key]
            offset = int(self.camera_x * parallax) % WIDTH
            self.screen.blit(image, (-offset, vertical_offset))
            self.screen.blit(image, (WIDTH - offset, vertical_offset))

    def draw_helicopter(self, x, y, scale=1.0):
        body_color = (245, 240, 220)
        dark = (70, 82, 92)
        accent = (255, 126, 74)
        rotor_len = 58 * scale
        rotor_height = 8 * scale
        body_w = 56 * scale
        body_h = 20 * scale

        pygame.draw.line(self.screen, dark, (x - rotor_len, y), (x + rotor_len, y), max(2, int(3 * scale)))
        pygame.draw.ellipse(self.screen, dark, (x - rotor_len, y - 4 * scale, rotor_len * 2, 8 * scale))
        pygame.draw.ellipse(self.screen, body_color, (x - body_w / 2, y - body_h / 2, body_w, body_h))
        pygame.draw.rect(self.screen, accent, (x + body_w * 0.3, y - 8 * scale, 18 * scale, 10 * scale))
        pygame.draw.line(self.screen, dark, (x + body_w / 2, y), (x + body_w / 2 + 26 * scale, y + 22 * scale), max(2, int(2 * scale)))
        pygame.draw.line(self.screen, dark, (x - body_w / 2 + 6 * scale, y + body_h / 2), (x - 16 * scale, y + 18 * scale), max(2, int(2 * scale)))
        pygame.draw.line(self.screen, dark, (x + body_w / 2 - 6 * scale, y + body_h / 2), (x + 16 * scale, y + 18 * scale), max(2, int(2 * scale)))

    def draw_helicopters(self):
        for config in self.level.get("helicopters", []):
            phase = self.elapsed * config.get("speed", 0.5) + config.get("phase", 0.0)
            drift = math.sin(phase) * config.get("drift", 30)
            lift = math.sin(phase * 1.7) * config.get("amplitude", 18)
            x = config["x"] - self.camera_x + drift
            y = config["y"] + lift
            if -120 < x < WIDTH + 120:
                self.draw_helicopter(x, y, config.get("scale", 1.0))

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

        if self.fake_game_over_timer > 0 and self.state != "won":
            flash = max(0, min(255, int(255 * (self.fake_game_over_timer / 1.1))))
            flash_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_overlay.fill((255, 140, 80, flash))
            self.screen.blit(flash_overlay, (0, 0))

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

    def apply_screen_shake(self):
        if self.shake_strength <= 0:
            return
        shake_x = random.uniform(-self.shake_strength, self.shake_strength)
        shake_y = random.uniform(-self.shake_strength, self.shake_strength)
        shaken = self.screen.copy()
        self.screen.fill(INK)
        self.screen.blit(shaken, (shake_x, shake_y))

    def draw(self):
        self.draw_background()
        self.draw_helicopters()
        for platform in self.platforms:
            platform.draw(self.screen, self.camera_x, self.assets["platforms"])
        for platform in self.bonus_platforms:
            platform.draw(self.screen, self.camera_x, self.assets)
        for x in range(0, WIDTH, self.assets["ground"].get_width()):
            self.screen.blit(self.assets["ground"], (x, 522), (0, 0, min(self.assets["ground"].get_width(), WIDTH - x), HEIGHT - 522))
        for decoration, world_x in self.level.get("decorations", []):
            supports = [
                platform for platform in self.platforms
                if platform.kind in ("solid", "crumble")
                and not platform.gone
                and platform.rect.left <= world_x < platform.rect.right
            ]
            if not supports:
                continue
            support = min(supports, key=lambda platform: platform.rect.top)
            sprite = self.assets["decorations"][decoration]
            screen_x = world_x - self.camera_x
            if -sprite.get_width() < screen_x < WIDTH + sprite.get_width():
                self.screen.blit(sprite, sprite.get_rect(midbottom=(screen_x, support.rect.top)))
        for trap in self.traps:
            trap.draw(self.screen, self.camera_x, self.elapsed, self.assets["spike"])
        for hazard in self.falling_rocks:
            hazard.draw(self.screen, self.camera_x, self.assets["falling_rock"], self.assets["fall_warning"])

        goal_x = self.level["exit"] - 20 - self.camera_x
        if -60 < goal_x < WIDTH + 60:
            key_sprite = self.assets["goal"]
            self.screen.blit(key_sprite, key_sprite.get_rect(midbottom=(goal_x + 18, 500)))

        player_screen = self.player.move(-self.camera_x, 0)
        if self.state == "dead":
            animation_name = "hurt"
        elif self.state == "playing" and not self.on_ground:
            animation_name = "jump"
        elif self.moving:
            animation_name = "run"
        else:
            animation_name = "idle"
        animation = self.assets["player"][animation_name]
        frame_index = 0 if animation_name == "idle" else int(self.elapsed * 12) % len(animation)
        frame = animation[frame_index]
        if getattr(self, "facing", 1) < 0:
            frame = pygame.transform.flip(frame, True, False)
        self.screen.blit(frame, frame.get_rect(midbottom=(player_screen.centerx, player_screen.bottom + 8)))

        self.draw_hud()
        if self.state == "title":
            self.draw_overlay("FAULTLINE", "THE GROUND IS LYING", "PRESS SPACE TO DROP IN", "A / D or arrows to move   |   Space to jump")
        elif self.state == "dead":
            self.draw_overlay("UNSTABLE", "That platform was a little too honest.")
        elif self.state == "won":
            self.draw_overlay("YOU MADE IT", f"Three levels. {self.deaths} failures.", "PRESS R TO RUN IT BACK")
        elif self.fake_game_over_timer > 0:
            self.draw_overlay("JUST KIDDING", "The ground is still lying.", "KEEP MOVING")

        self.apply_screen_shake()

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
