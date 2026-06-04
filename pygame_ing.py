import pygame
import random
import math
import time
import os

# 1. 초기화 및 설정
# [초기화] Pygame 엔진을 시작하고 화면 크기(1000x1000)를 설정합니다.
pygame.init()
WIDTH, HEIGHT = 1000, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("블러드 서퍼(Blood Surfer)")
clock = pygame.time.Clock()

# --- [상수 및 색상] ---
RED, DARK_RED = (220, 20, 60), (60, 0, 0)
WHITE, GOLD, GREEN, GRAY, SKYBLUE = (255, 255, 255), (255, 223, 0), (50, 205, 50), (150, 150, 150), (135, 206, 235)
FAT_COLOR_1, FAT_COLOR_2 = (130, 110, 20), (180, 150, 30)

# [적용] 원근감 중심점을 왼쪽으로 이동
CENTER, BASE_RADIUS, MAX_GAUGE = (WIDTH // 2 , HEIGHT // 2), 450, 100
WIDE_RANGE = math.radians(45)

# [최적화용 서피스] 매번 새로 만들면 느려지기 때문에, 안개 효과(fog)나
# 혈관 링(ring)을 그릴 투명 도화지를 미리 생성해둡니다.
ring_temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
fog_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
hole_surf = pygame.Surface((600, 600), pygame.SRCALPHA)

# 폰트 로드
try:
    font = pygame.font.Font('DungGeunMo.ttf', 20)
    big_font = pygame.font.Font('DungGeunMo.ttf', 35)  # 크기를 35 정도로 키움
    small_font = pygame.font.Font('DungGeunMo.ttf', 15)
    bigbig_font = pygame.font.Font('DungGeunMo.ttf', 70)
except:
    font = pygame.font.SysFont("malgungothic", 20)
    big_font = pygame.font.SysFont("malgungothic", 35, bold=True)
    small_font = pygame.font.SysFont("malgungothic", 15, bold=True)
    bigbig_font = pygame.font.SysFont("malgungothic", 70, bold=True)

# 이미지 로드 함수
def load_img(name, size=(200, 200), color=(100, 0, 0)):
    if os.path.exists(name):
        return pygame.transform.scale(pygame.image.load(name).convert_alpha(), size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (size[0]//2, size[1]//2), size[0]//2)
    return surf

# [최적화] 스케일 & 회전 캐시 (양자화 및 알파 지원)
scaled_cache = {}
# [get_scaled 함수] 이미지를 원하는 크기로 조절하되, 한 번 만든 건 'scaled_cache'에 저장합니다.
# 다음 프레임에서 같은 크기가 필요하면 계산하지 않고 저장된 걸 바로 꺼내 써서 렉을 방지합니다.
def get_scaled(img, w, h, alpha=255):
    # 크기를 2픽셀 단위, 알파를 5 단위로 세밀하게 조정하여 떨림 방지
    w, h = (max(1, int(w // 2) * 2), max(1, int(h // 2) * 2))
    alpha = (alpha // 5) * 5
    key = (id(img), w, h, alpha)
    
    if key not in scaled_cache:
        if len(scaled_cache) > 2000: 
            # 한 번에 여러 개 제거할 때 안전하게 키를 먼저 수집
            keys_to_remove = []
            it = iter(scaled_cache)
            for _ in range(100):
                try: keys_to_remove.append(next(it))
                except StopIteration: break
            for k in keys_to_remove:
                scaled_cache.pop(k, None)
        
        new_surf = pygame.transform.scale(img, (w, h))
        if alpha < 255:
            new_surf.set_alpha(alpha)
        scaled_cache[key] = new_surf
    return scaled_cache[key]

rotated_cache = {}
def get_rotated(img, angle):
    # 각도를 1도 단위로 정교화
    angle = int(angle) % 360
    key = (id(img), angle) 
    if key not in rotated_cache:
        if len(rotated_cache) > 360: rotated_cache.clear()
        rotated_cache[key] = pygame.transform.rotate(img, angle)
    return rotated_cache[key]

# 자산 로드
player_right = load_img("character.png", (100, 100))
player_left = load_img("character_1.png", (100, 100))
player_special = load_img("3d_d_character.png", (150, 150), color=GOLD) 
player_hit = load_img("3d_dm_character.png", (200, 200), color=WHITE) 
player_stunned = load_img("3d_stressed.png", (150, 150), color=GRAY) 
player_magnet = load_img("b_character.png", (130, 130), color=SKYBLUE) 
bg_wall_img = load_img("wall.png", (500, 500), (50, 0, 0))
ending_win = load_img('ending_win.png', (1000, 1000))
ending_fail = load_img('ending_fail.png', (1000, 1000))
pause_tutorial = load_img("pause.png", (800, 800))  # 파일명 맞춰서
title_img = load_img("title.png", (WIDTH, HEIGHT))
main_img = load_img("main.png", (WIDTH, HEIGHT))

story_imgs = [
    load_img("story1.png", (WIDTH, HEIGHT)),
    load_img("story2.png", (WIDTH, HEIGHT)),
    load_img("story3.png", (WIDTH, HEIGHT)),
    load_img("story4.png", (WIDTH, HEIGHT)),
    load_img("story5.png", (WIDTH, HEIGHT)),
]

tutorial_img = load_img("tutorial.png", (WIDTH, HEIGHT))

# 지방 이미지 로드
def load_keep_ratio(name, target_h=150):
    if not os.path.exists(name): return None
    img = pygame.image.load(name).convert_alpha()
    w, h = img.get_size()
    new_w = int(w * (target_h / h))
    scaled = pygame.transform.scale(img, (new_w, target_h))
    scaled.set_alpha(180)
    return scaled

def load_countdown_img(name, target_h=200):
    if not os.path.exists(name): return None
    img = pygame.image.load(name).convert_alpha()
    w, h = img.get_size()
    new_w = int(w * (target_h / h))
    return pygame.transform.scale(img, (new_w, target_h))

countdown_imgs = {
    "3": load_countdown_img("3.png", 200),
    "2": load_countdown_img("2.png", 200),
    "1": load_countdown_img("1.png", 200),
    "START!": load_countdown_img("start.png", 300)
}

fat_obstacle_imgs = []
img1 = load_keep_ratio("fat_small.png")
if img1: fat_obstacle_imgs.append(img1)
img2 = load_keep_ratio("fat_small1.png")
if img2: fat_obstacle_imgs.append(img2)

if not fat_obstacle_imgs:
    fat_obstacle_imgs.append(load_img("fat_small_placeholder", (100, 100), FAT_COLOR_2))

# 사운드 로드
pygame.mixer.init()
SFX = {}
def load_sfx(name, file):
    try: SFX[name] = pygame.mixer.Sound(file)
    except: SFX[name] = None
try:
    bgm_music = pygame.mixer.Sound("bgm.wav")
    bgm_music.set_volume(1.0)
except:
    bgm_music = None
# tutorial.wav
try:
    tutorial_music = pygame.mixer.Sound("tutorial.wav")
    tutorial_music.set_volume(1.0)
except:
    tutorial_music = None

# cpr.wav
try:
    cpr_music = pygame.mixer.Sound("cpr.wav")
except:
    cpr_music = None

# heartbeat.wav
try:
    heartbeat_music = pygame.mixer.Sound("heartbeat.wav")
except:
    heartbeat_music = None

# hylight.wav
try:
    hylight_music = pygame.mixer.Sound("hylight.wav")
    hylight_music.set_volume(1.0)
except:
    hylight_music = None
# --- BGM을 Sound로 쓸 거면 Channel로 통일 ---
BGM_CH = pygame.mixer.Channel(0)   # 0번 채널을 BGM 전용으로 사용
BGM_CH.set_volume(1.0)

def bgm_stop():
    BGM_CH.stop()

def bgm_play(sound, vol=1.0):
    if sound is None:
        return
    BGM_CH.stop()              # ✅ 겹침 방지
    BGM_CH.set_volume(vol)
    BGM_CH.play(sound, loops=-1)

def bgm_pause():
    BGM_CH.pause()

def bgm_unpause():
    BGM_CH.unpause()
    
for s in [("hit", "hit.wav"), ("item_good", "good.wav"), ("item_bad", "bad.wav"), 
          ("level_up", "powerup.wav"), ("win", "win.wav"), ("lose", "lose.wav")]:
    load_sfx(s[0], s[1])

ITEM_IMAGES = {
    'junk': load_img("3d_junkfood.png", color=(139, 69, 19)),
    'smoke': load_img("3d_cigarette.png", color=GRAY),
    'alcohol': load_img("3d_alcohol.png", color=(100, 100, 255)),
    'stress': load_img("3d_stress.png", color=(255, 100, 100)),
    'special': [load_img(g, (200, 200), SKYBLUE) for g in ["3d_dumbbell.png", "3d_pill.png", "3d_treadmill.png"]]
}

GOOD_EFFECTS = {
    "3d_broccoli.png":  {"purity": 8.0, "gauge": 12.0},  
    "3d_blueberry.png": {"purity": 6.0, "gauge": 22.0},  
    "3d_avocado.png":   {"purity": 5.0, "gauge": 18.0},  
    "3d_tomato.png":    {"purity": 4.0, "gauge": 16.0},  
    "3d_almond.png":    {"purity": 3.0, "gauge": 28.0},  
}

# [최적화] 선체 아이템 이미지 미리 로드
GOOD_ITEM_IMAGES = {k: load_img(k, (200, 200), GREEN) for k in GOOD_EFFECTS.keys()}

# ----------------------------
# 프리컴퓨트(아틀라스) 설정 - 렉 방지 핵심
# ----------------------------
ITEM_SZ_MIN = 16
ITEM_SZ_MAX = 700
ITEM_SZ_STEP = 2

BG_W_MIN = 200
BG_W_MAX = 3500
BG_W_STEP = 32
BG_ALPHA_STEP = 16

def snap(v, step, vmin=None, vmax=None):
    v = (int(v) // step) * step
    if vmin is not None: v = max(vmin, v)
    if vmax is not None: v = min(vmax, v)
    return v

item_atlas = {}
bg_atlas = {}

def build_item_atlas_for_image(img):
    atlas = {}
    for sz in range(ITEM_SZ_MIN, ITEM_SZ_MAX + 1, ITEM_SZ_STEP):
        atlas[sz] = pygame.transform.smoothscale(img, (sz, sz))
    item_atlas[id(img)] = atlas

def get_item_scaled(img, sz):
    sz = snap(sz, ITEM_SZ_STEP, ITEM_SZ_MIN, ITEM_SZ_MAX)
    atlas = item_atlas.get(id(img))
    if atlas is None:
        build_item_atlas_for_image(img)
        atlas = item_atlas[id(img)]
    return atlas[sz], sz

fat_atlas = {}

def get_fat_scaled(img, h, alpha=180):
    # 높이를 기준으로 스냅 적용 (최대 범위를 좀 더 넉넉히 1500까지 잡음)
    h = snap(h, ITEM_SZ_STEP, ITEM_SZ_MIN, 1500)
    
    # 캐시에 해당 이미지용 딕셔너리가 없으면 생성
    atlas = fat_atlas.get(id(img))
    if atlas is None:
        atlas = {}
        fat_atlas[id(img)] = atlas
        
    # 만약 해당 해상도(h) 이미지가 없으면 새로 생성해서 캐싱
    if h not in atlas:
        bw, bh = img.get_size()
        w = max(1, int(bw * (h / bh)))
        new_surf = pygame.transform.smoothscale(img, (w, h))
        if alpha < 255:
            new_surf.set_alpha(alpha)
        atlas[h] = new_surf
        
    return atlas[h]

def build_all_item_atlases():
    for k, v in ITEM_IMAGES.items():
        if k == "special":
            for im in v: build_item_atlas_for_image(im)
        else:
            build_item_atlas_for_image(v)
    for im in GOOD_ITEM_IMAGES.values():
        build_item_atlas_for_image(im)

build_all_item_atlases()

def get_bg_scaled(w, alpha):
    w = snap(w, BG_W_STEP, BG_W_MIN, BG_W_MAX)
    alpha = snap(alpha, BG_ALPHA_STEP, 0, 255)
    key = (w, alpha)
    surf = bg_atlas.get(key)
    if surf is None:
        surf = pygame.transform.smoothscale(bg_wall_img, (w, w))
        if alpha < 255:
            surf.set_alpha(alpha)
        bg_atlas[key] = surf
    return surf

def make_single_fat():
    return {
        'angle': random.uniform(0, math.pi * 2), 
        'z': random.uniform(200, 800), 
        'dist_mult': random.uniform(0.7, 1.3),
        'radius': random.randint(80, 150),
        'img_index': random.randint(0, len(fat_obstacle_imgs) - 1)
    }

def reset_game():
    scaled_cache.clear()
    rotated_cache.clear()
    
    return {
        'face_dir': 1, 'purity': 30.0, 'special_gauge': 0.0, 'start_time': time.time(),
        'visual_purity': 30.0, 
        'items_data': [], 'fat_rings': [make_single_fat() for _ in range(15)],
        'bg_layers': [0, 200, 400, 600, 800], 'game_state': "playing", 'angle': math.pi / 2,
        'is_inverted': False, 'is_blurred': False, 'is_stunned': False, 'exercise_mode': False,
        'invert_timer': 0, 'blur_timer': 0, 'stun_timer': 0, 'exercise_timer': 0, 
        'ultimate_hit_timer': 0, 'damage_timer': 0, 'invincible_timer': 0,
        'spawn_counter': 0, 'magnet_timer': 0,  
        'last_sector': -1,  
        'last_tick': time.time(),
        'difficulty': 1.0,
        'ring_offset': 0.0,
        'frame_i': 0,
        'is_paused': False,
        'pause_start': 0,
        'total_pause_time': 0,
        'dinner_mode_triggered': False,
        'pause_frame': None,
        'scene': 'title',   # title -> main -> story -> tutorial -> playing
        'story_idx': 0,
        'last_story_sound_idx': None,
        'countdown_start': 0,
        'countdown_active': False,
        'request_pause_with_countdown': False,
        'bgm_to_play': None,
    }

g = reset_game()

def draw_vessel_rings():
    purity_scale = (g['visual_purity'] / 100 * 0.75 + 0.35) 
    ring_alpha = int((1 - (g['visual_purity'] / 100)) * 80) 
    if ring_alpha <= 0: return 

    ring_temp_surf.fill((0, 0, 0, 0))
    for z in range(100, 1000, 200):
        # [수정] time.time() 대신 게임 내부 타이머 사용 유도 (현재는 g['ring_offset']이 없으므로 일단 유지하되 더 부드럽게)
        offset = (g.get('ring_offset', 0)) % 200
        pf = 150 / (z - offset + 1)
        if pf > 0:
            r = int(BASE_RADIUS * pf * purity_scale)
            if r < 15: continue
            darkness = max(0, min(1, (1000 - z) / 1000))
            c_r = int(max(60, min(200, 120 - g['visual_purity'])) * darkness)
            c_g = int((10 + g['visual_purity'] * 0.1) * darkness)
            pygame.draw.circle(ring_temp_surf, (c_r, c_g, 10, ring_alpha), CENTER, r, max(1, int(3 * darkness)))
    screen.blit(ring_temp_surf, (0, 0))

def draw_dynamic_fat(speed, px, py):
    """
    [발표 포인트] 2D 환경에서 3D 원근감을 구현하는 핵심 함수
    1. 거리(z)에 따른 물체의 크기와 위치 변화 계산
    2. 혈관 청정도(Purity)에 따른 실시간 난이도(공간 제약) 반영
    """
    
    # --- 1. 혈관 상태에 따른 반지름 결정 ---
    # 청정도(visual_purity)가 낮을수록 혈관 벽이 좁아지는 시각적 효과 반영
    p_scale = (g['visual_purity'] / 100 * 0.75 + 0.35) 
    curr_rad = BASE_RADIUS * p_scale
    
    # --- 2. 렌더링 순서 정렬 (Depth Sorting) ---
    # 멀리 있는 물체(z값이 큰 것)를 먼저 그려야 가까운 물체에 가려지는 입체감이 생김
    g['fat_rings'].sort(key=lambda x: x['z'], reverse=True)
    
    for fat in g['fat_rings']:
        # --- 3. 위치 업데이트 및 재배치 (Recycling) ---
        # 매 프레임마다 speed만큼 플레이어에게 다가옴
        fat['z'] -= speed
        
        # 화면을 지나쳐 뒤로 사라지면 다시 저 멀리(z=800) 생성하여 무한 루프 구현
        if fat['z'] < 10:
            fat['z'] = 800
            fat['angle'] = random.uniform(0, math.pi * 2) # 새로운 랜덤 각도
            fat['img_index'] = random.randint(0, len(fat_obstacle_imgs) - 1)

        # --- 4. 원근법(Perspective) 핵심 공식 적용 ---
        # pf(Projection Factor): 거리가 가까울수록(z가 작을수록) 수치가 커짐
        pf = 150 / (fat['z'] + 1)
        
        # 청정도가 낮을수록 지방이 안쪽으로 더 파고들게 설정 (난이도 조절)
        spread_factor = fat['dist_mult'] * (1.0 + (g['visual_purity'] / 100 * 0.2)) 
        
        # 삼각함수를 이용해 원형 혈관 벽면의 (x, y) 좌표 산출
        # pf를 곱해줌으로써 멀리 있으면 중앙에, 가까우면 외곽으로 퍼지게 만듦
        bx = CENTER[0] + math.cos(fat['angle']) * (curr_rad * spread_factor * pf)
        by = CENTER[1] + math.sin(fat['angle']) * (curr_rad * spread_factor * pf)
                
        # --- 5. 화면 범위 내에 있을 때만 렌더링 ---
        if 0 < bx < WIDTH and 0 < by < HEIGHT:
            base_img = fat_obstacle_imgs[fat['img_index']]
            bw, bh = base_img.get_size()
            
            # --- 6. 다이나믹 스케일링 (Dynamic Scaling) ---
            # pf에 지수(1.4)를 적용하여 가까워질 때 크기가 기하급수적으로 커지게 함 (역동성)
            dynamic_scale = pf ** 1.4 
            r_h = max(1, int(fat['radius'] * dynamic_scale * 2.5))
            
            # --- 7. 최적화된 지방 이미지 아틀라스 출력 ---
            # 메모리 관리를 위해 고정 크기 리스트에서 즉시 호출
            img = get_fat_scaled(base_img, r_h, alpha=180)
            
            # 혈관 각도에 맞춰 지방 이미지를 회전시켜 일체감 부여
            rot_img = get_rotated(img, math.degrees(-fat['angle']))
            
            # 최종 연산된 좌표(bx, by)를 중심으로 이미지 출력
            screen.blit(rot_img, rot_img.get_rect(center=(int(bx), int(by))))

running = True
while running:
    bg_color = (130, 20, 20) if g['damage_timer'] > 0 else DARK_RED
    

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # R: 언제 누르든 "완전 리셋 → 타이틀"로
            if event.key == pygame.K_r:
                bgm_stop()
                if tutorial_music: tutorial_music.stop()
                if heartbeat_music: heartbeat_music.stop()
                if cpr_music: cpr_music.stop()
                if hylight_music: hylight_music.stop()

                g = reset_game()

                g['scene'] = 'playing'
                g['game_state'] = "playing"
                g['start_time'] = time.time()
                g['last_tick'] = time.time()
                g['total_pause_time'] = 0
                g['is_paused'] = False
                g['pause_frame'] = None
                
                g['request_pause_with_countdown'] = True
                g['bgm_to_play'] = bgm_music
                continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                
                # -------------------------
                # 1) 인트로 씬이면: 다음 화면으로 넘기기
                # -------------------------
                if g['scene'] == 'title':
                    g['scene'] = 'main'
                    if tutorial_music:
                            tutorial_music.play(-1)
                elif g['scene'] == 'main':
                    g['scene'] = 'story'
                    g['story_idx'] = 0

                elif g['scene'] == 'story':
                    g['story_idx'] += 1

                    # 스토리 넘어갈 때 이전 스토리 전용 사운드 정리
                    if heartbeat_music: heartbeat_music.stop()
                    if cpr_music: cpr_music.stop()
                    g['last_story_sound_idx'] = None

                    if g['story_idx'] >= 5:
                        g['scene'] = 'tutorial'
                        
                elif g['scene'] == 'tutorial':
                    g['scene'] = 'playing'
                    g['game_state'] = "playing"
                    g['start_time'] = time.time()
                    g['last_tick'] = time.time()
                    g['total_pause_time'] = 0
                    g['is_paused'] = False
                    g['pause_frame'] = None
                    if tutorial_music:
                        tutorial_music.stop()
                    
                    bgm_stop()
                    g['request_pause_with_countdown'] = True
                    g['bgm_to_play'] = bgm_music
                # -------------------------
                # 2) 실제 게임 중이면: 일시정지 토글 + 음악 pause/unpause
                # -------------------------
                elif g['scene'] == 'playing' and g['game_state'] == "playing":
                    if not g.get('countdown_active'):
                        if not g['is_paused']:
                            # 일시정지 시작
                            g['is_paused'] = True
                            g['pause_start'] = time.time()
                            g['pause_frame'] = None
                            bgm_pause()
                        else:
                            # 카운트다운 시작
                            g['countdown_active'] = True
                            g['countdown_start'] = time.time()
    # -----------------------------
    # [씬 렌더링] title -> main -> story -> tutorial
    # -----------------------------
    if g['scene'] == 'title':
        if time.time() - g['start_time'] > 2.0:
            g['scene'] = 'main'
            if tutorial_music:
                tutorial_music.play(-1)
            continue
            
        screen.blit(title_img, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue

    if g['scene'] == 'main':
        screen.blit(main_img, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue

    if g['scene'] == 'story':
    # ✅ 스토리 진입/변경 감지해서 한 번만 재생 처리
        if g.get('last_story_sound_idx') != g['story_idx']:
            g['last_story_sound_idx'] = g['story_idx']

            # 일단 둘 다 끄고
            if heartbeat_music: heartbeat_music.stop()
            if cpr_music: cpr_music.stop()

            # 2번째 스토리(인덱스 1) -> heartbeat
            if g['story_idx'] == 1 and heartbeat_music:
                if tutorial_music:
                    tutorial_music.set_volume(0.4)
                    heartbeat_music.set_volume(1)
                    heartbeat_music.play(-1)

            # 3번째 스토리(인덱스 2) -> cpr
            elif g['story_idx'] == 2 and cpr_music:
                if tutorial_music:
                    tutorial_music.set_volume(0.4)
                    cpr_music.set_volume(1)
                    cpr_music.play(-1)
            elif g['story_idx'] == 3:
                if tutorial_music:
                    tutorial_music.set_volume(1.0)
                    
        screen.blit(story_imgs[g['story_idx']], (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue

    if g['scene'] == 'tutorial':
        screen.blit(tutorial_img, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue
    
    if g['scene'] == 'playing' and g['game_state'] == "playing" and g['is_paused']:
        if g.get('pause_frame') is None:
            g['pause_frame'] = screen.copy()

        screen.blit(g['pause_frame'], (0, 0))
        
        if g.get('countdown_active'):
            elapsed = time.time() - g['countdown_start']
            remain = 3 - int(elapsed)
            
            if remain > 0:
                text_str = str(remain)
            else:
                text_str = "START!"
                
            img = countdown_imgs.get(text_str)
            
            if img:
                img_rect = img.get_rect(center=(WIDTH//2, HEIGHT//2))
                screen.blit(img, img_rect)
            else:
                text_surf = bigbig_font.render(text_str, True, WHITE)
                text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                screen.blit(text_surf, text_rect)
                
            if elapsed > 3.5:
                g['countdown_active'] = False
                g['is_paused'] = False
                g['total_pause_time'] += time.time() - g['pause_start']
                g['last_tick'] = time.time()
                g['pause_frame'] = None
                
                if g.get('bgm_to_play'):
                    bgm_play(g['bgm_to_play'], vol=1.0)
                    g['bgm_to_play'] = None
                else:
                    bgm_unpause()
        else:
            screen.blit(pause_tutorial, (100, 100))
            
        pygame.display.flip()
        clock.tick(60)
        continue
    
    
    
    # 3) 여기서부터 평소 렌더링
    screen.fill(bg_color)
    # --- [일시정지 화면] ---
    
    if g['game_state'] == "playing" and not g['is_paused']:
        now = time.time()
        
        if g.get('request_pause_with_countdown'):
            dt = 0
            g['start_time'] += (now - g['last_tick'])
        else:
            dt = now - g['last_tick']
            
        g['last_tick'] = now
        elapsed = now - g['start_time']
        
        # 난이도 조절 (시간에 따라 완만하게 증폭)
        g['difficulty'] = 1.0 + (elapsed / 60.0) * 0.7 
        
        # [수정] 스크롤 속도 재조정
        scroll_speed = int((5 + (1 - (g['purity']/100)) * 5) * (1.0 + (g['difficulty'] - 1.0) * 0.4))
        g['ring_offset'] += scroll_speed * 60 * dt 
        
        if not g['exercise_mode']: 
            drain_rate = (0.5 + 0.03 * elapsed) * g['difficulty']
            g['purity'] = max(0.0, g['purity'] - drain_rate * dt)

        g['visual_purity'] += (g['purity'] - g['visual_purity']) * (10.0 * dt)
        curr_radius = BASE_RADIUS * (g['visual_purity'] / 100 * 0.75 + 0.35)
        
        # 1. 배경 렌더링 (레이어 수 조절 및 스케일 최적화)
        bg_layers_to_draw = sorted(g['bg_layers'], reverse=True)[:4] # 상위 4개만 그려 성능 확보
        for i in range(len(g['bg_layers'])):
            g['bg_layers'][i] -= scroll_speed
            if g['bg_layers'][i] < 0: g['bg_layers'][i] += 1000
                
        for bg_z in bg_layers_to_draw:
            # 원근감 지수를 높여(2.2) 더 역동적인 빨려들어감 구현
            s_f = ((1000 - bg_z) / 1000) ** 2.2
            radius_ratio_bg = g['visual_purity'] / 100 * 0.3 + 0.7 
            max_scale = max(2500, int(3500 * radius_ratio_bg))
            
            w = max(1, int(max_scale * s_f)) 
            scaled_bg = get_bg_scaled(w, int(160 * s_f))
            screen.blit(scaled_bg, scaled_bg.get_rect(center=CENTER))
        
        draw_vessel_rings()

        # 2. 플레이어 조작
        if not g['is_stunned']:
            keys = pygame.key.get_pressed()
            rot_s = 0.08 * (-1 if g['is_inverted'] else 1) 
            if keys[pygame.K_LEFT]: g['angle'] += rot_s; g['face_dir'] = -1
            if keys[pygame.K_RIGHT]: g['angle'] -= rot_s; g['face_dir'] = 1
            g['angle'] = max(math.pi/2 - WIDE_RANGE, min(g['angle'], math.pi/2 + WIDE_RANGE))

        track_r = curr_radius
        px = CENTER[0] + math.cos(g['angle']) * track_r
        py = CENTER[1] + math.sin(g['angle']) * track_r
        draw_dynamic_fat(scroll_speed, px, py)

        elapsed_real = now - g['start_time'] - g['total_pause_time']

        # [이벤트] 회식 모드 5초 전 경고 타이머 표시
        if 25 <= elapsed_real < 30:
            time_left = 30 - int(elapsed_real)
            if g.get('dinner_warning_time') != time_left:
                g['dinner_warning_time'] = time_left
                msg_surf = font.render(f"경고! 피할 수 없는 회식 파도 {time_left}초 전!", True, GOLD)
                bg_w, bg_h = msg_surf.get_width() + 40, msg_surf.get_height() + 20
                msg_box = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                pygame.draw.rect(msg_box, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=10)
                msg_box.blit(msg_surf, (20, 10))
                g['center_msg'] = {'surface': msg_box, 'timer': 60}

        # [이벤트] 회식 모드: 30초 경과 시 정크푸드, 담배, 술 동시 등장
        if elapsed_real >= 30 and not g.get('dinner_mode_triggered', False):
            g['dinner_mode_triggered'] = True
            # ✅ BGM을 hylight.wav로 교체
            # ✅ Sound 방식으로 확실히 교체
            bgm_play(hylight_music, vol=0.5)
            # 회식 경고 메시지
            msg_surf = font.render("앗! 피할 수 없는 회식 파도다!", True, RED)
            bg_w, bg_h = msg_surf.get_width() + 40, msg_surf.get_height() + 20
            msg_box = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
            pygame.draw.rect(msg_box, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=10)
            msg_box.blit(msg_surf, (20, 10))
            g['center_msg'] = {'surface': msg_box, 'timer': 120}
            
            dinner_types = ['junk', 'smoke', 'alcohol']
            
            # 피할 수 없는 폭격(파도) 생성: z축과 각도를 광범위하게 꽉 채워서 쏟아지게 만듬
            for wave in range(10): 
                z_pos = 1200 + wave * 90
                # 좌우 이동 가능 범위를 촘촘히 나눠서 빈공간을 막아버림
                for offset in [-0.8, -0.5, -0.2, 0.1, 0.4, 0.7]:
                    # 70% 확률로 각 위치에 아이템을 배치해, 섞이면서 내려오는 시각적 느낌 강화
                    if random.random() < 0.7:  
                        i_type = random.choice(dinner_types)
                        g['items_data'].append({
                            'type': i_type, 'subtype': None, 'image': ITEM_IMAGES[i_type], 'good_key': None,
                            'angle': math.pi/2 + offset, 'z': z_pos, 
                            'speed': random.randint(13, 17) * (1.0 + (g['difficulty'] - 1.0) * 0.15) * 1.25
                        })

        # 3. 아이템 생성 (생성 주기 완화)
        g['spawn_counter'] += 1 + (g['difficulty'] - 1.0) * 0.5
        if g['spawn_counter'] >= 35:
            num_to_spawn = random.choices([1, 2], weights=[85, 15])[0]
            sectors = [math.pi/2 - 0.8, math.pi/2, math.pi/2 + 0.8]
            
            for _ in range(num_to_spawn):
                curr_idx = random.randrange(len(sectors))
                while curr_idx == g['last_sector']:
                    curr_idx = random.randrange(len(sectors))
                g['last_sector'] = curr_idx
                
                good_key, subtype = None, None
                if g['special_gauge'] >= MAX_GAUGE:
                    itype = 'special'
                    g['special_gauge'] = 0
                    idx = random.randrange(len(ITEM_IMAGES['special']))
                    img = ITEM_IMAGES['special'][idx]
                    subtype = "pill" if idx == 1 else "equipment"
                else:
                    # 난이도가 높을수록 나쁜 아이템 확률 미세 증가
                    bad_weight = 2.0 + (g['difficulty'] - 1.0) * 0.5
                    itype = random.choices(['good', 'junk', 'smoke', 'alcohol', 'stress'], 
                                           weights=[5, bad_weight, 0.5 * g['difficulty'], 0.5 * g['difficulty'], 0.5 * g['difficulty']])[0]
                    if itype == 'good':
                        good_key = random.choice(list(GOOD_EFFECTS.keys()))
                        img = GOOD_ITEM_IMAGES[good_key]
                    else:
                        img = ITEM_IMAGES[itype]

                speed_multiplier = 1.25 if g.get('dinner_mode_triggered') else 1.0
                g['items_data'].append({
                    'type': itype, 'subtype': subtype, 'image': img, 'good_key': good_key,
                    'angle': sectors[curr_idx] + random.uniform(-0.1, 0.1), 'z': 1200, 
                    'speed': random.randint(10, 15) * (1.0 + (g['difficulty'] - 1.0) * 0.15) * speed_multiplier
                })
            g['spawn_counter'] = 0

        # 4. 아이템 업데이트 및 충돌
        new_items = []
        for item in g['items_data']:
            item['z'] -= item['speed']
            
            # 필살기(Special): 운동 모드 돌입 시 자석(Magnet) 효과로 좋은 아이템을 끌어당김
            if g['magnet_timer'] > 0 and item['type'] in ['good']:
                angle_diff = g['angle'] - item['angle']
                item['angle'] += angle_diff * 0.07 # 아이템의 각도를 플레이어 쪽으로 서서히 보정 

            if item['z'] < -10: continue
            
            pf = 150 / (item['z'] + 1)
            ix = CENTER[0] + math.cos(item['angle']) * (curr_radius * pf)
            iy = CENTER[1] + math.sin(item['angle']) * (curr_radius * pf)
            
            picked = False
            # [충돌 체크] 아이템의 z(깊이)값이 30~200 사이(플레이어의 위치)일 때만 충돌을 확인합니다.
            if 30 < item['z'] < 200 and math.hypot(px - ix, py - iy) < 70: # 플레이어와 아이템 사이의 직선 거리를 계산해 70 픽셀 이내면 먹은 것으로 간주합니다. # 아이템 효과 적용 (청정도 상승, 상태이상 발생 등)
                is_bad = item['type'] in ['junk', 'smoke', 'alcohol', 'stress']
                
                if g['exercise_mode'] and is_bad and g['magnet_timer'] <= 0:
                    picked = True 
                    if SFX.get('hit'): SFX['hit'].play()
                    g['ultimate_hit_timer'] = 15 
                    g['purity'] = min(100.0, g['purity'] + 2.0)
                
                elif g['magnet_timer'] > 0 and is_bad:
                    picked = False 
                
                elif g['invincible_timer'] > 0 and is_bad:
                    picked = False # 0.5초 무적 시간 동안은 장애물 무시
                
                else:
                    picked = True
                    if g['exercise_mode'] and is_bad:
                        pass
                    elif is_bad:
                        if SFX.get("item_bad"): SFX["item_bad"].play()
                        
                        if item['type']=='smoke': msg_text='시야가 2초간 뿌얘져!'
                        elif item['type']=='alcohol': msg_text='방향 감각 상실!'
                        elif item['type']=='stress': msg_text='1초간 멈춤!'
                        elif item['type']=='junk': msg_text='지방이 점점 쌓여가!'
                        
                        msg_surf = font.render(msg_text, True, GOLD)
                        bg_w, bg_h = msg_surf.get_width() + 40, msg_surf.get_height() + 20
                        msg_box = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                        pygame.draw.rect(msg_box, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=10)
                        msg_box.blit(msg_surf, (20, 10))
                        g['top_msg'] = {'surface': msg_box, 'timer': 120}
                        
                        g['purity'] = max(0.0, g['purity'] - 10.0)
                        g['invincible_timer'] = 30
                        if item['type'] == 'smoke': g['is_blurred'], g['blur_timer'] = True, 120
                        elif item['type'] == 'alcohol': g['is_inverted'], g['invert_timer'] = True, 150
                        elif item['type'] == 'stress': g['is_stunned'], g['stun_timer'] = True, 120
                        
                    elif item['type'] == 'good':
                        if SFX.get("item_good"): SFX["item_good"].play()
                        
                        # 1. 아이템 정보 가져오기
                        eff = GOOD_EFFECTS.get(item.get('good_key'), {"purity": 5.0, "gauge": 20.0})
                        p_inc = eff["purity"]
                        g_inc = eff["gauge"]
                        
                        # 2. 실제 수치 반영
                        g['purity'] = min(100.0, g['purity'] + p_inc)
                        g['special_gauge'] = min(MAX_GAUGE, g['special_gauge'] + g_inc)
                        
                        # 3. 화면 하단에 띄울 메시지 생성
                        item_name = item.get('good_key').replace("3d_", "").replace(".png", "").upper()
                        msg_text = f"청정도 +{p_inc}, 게이지 +{g_inc}"
                        
                        # 4. 메시지 박스 렌더링 (기존 bad_item 로직 활용)
                        msg_surf = font.render(msg_text, True, (50, 255, 50)) # 초록색 계열로 표시
                        bg_w, bg_h = msg_surf.get_width() + 40, msg_surf.get_height() + 20
                        msg_box = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                        
                        # 반투명 검정 배경 박스
                        pygame.draw.rect(msg_box, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=10)
                        msg_box.blit(msg_surf, (20, 10))
                        
                        # 전역 변수에 저장해서 화면에 그리게 함
                        g['top_msg'] = {'surface': msg_box, 'timer': 60} # 굿 아이템은 1초(60프레임)만 짧게 표시
                    
                    elif item['type'] == 'special':
                        if SFX.get("level_up"): SFX["level_up"].play()
                        g['exercise_mode'], g['exercise_timer'] = True, 300
                        if item.get('subtype') == "pill":
                            g['purity'] = min(100.0, g['purity'] + 15.0)
                            g['magnet_timer'] = 300 
                        else:
                            g['purity'] = min(100.0, g['purity'] + 25.0)
                            
                        msg_text = '필살기 모드 발동!'
                        msg_surf = font.render(msg_text, True, GOLD)
                        bg_w, bg_h = msg_surf.get_width() + 40, msg_surf.get_height() + 20
                        msg_box = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                        pygame.draw.rect(msg_box, (0, 0, 0, 180), (0, 0, bg_w, bg_h), border_radius=10)
                        msg_box.blit(msg_surf, (20, 10))
                        g['top_msg'] = {'surface': msg_box, 'timer': 120}
            if not picked:
                sz = int(210 * pf) 
                if sz > 0:
                    surf, snapped_sz = get_item_scaled(item['image'], sz)
                    screen.blit(surf, (int(ix - snapped_sz//2), int(iy - snapped_sz//2)))
                new_items.append(item)
        g['items_data'] = new_items

        # 5. 타이머 감소 및 상태 업데이트
        for k in ['blur_timer', 'invert_timer', 'stun_timer', 'exercise_timer', 'ultimate_hit_timer', 'invincible_timer', 'damage_timer', 'magnet_timer']:
            if g[k] > 0: g[k] -= 1
            elif k == 'blur_timer': g['is_blurred'] = False
            elif k == 'invert_timer': g['is_inverted'] = False
            elif k == 'stun_timer': g['is_stunned'] = False
            elif k == 'exercise_timer': g['exercise_mode'] = False

        # [지방 생성] 혈관 청정도(purity)가 낮을수록 더 많은 지방 장애물을 생성합니다.    
        t_fat = 1.0 - (g['visual_purity'] / 100.0) # 더러운 정도를 0~1로 환산
        target_inner = int(2 + 53 * t_fat) # 깨끗하면 2개, 더러우면 최대 85개까지 생성
        
        # 현재 지방 개수가 목표치보다 적으면 새로 만들고, 많으면 삭제하여 난이도를 실시간 조절합니다.
        while len(g['fat_rings']) < target_inner: g['fat_rings'].append(make_single_fat())
        while len(g['fat_rings']) > target_inner: g['fat_rings'].pop(0)
        
        # 6. 캐릭터 렌더링
        if g['ultimate_hit_timer'] > 0: active_img = player_hit
        elif g['magnet_timer'] > 0: active_img = player_magnet
        elif g['exercise_mode']: active_img = player_special
        elif g['is_stunned']: active_img = player_stunned
        else: active_img = player_left if g['face_dir'] == -1 else player_right

        img_draw = active_img.copy()
        if g['invincible_timer'] > 0 and g['exercise_mode'] == False and g['magnet_timer'] <= 0:
            if (g['invincible_timer'] // 5) % 2 == 0: img_draw.set_alpha(100)
        
        # [수정된 부분] 회전 이미지 계산
        rot_img = get_rotated(img_draw, math.degrees(-g['angle']) + 90)
        
        # [수정된 부분] 렌더링 위치 계산
        dirx, diry = math.cos(g['angle']), math.sin(g['angle'])
        render_r = max(0, track_r - (rot_img.get_height() / 2))
        render_px, render_py = CENTER[0] + dirx * render_r, CENTER[1] + diry * render_r
        
        # [수정된 부분] 화면에 캐릭터 그리기
        screen.blit(rot_img, rot_img.get_rect(center=(int(render_px), int(render_py))))
        
        if g['is_blurred']:
            fog_surf.fill((160, 160, 160, 230))
            hole_surf.fill((255, 255, 255, 255))
            pygame.draw.circle(hole_surf, (255, 255, 255, 0), (300, 300), 150)
            pygame.draw.circle(hole_surf, (255, 255, 255, 100), (300, 300), 220)
            
            fog_surf.blit(hole_surf, (int(render_px - 300), int(render_py - 250)), special_flags=pygame.BLEND_RGBA_MIN)
            screen.blit(fog_surf, (0, 0))

        # 7. UI 표시
            pygame.draw.rect(screen, (20, 0, 0), (35, 35, 310, 85))
        pygame.draw.rect(screen, GREEN if g['purity'] > 30 else RED, (40, 45, (g['purity']/100)*300, 30))
        screen.blit(small_font.render(f"혈관 청정도: {int(g['purity'])}%", True, WHITE), (50, 47))
        pygame.draw.rect(screen, SKYBLUE if g['special_gauge'] < MAX_GAUGE else GOLD, (40, 85, (g['special_gauge']/MAX_GAUGE)*300, 20))
        screen.blit(small_font.render(f"필살기 게이지: {int(g['special_gauge'])}%", True, WHITE), (50, 85))
        
        elapsed_real = time.time() - g['start_time'] - g['total_pause_time']
        time_left = max(0, 60 - int(elapsed_real))
        
        screen.blit(font.render(f"TIME: {time_left}s", True, WHITE), (WIDTH - 180, 45))
        
        if g.get('top_msg'):
            m = g['top_msg']
            screen.blit(m['surface'], m['surface'].get_rect(center=(WIDTH // 2, 200))) # 화면 상단에 표시
            
            m['timer'] -= 1
            if m['timer'] <= 0: g['top_msg'] = None
                
        if g.get('center_msg'):
            m = g['center_msg']
            # 화면 중간에서 약간 위쪽(HEIGHT // 3)에 표시
            screen.blit(m['surface'], m['surface'].get_rect(center=(WIDTH // 2, HEIGHT // 3)))
            
            m['timer'] -= 1
            if m['timer'] <= 0: g['center_msg'] = None
                
        # 8. 게임 종료 판정
        # [성공/실패 조건]
        # 1. 청정도가 0%가 되면 즉시 심부전(HEART FAILURE)으로 패배합니다.
        # 2. 60초를 버텼을 때, 청정도가 70% 이상이면 미션 성공, 아니면 실패입니다.
        if g['purity'] <= 0: 
            g['game_state'] = "lose"; bgm_stop()
            if SFX.get('lose'): SFX['lose'].play()
        elif time_left <= 0:
            bgm_stop()
            if g['purity'] >= 50: g['game_state'] = "success"; SFX['win'].play() if SFX.get('win') else None
            else: g['game_state'] = "lose"; SFX['lose'].play() if SFX.get('lose') else None
            
        if g.get('request_pause_with_countdown'):
            g['request_pause_with_countdown'] = False
            g['is_paused'] = True
            g['pause_frame'] = screen.copy()
            g['countdown_active'] = True
            g['countdown_start'] = time.time()
            g['pause_start'] = time.time()

    # 결과 화면 렌더링
    elif g['game_state'] in ["success", "lose"]:
        # 1. 배경 이미지 출력
        if g['game_state'] == "success":
            screen.blit(ending_win, (0, 0))
            title_text = "MISSION COMPLETE!"
        else:
            screen.blit(ending_fail, (0, 0))
            title_text = "HEART FAILURE..."

        # 2. 결과 정보 박스 그리기 (왼쪽 상단 배치)
        # 결과 텍스트 생성
        big_font.set_bold(True)
        res_purity = big_font.render(f"최종 혈관 청정도: {int(g['purity'])}%", True, WHITE)
        
        # 남은 시간 계산 (성공 시엔 남은 시간, 실패 시엔 0초로 표시)
        final_time = max(0, 60 - int(time.time() - g['start_time'] - g['total_pause_time']))
        if g['game_state'] == "lose" and g['purity'] <= 0: final_time = time_left # 미처 못 버텼을 때 시간
        
        res_time = big_font.render(f"남은 시간: {final_time}초", True, WHITE)

        # 텍스트 배치
        screen.blit(res_purity, (70, 200))
        screen.blit(res_time, (70, 250))

    pygame.display.flip()
    clock.tick(60)
pygame.quit()






#### 40초 ~1분 
### 7초 17초 