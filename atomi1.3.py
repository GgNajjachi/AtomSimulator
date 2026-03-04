import pygame
import math
import json
import os

# --- KONFIGURACIJA ---
pygame.init()

TITLE = "SIMULACIJA ATOMA"
info = pygame.display.Info()
sirina, visina = 1080, 720
screen = pygame.display.set_mode((sirina, visina), pygame.RESIZABLE)
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Fontovi
font_krug = pygame.font.SysFont("Arial", 14, bold=True)
font_tablica = pygame.font.SysFont("Arial", 11, bold=True)
font_valencija = pygame.font.SysFont("Arial", 10, bold=False)

# Matrica za prikaz periodnog sustava (TAB)
tablica_matrica = [
    ["H",  "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "He"],
    ["Li", "Be", "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "B",  "C",  "N",  "O",  "F",  "Ne"],
    ["Na", "Mg", "",   "",   "",   "",   "",   "",   "",   "",   "",   "",   "Al", "Si", "P",  "S",  "Cl", "Ar"],
    ["K",  "Ca", "Sc", "Ti", "V",  "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
    ["Rb", "Sr", "Y",  "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I",  "Xe"],
    ["Cs", "Ba", "L*", "Hf", "Ta", "W",  "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
    ["Fr", "Ra", "A*", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
    [""], 
    ["",   "",   "L*", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
    ["",   "",   "A*", "Ac", "Th", "Pa", "U",  "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]
]

def ucitaj_elemente():
    putanja = "elementi.txt"
    default_podaci = {}
    svi_simboli = [s for red in tablica_matrica for s in red if s not in ["", "L*", "A*"]]
    for s in svi_simboli:
        default_podaci[s] = {"boja": [200, 200, 200], "r": 20, "v": 4}
    if os.path.exists(putanja):
        try:
            with open(putanja, "r") as f:
                ucitani = json.load(f)
                for s in ucitani: default_podaci[s] = ucitani[s]
            return default_podaci
        except: print("Greška u datoteci!")
    return default_podaci

podaci_elemenata = ucitaj_elemente()

# --- VARIJABLE SIMULACIJE ---
ODBOJNA_SILA, SILA_OPRUGE, IDEALNA_DULJINA, TRENJE = 0.6, 0.06, 110, 0.1
krugovi, brzine, krug_simboli = [], [], []
veze = {} 
aktivni_mod = 0 
indeks_uhvacenog_kruga = None
prva_tocka_indeks = None
odabrani_element = "H"
prikazi_tablicu = False

def broj_trenutnih_veza(idx):
    suma = 0
    for (id1, id2), kolko in veze.items():
        if idx == id1 or idx == id2: suma += kolko
    return suma

def nacrtaj_ikone_moda(mod):
    x, y, vel = 20, 20, 40
    boja_bg = (240, 240, 240)
    boja_aktivna = (0, 150, 255) # Plava za aktivni mod

    # Okvir za ikonu
    pygame.draw.rect(screen, boja_bg, (x, y, vel, vel), border_radius=8)
    pygame.draw.rect(screen, boja_aktivna, (x, y, vel, vel), 2, border_radius=8)

    if mod == 0: # IKONA: MIŠ (Kursor strelica)
        # Crtanje poligoona koji izgleda kao kursor
        tocke_kursora = [
            (x + 12, y + 8),
            (x + 12, y + 28),
            (x + 18, y + 22),
            (x + 24, y + 30),
            (x + 27, y + 27),
            (x + 21, y + 20),
            (x + 28, y + 20)
        ]
        pygame.draw.polygon(screen, boja_aktivna, tocke_kursora)
        pygame.draw.polygon(screen, (50, 50, 50), tocke_kursora, 1) # Rub kursora

    elif mod == 1: # IKONA: ADD/REMOVE (Plus i krug)
        cx, cy = x + vel//2, y + vel//2
        pygame.draw.circle(screen, boja_aktivna, (cx, cy), 10, 2)
        pygame.draw.line(screen, boja_aktivna, (cx-6, cy), (cx+6, cy), 2)
        pygame.draw.line(screen, boja_aktivna, (cx, cy-6), (cx, cy+6), 2)

    elif mod == 2: # IKONA: LINK (Vezani atomi)
        pygame.draw.circle(screen, boja_aktivna, (x+12, y+vel-12), 4)
        pygame.draw.circle(screen, boja_aktivna, (x+vel-12, y+12), 4)
        pygame.draw.line(screen, boja_aktivna, (x+14, y+vel-14), (x+vel-14, y+14), 2)

fullscreen = False
lastWidth, lastHeight = sirina, visina
# --- GLAVNA PETLJA ---
running = True
while running:
    screen.fill((255, 255, 255))
    mis_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_TAB: prikazi_tablicu = not prikazi_tablicu
            if event.key == pygame.K_p: aktivni_mod = 1 if aktivni_mod != 1 else 0; prva_tocka_indeks = None
            if event.key == pygame.K_l: aktivni_mod = 2 if aktivni_mod != 2 else 0; prva_tocka_indeks = None
            if event.key == pygame.K_m: aktivni_mod = 0; prva_tocka_indeks = None
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                sirina, visina = info.current_w, info.current_h
                if (fullscreen):
                    pygame.display.set_mode((sirina, visina), pygame.FULLSCREEN)
                else:
                    pygame.display.set_mode((lastWidth, lastHeight), pygame.RESIZABLE)
                    
        if event.type == pygame.MOUSEBUTTONDOWN:
            if prikazi_tablicu:
                razmak = 42
                start_x, start_y = (sirina - 18 * razmak) // 2, (visina - 10 * razmak) // 2
                for r_idx, red in enumerate(tablica_matrica):
                    for c_idx, simbol in enumerate(red):
                        if simbol not in ["", "L*", "A*"]:
                            rect = pygame.Rect(start_x + c_idx * razmak, start_y + r_idx * razmak, 38, 38)
                            if rect.collidepoint(mis_pos): odabrani_element = simbol
            else:
                if event.button == 1: 
                    if aktivni_mod == 1: 
                        obrisano = False
                        for i in range(len(krugovi)-1, -1, -1):
                            r = podaci_elemenata[krug_simboli[i]]["r"]
                            if math.hypot(mis_pos[0]-krugovi[i][0], mis_pos[1]-krugovi[i][1]) <= r:
                                veze = {k: v for k, v in veze.items() if i not in k}
                                nove_veze = {}
                                for (id1, id2), v in veze.items():
                                    n1 = id1 - 1 if id1 > i else id1
                                    n2 = id2 - 1 if id2 > i else id2
                                    nove_veze[(n1, n2)] = v
                                veze = nove_veze
                                krugovi.pop(i); brzine.pop(i); krug_simboli.pop(i); obrisano = True; break
                        if not obrisano:
                            krugovi.append(list(mis_pos)); brzine.append([0,0]); krug_simboli.append(odabrani_element)
                    elif aktivni_mod == 2:
                        for i, p in enumerate(krugovi):
                            r = podaci_elemenata[krug_simboli[i]]["r"]
                            if math.hypot(mis_pos[0]-p[0], mis_pos[1]-p[1]) <= r:
                                if prva_tocka_indeks is None:
                                    if broj_trenutnih_veza(i) < podaci_elemenata[krug_simboli[i]]["v"]: prva_tocka_indeks = i
                                elif prva_tocka_indeks != i:
                                    if broj_trenutnih_veza(prva_tocka_indeks) < podaci_elemenata[krug_simboli[prva_tocka_indeks]]["v"] and broj_trenutnih_veza(i) < podaci_elemenata[krug_simboli[i]]["v"]:
                                        pair = tuple(sorted((prva_tocka_indeks, i)))
                                        veze[pair] = veze.get(pair, 0) + 1
                                    prva_tocka_indeks = None
                                break
                    elif aktivni_mod == 0:
                        for i, p in enumerate(krugovi):
                            if math.hypot(mis_pos[0]-p[0], mis_pos[1]-p[1]) <= podaci_elemenata[krug_simboli[i]]["r"]:
                                indeks_uhvacenog_kruga = i; break
                elif event.button == 3 and aktivni_mod == 2:
                    for i, p in enumerate(krugovi):
                        if math.hypot(mis_pos[0]-p[0], mis_pos[1]-p[1]) <= podaci_elemenata[krug_simboli[i]]["r"]:
                            for pair in list(veze.keys()):
                                if i in pair:
                                    veze[pair] -= 1
                                    if veze[pair] <= 0: del veze[pair]
                                    break
                            break

        if event.type == pygame.MOUSEBUTTONUP: indeks_uhvacenog_kruga = None

    # --- FIZIKA ---
    for i in range(len(krugovi)):
        for j in range(len(krugovi)):
            if i == j: continue
            dx, dy = krugovi[i][0]-krugovi[j][0], krugovi[i][1]-krugovi[j][1]
            dist = max(math.hypot(dx, dy), 1)
            r_sum = podaci_elemenata[krug_simboli[i]]["r"] + podaci_elemenata[krug_simboli[j]]["r"]
            if dist < r_sum + 60:
                brzine[i][0] += (dx/dist) * (ODBOJNA_SILA / (dist/10))
                brzine[i][1] += (dy/dist) * (ODBOJNA_SILA / (dist/10))
    for (id1, id2), kolko in veze.items():
        p1, p2 = krugovi[id1], krugovi[id2]
        dx, dy = p2[0]-p1[0], p2[1]-p1[1]
        dist = max(math.hypot(dx, dy), 1)
        sila = (dist - IDEALNA_DULJINA) * SILA_OPRUGE * (1 + (kolko-1)*0.4)
        fx, fy = (dx/dist)*sila, (dy/dist)*sila
        brzine[id1][0] += fx; brzine[id1][1] += fy
        brzine[id2][0] -= fx; brzine[id2][1] -= fy
    for i in range(len(krugovi)):
        r = podaci_elemenata[krug_simboli[i]]["r"]
        if i == indeks_uhvacenog_kruga: krugovi[i] = list(mis_pos); brzine[i] = [0,0]
        else:
            krugovi[i][0] += brzine[i][0]; krugovi[i][1] += brzine[i][1]
            brzine[i][0] *= TRENJE; brzine[i][1] *= TRENJE
            if krugovi[i][0] < r: krugovi[i][0] = r; brzine[i][0] *= -0.5
            if krugovi[i][0] > sirina-r: krugovi[i][0] = sirina-r; brzine[i][0] *= -0.5
            if krugovi[i][1] < r: krugovi[i][1] = r; brzine[i][1] *= -0.5
            if krugovi[i][1] > visina-r: krugovi[i][1] = visina-r; brzine[i][1] *= -0.5

    # --- CRTANJE ---
    for (id1, id2), kolko in veze.items():
        p1, p2 = krugovi[id1], krugovi[id2]
        dx, dy = p2[0]-p1[0], p2[1]-p1[1]
        dist = max(math.hypot(dx, dy), 1)
        ox, oy = -dy/dist * 5, dx/dist * 5
        if kolko == 1: pygame.draw.line(screen, (150, 150, 150), p1, p2, 3)
        elif kolko == 2:
            pygame.draw.line(screen, (150, 150, 150), (p1[0]+ox, p1[1]+oy), (p2[0]+ox, p2[1]+oy), 2)
            pygame.draw.line(screen, (150, 150, 150), (p1[0]-ox, p1[1]-oy), (p2[0]-ox, p2[1]-oy), 2)
        else:
            pygame.draw.line(screen, (150, 150, 150), p1, p2, 2)
            pygame.draw.line(screen, (150, 150, 150), (p1[0]+ox*1.5, p1[1]+oy*1.5), (p2[0]+ox*1.5, p2[1]+oy*1.5), 2)
            pygame.draw.line(screen, (150, 150, 150), (p1[0]-ox*1.5, p1[1]-oy*1.5), (p2[0]-ox*1.5, p2[1]-oy*1.5), 2)
    if aktivni_mod == 2 and prva_tocka_indeks is not None: pygame.draw.line(screen, (200, 200, 200), krugovi[prva_tocka_indeks], mis_pos, 2)
    for i, p in enumerate(krugovi):
        simb = krug_simboli[i]
        el = podaci_elemenata[simb]
        boja = el["boja"]
        if i == indeks_uhvacenog_kruga: boja = (100, 100, 255)
        if i == prva_tocka_indeks: boja = (255, 200, 0)
        pygame.draw.circle(screen, boja, (int(p[0]), int(p[1])), el["r"])
        pygame.draw.circle(screen, (50, 50, 50), (int(p[0]), int(p[1])), el["r"], 1)
        txt = font_krug.render(simb, True, (0,0,0))
        screen.blit(txt, (p[0]-txt.get_width()//2, p[1]-txt.get_height()//2))
        v_srf = font_valencija.render(f"{broj_trenutnih_veza(i)}/{el['v']}", True, (80, 80, 80))
        screen.blit(v_srf, (p[0]-v_srf.get_width()//2, p[1]-el["r"]-14))

    if prikazi_tablicu:
        overlay = pygame.Surface((sirina, visina), pygame.SRCALPHA); overlay.fill((0,0,0,220)); screen.blit(overlay, (0,0))
        razmak = 42
        start_x, start_y = (sirina - 18 * razmak) // 2, (visina - 10 * razmak) // 2
        for r_idx, red in enumerate(tablica_matrica):
            for c_idx, simbol in enumerate(red):
                if simbol != "":
                    rect = pygame.Rect(start_x + c_idx * razmak, start_y + r_idx * razmak, 38, 38)
                    if simbol not in ["L*", "A*"]:
                        pygame.draw.rect(screen, podaci_elemenata[simbol]["boja"], rect, border_radius=4)
                        if odabrani_element == simbol: pygame.draw.rect(screen, (0,255,0), rect, 2, border_radius=4)
                        t = font_tablica.render(simbol, True, (0,0,0)); screen.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))
                        vt = font_valencija.render(str(podaci_elemenata[simbol]["v"]), True, (50,50,50)); screen.blit(vt, (rect.right-9, rect.top+2))
                    else:
                        t = font_tablica.render(simbol, True, (255,255,255)); screen.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2))

    nacrtaj_ikone_moda(aktivni_mod)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
