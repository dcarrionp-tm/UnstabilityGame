import random

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
        if self.kind == "crumble" and self.timer > 0:
            self.timer += dt
            if self.timer >= 0.72:
                self.gone = True
        if self.kind == "moving" and self.end_x is not None:
            self.previous_x = self.rect.x
            self.rect.x += round(self.speed * self.direction * dt)
            if self.rect.x >= self.end_x:
                self.rect.x = self.end_x
                self.direction = -1
            elif self.rect.x <= self.start_x:
                self.rect.x = self.start_x
                self.direction = 1

    def draw(self, surface, camera_x, sprites):
        if self.gone:
            return
        rect = self.rect.move(-camera_x, 0)
        texture = sprites[self.kind]
        for offset in range(0, rect.w, texture.get_width()):
            tile_width = min(texture.get_width(), rect.w - offset)
            area = pygame.Rect(0, 0, tile_width, texture.get_height())
            surface.blit(texture, (rect.x + offset, rect.y - 8), area)
        if self.kind == "fake":
            sign = sprites["fallthrough_sign"]
            surface.blit(sign, sign.get_rect(midbottom=(rect.centerx, rect.top - 2)))


class BonusPlatform:
    OUTCOMES = ("safe", "false", "spikes", "temporary")

    def __init__(self, x, y, outcome, width=64):
        self.rect = pygame.Rect(x, y, width, 48)
        self.outcome = outcome
        self.revealed = False
        self.timer = 0.0
        self.gone = False

    @classmethod
    def create_all(cls, definitions):
        outcomes = list(cls.OUTCOMES)
        random.shuffle(outcomes)
        previous_outcome = None
        platforms = []

        for definition in definitions:
            config = definition.copy()
            if config["outcome"] == "random":
                if not outcomes:
                    outcomes = list(cls.OUTCOMES)
                    random.shuffle(outcomes)
                    if len(outcomes) > 1 and outcomes[-1] == previous_outcome:
                        outcomes[0], outcomes[-1] = outcomes[-1], outcomes[0]
                config["outcome"] = outcomes.pop()
                previous_outcome = config["outcome"]
            platforms.append(cls(**config))

        return platforms

    def land(self):
        if self.revealed:
            return None
        self.revealed = True
        if self.outcome == "spikes":
            self.gone = True
        elif self.outcome in ("false", "temporary"):
            self.timer = 0.001
        return self.outcome

    def update(self, dt):
        if self.timer <= 0:
            return
        self.timer += dt
        duration = 0.18 if self.outcome == "false" else 0.72
        if self.timer >= duration:
            self.gone = True

    def draw(self, surface, camera_x, sprites):
        if self.gone:
            return
        if not self.revealed:
            texture = sprites["bonus"]
        else:
            texture = sprites["bonus_outcomes"][self.outcome]
        surface.blit(texture, (self.rect.x - camera_x, self.rect.y))


class FallingRock:
    def __init__(self, x, trigger_x, warning_duration=0.75, fall_acceleration=1150, max_fall_speed=760, fake=False, on_fire=None):
        self.x = x
        self.trigger_x = trigger_x
        self.warning_duration = warning_duration
        self.fall_acceleration = fall_acceleration
        self.max_fall_speed = max_fall_speed
        self.fake = fake
        self.on_fire = random.choice([True, False]) if on_fire is None else on_fire
        self.warning_timer = None
        self.y = -36.0
        self.velocity_y = 0.0
        self.landed = False
        self.landed_this_frame = False
        self.fall_sound_played = False
        self.smoke_particles = []

    def update(self, dt, player):
        self.landed_this_frame = False
        if self.warning_timer is None and player.centerx >= self.trigger_x:
            self.warning_timer = self.warning_duration
        if self.landed:
            return
        if self.warning_timer is None:
            return
        if self.warning_timer > 0:
            self.warning_timer = max(0.0, self.warning_timer - dt)
            return
        self.velocity_y = min(self.max_fall_speed, self.velocity_y + self.fall_acceleration * dt)
        self.y += self.velocity_y * dt
        if self.y >= GROUND_Y - 30:
            self.y = GROUND_Y - 30
            self.landed = True
            self.landed_this_frame = True

        smoke_amount = max(1, int(5 * dt * 60))
        for _ in range(smoke_amount):
            self.smoke_particles.append({
                "x": self.x + random.uniform(-12, 12),
                "y": self.y + random.uniform(0, 18),
                "size": random.uniform(6, 14),
                "life": random.uniform(0.4, 0.9),
                "max_life": random.uniform(0.4, 0.9),
                "velocity_y": random.uniform(-18, 2),
                "velocity_x": random.uniform(-12, 12),
            })

        for particle in self.smoke_particles:
            particle["life"] -= dt
            particle["x"] += particle["velocity_x"] * dt
            particle["y"] += particle["velocity_y"] * dt
            particle["velocity_y"] -= 10 * dt
            particle["size"] += 3 * dt

        self.smoke_particles = [p for p in self.smoke_particles if p["life"] > 0]

    def draw(self, surface, camera_x, rock_sprite, warning_sprite):
        if self.warning_timer is None:
            return
        screen_x = self.x - camera_x
        if self.warning_timer > 0:
            larger_warning = pygame.transform.smoothscale(warning_sprite, (warning_sprite.get_width() + 12, warning_sprite.get_height() + 12))
            surface.blit(larger_warning, larger_warning.get_rect(midbottom=(screen_x, GROUND_Y - 8)))

            rock_preview = pygame.transform.smoothscale(rock_sprite, (rock_sprite.get_width() + 18, rock_sprite.get_height() + 18))
            preview_alpha = max(70, int(255 * (1.0 - self.warning_timer / max(self.warning_duration, 0.05))))
            rock_preview.set_alpha(preview_alpha)
            surface.blit(rock_preview, rock_preview.get_rect(midtop=(screen_x, 30)))

            if self.on_fire:
                flame = pygame.Surface((rock_preview.get_width() + 24, rock_preview.get_height() + 40), pygame.SRCALPHA)
                for offset, color, size in [
                    (0, (255, 178, 65, 180), (rock_preview.get_width() * 0.54, 26)),
                    (6, (255, 98, 0, 190), (rock_preview.get_width() * 0.42, 22)),
                    (12, (255, 225, 120, 170), (rock_preview.get_width() * 0.28, 16)),
                ]:
                    pygame.draw.ellipse(flame, color, (rock_preview.get_width() * 0.22, rock_preview.get_height() + 8 + offset, *size))
                surface.blit(flame, flame.get_rect(midtop=(screen_x, 50)))
        else:
            larger_rock = pygame.transform.smoothscale(rock_sprite, (rock_sprite.get_width() + 18, rock_sprite.get_height() + 18))

            if self.on_fire:
                flame = pygame.Surface((larger_rock.get_width() + 26, larger_rock.get_height() + 44), pygame.SRCALPHA)
                for color, rect in [
                    ((255, 220, 100, 200), (8, 8, larger_rock.get_width() * 0.58, 18)),
                    ((255, 120, 0, 220), (12, 18, larger_rock.get_width() * 0.46, 22)),
                    ((255, 70, 0, 180), (18, 30, larger_rock.get_width() * 0.32, 16)),
                ]:
                    pygame.draw.ellipse(flame, color, rect)
                flame_rect = flame.get_rect(midtop=(screen_x, round(self.y) - 26))
                surface.blit(flame, flame_rect)

                for particle in self.smoke_particles:
                    alpha = int(180 * (particle["life"] / particle["max_life"]))
                    smoke = pygame.Surface((max(4, particle["size"]), max(4, particle["size"])), pygame.SRCALPHA)
                    pygame.draw.ellipse(smoke, (180, 180, 180), smoke.get_rect())
                    smoke.set_alpha(alpha)
                    smoke_rect = smoke.get_rect(center=(particle["x"] - camera_x, particle["y"]))
                    surface.blit(smoke, smoke_rect)

                fire_rock = larger_rock.copy()
                fire_rock.fill((255, 120, 0), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(fire_rock, fire_rock.get_rect(midtop=(screen_x, round(self.y))))
            else:
                surface.blit(larger_rock, larger_rock.get_rect(midtop=(screen_x, round(self.y))))

    def collides(self, player):
        if self.warning_timer is None or self.warning_timer > 0 or (self.landed and not self.landed_this_frame):
            return False
        rock_rect = pygame.Rect(round(self.x - 20), round(self.y), 40, 30)
        return player.colliderect(rock_rect)


class SpikeTrap:
    def __init__(self, x, count=4, kind="on_jump", trigger_x=None, base_y=GROUND_Y):
        self.x = x
        self.count = count
        self.kind = kind
        self.trigger_x = trigger_x
        self.base_y = base_y
        self.activated_at = 0.0 if kind == "static" else None

    def update(self, now, player, jumped=False, landed=False):
        if self.activated_at is None:
            crossed_trigger = self.trigger_x is not None and player.centerx > self.trigger_x
            triggered = (
                (self.kind == "on_jump" and jumped)
                or (self.kind == "on_land" and landed)
                or (self.kind == "hidden" and crossed_trigger)
                or (self.kind == "fake" and landed and player.bottom >= self.base_y - 2
                    and player.right > self.x and player.left < self.x + self.count * 25)
            )
            if triggered:
                self.activated_at = now

    def active(self, now):
        if self.kind == "fake":
            return False
        return self.kind == "static" or (self.activated_at is not None and now - self.activated_at > 0.28)

    def draw(self, surface, camera_x, now, sprite):
        if self.activated_at is None:
            return
        elapsed = now - self.activated_at
        rise_duration = 0.1 if self.kind == "fake" else 0.28
        height = 25 if self.kind == "static" else int(25 * min(1.0, elapsed / rise_duration))
        if height <= 0:
            return
        rendered = pygame.transform.smoothscale(sprite, (self.count * 25, height + 12))
        surface.blit(rendered, (self.x - camera_x, self.base_y - rendered.get_height()))

    def collides(self, player, now, sprite):
        if self.kind == "fake" or not self.active(now):
            return False
        elapsed = now - self.activated_at
        height = 25 if self.kind == "static" else int(25 * min(1.0, elapsed / 0.28))
        if height <= 0:
            return False
        width = self.count * 25
        rendered = pygame.transform.smoothscale(sprite, (width, height + 12))
        spike_height = max(1, round(rendered.get_height() * 0.72))
        key = (width, spike_height)
        if not hasattr(self, "_hit_masks"):
            self._hit_masks = {}
        if key not in self._hit_masks:
            spike_surface = pygame.Surface((width, spike_height), pygame.SRCALPHA)
            spike_surface.blit(rendered, (0, 0), pygame.Rect(0, 0, width, spike_height))
            self._hit_masks[key] = pygame.mask.from_surface(spike_surface)
        hit_mask = self._hit_masks[key]
        spike_rect = pygame.Rect(self.x, self.base_y - rendered.get_height(), width, spike_height)
        player_mask = pygame.mask.Mask(player.size, fill=True)
        offset = player.left - spike_rect.left, player.top - spike_rect.top
        return hit_mask.overlap(player_mask, offset) is not None