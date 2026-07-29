import pygame
import random
import math
import os
import struct
from array import array

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)

clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 28)
BIG = pygame.font.SysFont("Arial", 60)

TITLE_FONT = pygame.font.SysFont("Impact", 82)
MENU_FONT = pygame.font.SysFont("Trebuchet MS", 34)
SMALL_FONT = pygame.font.SysFont("Consolas", 24)
GAME_OVER_FONT = pygame.font.SysFont("Impact", 96)

COIN_FILE = "coins.txt"
SKIN_FILE = "skins.txt"

ship_skin = 0

stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(120)]

# FUNDO ESPACIAL REALISTA
def create_space_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    bg.fill((4, 4, 10))

    # Fundo espacial limpo: apenas estrelas, sem nébulas
    for _ in range(280):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        brilho = random.randint(130, 230)
        pygame.draw.circle(bg, (brilho, brilho, min(255, brilho + 25)), (x, y), 1)

    # Estrelas maiores com brilho discreto
    for _ in range(65):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)

        pygame.draw.circle(bg, (12, 16, 26), (x, y), 2)
        pygame.draw.circle(bg, (210, 215, 225), (x, y), 1)

    # Algumas estrelas em cruz
    for _ in range(20):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)

        pygame.draw.line(bg, (180, 210, 255), (x - 4, y), (x + 4, y), 1)
        pygame.draw.line(bg, (180, 210, 255), (x, y - 4), (x, y + 4), 1)
        pygame.draw.circle(bg, (255, 255, 255), (x, y), 1)

    return bg


SPACE_BACKGROUND = create_space_background()


def draw_space_background():
    # Fundo pré-renderizado para evitar travamentos e erros em todas as telas.
    screen.blit(SPACE_BACKGROUND, (0, 0))


# ÁUDIO PROCEDURAL — trilhas separadas + SFX detalhados
# Versão segura: não grava arquivos .wav e não usa pygame.mixer.music.load.
# Tudo é gerado em memória e, se o áudio falhar, o jogo continua sem travar.
AUDIO_ENABLED = False
SOUNDS = {}
CURRENT_MUSIC_MODE = None
MUSIC_CHANNEL = None


def clamp_audio(v):
    return max(-32767, min(32767, int(v)))


def make_sound_from_samples(samples):
    data = array("h")
    for left, right in samples:
        data.append(clamp_audio(left * 32767))
        data.append(clamp_audio(right * 32767))
    return pygame.mixer.Sound(buffer=data.tobytes())


def synth_sound(kind="square", freq=440, duration=0.12, volume=0.35, slide=0.0, noise=0.0, tremolo=0.0):
    sample_rate = 44100
    total = max(1, int(sample_rate * duration))
    samples = []

    for i in range(total):
        t = i / sample_rate
        life = i / total
        env = (1.0 - life) ** 1.8
        f = max(35, freq + slide * life)
        phase = 2 * math.pi * f * t

        if kind == "square":
            sample = 1.0 if math.sin(phase) >= 0 else -1.0
        elif kind == "saw":
            sample = 2.0 * ((f * t) % 1.0) - 1.0
        elif kind == "tri":
            sample = 2.0 * abs(2.0 * ((f * t) % 1.0) - 1.0) - 1.0
        elif kind == "noise":
            sample = random.uniform(-1.0, 1.0)
        else:
            sample = math.sin(phase)

        if noise > 0:
            sample = sample * (1.0 - noise) + random.uniform(-1.0, 1.0) * noise

        if tremolo > 0:
            sample *= 0.65 + 0.35 * math.sin(2 * math.pi * tremolo * t)

        sample *= env * volume
        samples.append((sample, sample))

    return make_sound_from_samples(samples)


def synth_layered_sound(layers):
    sample_rate = 44100
    duration = max(layer.get("duration", 0.1) + layer.get("delay", 0.0) for layer in layers)
    total = max(1, int(sample_rate * duration))
    left = [0.0] * total
    right = [0.0] * total

    for layer in layers:
        kind = layer.get("kind", "sine")
        freq = layer.get("freq", 440)
        slide = layer.get("slide", 0.0)
        volume = layer.get("volume", 0.2)
        noise = layer.get("noise", 0.0)
        pan = layer.get("pan", 0.0)
        dur = layer.get("duration", duration)
        delay = int(sample_rate * layer.get("delay", 0.0))
        decay = layer.get("decay", 1.8)
        layer_total = max(1, int(sample_rate * dur))

        for n in range(layer_total):
            idx = n + delay
            if idx >= total:
                break
            t = n / sample_rate
            life = n / layer_total
            env = (1.0 - life) ** decay
            f = max(35, freq + slide * life)
            phase = 2 * math.pi * f * t

            if kind == "square":
                sample = 1.0 if math.sin(phase) >= 0 else -1.0
            elif kind == "saw":
                sample = 2.0 * ((f * t) % 1.0) - 1.0
            elif kind == "tri":
                sample = 2.0 * abs(2.0 * ((f * t) % 1.0) - 1.0) - 1.0
            elif kind == "noise":
                sample = random.uniform(-1.0, 1.0)
            else:
                sample = math.sin(phase)

            if noise > 0:
                sample = sample * (1.0 - noise) + random.uniform(-1.0, 1.0) * noise

            sample *= env * volume
            left[idx] += sample * (1.0 - max(0, pan))
            right[idx] += sample * (1.0 + min(0, pan))

    return make_sound_from_samples(zip(left, right))


def synth_music_loop(mode):
    sample_rate = 44100

    if mode == "menu":
        bpm = 104
        steps = 48
        bass_notes = [65.41, 65.41, 87.31, 98.0, 73.42, 73.42, 98.0, 116.54]
        arp_notes = [261.63, 329.63, 392.0, 493.88, 392.0, 329.63, 261.63, 196.0]
        energy = 0.55
    elif mode == "game_over":
        bpm = 82
        steps = 40
        bass_notes = [55.0, 65.41, 49.0, 43.65, 55.0, 41.2, 49.0, 36.71]
        arp_notes = [220.0, 261.63, 329.63, 293.66, 246.94, 196.0, 174.61, 164.81]
        energy = 0.42
    else:
        bpm = 156
        steps = 64
        bass_notes = [55, 65.41, 77.78, 87.31, 98.0, 116.54, 130.81, 155.56]
        arp_notes = [440, 523.25, 392, 659.25, 587.33, 493.88, 783.99, 659.25]
        energy = 0.72

    step_time = 60 / bpm / 2
    total_samples = int(step_time * steps * sample_rate)
    samples = []

    for i in range(total_samples):
        t = i / sample_rate
        step = int(t / step_time) % steps
        local = (t % step_time) / step_time

        bass_freq = bass_notes[(step // 4) % len(bass_notes)]
        bass_env = max(0, 1 - local * (2.6 if mode != "game_over" else 1.4))
        bass_wave = 1 if math.sin(2 * math.pi * bass_freq * t) > 0 else -1
        bass = bass_wave * 0.18 * bass_env

        arp_freq = arp_notes[(step * (3 if mode == "game" else 1)) % len(arp_notes)]
        arp_env = max(0, 1 - local * (3.8 if mode == "game" else 2.2))
        arp = math.sin(2 * math.pi * arp_freq * t) * 0.10 * arp_env
        arp += (2 * ((arp_freq * 2 * t) % 1) - 1) * 0.035 * arp_env

        pad_freq = bass_notes[(step // 16) % len(bass_notes)] * (3 if mode == "game_over" else 4)
        pad = math.sin(2 * math.pi * pad_freq * t) * (0.045 if mode != "game" else 0.028)
        pad += math.sin(2 * math.pi * pad_freq * 1.5 * t) * 0.018

        kick = snare = hat = 0

        if mode == "game":
            if step % 8 in (0, 4):
                kick = math.sin(2 * math.pi * (110 - 70 * min(1, local * 2.5)) * t) * max(0, 1 - local * 5) * 0.36
            if step % 8 == 4:
                snare = random.uniform(-1, 1) * max(0, 1 - local * 7) * 0.16
            if step % 2 == 1:
                hat = random.uniform(-1, 1) * max(0, 1 - local * 13) * 0.05
        elif mode == "menu":
            if step % 16 == 0:
                kick = math.sin(2 * math.pi * (80 - 30 * min(1, local * 2.2)) * t) * max(0, 1 - local * 4) * 0.20
            if step % 4 == 2:
                hat = random.uniform(-1, 1) * max(0, 1 - local * 9) * 0.028
        else:
            if step % 16 == 0:
                kick = math.sin(2 * math.pi * (70 - 25 * min(1, local * 2)) * t) * max(0, 1 - local * 3.5) * 0.14
            if step % 8 == 6:
                snare = random.uniform(-1, 1) * max(0, 1 - local * 5) * 0.05

        sample = (bass + arp + pad + kick + snare + hat) * energy
        samples.append((sample, sample * 0.92 + arp * 0.08 - pad * 0.035))

    return make_sound_from_samples(samples)


def set_music(mode):
    global CURRENT_MUSIC_MODE, MUSIC_CHANNEL, AUDIO_ENABLED
    if not AUDIO_ENABLED or CURRENT_MUSIC_MODE == mode:
        return

    try:
        if MUSIC_CHANNEL is None:
            MUSIC_CHANNEL = pygame.mixer.Channel(0)

        MUSIC_CHANNEL.stop()
        track = SOUNDS.get("music_" + mode)
        if track:
            volume = 0.28 if mode == "menu" else 0.34 if mode == "game" else 0.30
            MUSIC_CHANNEL.set_volume(volume)
            MUSIC_CHANNEL.play(track, loops=-1, fade_ms=450)
            CURRENT_MUSIC_MODE = mode
    except Exception:
        AUDIO_ENABLED = False


def init_audio():
    global AUDIO_ENABLED, SOUNDS, MUSIC_CHANNEL

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)

        pygame.mixer.set_num_channels(24)
        MUSIC_CHANNEL = pygame.mixer.Channel(0)

        SOUNDS = {
            # Músicas
            "music_menu": synth_music_loop("menu"),
            "music_game": synth_music_loop("game"),
            "music_game_over": synth_music_loop("game_over"),

            # Tiros
            "shoot_normal": synth_layered_sound([
                {"kind": "square", "freq": 760, "duration": 0.055, "volume": 0.13, "slide": 380},
                {"kind": "sine", "freq": 1180, "duration": 0.045, "volume": 0.09, "slide": -260},
            ]),
            "shoot_wasp": synth_layered_sound([
                {"kind": "tri", "freq": 980, "duration": 0.07, "volume": 0.12, "slide": 520},
                {"kind": "noise", "freq": 420, "duration": 0.05, "volume": 0.04, "noise": 0.85},
            ]),
            "shoot_fast": synth_layered_sound([
                {"kind": "sine", "freq": 1260, "duration": 0.04, "volume": 0.13, "slide": 680},
                {"kind": "square", "freq": 980, "duration": 0.035, "volume": 0.06, "slide": -120},
            ]),
            "shoot_heavy": synth_layered_sound([
                {"kind": "saw", "freq": 210, "duration": 0.18, "volume": 0.22, "slide": -70},
                {"kind": "sine", "freq": 70, "duration": 0.18, "volume": 0.15, "slide": -20},
            ]),
            "shoot_prism": synth_layered_sound([
                {"kind": "sine", "freq": 920, "duration": 0.09, "volume": 0.11, "slide": 420},
                {"kind": "tri", "freq": 1340, "duration": 0.07, "volume": 0.08, "slide": -180},
                {"kind": "noise", "freq": 520, "duration": 0.04, "volume": 0.03, "noise": 0.55},
            ]),

            # Habilidades
            "ability_dash": synth_layered_sound([
                {"kind": "saw", "freq": 330, "duration": 0.26, "volume": 0.16, "slide": 980},
                {"kind": "noise", "freq": 440, "duration": 0.14, "volume": 0.08, "noise": 0.7},
            ]),
            "ability_wasp": synth_layered_sound([
                {"kind": "tri", "freq": 640, "duration": 0.36, "volume": 0.13, "slide": 900},
                {"kind": "square", "freq": 1180, "duration": 0.18, "volume": 0.08, "slide": -300, "delay": 0.04},
                {"kind": "noise", "freq": 600, "duration": 0.22, "volume": 0.06, "noise": 0.65},
            ]),
            "ability_ruby": synth_layered_sound([
                {"kind": "saw", "freq": 520, "duration": 0.28, "volume": 0.18, "slide": -240},
                {"kind": "sine", "freq": 1560, "duration": 0.12, "volume": 0.08, "slide": 400},
            ]),
            "ability_titan": synth_layered_sound([
                {"kind": "sine", "freq": 110, "duration": 0.46, "volume": 0.24, "slide": -70},
                {"kind": "tri", "freq": 440, "duration": 0.32, "volume": 0.11, "slide": 340},
                {"kind": "noise", "freq": 90, "duration": 0.38, "volume": 0.08, "noise": 0.8},
            ]),
            "ability_blackhole": synth_layered_sound([
                {"kind": "saw", "freq": 220, "duration": 0.58, "volume": 0.15, "slide": -150},
                {"kind": "sine", "freq": 60, "duration": 0.65, "volume": 0.18, "slide": -25},
            ]),
            "ability_cyan": synth_layered_sound([
                {"kind": "square", "freq": 740, "duration": 0.30, "volume": 0.13, "slide": 520},
                {"kind": "tri", "freq": 1040, "duration": 0.30, "volume": 0.10, "slide": -220},
            ]),
            "ability_prism": synth_layered_sound([
                {"kind": "sine", "freq": 420, "duration": 0.65, "volume": 0.12, "slide": 1220},
                {"kind": "square", "freq": 860, "duration": 0.62, "volume": 0.08, "slide": 980, "delay": 0.03},
                {"kind": "tri", "freq": 1320, "duration": 0.48, "volume": 0.06, "slide": 420, "delay": 0.05},
            ]),

            # Impactos / UI
            "hit": synth_sound("noise", 260, 0.12, 0.28, -40, 0.65),
            "explosion": synth_sound("noise", 120, 0.32, 0.42, -70, 0.85),
            "coin": synth_sound("sine", 980, 0.16, 0.28, 620, 0.0),
            "select": synth_sound("sine", 620, 0.08, 0.18, 160, 0.0),
            "buy": synth_sound("tri", 740, 0.28, 0.28, 540, 0.02),
            "damage": synth_sound("saw", 150, 0.22, 0.34, -70, 0.18),
            "ship_defeat_explosion": synth_layered_sound([
                {"kind": "noise", "freq": 95, "duration": 0.95, "volume": 0.36, "slide": -60, "noise": 0.95, "decay": 1.2},
                {"kind": "sine", "freq": 65, "duration": 0.70, "volume": 0.24, "slide": -35, "decay": 1.0},
                {"kind": "saw", "freq": 220, "duration": 0.30, "volume": 0.18, "slide": -120, "delay": 0.04},
            ]),
            "game_over": synth_sound("saw", 180, 0.65, 0.36, -140, 0.15),
        }

        SOUNDS["shoot"] = SOUNDS["shoot_normal"]
        SOUNDS["heavy"] = SOUNDS["shoot_heavy"]
        SOUNDS["ability"] = SOUNDS["ability_dash"]

        for name, snd in SOUNDS.items():
            if not name.startswith("music_"):
                snd.set_volume(0.55)

        AUDIO_ENABLED = True
        set_music("menu")

    except Exception:
        SOUNDS = {}
        AUDIO_ENABLED = False


def play_sound(name):
    if AUDIO_ENABLED and name in SOUNDS:
        try:
            SOUNDS[name].play()
        except Exception:
            pass


init_audio()

# NAVES MAIS ELABORADAS
# Cada modelo tem uma silhueta própria e uma cor única,
# inspirado no visual arcade/mobile de jogos de guerra espacial:
# casco central forte, asas angulares, cockpit destacado e motores brilhantes.
SHIP_MODELS = [
    {
        "name": "Falcon Azul",
        "color": (0, 180, 255),
        "accent": (130, 240, 255),
        "engine": (50, 120, 255),
        "hull": [(32,0),(16,10),(-6,12),(-22,22),(-18,7),(-32,0),(-18,-7),(-22,-22),(-6,-12),(16,-10)],
        "wing_l": [(-2,-10),(-28,-28),(-20,-8),(-8,-2)],
        "wing_r": [(-2,10),(-28,28),(-20,8),(-8,2)],
        "cockpit": [(18,0),(6,-5),(-4,0),(6,5)],
        "details": [[(2,-10),(-12,-15),(-8,-7)], [(2,10),(-12,15),(-8,7)]],
        "engines": [(-26,-6),(-36,-10),(-30,-2), (-26,6),(-36,10),(-30,2)]
    },
    {
        "name": "Vespa Verde",
        "color": (70, 255, 120),
        "accent": (210, 255, 180),
        "engine": (0, 255, 180),
        "hull": [(34,0),(12,8),(-4,18),(-12,8),(-30,6),(-18,0),(-30,-6),(-12,-8),(-4,-18),(12,-8)],
        "wing_l": [(0,-11),(-18,-34),(-26,-16),(-9,-6)],
        "wing_r": [(0,11),(-18,34),(-26,16),(-9,6)],
        "cockpit": [(20,0),(8,-6),(-2,0),(8,6)],
        "details": [[(8,-8),(-10,-18),(-6,-8)], [(8,8),(-10,18),(-6,8)]],
        "engines": [(-24,-4),(-38,-8),(-28,0), (-24,4),(-38,8),(-28,0)]
    },
    {
        "name": "Lança Rubi",
        "color": (255, 70, 70),
        "accent": (255, 180, 120),
        "engine": (255, 140, 0),
        "hull": [(38,0),(10,7),(-8,18),(-4,6),(-30,10),(-18,0),(-30,-10),(-4,-6),(-8,-18),(10,-7)],
        "wing_l": [(2,-8),(-14,-30),(-24,-12),(-8,-3)],
        "wing_r": [(2,8),(-14,30),(-24,12),(-8,3)],
        "cockpit": [(24,0),(8,-4),(-6,0),(8,4)],
        "details": [[(2,-14),(-8,-18),(-4,-7)], [(2,14),(-8,18),(-4,7)]],
        "engines": [(-24,-7),(-36,-12),(-30,-2), (-24,7),(-36,12),(-30,2)]
    },
    {
        "name": "Titã Dourado",
        "color": (255, 190, 40),
        "accent": (255, 245, 150),
        "engine": (255, 90, 20),
        "hull": [(36,0),(18,14),(-6,16),(-20,26),(-26,10),(-36,0),(-26,-10),(-20,-26),(-6,-16),(18,-14)],
        "wing_l": [(4,-12),(-18,-36),(-30,-18),(-10,-6)],
        "wing_r": [(4,12),(-18,36),(-30,18),(-10,6)],
        "cockpit": [(18,0),(4,-7),(-8,0),(4,7)],
        "details": [[(10,-12),(-12,-18),(-8,-8)], [(10,12),(-12,18),(-8,8)]],
        "engines": [(-30,-9),(-44,-14),(-34,-3), (-30,9),(-44,14),(-34,3), (-34,0),(-48,0),(-36,5)]
    },
    {
        "name": "Nebula roxa",
        "color": (210, 80, 255),
        "accent": (255, 180, 255),
        "engine": (120, 80, 255),
        "hull": [(30,0),(8,12),(-8,22),(-2,8),(-28,14),(-18,0),(-28,-14),(-2,-8),(-8,-22),(8,-12)],
        "wing_l": [(-4,-9),(-24,-32),(-34,-14),(-12,-4)],
        "wing_r": [(-4,9),(-24,32),(-34,14),(-12,4)],
        "cockpit": [(16,0),(3,-6),(-10,0),(3,6)],
        "details": [[(5,-13),(-15,-20),(-7,-8)], [(5,13),(-15,20),(-7,8)]],
        "engines": [(-26,-7),(-40,-12),(-31,-1), (-26,7),(-40,12),(-31,1)]
    },
    {
        "name": "Cometa Ciano",
        "color": (0, 255, 220),
        "accent": (190, 255, 245),
        "engine": (0, 140, 255),
        "hull": [(40,0),(14,9),(0,16),(-16,8),(-34,12),(-22,0),(-34,-12),(-16,-8),(0,-16),(14,-9)],
        "wing_l": [(4,-8),(-12,-28),(-28,-20),(-10,-5)],
        "wing_r": [(4,8),(-12,28),(-28,20),(-10,5)],
        "cockpit": [(24,0),(10,-5),(-2,0),(10,5)],
        "details": [[(8,-10),(-12,-16),(-5,-7)], [(8,10),(-12,16),(-5,7)]],
        "engines": [(-28,-6),(-42,-10),(-32,-1), (-28,6),(-42,10),(-32,1)]
    },
    {
        "name": "O Prisma",
        "color": (248, 248, 255),
        "accent": (255, 255, 255),
        "engine": (170, 230, 255),
        "rainbow_outline": True,
        "hull": [(40,0),(18,9),(4,15),(-10,18),(-18,11),(-30,8),(-38,0),(-30,-8),(-18,-11),(-10,-18),(4,-15),(18,-9)],
        "wing_l": [(4,-8),(-6,-16),(-24,-30),(-34,-12),(-10,-4)],
        "wing_r": [(4,8),(-6,16),(-24,30),(-34,12),(-10,4)],
        "cockpit": [(24,0),(10,-6),(-2,0),(10,6)],
        "details": [[(12,-10),(0,-14),(-10,-7),(-2,-3)], [(12,10),(0,14),(-10,7),(-2,3)], [(18,0),(4,-3),(-6,0),(4,3)]],
        "engines": [(-30,-8),(-44,-11),(-34,-2), (-30,8),(-44,11),(-34,2), (-33,0),(-47,0),(-36,5)]
    },
]

def rotate_points(points, x, y, a, scale=1):
    rotated = []
    for px, py in points:
        px *= scale
        py *= scale
        rx = px * math.cos(a) - py * math.sin(a)
        ry = px * math.sin(a) + py * math.cos(a)
        rotated.append((x + rx, y + ry))
    return rotated

def draw_ship_model(x, y, a, skin, scale=1, inv=0):
    model = SHIP_MODELS[skin]
    color = model["color"] if inv % 10 < 5 else (90, 90, 90)
    accent = model["accent"] if inv % 10 < 5 else (130, 130, 130)
    engine = model["engine"] if inv % 10 < 5 else (80, 80, 80)

    wing_l = rotate_points(model["wing_l"], x, y, a, scale)
    wing_r = rotate_points(model["wing_r"], x, y, a, scale)
    hull = rotate_points(model["hull"], x, y, a, scale)
    cockpit = rotate_points(model["cockpit"], x, y, a, scale)

    # Asas traseiras
    pygame.draw.polygon(screen, color, wing_l, 0)
    pygame.draw.polygon(screen, color, wing_r, 0)

    # Casco principal
    pygame.draw.polygon(screen, color, hull, 0)
    pygame.draw.polygon(screen, (20, 20, 30), hull, 2)

    # Cockpit
    pygame.draw.polygon(screen, accent, cockpit, 0)
    pygame.draw.polygon(screen, (255, 255, 255), cockpit, 1)

    # Painéis internos
    detail_polys = []
    for detail in model["details"]:
        detail_pts = rotate_points(detail, x, y, a, scale)
        detail_polys.append(detail_pts)
        pygame.draw.polygon(screen, (35, 35, 45), detail_pts, 0)
        pygame.draw.polygon(screen, accent, detail_pts, 1)

    # Motores
    engines = model["engines"]
    for i in range(0, len(engines), 3):
        tri = rotate_points(engines[i:i+3], x, y, a, scale)
        pygame.draw.polygon(screen, engine, tri, 0)

    if model.get("rainbow_outline") and inv % 10 < 5:
        draw_rainbow_polygon_outline(wing_l, max(1, int(2 * scale / 1.5)), 0.00)
        draw_rainbow_polygon_outline(wing_r, max(1, int(2 * scale / 1.5)), 0.12)
        draw_rainbow_polygon_outline(hull, max(1, int(2 * scale / 1.5)), 0.24)
        draw_rainbow_polygon_outline(cockpit, 1, 0.36)
        for idx, detail_pts in enumerate(detail_polys):
            draw_rainbow_polygon_outline(detail_pts, 1, 0.48 + idx * 0.08)


def mix_color(c1, c2, t):
    return tuple(max(0, min(255, int(c1[i] * (1 - t) + c2[i] * t))) for i in range(3))


def rainbow_cycle_color(t):
    return (
        int(128 + 127 * math.sin(math.tau * (t + 0.00))),
        int(128 + 127 * math.sin(math.tau * (t + 0.33))),
        int(128 + 127 * math.sin(math.tau * (t + 0.66)))
    )


def draw_rainbow_polygon_outline(points, width=2, time_shift=0.0):
    base_t = pygame.time.get_ticks() * 0.00035 + time_shift
    total = len(points)
    for i in range(total):
        p1 = points[i]
        p2 = points[(i + 1) % total]
        color = rainbow_cycle_color((base_t + i / max(1, total)) % 1.0)
        pygame.draw.line(screen, color, p1, p2, width)


def scale_polygon(points, amount):
    cx = sum(px for px, _ in points) / len(points)
    cy = sum(py for _, py in points) / len(points)
    return [
        (cx + (px - cx) * amount, cy + (py - cy) * amount)
        for px, py in points
    ]


def draw_ship_showcase(x, y, a, skin, scale=1, locked=False, show_engine_halo=True):
    model = SHIP_MODELS[skin]

    base = model["color"]
    accent = model["accent"]
    engine = model["engine"]

    if locked:
        base = mix_color(base, (92, 92, 98), 0.68)
        accent = mix_color(accent, (150, 150, 155), 0.55)
        engine = mix_color(engine, (100, 100, 105), 0.72)

    deep = mix_color(base, (18, 22, 34), 0.55)
    highlight = mix_color(base, (255, 255, 255), 0.25)
    glow = mix_color(engine, (255, 255, 255), 0.30)
    panel_dark = mix_color(base, (16, 20, 30), 0.72)
    line_dark = mix_color(base, (10, 12, 18), 0.70)

    hull_pts = rotate_points(model["hull"], x, y, a, scale)
    wing_l_pts = rotate_points(model["wing_l"], x, y, a, scale)
    wing_r_pts = rotate_points(model["wing_r"], x, y, a, scale)
    cockpit_pts = rotate_points(model["cockpit"], x, y, a, scale)

    # Sombra suave
    shadow_offset = 12 * max(1, scale / 3.2)
    shadow_hull = rotate_points(model["hull"], x + shadow_offset, y + shadow_offset, a, scale)
    shadow_wl = rotate_points(model["wing_l"], x + shadow_offset, y + shadow_offset, a, scale)
    shadow_wr = rotate_points(model["wing_r"], x + shadow_offset, y + shadow_offset, a, scale)
    pygame.draw.polygon(screen, (0, 0, 0), shadow_wl, 0)
    pygame.draw.polygon(screen, (0, 0, 0), shadow_wr, 0)
    pygame.draw.polygon(screen, (0, 0, 0), shadow_hull, 0)

    # Halo opcional dos motores no preview
    engine_points = model["engines"]
    if show_engine_halo:
        for i in range(0, len(engine_points), 3):
            tri = rotate_points(engine_points[i:i+3], x, y, a, scale)
            cx = sum(px for px, _ in tri) / 3
            cy = sum(py for _, py in tri) / 3
            for r in range(30, 6, -8):
                pygame.draw.circle(screen, glow, (int(cx), int(cy)), int(r * max(1, scale / 3.6)), 1)

    # Camada inferior/volume
    pygame.draw.polygon(screen, deep, wing_l_pts, 0)
    pygame.draw.polygon(screen, deep, wing_r_pts, 0)
    pygame.draw.polygon(screen, deep, hull_pts, 0)

    wing_l_inner = scale_polygon(wing_l_pts, 0.78)
    wing_r_inner = scale_polygon(wing_r_pts, 0.78)
    hull_inner = scale_polygon(hull_pts, 0.88)

    pygame.draw.polygon(screen, base, wing_l_inner, 0)
    pygame.draw.polygon(screen, base, wing_r_inner, 0)
    pygame.draw.polygon(screen, base, hull_inner, 0)

    # Placas e linhas estruturais
    for pts in (wing_l_pts, wing_r_pts, hull_pts):
        pygame.draw.polygon(screen, line_dark, pts, 3)
        inner = scale_polygon(pts, 0.90)
        pygame.draw.polygon(screen, highlight, inner, 1)

        for j in range(len(inner)):
            p1 = inner[j]
            p2 = inner[(j + 1) % len(inner)]
            mid1 = ((p1[0] * 0.75 + p2[0] * 0.25), (p1[1] * 0.75 + p2[1] * 0.25))
            mid2 = ((p1[0] * 0.25 + p2[0] * 0.75), (p1[1] * 0.25 + p2[1] * 0.75))
            pygame.draw.line(screen, panel_dark, mid1, mid2, 2)

    if model.get("rainbow_outline") and not locked:
        draw_rainbow_polygon_outline(wing_l_pts, 3, 0.00)
        draw_rainbow_polygon_outline(wing_r_pts, 3, 0.14)
        draw_rainbow_polygon_outline(hull_pts, 3, 0.28)

    # Painéis extras das asas
    wing_tip_l = scale_polygon(wing_l_pts, 0.52)
    wing_tip_r = scale_polygon(wing_r_pts, 0.52)
    pygame.draw.polygon(screen, mix_color(accent, base, 0.35), wing_tip_l, 0)
    pygame.draw.polygon(screen, mix_color(accent, base, 0.35), wing_tip_r, 0)
    pygame.draw.polygon(screen, highlight, wing_tip_l, 1)
    pygame.draw.polygon(screen, highlight, wing_tip_r, 1)

    # Painéis internos originais melhorados
    for detail in model["details"]:
        detail_pts = rotate_points(detail, x, y, a, scale)
        pygame.draw.polygon(screen, panel_dark, detail_pts, 0)
        pygame.draw.polygon(screen, accent, detail_pts, 2)
        detail_inner = scale_polygon(detail_pts, 0.72)
        pygame.draw.polygon(screen, mix_color(accent, (255, 255, 255), 0.25), detail_inner, 1)

    # Cockpit com camadas
    cockpit_outer = scale_polygon(cockpit_pts, 1.10)
    cockpit_inner = scale_polygon(cockpit_pts, 0.72)
    pygame.draw.polygon(screen, mix_color(accent, (245, 250, 255), 0.18), cockpit_outer, 0)
    pygame.draw.polygon(screen, (255, 255, 255), cockpit_outer, 2)
    pygame.draw.polygon(screen, accent, cockpit_pts, 0)
    pygame.draw.polygon(screen, mix_color(accent, (255, 255, 255), 0.55), cockpit_inner, 0)
    if model.get("rainbow_outline") and not locked:
        draw_rainbow_polygon_outline(cockpit_outer, 2, 0.42)

    # Nervuras do casco apontando para a proa
    nose = max(hull_pts, key=lambda p: p[0] * math.cos(-a) - p[1] * math.sin(-a))
    for source in (wing_l_inner[0], wing_r_inner[0], hull_inner[-1], hull_inner[1]):
        end = ((source[0] + nose[0]) / 2, (source[1] + nose[1]) / 2)
        pygame.draw.line(screen, mix_color(base, (255, 255, 255), 0.20), source, end, 2)

    # Motores detalhados
    for i in range(0, len(engine_points), 3):
        tri = rotate_points(engine_points[i:i+3], x, y, a, scale)
        pygame.draw.polygon(screen, mix_color(engine, (20, 20, 26), 0.20), tri, 0)
        pygame.draw.polygon(screen, mix_color(engine, (255, 255, 255), 0.18), tri, 1)
        core = scale_polygon(tri, 0.55)
        pygame.draw.polygon(screen, mix_color(engine, (255, 240, 210), 0.45), core, 0)
        pygame.draw.polygon(screen, mix_color(engine, (255, 255, 255), 0.6), core, 1)

SHIP_WEAPONS = ["normal","spread","fast","heavy","spread","fast","quad"]

SHIP_PRICES = [0, 15000, 6000, 2500, 10000, 4000, 30000]

HANGAR_ORDER = [0, 3, 5, 2, 4, 1, 6]
SHOP_ORDER = [0, 3, 5, 2, 4, 1, 6]
SHOP_POSITIONS = {
    0: (0, 0),  # Falcon Azul -> esquerda superior
    3: (1, 0),  # Titã Dourado -> centro superior
    5: (2, 0),  # Cometa Ciano -> direita superior
    2: (0, 1),  # Lança Rubi -> esquerda meio
    4: (1, 1),  # Nébula Roxa -> centro meio
    1: (2, 1),  # Vespa Verde -> direita meio
    6: (0, 2),  # O Prisma -> esquerda inferior
}

def load(file, default):
    return int(open(file).read()) if os.path.exists(file) else default

def save(file, value):
    open(file,"w").write(str(value))

coins = load(COIN_FILE,0)

def load_skins():
    # A Falcon Azul é a única nave grátis.
    if os.path.exists(SKIN_FILE):
        data = open(SKIN_FILE).read().strip()

        if data:
            skins = []
            for item in data.split(","):
                if item.strip().isdigit():
                    skin_id = int(item.strip())
                    if 0 <= skin_id < len(SHIP_MODELS):
                        skins.append(skin_id)

            skins = sorted(set(skins + [0]))
            return skins

    return [0]

def save_skins(s):
    open(SKIN_FILE,"w").write(",".join(map(str,s)))

owned_skins = load_skins()

def draw_stars():
    for x,y in stars:
        pygame.draw.circle(screen,(200,200,255),(x,y),1)

def draw_lives(lives):
    spacing = 62

    for i in range(lives):

        x = 55 + i * spacing
        y = 72

        # sombra suave
        draw_ship_model(
            x + 3,
            y + 3,
            -0.35,
            ship_skin,
            scale=0.42,
            inv=8
        )

        # nave principal
        draw_ship_model(
            x,
            y,
            -0.35,
            ship_skin,
            scale=0.42,
            inv=0
        )

def draw_coin_icon(x, y, scale=1):

    outer = int(18 * scale)
    inner = int(11 * scale)

    # brilho externo
    pygame.draw.circle(screen, (255, 210, 70), (x, y), outer)

    # anel principal
    pygame.draw.circle(screen, (255, 245, 140), (x, y), outer - 3, 3)

    # núcleo escuro
    pygame.draw.circle(screen, (120, 80, 20), (x, y), inner)

    # detalhes futuristas
    pygame.draw.line(
        screen,
        (255, 240, 180),
        (x - 6, y),
        (x + 6, y),
        2
    )

    pygame.draw.line(
        screen,
        (255, 240, 180),
        (x, y - 6),
        (x, y + 6),
        2
    )

    pygame.draw.circle(screen, (255,255,255), (x - 5, y - 5), 2)


def draw_menu_coin_display(x, y, amount):
    badge = pygame.Rect(x, y, 250, 52)
    pygame.draw.rect(screen, (7, 12, 22), badge, border_radius=14)
    pygame.draw.rect(screen, (80, 95, 115), badge, 1, border_radius=14)

    icon_x = x + 28
    icon_y = y + badge.h // 2

    # moeda amarela com navezinha no miolo
    pygame.draw.circle(screen, (255, 194, 58), (icon_x, icon_y), 18)
    pygame.draw.circle(screen, (255, 242, 155), (icon_x, icon_y), 14)
    pygame.draw.circle(screen, (168, 110, 20), (icon_x, icon_y), 12, 2)
    pygame.draw.circle(screen, (255, 250, 210), (icon_x - 5, icon_y - 5), 3)

    ship_pts = [
        (10, 0), (2, 4), (-5, 5), (-9, 0), (-5, -5), (2, -4)
    ]
    ship_body = []
    for px, py in ship_pts:
        ship_body.append((icon_x + px * 0.72, icon_y + py * 0.72))
    pygame.draw.polygon(screen, (112, 76, 16), ship_body, 0)
    pygame.draw.polygon(screen, (255, 244, 200), ship_body, 1)

    wing_l = [(icon_x - 1, icon_y - 2), (icon_x - 10, icon_y - 8), (icon_x - 7, icon_y - 2)]
    wing_r = [(icon_x - 1, icon_y + 2), (icon_x - 10, icon_y + 8), (icon_x - 7, icon_y + 2)]
    pygame.draw.polygon(screen, (142, 95, 22), wing_l, 0)
    pygame.draw.polygon(screen, (142, 95, 22), wing_r, 0)

    label_shadow = SMALL_FONT.render(f"MOEDAS: {amount}", True, (40, 20, 0))
    label = SMALL_FONT.render(f"MOEDAS: {amount}", True, (255, 224, 95))
    screen.blit(label_shadow, (x + 54, y + 15))
    screen.blit(label, (x + 52, y + 13))
        
particles=[]
black_holes = []
titan_shockwaves = []
ruby_lances = []
wasp_missiles = []
prism_beams = []
class Particle:
    def __init__(self,x,y):
        self.x=x; self.y=y
        self.vx=random.uniform(-4,4)
        self.vy=random.uniform(-4,4)
        self.life=40
    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.life-=1
    def draw(self):
        pygame.draw.circle(screen,(255,random.randint(100,255),0),(int(self.x),int(self.y)),2)

coins_drops=[]
class Coin:
    def __init__(self,x,y):
        self.x=x; self.y=y
    def update(self,ship):
        dx=ship.x-self.x; dy=ship.y-self.y
        d=math.hypot(dx,dy)
        if d<250:  # alcance maior (melhoria)
            self.x+=dx*0.07
            self.y+=dy*0.07
    def draw(self):
        pygame.draw.circle(screen,(255,215,0),(int(self.x),int(self.y)),5)

class Bullet:
    def __init__(self,x,y,a,speed=8,size=20):
        self.x=x; self.y=y
        self.vx=math.cos(a)*speed
        self.vy=math.sin(a)*speed
        self.life=60
        self.size=size
    def update(self):
        self.x=(self.x+self.vx)%WIDTH
        self.y=(self.y+self.vy)%HEIGHT
        self.life-=1

    def draw(self):
        weapon = SHIP_WEAPONS[ship_skin]

        # direção do projétil
        angle = math.atan2(self.vy, self.vx)

        def rotated_shape(points):
            result = []
            for px, py in points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                result.append((self.x + rx, self.y + ry))
            return result

        if weapon == "normal":
            core = (220, 255, 255)
            glow = (0, 190, 255)

            pygame.draw.line(
                screen,
                glow,
                (int(self.x - self.vx * 2.2), int(self.y - self.vy * 2.2)),
                (int(self.x), int(self.y)),
                7
            )

            pygame.draw.polygon(screen, glow, rotated_shape([
                (9, 0), (-5, -4), (-11, 0), (-5, 4)
            ]))

            pygame.draw.polygon(screen, core, rotated_shape([
                (6, 0), (-3, -2), (-7, 0), (-3, 2)
            ]))

        elif weapon == "spread":
            core = (230, 255, 220)
            glow = (70, 255, 120)

            pygame.draw.line(
                screen,
                glow,
                (int(self.x - self.vx * 1.8), int(self.y - self.vy * 1.8)),
                (int(self.x), int(self.y)),
                5
            )

            pygame.draw.polygon(screen, glow, rotated_shape([
                (8, 0), (-6, -5), (-10, 0), (-6, 5)
            ]))

            pygame.draw.circle(screen, core, (int(self.x), int(self.y)), self.size + 1)

        elif weapon == "fast":
            core = (255, 255, 255)
            glow = (0, 255, 255)

            pygame.draw.line(
                screen,
                glow,
                (int(self.x - self.vx * 3.4), int(self.y - self.vy * 3.4)),
                (int(self.x + self.vx * 0.4), int(self.y + self.vy * 0.4)),
                3
            )

            pygame.draw.line(
                screen,
                core,
                (int(self.x - self.vx * 1.8), int(self.y - self.vy * 1.8)),
                (int(self.x + self.vx * 0.3), int(self.y + self.vy * 0.3)),
                1
            )

        elif weapon == "heavy":
            core = (255, 255, 220)
            mid = (255, 180, 60)
            glow = (255, 80, 30)

            pygame.draw.circle(screen, glow, (int(self.x), int(self.y)), self.size + 9)
            pygame.draw.circle(screen, mid, (int(self.x), int(self.y)), self.size + 6)
            pygame.draw.circle(screen, core, (int(self.x), int(self.y)), self.size + 2)

        elif weapon == "quad":
            hue = (pygame.time.get_ticks() * 0.0015 + (self.x + self.y) * 0.002) % 1.0
            glow = rainbow_cycle_color(hue)
            core = (255, 255, 255)

            pygame.draw.line(
                screen,
                glow,
                (int(self.x - self.vx * 2.6), int(self.y - self.vy * 2.6)),
                (int(self.x + self.vx * 0.25), int(self.y + self.vy * 0.25)),
                4
            )

            pygame.draw.polygon(screen, glow, rotated_shape([
                (10, 0), (-4, -4), (-10, 0), (-4, 4)
            ]))
            pygame.draw.polygon(screen, core, rotated_shape([
                (6, 0), (-1, -2), (-5, 0), (-1, 2)
            ]))

        pygame.draw.polygon(screen, glow, rotated_shape([
            (-6, 0), (-18, -7), (-14, 0), (-18, 7)
        ]))

class RubyLance:
    def __init__(self, x, y, a):
        self.x = x
        self.y = y
        self.vx = math.cos(a) * 22
        self.vy = math.sin(a) * 22
        self.angle = a
        self.life = 150
        self.bounces_left = 4
        self.hit_targets = []
        self.trail = []

    def find_nearest_asteroid(self, ast):
        nearest = None
        nearest_dist = 999999

        for target in ast:
            if target in self.hit_targets:
                continue

            dx = target.x - self.x
            dy = target.y - self.y
            d = math.hypot(dx, dy)

            if d < nearest_dist:
                nearest_dist = d
                nearest = target

        return nearest

    def redirect_to(self, target):
        dx = target.x - self.x
        dy = target.y - self.y
        ang = math.atan2(dy, dx)
        self.angle = ang
        self.vx = math.cos(ang) * 24
        self.vy = math.sin(ang) * 24

    def break_asteroid(self, asteroid, ast):
        if asteroid not in ast:
            return 0

        break_asteroid(asteroid, ast)

        for _ in range(32):
            particles.append(Particle(asteroid.x, asteroid.y))

        self.hit_targets.append(asteroid)
        return 100

    def update(self, ast):
        score_gain = 0

        for _ in range(3):
            self.x = (self.x + self.vx / 3) % WIDTH
            self.y = (self.y + self.vy / 3) % HEIGHT

            self.trail.append((self.x, self.y))
            if len(self.trail) > 16:
                self.trail.pop(0)

            for asteroid in ast[:]:
                if asteroid in self.hit_targets:
                    continue

                if asteroid.collides_with_point(self.x, self.y):
                    score_gain += self.break_asteroid(asteroid, ast)
                    play_sound("hit")

                    if self.bounces_left > 0:
                        next_target = self.find_nearest_asteroid(ast)

                        if next_target:
                            self.bounces_left -= 1
                            self.redirect_to(next_target)
                        else:
                            self.life = 0
                    else:
                        self.life = 0

                    return score_gain

        self.life -= 1
        return score_gain

    def draw(self):
        # Rastro vermelho elegante
        for index, point in enumerate(self.trail):
            fade = index / max(1, len(self.trail))
            radius = max(1, int(8 * fade))
            color = (int(150 * fade), 15, 20)
            pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), radius)

        angle = self.angle

        def rotated_shape(points):
            result = []
            for px, py in points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                result.append((self.x + rx, self.y + ry))
            return result

        # Haste da lança
        pygame.draw.line(
            screen,
            (255, 45, 45),
            (int(self.x - math.cos(angle) * 34), int(self.y - math.sin(angle) * 34)),
            (int(self.x + math.cos(angle) * 26), int(self.y + math.sin(angle) * 26)),
            5
        )

        pygame.draw.line(
            screen,
            (255, 190, 150),
            (int(self.x - math.cos(angle) * 26), int(self.y - math.sin(angle) * 26)),
            (int(self.x + math.cos(angle) * 18), int(self.y + math.sin(angle) * 18)),
            2
        )

        # Ponta agressiva
        tip = rotated_shape([(34, 0), (10, -10), (15, 0), (10, 10)])
        pygame.draw.polygon(screen, (255, 35, 35), tip, 0)
        pygame.draw.polygon(screen, (255, 220, 190), tip, 2)

        # Aletas traseiras
        fins = rotated_shape([(-30, 0), (-45, -12), (-36, 0), (-45, 12)])
        pygame.draw.polygon(screen, (145, 0, 20), fins, 0)
        pygame.draw.polygon(screen, (255, 75, 75), fins, 1)

        # Núcleo brilhante
        pygame.draw.circle(screen, (255, 235, 210), (int(self.x + math.cos(angle) * 18), int(self.y + math.sin(angle) * 18)), 3)


class WaspMissile:
    def __init__(self, x, y, target, launch_angle):
        self.x = x
        self.y = y
        self.target = target
        self.angle = launch_angle
        self.speed = 5.5
        self.max_speed = 12.5
        self.turn_rate = 0.16
        self.life = 165
        self.trail = []
        self.wing_phase = random.uniform(0, math.pi * 2)

    def find_new_target(self, ast, reserved=None):
        reserved = reserved or []
        nearest = None
        nearest_dist = 999999

        for asteroid in ast:
            if asteroid in reserved:
                continue

            dx = asteroid.x - self.x
            dy = asteroid.y - self.y
            d = math.hypot(dx, dy)

            if d < nearest_dist:
                nearest_dist = d
                nearest = asteroid

        return nearest

    def break_asteroid(self, asteroid, ast):
        if asteroid not in ast:
            return 0

        break_asteroid(asteroid, ast)

        for _ in range(22):
            particles.append(Particle(asteroid.x, asteroid.y))

        self.life = 0
        return 100

    def update(self, ast):
        score_gain = 0

        if self.target not in ast:
            self.target = self.find_new_target(ast)

            if self.target is None:
                self.life = 0
                return 0

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        desired = math.atan2(dy, dx)
        diff = (desired - self.angle + math.pi) % (math.pi * 2) - math.pi
        diff = max(-self.turn_rate, min(self.turn_rate, diff))
        self.angle += diff

        self.speed = min(self.max_speed, self.speed + 0.22)
        self.x = (self.x + math.cos(self.angle) * self.speed) % WIDTH
        self.y = (self.y + math.sin(self.angle) * self.speed) % HEIGHT

        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)

        for asteroid in ast[:]:
            if asteroid.collides_with_point(self.x, self.y):
                score_gain += self.break_asteroid(asteroid, ast)
                play_sound("hit")
                break

        self.life -= 1
        self.wing_phase += 0.45
        return score_gain

    def draw(self):
        # rastro verde-dourado
        for index, point in enumerate(self.trail):
            fade = index / max(1, len(self.trail))
            radius = max(1, int(6 * fade))
            color = (int(80 * fade), int(220 * fade), int(80 * fade))
            pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), radius)

        angle = self.angle
        flap = math.sin(self.wing_phase) * 3

        def rotated_shape(points):
            result = []
            for px, py in points:
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)
                result.append((self.x + rx, self.y + ry))
            return result

        # corpo em formato de vespa
        body = rotated_shape([(17, 0), (8, -5), (-11, -4), (-18, 0), (-11, 4), (8, 5)])
        pygame.draw.polygon(screen, (225, 255, 80), body, 0)
        pygame.draw.polygon(screen, (60, 130, 45), body, 2)

        # listras da vespa/míssil
        for stripe_x in [-7, -1, 5]:
            stripe = rotated_shape([(stripe_x, -4), (stripe_x + 3, -3), (stripe_x + 3, 3), (stripe_x, 4)])
            pygame.draw.polygon(screen, (30, 55, 35), stripe, 0)

        # asas translúcidas estilizadas
        left_wing = rotated_shape([(2, -3), (-8, -16 - flap), (10, -11 - flap), (14, -3)])
        right_wing = rotated_shape([(2, 3), (-8, 16 + flap), (10, 11 + flap), (14, 3)])
        pygame.draw.polygon(screen, (150, 255, 170), left_wing, 0)
        pygame.draw.polygon(screen, (150, 255, 170), right_wing, 0)
        pygame.draw.polygon(screen, (230, 255, 220), left_wing, 1)
        pygame.draw.polygon(screen, (230, 255, 220), right_wing, 1)

        # ferrão/ponta do míssil
        sting = rotated_shape([(23, 0), (15, -4), (15, 4)])
        pygame.draw.polygon(screen, (255, 245, 160), sting, 0)
        pygame.draw.circle(screen, (255, 255, 210), (int(self.x + math.cos(angle) * 15), int(self.y + math.sin(angle) * 15)), 3)

class PrismBeam:
    def __init__(self, ship):
        self.ship = ship
        self.life = 120
        self.max_life = 120
        self.length = max(WIDTH, HEIGHT) * 0.95
        self.width = 20
        self.damage_interval = 5
        self.phase = random.uniform(0, math.tau)

    def current_geometry(self):
        angle = self.ship.a + math.sin(self.phase) * 0.03
        start_x = self.ship.x + math.cos(angle) * 32
        start_y = self.ship.y + math.sin(angle) * 32
        end_x = start_x + math.cos(angle) * self.length
        end_y = start_y + math.sin(angle) * self.length
        return angle, start_x, start_y, end_x, end_y

    def point_line_distance(self, ax, ay, bx, by, px, py):
        abx = bx - ax
        aby = by - ay
        apx = px - ax
        apy = py - ay
        ab_len_sq = abx * abx + aby * aby
        if ab_len_sq == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len_sq))
        cx = ax + abx * t
        cy = ay + aby * t
        return math.hypot(px - cx, py - cy)

    def asteroid_hit(self, asteroid):
        _, sx, sy, ex, ey = self.current_geometry()
        return self.point_line_distance(sx, sy, ex, ey, asteroid.x, asteroid.y) <= asteroid.r + self.width * 0.55

    def update(self, ast):
        self.life -= 1
        self.phase += 0.22
        score_gain = 0

        if self.life % self.damage_interval == 0:
            for asteroid in ast[:]:
                if self.asteroid_hit(asteroid):
                    destroyed = damage_asteroid(asteroid, ast, amount=1)
                    for _ in range(10 if destroyed else 4):
                        particles.append(Particle(asteroid.x + random.uniform(-12, 12), asteroid.y + random.uniform(-12, 12)))
                    if destroyed:
                        play_sound("hit")
                        score_gain += 100

        return score_gain

    def draw(self):
        _, sx, sy, ex, ey = self.current_geometry()
        pulse = 0.72 + 0.28 * math.sin(self.phase * 1.7)
        perp_x = -(ey - sy)
        perp_y = ex - sx
        length = math.hypot(perp_x, perp_y) or 1.0
        perp_x /= length
        perp_y /= length

        rainbow = [
            (255, 60, 60),
            (255, 150, 60),
            (255, 235, 80),
            (90, 255, 140),
            (80, 220, 255),
            (170, 120, 255),
        ]

        for idx, color in enumerate(rainbow):
            offset = (idx - (len(rainbow) - 1) / 2) * 3.3
            ox = perp_x * offset
            oy = perp_y * offset
            width = max(1, int((8 - idx * 0.5) * pulse))
            pygame.draw.line(screen, color, (int(sx + ox), int(sy + oy)), (int(ex + ox), int(ey + oy)), width)

        pygame.draw.line(screen, (255, 255, 255), (int(sx), int(sy)), (int(ex), int(ey)), max(2, int(5 * pulse)))

        for step in range(0, 9):
            glow_t = step / 8
            px = sx + (ex - sx) * glow_t
            py = sy + (ey - sy) * glow_t
            radius = max(2, int(10 * (1 - glow_t * 0.65)))
            color = rainbow[step % len(rainbow)]
            pygame.draw.circle(screen, color, (int(px), int(py)), radius, 1)


class TitanShockwave:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 18
        self.max_radius = 285
        self.life = 34
        self.max_life = 34

    def update(self):
        self.radius += 8.5
        self.life -= 1

    def draw(self):
        alpha_ratio = max(0, self.life / self.max_life)
        thickness = max(2, int(7 * alpha_ratio))

        # Anel principal amarelo
        pygame.draw.circle(
            screen,
            (255, 215, 60),
            (int(self.x), int(self.y)),
            int(self.radius),
            thickness
        )

        # Anel interno mais claro, dando sensação de energia
        pygame.draw.circle(
            screen,
            (255, 245, 150),
            (int(self.x), int(self.y)),
            max(1, int(self.radius * 0.72)),
            max(1, thickness // 2)
        )

        # Pequenos raios de impacto ao redor da onda
        for i in range(14):
            ang = math.pi * 2 * i / 14
            inner = self.radius * 0.88
            outer = self.radius * 1.06
            x1 = self.x + math.cos(ang) * inner
            y1 = self.y + math.sin(ang) * inner
            x2 = self.x + math.cos(ang) * outer
            y2 = self.y + math.sin(ang) * outer
            pygame.draw.line(
                screen,
                (255, 230, 90),
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                max(1, thickness // 2)
            )

class BlackHole:
    def __init__(self, x, y, a):
        self.x = x
        self.y = y
        self.vx = math.cos(a) * 3
        self.vy = math.sin(a) * 3
        self.life = 360
        self.radius = 170

    def update(self, ast):
        self.x = (self.x + self.vx) % WIDTH
        self.y = (self.y + self.vy) % HEIGHT
        self.life -= 1

        for a in ast:
            dx = self.x - a.x
            dy = self.y - a.y
            d = math.hypot(dx, dy)

            if 20 < d < self.radius:
                force = (1 - d / self.radius) * 0.18
                a.vx += dx / d * force
                a.vy += dy / d * force

    def draw(self):
        pygame.draw.circle(screen, (30, 0, 45), (int(self.x), int(self.y)), 28)
        pygame.draw.circle(screen, (160, 70, 255), (int(self.x), int(self.y)), 36, 3)
        pygame.draw.circle(screen, (220, 170, 255), (int(self.x), int(self.y)), 18, 2)

        for r in range(55, self.radius, 35):
            pygame.draw.circle(screen, (70, 20, 110), (int(self.x), int(self.y)), r, 1)

class Ship:
    def __init__(self):
        self.x=WIDTH/2
        self.y=HEIGHT/2
        self.a=0
        self.vx=0
        self.vy=0
        self.cd=0
        self.inv=120
    def update(self,keys):
        if keys[pygame.K_a]: self.a-=0.08
        if keys[pygame.K_d]: self.a+=0.08
        if keys[pygame.K_w]:
            self.vx+=math.cos(self.a)*0.3
            self.vy+=math.sin(self.a)*0.3
        self.x=(self.x+self.vx)%WIDTH
        self.y=(self.y+self.vy)%HEIGHT
        self.vx*=0.99; self.vy*=0.99
        if self.inv>0: self.inv-=1
        if self.cd>0: self.cd-=1

        if hasattr(self, "ability_cd") and self.ability_cd > 0:
            self.ability_cd -= 1

        if hasattr(self, "magnet_timer") and self.magnet_timer > 0:
            self.magnet_timer -= 1

        if hasattr(self, "slow_timer") and self.slow_timer > 0:
            self.slow_timer -= 1

        if hasattr(self, "dash_break_timer") and self.dash_break_timer > 0:
            self.dash_break_timer -= 1

    def shoot(self,bullets):
        if self.cd>0: return
        weapon = SHIP_WEAPONS[ship_skin]
        if weapon=="normal":
            bullets.append(Bullet(self.x,self.y,self.a))
            self.cd=10
            play_sound("shoot_normal")
        elif weapon=="spread":
            # Vespa Verde: dois disparos em vez de três
            if ship_skin == 1:
                for ang in [-0.13, 0.13]:
                    bullets.append(Bullet(self.x,self.y,self.a+ang,7))
            else:
                for ang in [-0.2,0,0.2]:
                    bullets.append(Bullet(self.x,self.y,self.a+ang,7))
            self.cd=18
            play_sound("shoot_wasp" if ship_skin == 1 else "shoot_normal")
        elif weapon=="fast":
            bullets.append(Bullet(self.x,self.y,self.a,12))
            self.cd=6
            play_sound("shoot_fast")
        elif weapon=="heavy":
            # Titã Dourado: tiro mais lento, maior e mais destrutivo
            bullets.append(Bullet(self.x,self.y,self.a,4,6))
            self.cd=26
            play_sound("shoot_heavy")
        elif weapon=="quad":
            for ang in [-0.18, -0.06, 0.06, 0.18]:
                bullets.append(Bullet(self.x, self.y, self.a + ang, 10, 3))
            self.cd=12
            play_sound("shoot_prism")
    def draw(self):
        draw_ship_model(self.x, self.y, self.a, ship_skin, scale=1, inv=self.inv)

    def use_ability(self, bullets, ast):
        if not hasattr(self, "ability_cd"):
            self.ability_cd = 0
            self.magnet_timer = 0
            self.slow_timer = 0

        if self.ability_cd > 0:
            return

        # FALCON AZUL — DASH
        if ship_skin == 0:
            self.vx += math.cos(self.a) * 12
            self.vy += math.sin(self.a) * 12
            self.inv = 40
            self.dash_break_timer = 26
            self.ability_cd = 960
            play_sound("ability_dash")

        # VESPA VERDE — MÍSSEIS TELEGUIADOS
        elif ship_skin == 1:
            available_targets = sorted(
                ast,
                key=lambda asteroid: math.hypot(asteroid.x - self.x, asteroid.y - self.y)
            )[:8]

            if available_targets:
                for i, target in enumerate(available_targets):
                    spread = -0.55 + (1.10 * i / max(1, len(available_targets) - 1))
                    launch_angle = self.a + spread
                    wasp_missiles.append(WaspMissile(self.x, self.y, target, launch_angle))

            self.ability_cd = 960
            play_sound("ability_wasp")

        # LANÇA RUBI — LANÇA RICOCHETEANTE
        elif ship_skin == 2:
            ruby_lances.append(RubyLance(self.x, self.y, self.a))
            self.ability_cd = 960
            play_sound("ability_ruby")

        # TITÃ DOURADO — ONDA DE IMPACTO
        elif ship_skin == 3:
            titan_shockwaves.append(TitanShockwave(self.x, self.y))

            for a in ast[:]:
                if math.hypot(self.x-a.x,self.y-a.y) < 260:
                    break_asteroid(a, ast)
                    for _ in range(12):
                        particles.append(Particle(a.x,a.y))
            self.ability_cd = 960
            play_sound("ability_titan")

        # NÉBULA ROXA — EXPLOSÃO GRAVITACIONAL
        
        elif ship_skin == 4:
            black_holes.append(BlackHole(self.x, self.y, self.a))
            self.ability_cd = 960
            play_sound("ability_blackhole")

        # COMETA CIANO — DISPARO CIRCULAR
        elif ship_skin == 5:
            for i in range(16):
                ang = math.pi * 2 * i / 16
                bullets.append(Bullet(self.x,self.y,ang,9,2))
            self.ability_cd = 960
            play_sound("ability_cyan")

        # O PRISMA — FEIXE PRISMATICO
        elif ship_skin == 6:
            prism_beams.append(PrismBeam(self))
            self.ability_cd = 960
            play_sound("ability_prism")

class Asteroid:
    def __init__(self,x=None,y=None,size=3,special=None):
        self.size = size
        self.r = 22 * size

        # Asteroides novos nascem fora da tela e entram vagando no espaço.
        spawned_outside = x is None or y is None
        if spawned_outside:
            margin = self.r + 45
            side = random.choice(["left", "right", "top", "bottom"])

            if side == "left":
                self.x = -margin
                self.y = random.uniform(-margin, HEIGHT + margin)
            elif side == "right":
                self.x = WIDTH + margin
                self.y = random.uniform(-margin, HEIGHT + margin)
            elif side == "top":
                self.x = random.uniform(-margin, WIDTH + margin)
                self.y = -margin
            else:
                self.x = random.uniform(-margin, WIDTH + margin)
                self.y = HEIGHT + margin

            target_x = random.uniform(WIDTH * 0.20, WIDTH * 0.80)
            target_y = random.uniform(HEIGHT * 0.20, HEIGHT * 0.80)
            ang = math.atan2(target_y - self.y, target_x - self.x)
            speed = random.uniform(0.75, 1.65)
            drift = random.uniform(-0.38, 0.38)
            self.vx = math.cos(ang) * speed + math.cos(ang + math.pi / 2) * drift
            self.vy = math.sin(ang) * speed + math.sin(ang + math.pi / 2) * drift
        else:
            self.x = x
            self.y = y
            self.vx = random.uniform(-1.6, 1.6)
            self.vy = random.uniform(-1.6, 1.6)

        self.max_hp = {3: 4, 2: 2, 1: 1}.get(size, 1)
        self.hp = self.max_hp

        self.angle = random.uniform(0, math.pi * 2)
        self.spin = random.uniform(-0.008, 0.008)

        self.special = random.random() < 0.15 if special is None else special

        self.shape = []
        points = 34

        for j in range(points):
            ang = (math.pi * 2 / points) * j

            radius = self.r * random.uniform(0.86, 1.10)
            radius += math.sin(ang * 2.2) * self.r * 0.05
            radius += math.cos(ang * 4.7) * self.r * 0.035

            self.shape.append((math.cos(ang) * radius, math.sin(ang) * radius))

        self.surface_marks = []
        for _ in range(12 + size * 3):
            ang = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, self.r * 0.68)
            mark_size = random.randint(2, 6) * size // 2

            self.surface_marks.append((
                math.cos(ang) * dist,
                math.sin(ang) * dist,
                max(1, mark_size)
            ))

        self.rock_planes = []
        for _ in range(8 + size):
            ang = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, self.r * 0.55)
            w = random.uniform(0.12, 0.28) * self.r
            h = random.uniform(0.08, 0.18) * self.r

            cx = math.cos(ang) * dist
            cy = math.sin(ang) * dist

            self.rock_planes.append([
                (cx - w, cy),
                (cx - w * 0.25, cy - h),
                (cx + w, cy - h * 0.25),
                (cx + w * 0.35, cy + h)
            ])

        self.crystals = []
        if self.special:
            for _ in range(5 + size):
                ang = random.uniform(0, math.pi * 2)
                base = self.r * 0.86
                length = random.randint(9, 16) * size / 2
                width = random.randint(3, 6) * size / 2

                bx = math.cos(ang) * base
                by = math.sin(ang) * base
                tx = math.cos(ang) * (base + length)
                ty = math.sin(ang) * (base + length)

                lx = math.cos(ang + math.pi/2) * width
                ly = math.sin(ang + math.pi/2) * width

                self.crystals.append([
                    (bx + lx, by + ly),
                    (tx, ty),
                    (bx - lx, by - ly)
                ])

    def rotate_points(self, points):
        rotated = []

        for px, py in points:
            rx = px * math.cos(self.angle) - py * math.sin(self.angle)
            ry = px * math.sin(self.angle) + py * math.cos(self.angle)
            rotated.append((self.x + rx, self.y + ry))

        return rotated

    def point_inside_polygon(self, px, py, polygon):
        inside = False
        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            intersect = ((yi > py) != (yj > py)) and \
                        (px < (xj - xi) * (py - yi) / (yj - yi + 0.00001) + xi)

            if intersect:
                inside = not inside

            j = i

        return inside

    def collides_with_point(self, px, py):
        return self.point_inside_polygon(px, py, self.rotate_points(self.shape))

    def collides_with_ship(self, ship):
        ship_points = rotate_points(
            SHIP_MODELS[ship_skin]["hull"],
            ship.x,
            ship.y,
            ship.a,
            1
        )

        asteroid_poly = self.rotate_points(self.shape)

        for px, py in ship_points:
            if self.point_inside_polygon(px, py, asteroid_poly):
                return True

        for px, py in asteroid_poly:
            if self.point_inside_polygon(px, py, ship_points):
                return True

        return False

    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0

    def update(self):
        self.x += self.vx
        self.y += self.vy

        margin = self.r + 80
        if self.x < -margin:
            self.x = WIDTH + margin
            self.y = random.uniform(-margin, HEIGHT + margin)
        elif self.x > WIDTH + margin:
            self.x = -margin
            self.y = random.uniform(-margin, HEIGHT + margin)

        if self.y < -margin:
            self.y = HEIGHT + margin
            self.x = random.uniform(-margin, WIDTH + margin)
        elif self.y > HEIGHT + margin:
            self.y = -margin
            self.x = random.uniform(-margin, WIDTH + margin)

        self.angle += self.spin

    def draw(self):
        pts = self.rotate_points(self.shape)

        # Cristais dos asteroides especiais que dropam moedas
        if self.special:
            for crystal in self.crystals:
                cpts = self.rotate_points(crystal)

                pygame.draw.polygon(screen, (105, 170, 255), cpts, 0)
                pygame.draw.polygon(screen, (210, 240, 255), cpts, 1)

                tip = cpts[1]
                pygame.draw.circle(screen, (150, 220, 255), (int(tip[0]), int(tip[1])), 2)

        # Corpo principal, uma cor sólida para evitar sobreposição feia
        pygame.draw.polygon(screen, (95, 92, 88), pts, 0)

        # Sombra lateral simples
        shadow_pts = []
        for px, py in self.shape:
            if px < 0:
                shadow_pts.append((px * 0.92, py * 0.92))
            else:
                shadow_pts.append((px * 0.35, py * 0.35))

        pygame.draw.polygon(screen, (58, 56, 54), self.rotate_points(shadow_pts), 0)

        # Planos rochosos discretos, sem random.choice no draw
        plane_colors = [
            (76, 74, 71),
            (110, 106, 100),
            (88, 85, 80)
        ]

        for index, plane in enumerate(self.rock_planes):
            p = self.rotate_points(plane)
            color = plane_colors[index % len(plane_colors)]
            pygame.draw.polygon(screen, color, p, 0)

        # Crateras limpas
        for mx, my, mr in self.surface_marks:
            rx = mx * math.cos(self.angle) - my * math.sin(self.angle)
            ry = mx * math.sin(self.angle) + my * math.cos(self.angle)

            pygame.draw.circle(
                screen,
                (42, 40, 38),
                (int(self.x + rx), int(self.y + ry)),
                mr,
                0
            )

            pygame.draw.circle(
                screen,
                (120, 116, 108),
                (int(self.x + rx - 1), int(self.y + ry - 1)),
                max(1, mr // 2),
                1
            )


    # Contorno final por cima de tudo
        pygame.draw.polygon(screen, (155, 150, 140), pts, 2)

        # Barra de vida acompanha o asteroide
        bar_w = max(34, self.r * 1.35)
        bar_h = 6
        bar_x = self.x - bar_w / 2
        bar_y = self.y - self.r - 18
        health_ratio = max(0, min(1, self.hp / self.max_hp))

        pygame.draw.rect(screen, (12, 18, 24), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, (70, 85, 95), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)

        if health_ratio > 0.55:
            hp_color = (90, 240, 150)
        elif health_ratio > 0.28:
            hp_color = (255, 215, 80)
        else:
            hp_color = (255, 95, 80)

        pygame.draw.rect(
            screen,
            hp_color,
            (bar_x + 1, bar_y + 1, max(0, (bar_w - 2) * health_ratio), bar_h - 2),
            border_radius=3
        )

    def split(self, pieces=2):
        if self.size > 1:
            return [
                Asteroid(self.x, self.y, self.size - 1, self.special)
                for _ in range(pieces)
            ]

        return []

def break_asteroid(asteroid, ast, pieces=2, force_small=False):
    if asteroid not in ast:
        return []

    ast.remove(asteroid)

    if force_small and asteroid.size > 1:
        parts = [Asteroid(asteroid.x, asteroid.y, 1, asteroid.special) for _ in range(pieces)]
    else:
        parts = asteroid.split(pieces)

    if parts:
        ast.extend(parts)
    elif asteroid.special:
        coins_drops.append(Coin(asteroid.x, asteroid.y))

    return parts

def damage_asteroid(asteroid, ast, amount=1, pieces=2, force_small=False):
    if asteroid not in ast:
        return False

    if asteroid.take_damage(amount):
        break_asteroid(asteroid, ast, pieces, force_small)
        return True

    return False

# MENU COMPLETO

def draw_menu_hero_ship():
    time = pygame.time.get_ticks()
    hero_skin = (time // 10000) % len(SHIP_MODELS)

    model = SHIP_MODELS[hero_skin]
    main_color = model["color"]
    accent_color = model["accent"]
    engine_color = model["engine"]

    x = WIDTH * 0.76
    y = HEIGHT * 0.50
    angle = -0.22

    pulse = math.sin(time * 0.004) * 0.08
    scale = 5.45 + pulse

    # rastro laser com a cor da nave atual
    for i in range(22):
        length = 760 - i * 26
        thickness = max(2, 34 - i)

        drift = math.sin(time * 0.004 + i * 0.45) * 9

        start = (
            int(x - math.cos(angle) * length - 110),
            int(y - math.sin(angle) * length + drift)
        )

        end = (
            int(x - math.cos(angle) * 130),
            int(y - math.sin(angle) * 130)
        )

        fade = 1 - (i / 22)

        color = (
            max(0, int(engine_color[0] * fade)),
            max(0, int(engine_color[1] * fade)),
            max(0, int(engine_color[2] * fade))
        )

        pygame.draw.line(screen, color, start, end, thickness)

    # raios finos extras na cor de destaque da nave
    for i in range(7):
        offset = -45 + i * 15
        pygame.draw.line(
            screen,
            accent_color,
            (int(x - 720), int(y + offset)),
            (int(x - 120), int(y + offset * 0.25)),
            2
        )

    # brilho do motor baseado na cor da nave
    glow_color = (
        max(5, engine_color[0] // 5),
        max(5, engine_color[1] // 5),
        max(10, engine_color[2] // 5)
    )

    for r in range(130, 25, -20):
        pygame.draw.circle(
            screen,
            glow_color,
            (int(x - 115), int(y + 20)),
            r,
            2
        )

    draw_ship_showcase(
        x,
        y,
        angle,
        hero_skin,
        scale=scale,
        locked=False
    )


def menu():
    set_music("menu")
    options = ["Jogar", "Naves", "Loja", "Sair"]

    title_big = pygame.font.SysFont("Impact", 112)
    ultra_big = pygame.font.SysFont("Trebuchet MS", 52)
    option_big = pygame.font.SysFont("Trebuchet MS", 46)

    while True:
        draw_space_background()

        mouse_pos = pygame.mouse.get_pos()
        rects = []

        # Nave gigante alternando no lado direito
        draw_menu_hero_ship()

        # Bloco do menu no canto inferior esquerdo, um pouco mais à direita
        panel_x = 155
        title_y = HEIGHT * 0.26
        options_start_y = HEIGHT * 0.52

        # Título grande acima das opções
        title_shadow = title_big.render("ASTEROIDS", True, (0, 40, 55))
        title = title_big.render("ASTEROIDS", True, (180, 245, 255))

        ultra_shadow = ultra_big.render("ULTRA", True, (0, 40, 55))
        ultra = ultra_big.render("ULTRA", True, (0, 220, 255))

        screen.blit(title_shadow, (panel_x + 4, title_y + 4))
        screen.blit(title, (panel_x, title_y))

        screen.blit(ultra_shadow, (panel_x + 8, title_y + 120))
        screen.blit(ultra, (panel_x + 4, title_y + 116))

        # Linha decorativa
        pygame.draw.line(
            screen,
            (0, 180, 220),
            (panel_x, title_y + 180),
            (panel_x + 430, title_y + 180),
            4
        )

        for i, opt in enumerate(options):
            y = options_start_y + i * 75

            text_color = (230, 240, 245)
            label = option_big.render(opt.upper(), True, text_color)
            rect = label.get_rect(topleft=(panel_x + 38, y))

            button_rect = pygame.Rect(panel_x, y - 10, 350, 62)

            if button_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (16, 28, 38), button_rect, border_radius=10)
                pygame.draw.rect(screen, (0, 220, 255), button_rect, 2, border_radius=10)

                arrow = option_big.render("›", True, (0, 220, 255))
                screen.blit(arrow, (panel_x + 10, y - 3))
            else:
                pygame.draw.rect(screen, (8, 12, 20), button_rect, 1, border_radius=10)

            screen.blit(label, rect)
            rects.append((button_rect, i))

        # Moedas no canto superior esquerdo
        draw_menu_coin_display(30, 26, coins)

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                for r, i in rects:
                    if r.collidepoint(e.pos):
                        play_sound("select")
                        if i == 0:
                            return
                        if i == 1:
                            skins()
                        if i == 2:
                            shop()
                        if i == 3:
                            pygame.quit()
                            exit()

# NAVES

def skins():
    global ship_skin

    selected = ship_skin

    DESCRIPTIONS = [
        "A nave inicial mais equilibrada. Boa para sobreviver, aprender o ritmo do jogo e escapar de colisões perigosas.",
        "Leve, agressiva e ótima para pressionar vários alvos com tiros duplos e um enxame inteligente de mísseis-vespa.",
        "Uma nave veloz de ataque frontal. Perfeita para jogadores que gostam de tiros rápidos e precisão.",
        "Casco pesado, presença forte e disparo de impacto. Ideal para limpar áreas próximas com segurança.",
        "Tecnologia experimental roxa. Controla o campo de batalha com distorção gravitacional.",
        "Nave ciano de resposta rápida. Excelente para situações cercadas e ataques em todas as direções.",
        "Uma nave lendária de luz pura: casco branco, contorno arco-íris e poder concentrado em rajadas cristalinas e um feixe devastador."
    ]

    WEAPON_NAMES = [
        "Canhão Padrão",
        "Disparo Duplo",
        "Laser Rápido",
        "Projétil Pesado",
        "Pulso Nebular",
        "Rajada Ciano",
        "Rajada Prismática"
    ]

    WEAPON_DESCRIPTIONS = [
        "Tiro azul equilibrado, com boa cadência e controle.",
        "Dois tiros em leque curto, rápidos e eficientes para pressão constante.",
        "Laser fino e veloz, feito para pressão constante.",
        "Esfera energética mais lenta e destrutiva, capaz de dividir asteroides em 4 partes pequenas.",
        "Rajada energética versátil para controlar o espaço à frente.",
        "Disparos velozes e energéticos para combate agressivo.",
        "Quatro tiros cristalinos de luz, rápidos e precisos, disparados em leque elegante."
    ]

    ABILITY_NAMES = [
        "TURBO DASH",
        "MÍSSEIS VESPA",
        "LANÇA RUBI",
        "ONDA DE CHOQUE",
        "BURACO NEGRO",
        "EXPLOSÃO CIANO",
        "FEIXE PRISMÁTICO"
    ]

    ABILITY_DESCRIPTIONS = [
        "Avança rapidamente na direção da nave, quebrando meteoros atravessados e concedendo uma pequena janela de invencibilidade.",
        "Ejeta cerca de 8 mísseis teleguiados em formato de vespa. Cada míssil procura um asteroide diferente sempre que possível.",
        "Ejeta uma lança vermelha em alta velocidade. Ao atingir um asteroide, ricocheteia até 4 vezes para o alvo mais próximo.",
        "Cria uma onda de impacto ao redor da nave, destruindo asteroides próximos.",
        "Lança um projétil gravitacional que puxa asteroides ao redor durante alguns segundos.",
        "Dispara projéteis em círculo, protegendo a nave quando ela está cercada.",
        "Canaliza um feixe contínuo de luz arco-íris inspirado no Último Prisma, derretendo tudo o que cruzar sua linha de fogo."
    ]

    COOLDOWNS = ["16s", "16s", "16s", "16s", "16s", "16s", "16s"]

    select_font = pygame.font.SysFont("Trebuchet MS", 28)
    name_font = pygame.font.SysFont("Impact", 64)
    section_font = pygame.font.SysFont("Trebuchet MS", 32)
    body_font = pygame.font.SysFont("Consolas", 22)
    status_font = pygame.font.SysFont("Consolas", 24)
    small_font = pygame.font.SysFont("Consolas", 18)

    def selected_display_index():
        if selected in HANGAR_ORDER:
            return HANGAR_ORDER.index(selected)
        return 0


    def draw_text_block(text, font, color, x, y, max_width, line_gap=6):
        words = text.split(" ")
        line = ""
        current_y = y

        for word in words:
            test = word if line == "" else line + " " + word

            if font.size(test)[0] <= max_width:
                line = test
            else:
                rendered = font.render(line, True, color)
                screen.blit(rendered, (x, current_y))
                current_y += rendered.get_height() + line_gap
                line = word

        if line:
            rendered = font.render(line, True, color)
            screen.blit(rendered, (x, current_y))
            current_y += rendered.get_height() + line_gap

        return current_y

    def draw_info_panel(rect, title, text, border_color):
        pygame.draw.rect(screen, (8, 14, 24), rect, border_radius=18)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=18)

        pad_x = 32
        title_y = rect.y + 20
        text_y = rect.y + 74

        title_label = section_font.render(title, True, border_color)
        screen.blit(title_label, (rect.x + pad_x, title_y))

        return draw_text_block(
            text,
            body_font,
            (190, 205, 215),
            rect.x + pad_x,
            text_y,
            rect.w - pad_x * 2,
            4
        )

    while True:
        draw_space_background()

        mouse_pos = pygame.mouse.get_pos()
        card_rects = []
        selected = max(0, min(selected, len(SHIP_MODELS) - 1))

        model = SHIP_MODELS[selected]
        main_color = model["color"]
        accent_color = model["accent"]
        engine_color = model["engine"]

        # Título
        title_shadow = TITLE_FONT.render("SELEÇÃO DE NAVES", True, (0, 35, 50))
        title = TITLE_FONT.render("SELEÇÃO DE NAVES", True, (215, 245, 255))
        screen.blit(title_shadow, title_shadow.get_rect(center=(WIDTH // 2 + 4, 76)))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 72)))

        # Painel principal ocupa quase toda a tela
        outer = pygame.Rect(70, 160, WIDTH - 140, HEIGHT - 225)
        pygame.draw.rect(screen, (5, 9, 17), outer, border_radius=26)
        pygame.draw.rect(screen, (0, 125, 160), outer, 2, border_radius=26)

        # Lista lateral
        list_panel = pygame.Rect(outer.x + 28, outer.y + 28, 360, outer.h - 56)
        pygame.draw.rect(screen, (8, 13, 23), list_panel, border_radius=22)
        pygame.draw.rect(screen, (35, 60, 75), list_panel, 2, border_radius=22)

        list_title = section_font.render("HANGAR", True, (210, 235, 245))
        screen.blit(list_title, (list_panel.x + 26, list_panel.y + 22))

        if len(SHIP_MODELS) > 6:
            card_h = 68
            card_gap = 10
            first_y = list_panel.y + 74
        else:
            card_h = 76
            card_gap = 14
            first_y = list_panel.y + 76

        for display_i, ship_id in enumerate(HANGAR_ORDER):
            ship = SHIP_MODELS[ship_id]
            card = pygame.Rect(list_panel.x + 22, first_y + display_i * (card_h + card_gap), list_panel.w - 44, card_h)
            hover = card.collidepoint(mouse_pos)
            unlocked = ship_id in owned_skins
            equipped = ship_id == ship_skin
            is_selected = ship_id == selected

            if is_selected:
                bg = (18, 34, 50)
                border = ship["color"]
            elif hover:
                bg = (14, 24, 36)
                border = (90, 115, 130)
            else:
                bg = (9, 15, 25)
                border = (45, 60, 72)

            pygame.draw.rect(screen, bg, card, border_radius=14)
            pygame.draw.rect(screen, border, card, 2, border_radius=14)

            draw_ship_showcase(card.x + 45, card.centery, -0.18, ship_id, scale=0.52, locked=not unlocked, show_engine_halo=False)

            ship_name = select_font.render(ship["name"].upper(), True, ship["color"] if unlocked else (120, 125, 130))
            screen.blit(ship_name, (card.x + 88, card.y + 13))

            if equipped:
                status = "EQUIPADA"
                status_color = (255, 225, 105)
            elif unlocked:
                status = "DESBLOQUEADA"
                status_color = (180, 255, 210)
            else:
                status = "BLOQUEADA"
                status_color = (150, 150, 155)

            status_label = small_font.render(status, True, status_color)
            screen.blit(status_label, (card.x + 90, card.y + 45))

            card_rects.append((card, ship_id))

        # Área de apresentação da nave
        preview_rect = pygame.Rect(list_panel.right + 30, outer.y + 28, 520, outer.h - 56)
        pygame.draw.rect(screen, (7, 11, 20), preview_rect, border_radius=24)
        pygame.draw.rect(screen, main_color, preview_rect, 2, border_radius=24)

        # Decoração do painel
        pygame.draw.line(screen, main_color, (preview_rect.x + 34, preview_rect.y + 34), (preview_rect.right - 34, preview_rect.y + 34), 4)
        pygame.draw.line(screen, (25, 45, 60), (preview_rect.x + 34, preview_rect.bottom - 88), (preview_rect.right - 34, preview_rect.bottom - 88), 2)

        preview_center_x = preview_rect.centerx
        preview_center_y = preview_rect.y + preview_rect.h * 0.43

        # Brilho discreto atrás da nave
        glow = (
            max(8, engine_color[0] // 8),
            max(8, engine_color[1] // 8),
            max(14, engine_color[2] // 8)
        )

        for r in range(210, 40, -34):
            pygame.draw.circle(screen, glow, (int(preview_center_x), int(preview_center_y)), r, 2)

        # Nave em destaque com mais detalhes visuais
        draw_ship_showcase(preview_center_x, preview_center_y, -0.18, selected, scale=3.6, locked=selected not in owned_skins)

        ship_title = name_font.render(model["name"].upper(), True, main_color)
        screen.blit(ship_title, ship_title.get_rect(center=(preview_center_x, preview_rect.bottom - 58)))

        # Painel de informações
        info_x = preview_rect.right + 30
        info_w = outer.right - info_x - 28
        info_rect = pygame.Rect(info_x, outer.y + 28, info_w, outer.h - 56)
        pygame.draw.rect(screen, (7, 11, 20), info_rect, border_radius=24)
        pygame.draw.rect(screen, (35, 60, 75), info_rect, 2, border_radius=24)

        panel_pad_x = 28
        body_color = (190, 205, 215)
        heading_color = (230, 240, 245)

        y_cursor = info_rect.y + 26

        desc_rect = pygame.Rect(info_rect.x + 26, y_cursor, info_rect.w - 52, 200)
        draw_info_panel(desc_rect, "DESCRIÇÃO", DESCRIPTIONS[selected], main_color)
        y_cursor = desc_rect.bottom + 22

        weapon_rect = pygame.Rect(info_rect.x + 26, y_cursor, info_rect.w - 52, 170)
        pygame.draw.rect(screen, (8, 14, 24), weapon_rect, border_radius=18)
        pygame.draw.rect(screen, accent_color, weapon_rect, 2, border_radius=18)

        weapon_title = section_font.render("ARMA", True, accent_color)
        screen.blit(weapon_title, (weapon_rect.x + panel_pad_x + 4, weapon_rect.y + 20))

        weapon_name = status_font.render(WEAPON_NAMES[selected], True, heading_color)
        weapon_name_y = weapon_rect.y + 66
        screen.blit(weapon_name, (weapon_rect.x + panel_pad_x + 4, weapon_name_y))

        draw_text_block(
            WEAPON_DESCRIPTIONS[selected],
            body_font,
            body_color,
            weapon_rect.x + panel_pad_x + 4,
            weapon_name_y + weapon_name.get_height() + 12,
            weapon_rect.w - (panel_pad_x + 4) * 2,
            4
        )

        y_cursor = weapon_rect.bottom + 22

        # Botão grande de seleção
        button = pygame.Rect(info_rect.x + 26, info_rect.bottom - 72, info_rect.w - 52, 46)

        ability_rect = pygame.Rect(
            info_rect.x + 26,
            y_cursor,
            info_rect.w - 52,
            button.y - 24 - y_cursor
        )
        pygame.draw.rect(screen, (8, 14, 24), ability_rect, border_radius=18)
        pygame.draw.rect(screen, engine_color, ability_rect, 2, border_radius=18)

        ability_title = section_font.render("HABILIDADE ESPECIAL", True, engine_color)
        ability_name = status_font.render(ABILITY_NAMES[selected], True, heading_color)
        cooldown = small_font.render(f"Cooldown: {COOLDOWNS[selected]} • tecla E", True, (255, 225, 105))

        ability_text_start_y = ability_rect.y + max(
            18,
            (ability_rect.h - 128) // 2
        )

        screen.blit(ability_title, (ability_rect.x + panel_pad_x + 4, ability_text_start_y))

        ability_name_y = ability_text_start_y + 46
        screen.blit(ability_name, (ability_rect.x + panel_pad_x + 4, ability_name_y))

        cooldown_y = ability_name_y + ability_name.get_height() + 6
        screen.blit(cooldown, (ability_rect.x + panel_pad_x + 4, cooldown_y))

        draw_text_block(
            ABILITY_DESCRIPTIONS[selected],
            body_font,
            body_color,
            ability_rect.x + panel_pad_x + 4,
            cooldown_y + cooldown.get_height() + 12,
            ability_rect.w - (panel_pad_x + 4) * 2,
            4
        )

        can_select = selected in owned_skins and selected != ship_skin

        if selected == ship_skin:
            button_text = "EQUIPADA"
            button_color = (255, 225, 105)
        elif selected in owned_skins:
            button_text = "EQUIPAR ESTA NAVE"
            button_color = main_color
        else:
            button_text = "BLOQUEADA"
            button_color = (120, 125, 135)

        hover_button = button.collidepoint(mouse_pos) and can_select
        pygame.draw.rect(screen, (14, 25, 36) if hover_button else (8, 14, 24), button, border_radius=14)
        pygame.draw.rect(screen, button_color, button, 2, border_radius=14)

        button_label = status_font.render(button_text, True, button_color)
        screen.blit(button_label, button_label.get_rect(center=button.center))

        # Dica inferior discreta
        esc_hint = SMALL_FONT.render("ESC para sair", True, (145, 165, 180))
        screen.blit(esc_hint, (72, HEIGHT - 52))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return

                if e.key in [pygame.K_UP, pygame.K_w]:
                    current_idx = selected_display_index()
                    selected = HANGAR_ORDER[(current_idx - 1) % len(HANGAR_ORDER)]

                if e.key in [pygame.K_DOWN, pygame.K_s]:
                    current_idx = selected_display_index()
                    selected = HANGAR_ORDER[(current_idx + 1) % len(HANGAR_ORDER)]

                if e.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if selected in owned_skins:
                        ship_skin = selected
                        play_sound("select")

            if e.type == pygame.MOUSEBUTTONDOWN:
                for card, i in card_rects:
                    if card.collidepoint(e.pos):
                        selected = i

                if button.collidepoint(e.pos) and can_select:
                    ship_skin = selected
                    play_sound("select")

# LOJA
def shop():
    global coins, ship_skin

    card_w = 300
    card_h = 190
    gap = 28
    cols = 3

    total_w = cols * card_w + (cols - 1) * gap
    rows = math.ceil(len(SHIP_MODELS) / cols)
    total_h = rows * card_h + (rows - 1) * gap

    start_x = WIDTH // 2 - total_w // 2

    # centraliza apenas o bloco dos cards na área útil da loja
    top_area = 170      # área ocupada por título/subtítulo
    bottom_area = HEIGHT - 70   # margem inferior / "ESC para voltar"
    available_h = bottom_area - top_area
    start_y = top_area + (available_h - total_h) // 2

    while True:
        draw_space_background()

        mouse_pos = pygame.mouse.get_pos()
        rects = []

        title = TITLE_FONT.render("LOJA DE NAVES", True, (220, 245, 255))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

        subtitle = SMALL_FONT.render("Use as moedas coletadas no jogo para desbloquear novas naves", True, (180, 200, 215))
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 138)))

        coin_text = SMALL_FONT.render(f"MOEDAS: {coins}", True, (255, 220, 90))
        screen.blit(coin_text, (70, 50))

        for ship_id in SHOP_ORDER:
            model = SHIP_MODELS[ship_id]
            col, row = SHOP_POSITIONS[ship_id]

            x = start_x + col * (card_w + gap)
            y = start_y + row * (card_h + gap)

            card = pygame.Rect(x, y, card_w, card_h)
            hover = card.collidepoint(mouse_pos)

            base_color = (12, 20, 32) if not hover else (18, 32, 48)
            border_color = model["color"] if ship_id in owned_skins else (80, 95, 110)

            pygame.draw.rect(screen, base_color, card, border_radius=18)
            pygame.draw.rect(screen, border_color, card, 3, border_radius=18)

            # faixa superior colorida da nave
            pygame.draw.rect(
                screen,
                model["color"],
                (x + 14, y + 14, card_w - 28, 8),
                border_radius=4
            )

            # preview da nave
            draw_ship_showcase(x + card_w // 2, y + 70, -0.18, ship_id, scale=1.25, locked=ship_id not in owned_skins)

            name = SMALL_FONT.render(model["name"].upper(), True, (230, 240, 245))
            screen.blit(name, name.get_rect(center=(x + card_w // 2, y + 120)))

            if ship_id in owned_skins:
                action_text = "JÁ OBTIDA"
                action_color = (180, 255, 210)
            else:
                action_text = f"COMPRAR - {SHIP_PRICES[ship_id]}"
                action_color = (255, 220, 90) if coins >= SHIP_PRICES[ship_id] else (140, 145, 150)

            button = pygame.Rect(x + 35, y + 142, card_w - 70, 34)
            pygame.draw.rect(screen, (8, 14, 24), button, border_radius=10)
            pygame.draw.rect(screen, action_color, button, 2, border_radius=10)

            label = SMALL_FONT.render(action_text, True, action_color)
            screen.blit(label, label.get_rect(center=button.center))

            rects.append((button, ship_id))

        tip = SMALL_FONT.render("ESC para voltar", True, (150, 170, 185))
        screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT - 45)))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return

            if e.type == pygame.MOUSEBUTTONDOWN:
                for button, i in rects:
                    if button.collidepoint(e.pos):

                        if i not in owned_skins:
                            price = SHIP_PRICES[i]

                            if coins >= price:
                                coins -= price
                                owned_skins.append(i)
                                owned_skins.sort()

                                save(COIN_FILE, coins)
                                save_skins(owned_skins)
                                play_sound("buy")



def ship_defeat_animation(ship, ast, bullets, score):
    play_sound("ship_defeat_explosion")
    explosion_bits = []
    shockwaves = []

    for _ in range(90):
        ang = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 9.0)
        explosion_bits.append({
            "x": ship.x,
            "y": ship.y,
            "vx": math.cos(ang) * speed + random.uniform(-1.2, 1.2),
            "vy": math.sin(ang) * speed + random.uniform(-1.2, 1.2),
            "life": random.randint(35, 85),
            "size": random.randint(2, 6),
            "color": random.choice([
                (255, 230, 120),
                (255, 150, 50),
                (255, 80, 45),
                SHIP_MODELS[ship_skin]["accent"],
                SHIP_MODELS[ship_skin]["engine"]
            ])
        })

    for frame in range(130):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

        shake = max(0, 11 - frame * 0.14)
        ox = int(random.uniform(-shake, shake))
        oy = int(random.uniform(-shake, shake))

        draw_space_background()

        for a in ast:
            a.update()
            a.draw()

        for b in bullets[:]:
            b.update()
            b.draw()
            if b.life <= 0:
                bullets.remove(b)

        for bh in black_holes[:]:
            bh.update(ast)
            bh.draw()
            if bh.life <= 0:
                black_holes.remove(bh)

        if frame < 42:
            fall_angle = ship.a + frame * 0.23
            scale = max(0.15, 1 - frame * 0.017)
            flicker = 0 if frame % 6 < 3 else 8

            # rastro da nave avariada
            for i in range(7):
                tx = ship.x - math.cos(ship.a) * (28 + i * 16) + random.randint(-8, 8)
                ty = ship.y - math.sin(ship.a) * (28 + i * 16) + random.randint(-8, 8)
                radius = max(2, 9 - i)
                pygame.draw.circle(screen, (255, 90, 35), (int(tx + ox), int(ty + oy)), radius)
                pygame.draw.circle(screen, (255, 190, 80), (int(tx + ox), int(ty + oy)), max(1, radius // 2))

            draw_ship_model(ship.x + ox, ship.y + oy, fall_angle, ship_skin, scale=scale, inv=flicker)

        if frame in [8, 18, 30]:
            shockwaves.append({"r": 18, "life": 32})

        if frame >= 20:
            if frame == 20:
                shockwaves.append({"r": 24, "life": 45})

            for bit in explosion_bits[:]:
                bit["x"] = (bit["x"] + bit["vx"]) % WIDTH
                bit["y"] = (bit["y"] + bit["vy"]) % HEIGHT
                bit["vx"] *= 0.985
                bit["vy"] *= 0.985
                bit["life"] -= 1

                if bit["life"] <= 0:
                    explosion_bits.remove(bit)
                    continue

                fade = bit["life"] / 85
                size = max(1, int(bit["size"] * fade + 1))
                pygame.draw.circle(screen, bit["color"], (int(bit["x"] + ox), int(bit["y"] + oy)), size)

        for wave in shockwaves[:]:
            wave["r"] += 9
            wave["life"] -= 1

            if wave["life"] <= 0:
                shockwaves.remove(wave)
                continue

            intensity = max(35, min(220, wave["life"] * 6))
            pygame.draw.circle(
                screen,
                (intensity, intensity // 2, 255),
                (int(ship.x + ox), int(ship.y + oy)),
                wave["r"],
                2
            )

        if frame > 70:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, min(150, (frame - 70) * 3)))
            screen.blit(overlay, (0, 0))

        score_shadow = SMALL_FONT.render(f"SCORE: {score}", True, (0, 35, 55))
        score_text = SMALL_FONT.render(f"SCORE: {score}", True, (210, 240, 255))
        screen.blit(score_shadow, (24, 24))
        screen.blit(score_text, (20, 20))

        draw_lives(0)

        pygame.display.flip()
        clock.tick(60)

def game_over(score):
    global coins
    set_music("game_over")

    revive_cost = 10000
    revive_message = ""
    revive_message_timer = 0

    while True:
        draw_space_background()

        mouse_pos = pygame.mouse.get_pos()
        can_revive = coins >= revive_cost

        title = GAME_OVER_FONT.render("GAME OVER", True, (255,60,60))
        screen.blit(title, title.get_rect(center=(WIDTH//2,155)))

        score_text = SMALL_FONT.render(f"PONTOS: {score}", True, (220,220,220))
        screen.blit(score_text, score_text.get_rect(center=(WIDTH//2,235)))

        coins_text = SMALL_FONT.render(f"MOEDAS: {coins}", True, (255, 225, 105))
        screen.blit(coins_text, coins_text.get_rect(center=(WIDTH//2,275)))

        revive_color = (255, 225, 105) if can_revive else (115, 105, 80)
        revive_txt = MENU_FONT.render("REVIVER - 10000 MOEDAS", True, revive_color)
        continuar = MENU_FONT.render("CONTINUAR", True, (255,255,255))
        menu_txt = MENU_FONT.render("VOLTAR AO MENU", True, (255,255,255))

        revive_rect = revive_txt.get_rect(center=(WIDTH//2,350))
        continuar_rect = continuar.get_rect(center=(WIDTH//2,430))
        menu_rect = menu_txt.get_rect(center=(WIDTH//2,510))

        if revive_rect.collidepoint(mouse_pos):
            bg = (80, 65, 20) if can_revive else (45, 40, 38)
            pygame.draw.rect(screen, bg, revive_rect.inflate(36,16), border_radius=10)
            pygame.draw.rect(screen, revive_color, revive_rect.inflate(36,16), 2, border_radius=10)

        if continuar_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (70,70,70), continuar_rect.inflate(30,15), border_radius=10)
            pygame.draw.rect(screen, (255,255,255), continuar_rect.inflate(30,15), 2, border_radius=10)

        if menu_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (70,70,70), menu_rect.inflate(30,15), border_radius=10)
            pygame.draw.rect(screen, (255,255,255), menu_rect.inflate(30,15), 2, border_radius=10)

        screen.blit(revive_txt, revive_rect)
        screen.blit(continuar, continuar_rect)
        screen.blit(menu_txt, menu_rect)

        if not can_revive:
            locked = SMALL_FONT.render("moedas insuficientes", True, (150, 130, 90))
            screen.blit(locked, locked.get_rect(center=(WIDTH//2,385)))

        if revive_message_timer > 0:
            msg = SMALL_FONT.render(revive_message, True, (255, 120, 90))
            screen.blit(msg, msg.get_rect(center=(WIDTH//2,560)))
            revive_message_timer -= 1

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                if revive_rect.collidepoint(e.pos):
                    if can_revive:
                        coins -= revive_cost
                        save(COIN_FILE, coins)
                        play_sound("coin")
                        return "revive"
                    else:
                        play_sound("damage")
                        revive_message = "Você precisa de 10000 moedas para reviver"
                        revive_message_timer = 90

                if continuar_rect.collidepoint(e.pos):
                    play_sound("select")
                    return "restart"

                if menu_rect.collidepoint(e.pos):
                    play_sound("select")
                    return "menu"

def draw_ability_hud(ship):
    ability_names = [
        "TURBO DASH",
        "MISSEIS VESPA",
        "LANÇA RUBI",
        "ONDA DE CHOQUE",
        "DISTORCAO TEMPORAL",
        "EXPLOSAO CIANO",
        "FEIXE PRISMATICO"
    ]

    max_cooldowns = [960, 960, 960, 960, 960, 960, 960]

    name = ability_names[ship_skin]
    max_cd = max_cooldowns[ship_skin]
    cd = getattr(ship, "ability_cd", 0)

    x = 40
    y = HEIGHT - 95
    w = 310
    h = 58

    ready = cd <= 0
    progress = 1 - min(cd / max_cd, 1)

    pygame.draw.rect(screen, (8, 14, 24), (x, y, w, h), border_radius=10)
    pygame.draw.rect(screen, (0, 180, 220), (x, y, w, h), 2, border_radius=10)

    # ícone
    icon_x = x + 32
    icon_y = y + 29

    pygame.draw.circle(screen, (20, 35, 50), (icon_x, icon_y), 22)
    pygame.draw.circle(screen, SHIP_MODELS[ship_skin]["engine"], (icon_x, icon_y), 18, 2)

    if ready:
        pygame.draw.circle(screen, SHIP_MODELS[ship_skin]["accent"], (icon_x, icon_y), 7)
    else:
        pygame.draw.arc(
            screen,
            SHIP_MODELS[ship_skin]["accent"],
            (icon_x - 17, icon_y - 17, 34, 34),
            -math.pi / 2,
            -math.pi / 2 + math.pi * 2 * progress,
            4
        )

    label = SMALL_FONT.render(name, True, (220, 240, 255))
    screen.blit(label, (x + 70, y + 9))

    status = "E PRONTO" if ready else f"{cd // 60 + 1}s"

    status_text = SMALL_FONT.render(status, True, (255, 230, 120) if ready else (150, 170, 180))
    screen.blit(status_text, (x + 70, y + 31))

def game():
    set_music("game")
    global coins
    ship=Ship()
    bullets=[]
    ast=[Asteroid(size=3)]
    score=0
    lives=3

    while True:
        draw_space_background()
        keys=pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN:
                
                if e.key == pygame.K_SPACE:
                    ship.shoot(bullets)

                if e.key == pygame.K_e:
                    ship.use_ability(bullets, ast)

                if e.key == pygame.K_ESCAPE:
                    play_sound("select")
                    return "menu"

        ship.update(keys)
        ship.draw()

        for a in ast[:]:
            
            if hasattr(ship, "slow_timer") and ship.slow_timer > 0:
                a.x += a.vx * 0.35
                a.y += a.vy * 0.35
                margin = a.r + 80
                if a.x < -margin:
                    a.x = WIDTH + margin
                elif a.x > WIDTH + margin:
                    a.x = -margin
                if a.y < -margin:
                    a.y = HEIGHT + margin
                elif a.y > HEIGHT + margin:
                    a.y = -margin
                a.angle += a.spin * 0.35
            else:
                a.update()

            a.draw()

            if a.collides_with_ship(ship):
                if ship_skin == 0 and getattr(ship, "dash_break_timer", 0) > 0:
                    break_asteroid(a, ast)
                    play_sound("hit")
                    for _ in range(30):
                        particles.append(Particle(a.x, a.y))
                    score += 100
                    continue

                if ship.inv<=0:
                    lives-=1
                    play_sound("damage")
                    ship.inv=120
                    break_asteroid(a, ast)
                    for _ in range(30): particles.append(Particle(a.x,a.y))
                    if lives <= 0:
                        play_sound("game_over")
                        ship_defeat_animation(ship, ast, bullets, score)
                        escolha = game_over(score)

                        if escolha == "revive":
                            set_music("game")
                            lives = 3
                            ship.inv = 180
                            ship.vx = 0
                            ship.vy = 0
                            ship.dash_break_timer = 0
                            ship.ability_cd = max(getattr(ship, "ability_cd", 0), 60)
                            continue

                        if escolha == "restart":
                            play_sound("select")
                            return "restart"

                        if escolha == "menu":
                            play_sound("select")
                            return "menu"
    
            for b in bullets[:]:
                if a.collides_with_point(b.x, b.y):
                    bullets.remove(b)
                    play_sound("hit")

                    if ship_skin == 3:
                        # Titã Dourado preserva o tiro pesado: explode o alvo direto em 4 partes pequenas.
                        destroyed = damage_asteroid(a, ast, amount=a.hp, pieces=4, force_small=True)
                    else:
                        destroyed = damage_asteroid(a, ast, amount=1)

                    for _ in range(25):
                        particles.append(Particle(a.x,a.y))

                    if destroyed:
                        score += 100
                    break

    
        if len(ast)<5:
            ast.append(Asteroid(size=3))

        for b in bullets[:]:
            b.update(); b.draw()
            if b.life<=0: bullets.remove(b)

        for p in particles[:]:
            p.update(); p.draw()
            if p.life<=0: particles.remove(p)

        for c in coins_drops[:]:
            c.update(ship)
            c.draw()

            if math.hypot(ship.x-c.x,ship.y-c.y)<20:
                coins += 200
                play_sound("coin")
                save(COIN_FILE, coins)
                coins_drops.remove(c)

        score_shadow = SMALL_FONT.render(f"SCORE: {score}", True, (0, 35, 55))
        score_text = SMALL_FONT.render(f"SCORE: {score}", True, (210, 240, 255))

        screen.blit(score_shadow, (24, 24))
        screen.blit(score_text, (20, 20))

        for bh in black_holes[:]:
            bh.update(ast)
            bh.draw()

            if bh.life <= 0:
                black_holes.remove(bh)

        for lance in ruby_lances[:]:
            score += lance.update(ast)
            lance.draw()

            if lance.life <= 0:
                ruby_lances.remove(lance)

        for missile in wasp_missiles[:]:
            score += missile.update(ast)
            missile.draw()

            if missile.life <= 0:
                wasp_missiles.remove(missile)

        for sw in titan_shockwaves[:]:
            sw.update()
            sw.draw()

            if sw.life <= 0 or sw.radius >= sw.max_radius:
                titan_shockwaves.remove(sw)

        for beam in prism_beams[:]:
            score += beam.update(ast)
            beam.draw()

            if beam.life <= 0:
                prism_beams.remove(beam)

        draw_lives(lives)
        draw_ability_hud(ship)

        pygame.display.flip()
        clock.tick(60)
while True:
    menu()

    while True:
        resultado = game()

        if resultado == "restart":
            continue

        if resultado == "menu":
            break
        