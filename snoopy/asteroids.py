import pygame
import random
import math
import os

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 28)
big_font = pygame.font.SysFont("consolas", 72)

try:
    laser_sound = pygame.mixer.Sound("laser.wav")
except:
    laser_sound = None

try:
    explosion_sound = pygame.mixer.Sound("explosion.wav")
except:
    explosion_sound = None

GOLD_UNLOCK_SCORE = 10000

SHIP_SKINS = [
    {"color": (50,220,255), "shape": [(20,0),(-15,12),(-10,0),(-15,-12)]},
    {"color": (255,80,80), "shape": [(22,0),(-18,15),(-5,0),(-18,-15)]},
    {"color": (80,255,120), "shape": [(20,0),(-10,18),(-20,0),(-10,-18)]},
    {"color": (255,220,50), "shape": [(24,0),(-14,10),(-8,0),(-14,-10)]},
    {"color": (200,120,255), "shape": [(20,0),(-20,14),(-5,0),(-20,-14)]},
    {"color": (255,215,0), "shape": [(24,0),(-18,16),(-8,0),(-18,-16)], "gold": True}
]


def wrap_position(obj):
    if obj.x > WIDTH:
        obj.x = 0
    if obj.x < 0:
        obj.x = WIDTH
    if obj.y > HEIGHT:
        obj.y = 0
    if obj.y < 0:
        obj.y = HEIGHT


def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)


class Bullet:
    def __init__(self, x, y, angle, color):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10
        self.radius = 3
        self.life = 120
        self.color = color

    def update(self):
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y -= math.sin(rad) * self.speed
        wrap_position(self)
        self.life -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 4)


class Player:
    def __init__(self, x, y, skin, controls):
        self.x = x
        self.y = y
        self.skin = skin
        self.color = skin["color"]
        self.controls = controls
        self.angle = 90
        self.vel_x = 0
        self.vel_y = 0
        self.acceleration = 0.2
        self.rotation_speed = 4
        self.friction = 0.99
        self.radius = 18
        self.bullets = []
        self.cooldown = 0
        self.lives = 3
        self.score = 0
        self.invincible = 120

    def update(self, keys):
        if keys[self.controls['left']]:
            self.angle += self.rotation_speed

        if keys[self.controls['right']]:
            self.angle -= self.rotation_speed

        if keys[self.controls['forward']]:
            rad = math.radians(self.angle)
            self.vel_x += math.cos(rad) * self.acceleration
            self.vel_y -= math.sin(rad) * self.acceleration

        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= self.friction
        self.vel_y *= self.friction

        wrap_position(self)

        if self.cooldown > 0:
            self.cooldown -= 1

        if self.invincible > 0:
            self.invincible -= 1

        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.life <= 0:
                self.bullets.remove(bullet)

    def shoot(self):
        if self.skin.get('gold'):
            for spread in [-6, -3, 0, 3, 6]:
                self.bullets.append(Bullet(self.x, self.y, self.angle + spread, self.color))
            self.cooldown = 6
        else:
            if self.cooldown == 0:
                self.bullets.append(Bullet(self.x, self.y, self.angle, self.color))
                self.cooldown = 15

        if laser_sound:
            laser_sound.play()

    def draw(self, surface):
        rad = math.radians(self.angle)
        transformed = []

        for px, py in self.skin['shape']:
            rx = px * math.cos(rad) - py * math.sin(rad)
            ry = px * math.sin(rad) + py * math.cos(rad)
            transformed.append((self.x + rx, self.y - ry))

        if self.invincible % 10 < 5:
            if self.skin.get('gold'):
                pygame.draw.polygon(surface, self.color, transformed)
            else:
                pygame.draw.polygon(surface, self.color, transformed, 2)

        for bullet in self.bullets:
            bullet.draw(surface)

    def respawn(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(100, HEIGHT - 100)
        self.vel_x = 0
        self.vel_y = 0
        self.invincible = 180


class Asteroid:
    def __init__(self, x, y, size=3):
        self.x = x
        self.y = y
        self.size = size

        self.radius = {3: 60, 2: 35, 1: 20}[size]

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 3)

        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed

        self.points = []

        total = random.randint(10, 16)

        for i in range(total):
            a = (math.pi * 2 / total) * i
            offset = random.uniform(0.7, 1.3)
            r = self.radius * offset
            self.points.append((math.cos(a) * r, math.sin(a) * r))

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        wrap_position(self)

    def draw(self, surface):
        transformed = []

        for point in self.points:
            transformed.append((self.x + point[0], self.y + point[1]))

        pygame.draw.polygon(surface, WHITE, transformed, 2)

    def split(self):
        if self.size > 1:
            return [Asteroid(self.x, self.y, self.size - 1), Asteroid(self.x, self.y, self.size - 1)]
        return []


def create_wave(amount):
    asteroids = []

    for _ in range(amount):
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            x = random.randint(0, WIDTH)
            y = -50
        elif side == "bottom":
            x = random.randint(0, WIDTH)
            y = HEIGHT + 50
        elif side == "left":
            x = -50
            y = random.randint(0, HEIGHT)
        else:
            x = WIDTH + 50
            y = random.randint(0, HEIGHT)

        asteroids.append(Asteroid(x, y, 3))

    return asteroids


def get_highscore():
    if os.path.exists("highscore.txt"):
        with open("highscore.txt", "r") as f:
            return int(f.read())
    return 0


def save_highscore(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))


def start_screen():
    players = 2
    skin1 = 0
    skin2 = 1
    game_mode = "classic"

    while True:
        screen.fill(BLACK)

        title = big_font.render("ASTEROIDS", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        screen.blit(font.render(f"Players: {players} (1 ou 2)", True, WHITE), (100, 220))
        screen.blit(font.render(f"Modo: {game_mode}", True, WHITE), (100, 260))
        screen.blit(font.render(f"Recorde: {get_highscore()}", True, WHITE), (100, 270))
        screen.blit(font.render("Q/E muda skin P1", True, WHITE), (100, 350))
        screen.blit(font.render("Setas muda skin P2", True, WHITE), (100, 390))
        screen.blit(font.render("M = modo batalha", True, WHITE), (100, 560))
        screen.blit(font.render("R = resetar recorde", True, WHITE), (100, 600))
        screen.blit(font.render("ENTER para iniciar", True, WHITE), (100, 640))

        available_skins = SHIP_SKINS[:5]

        if get_highscore() >= GOLD_UNLOCK_SCORE:
            unlock_text = font.render("NAVE DOURADA DESBLOQUEADA", True, (255,215,0))
            screen.blit(unlock_text, (100, 650))
            available_skins = SHIP_SKINS

        for i, skin in enumerate(available_skins):
            preview = []
            center_x = 650 + i * 110
            center_y = 450

            for px, py in skin['shape']:
                preview.append((center_x + px, center_y + py))

            selected = (i == skin1)

            if skin.get('gold'):
                pygame.draw.polygon(screen, skin['color'], preview)
            pygame.draw.polygon(screen, skin['color'], preview, 3)

            if selected:
                pygame.draw.circle(screen, skin['color'], (center_x, center_y), 45, 3)

        if players == 2:
            for i, skin in enumerate(available_skins):
                center_x = 650 + i * 110
                center_y = 560

                preview = []

                for px, py in skin['shape']:
                    preview.append((center_x + px, center_y + py))

                selected = (i == skin2)

                if skin.get('gold'):
                    pygame.draw.polygon(screen, skin['color'], preview)
                else:
                    pygame.draw.polygon(screen, skin['color'], preview, 3)

                if selected:
                    pygame.draw.circle(screen, skin['color'], (center_x, center_y), 45, 3)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    players = 1

                if event.key == pygame.K_2:
                    players = 2

                if event.key == pygame.K_q:
                    skin1 = (skin1 - 1) % len(available_skins)

                if event.key == pygame.K_e:
                    skin1 = (skin1 + 1) % len(available_skins)

                if event.key == pygame.K_LEFT:
                    skin2 = (skin2 - 1) % len(available_skins)

                if event.key == pygame.K_RIGHT:
                    skin2 = (skin2 + 1) % len(available_skins)

                if event.key == pygame.K_m:
                    game_mode = "battle" if game_mode == "classic" else "classic"

                if event.key == pygame.K_r:
                    save_highscore(0)

                if event.key == pygame.K_RETURN:
                    return players, skin1, skin2, game_mode


def game_over_screen():
    while True:
        screen.fill(BLACK)

        title = big_font.render("GAME OVER", True, (255, 60, 60))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 300))
        screen.blit(font.render("R para reiniciar", True, WHITE), (WIDTH // 2 - 120, 420))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return


def main_game(players_count, skin1, skin2, game_mode):
    player1 = Player(WIDTH * 0.3, HEIGHT // 2, SHIP_SKINS[skin1], {
        'forward': pygame.K_w,
        'left': pygame.K_a,
        'right': pygame.K_d
    })

    player2 = None

    if players_count == 2:
        player2 = Player(WIDTH * 0.7, HEIGHT // 2, SHIP_SKINS[skin2], {
            'forward': pygame.K_UP,
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT
        })

    asteroids = create_wave(5) if game_mode == "classic" else []
    wave = 1

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()

                if event.key == pygame.K_SPACE:
                    player1.shoot()

                if player2 and event.key == pygame.K_RETURN:
                    player2.shoot()

        keys = pygame.key.get_pressed()

        player1.update(keys)

        if player2:
            player2.update(keys)

        for asteroid in asteroids:
            asteroid.update()

        if 'players' not in locals():
            players = [player1]

            if player2:
                players.append(player2)

        for player in players:
            for bullet in player.bullets[:]:
                for asteroid in asteroids[:]:
                    if distance(bullet.x, bullet.y, asteroid.x, asteroid.y) < asteroid.radius:
                        if bullet in player.bullets:
                            player.bullets.remove(bullet)

                        if asteroid in asteroids:
                            asteroids.remove(asteroid)

                        asteroids.extend(asteroid.split())

                        if explosion_sound:
                            explosion_sound.play()

                        player.score += {3: 20, 2: 50, 1: 100}[asteroid.size]
                        break

        if game_mode == "battle" and player2:
            for bullet in player1.bullets[:]:
                if distance(bullet.x, bullet.y, player2.x, player2.y) < player2.radius:
                    player1.score += 100
                    player2.lives -= 1
                    player1.bullets.remove(bullet)

                    if player2.lives > 0:
                        player2.respawn()
                    else:
                        save_highscore(max(player1.score, player2.score))
                        return

            for bullet in player2.bullets[:]:
                if distance(bullet.x, bullet.y, player1.x, player1.y) < player1.radius:
                    player2.score += 100
                    player1.lives -= 1
                    player2.bullets.remove(bullet)

                    if player1.lives > 0:
                        player1.respawn()
                    else:
                        save_highscore(max(player1.score, player2.score))
                        return

        for player in players[:]:
            if player.invincible <= 0:
                for asteroid in asteroids:
                    if distance(player.x, player.y, asteroid.x, asteroid.y) < asteroid.radius + player.radius:
                        player.lives -= 1

                        if player.lives > 0:
                            player.respawn()
                        else:
                            players.remove(player)

                        break

        alive_players = len(players)

        if alive_players == 0:
            total = max(player1.score, player2.score if player2 else 0)

            if total > get_highscore():
                save_highscore(total)

            return

        if game_mode == "classic":
            if len(asteroids) == 0:
                wave += 1
                asteroids = create_wave(4 + wave)

        screen.fill(BLACK)

        for asteroid in asteroids:
            asteroid.draw(screen)

        if player1 in players:
            player1.draw(screen)

        if player2 and player2 in players:
            player2.draw(screen)

        if player1 in players:
            screen.blit(font.render(f"P1 {player1.score}  Vidas {player1.lives}", True, player1.color), (20, 20))
        else:
            screen.blit(font.render(f"P1 ELIMINADO", True, player1.color), (20, 20))

        if player2:
            if player2 in players:
                screen.blit(font.render(f"P2 {player2.score}  Vidas {player2.lives}", True, player2.color), (20, 60))
            else:
                screen.blit(font.render(f"P2 ELIMINADO", True, player2.color), (20, 60))

        if game_mode == "classic":
            screen.blit(font.render(f"Wave {wave}", True, WHITE), (WIDTH - 200, 20))
        else:
            screen.blit(font.render("MODO BATALHA", True, WHITE), (WIDTH - 320, 20))

        pygame.display.flip()


while True:
    players, skin1, skin2, game_mode = start_screen()
    main_game(players, skin1, skin2, game_mode)
    game_over_screen()
