import pygame, sys, os, random
import asyncio  # Zaroori hai web/apk ke liye

# --------- Init ----------
async def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    os.environ.setdefault('SDL_VIDEO_CENTERED', '1')

    # --------- Render & Display sizes ----------
    GAME_W, GAME_H = 960, 540
    game_surf = pygame.Surface((GAME_W, GAME_H))

    # Full window 
    info = pygame.display.Info()
    WIN_W, WIN_H = info.current_w, info.current_h
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("FlYING RUMAN (scaled)")

    clock = pygame.time.Clock()
    FPS = 60

    # --------- Assets filenames ----------
    BG_FILE = "background.jpg"
    BIRD_FILE = "bird.png"
    PIPE_FILE = "wall.png"
    GAMEOVER_FILE = "gameover.jpg"
    LOGO_FILE = "logo.jpg" # <--- Added Logo Filename
    BGM_FILE = "bgmusic.ogg"
    JUMP_FILE = "jump.ogg"
    DEATH_FILE = "gameover.ogg"
    HIGHSCORE_FILE = "highscore.txt"

    # --------- Helpers ----------
    def load_img(name, alpha=False):
        try:
            img = pygame.image.load(name)
            return img.convert_alpha() if alpha else img.convert()
        except:
            print(f"[WARN] image load failed: {name}")
            surf = pygame.Surface((100,100))
            surf.fill((255,0,0))
            return surf

    def load_sound(name):
        try: return pygame.mixer.Sound(name)
        except: return None

    # --------- Load Assets (Yahan ek baar load hoga) ----------
    bg_img = pygame.transform.smoothscale(load_img(BG_FILE), (GAME_W, GAME_H))
    bird_img = pygame.transform.smoothscale(load_img(BIRD_FILE, True), (40, 40))
    pipe_img = pygame.transform.scale(load_img(PIPE_FILE, True), (70, 300))
    gameover_img = pygame.transform.smoothscale(load_img(GAMEOVER_FILE), (int(GAME_W * 0.2), int(GAME_H * 0.35)))
    
    # --- Logo loading fix ---
    logo_img = load_img(LOGO_FILE, alpha=True)
    logo_img = pygame.transform.scale(logo_img, (250, 250)) 
    # ------------------------

    jump_sfx = load_sound(JUMP_FILE)
    death_sfx = load_sound(DEATH_FILE)
    try:
        pygame.mixer.music.load(BGM_FILE)
        pygame.mixer.music.set_volume(0.75)
        pygame.mixer.music.play(-1)
    except: pass

    # --------- Gameplay Tuning ----------
    GRAVITY = 0.6
    FLAP_V = -10
    PIPE_SPEED = 6.5
    PIPE_GAP = int(GAME_H * 0.48)
    SPAWN_MS = 1600
    MIN_PIPE_Y, MAX_PIPE_Y = int(GAME_H * 0.22), int(GAME_H * 0.78)

    # --------- State ----------
    bird_x = int(GAME_W * 0.25)
    bird_y = GAME_H // 2
    bird_vel = 0.0
    bird_rect = bird_img.get_rect(center=(bird_x, bird_y))
    pipes = []
    score = 0
    high_score = 0

    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                high_score = int(f.read().strip() or 0)
        except: pass

    SPAWNPIPE = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWNPIPE, SPAWN_MS)
    bg_x = 0
    BG_SCROLL_SPEED = 1.8

    font_big = pygame.font.SysFont("arial", 48)
    font_small = pygame.font.SysFont("arial", 28)
    WHITE, YELLOW, ORANGE, SHADOW = (255,255,255), (255,215,0), (255,140,0), (0,0,0)

    playing = False
    dead = False
    running = True

    # --------- Internal Functions ----------
    def create_pipe():
        cy = random.randint(MIN_PIPE_Y, MAX_PIPE_Y)
        # add slight jitter
        cy += random.randint(-20, 20)
        cy = max(MIN_PIPE_Y, min(cy, MAX_PIPE_Y))
        return {"x": float(GAME_W + 60), "y": cy, "passed": False}

    # Shadow function wapas add kiya better look ke liye
    def draw_text_with_shadow(surf, txt, font, color, cx, cy):
        sh = font.render(txt, True, SHADOW)
        tx = font.render(txt, True, color)
        r = tx.get_rect(center=(cx, cy))
        surf.blit(sh, (r.x+2, r.y+2))
        surf.blit(tx, r)

    # --------- Main Loop ----------
    while running:
        dt = clock.tick(FPS)
        scale = dt / (1000.0 / FPS)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if not playing or dead:
                    # Start/Restart
                    playing, dead, score, pipes, bird_y, bird_vel = True, False, 0, [], GAME_H//2, 0.0
                    bird_rect.center = (bird_x, bird_y)
                    if not pygame.mixer.music.get_busy(): pygame.mixer.music.play(-1)
                else:
                    # Flap
                    bird_vel = FLAP_V
                    if jump_sfx: jump_sfx.play()

            if ev.type == SPAWNPIPE and playing and not dead:
                if (not pipes) or (pipes[-1]["x"] < GAME_W - int(GAME_W * 0.45)):
                    pipes.append(create_pipe())

        # --- Updates ---
        if playing and not dead:
            bird_vel += GRAVITY * scale
            bird_y += bird_vel * scale
            bird_rect.center = (bird_x, int(bird_y))
            bg_x = (bg_x - BG_SCROLL_SPEED * scale) % -GAME_W

            for p in pipes:
                p["x"] -= PIPE_SPEED * scale
                if not p["passed"] and p["x"] + 70 < bird_x:
                    p["passed"] = True
                    score += 1
            
            pipes = [p for p in pipes if p["x"] > -100]

            # Collision logic
            if bird_rect.top <= 0 or bird_rect.bottom >= GAME_H:
                dead = True
            for p in pipes:
                # Pipe rects based on internal size (70x300)
                t_r = pygame.Rect(p["x"], p["y"] - PIPE_GAP - 300, 70, 300)
                b_r = pygame.Rect(p["x"], p["y"], 70, 300)
                if bird_rect.colliderect(t_r) or bird_rect.colliderect(b_r):
                    dead = True
            
            if dead:
                if death_sfx: death_sfx.play()
                if score > high_score:
                    high_score = score
                    with open(HIGHSCORE_FILE, "w") as f: f.write(str(high_score))
                pygame.mixer.music.stop()

        # --- Draw ---
        game_surf.blit(bg_img, (int(bg_x), 0))
        game_surf.blit(bg_img, (int(bg_x + GAME_W), 0))
        for p in pipes:
            game_surf.blit(pygame.transform.flip(pipe_img, False, True), (p["x"], p["y"] - PIPE_GAP - 300))
            game_surf.blit(pipe_img, (p["x"], p["y"]))
        game_surf.blit(bird_img, bird_rect)

        # --- UI Drawing ---
        if not playing and not dead:
            # Start Screen
            draw_text_with_shadow(game_surf, "FLYING RUMAN", font_big, YELLOW, GAME_W//2, int(GAME_H*0.25))
            # --- LOGO ADDED HERE ---
            game_surf.blit(logo_img, (GAME_W//2 - 125, int(GAME_H*0.35)))
            # -----------------------
            draw_text_with_shadow(game_surf, "Tap to Start", font_small, ORANGE, GAME_W//2, GAME_H//2)
            draw_text_with_shadow(game_surf, f"High Score: {high_score}", font_small, WHITE, GAME_W//2, int(GAME_H*0.65))
        elif dead:
            # Game Over Screen
            game_surf.blit(gameover_img, gameover_img.get_rect(center=(GAME_W//2, GAME_H//2 - 30)))
            draw_text_with_shadow(game_surf, f"Score: {score}", font_small, WHITE, GAME_W//2, int(GAME_H*0.62))
            draw_text_with_shadow(game_surf, f"High Score: {high_score}", font_small, YELLOW, GAME_W//2, int(GAME_H*0.70))
            
        else:
            # In-game Score
            draw_text_with_shadow(game_surf, f"Score: {score}", font_small, WHITE, int(GAME_W*0.12), int(GAME_H*0.06))

        scaled = pygame.transform.smoothscale(game_surf, (WIN_W, WIN_H))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
        # ZAROORI: Browser/APK ko hang hone se bachata hai
        await asyncio.sleep(0)

# Start
if __name__ == "__main__":
    asyncio.run(main())
