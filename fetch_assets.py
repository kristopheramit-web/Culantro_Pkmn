# fetch_assets.py
import os
import math
import urllib.request
from PIL import Image, ImageDraw, ImageFilter

from lental_pokedex_data import WILD_POKEDEX_150

ASSET_DIRS = [
    "assets/map",
    "assets/roles",
    "assets/pokemon",
    "assets/pokemon_back",
    "assets/illumina",
    "assets/poachers",
    "assets/items",
    "assets/placeholders",
    "downloads",
]

POKE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
POKE_BACK_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/"
ITEM_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/"

SPRITE_MANIFEST = {
    "illumina": {
        "illumina_154.png": "154.png", "illumina_350.png": "350.png", "illumina_10127.png": "10127.png",
        "illumina_637.png": "637.png", "illumina_208.png": "208.png", "illumina_716.png": "716.png",
        "illumina_6.png": "6.png", "illumina_9.png": "9.png", "illumina_59.png": "59.png",
        "illumina_130.png": "130.png", "illumina_131.png": "131.png", "illumina_143.png": "143.png",
        "illumina_149.png": "149.png", "illumina_150.png": "150.png", "illumina_248.png": "248.png",
        "illumina_249.png": "249.png", "illumina_250.png": "250.png", "illumina_373.png": "373.png",
        "illumina_376.png": "376.png", "illumina_384.png": "384.png", "illumina_445.png": "445.png",
        "illumina_635.png": "635.png", "illumina_983.png": "983.png", "illumina_998.png": "998.png",
        "illumina_1005.png": "1005.png", "illumina_darkrai_mega.png": "491.png",
    },
    "poachers": {
        "poacher_grunt_m.png": "108.png",
        "poacher_grunt_f.png": "115.png",
        "poacher_hunter_sneasel.png": "215.png",
    },
    "items": {
        "item_decoy.png": "poke-doll.png",
        "item_knife.png": "razor-claw.png",
        "item_soothe_bell.png": "soothe-bell.png",
        "item_repel.png": "super-repel.png",
        "item_karate_trophy.png": "black-belt.png",
        "item_rare_candy.png": "rare-candy.png",
        "item_fluffruit.png": "fancy-apple.png",
        "item_illumina_orb.png": "light-ball.png",
    },
}

BOSS_AVATARS = {
    "Boss_Captain_B.Jack.png": {"bg": "#2d3748", "fg": "#cbd5e0", "initial": "BJ", "title": "C. JACK"},
    "Boss_Lt._Deuce.png": {"bg": "#744210", "fg": "#f6ad55", "initial": "DE", "title": "LT. DEUCE"},
    "Boss_Chief_J.Pot.png": {"bg": "#975a16", "fg": "#ecc94b", "initial": "JP", "title": "JACKPOT"},
    "Boss_Marshall_Ace.png": {"bg": "#22543d", "fg": "#68d391", "initial": "AC", "title": "ACE"},
    "Boss_Baron_Roulette.png": {"bg": "#742a2a", "fg": "#fc8181", "initial": "BR", "title": "BARON"},
    "Boss_Warden_Croupier.png": {"bg": "#1a202c", "fg": "#e2e8f0", "initial": "WC", "title": "WARDEN"},
}

PLACEHOLDER_STYLES = {
    "pokemon": {"bg": "#1e3a5f", "border": "#58a6ff", "label": "PKMN"},
    "pokemon_back": {"bg": "#1e3a5f", "border": "#38bdf8", "label": "BACK"},
    "illumina": {"bg": "#4a2500", "border": "#ffd166", "label": "BOSS"},
    "poachers": {"bg": "#4c111b", "border": "#f85149", "label": "SYND"},
    "items": {"bg": "#1b4332", "border": "#3fb950", "label": "ITEM"},
    "roles": {"bg": "#3c1e70", "border": "#bc8cff", "label": "ROLE"},
    "default": {"bg": "#21262d", "border": "#8b949e", "label": "TEMP"},
}


def create_placeholder_png(dest_path: str, category: str = "default", title: str = ""):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    style = PLACEHOLDER_STYLES.get(category, PLACEHOLDER_STYLES["default"])
    img = Image.new("RGBA", (96, 96), style["bg"])
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, 93, 93], outline=style["border"], width=3)
    draw.rectangle([7, 7, 88, 88], outline="#000000", width=1)
    short_title = (title or os.path.basename(dest_path).replace(".png", ""))[:10].upper()
    draw.text((14, 22), f"[{style['label']}]", fill=style["border"])
    draw.text((10, 44), short_title, fill="#ffffff")
    draw.text((10, 68), "PLACEHOLDER", fill="#cbd5e0")
    img.save(dest_path)


def generate_default_placeholders():
    for cat in PLACEHOLDER_STYLES:
        dest = os.path.join("assets/placeholders", f"placeholder_{cat}.png")
        create_placeholder_png(dest, category=cat, title=cat.upper())


def generate_3d_archipelago_background():
    """
    Procedurally renders a 3D-extruded relief map background (assets/map/culantro_3d_map.png)
    with <20% ocean border, 3D cliff bevels, coastal sand, and 6 distinct biome regions.
    """
    dest = os.path.join("assets/map", "culantro_3d_map.png")
    w, h = 980, 610
    img = Image.new("RGBA", (w, h), (7, 26, 44, 255))
    draw = ImageDraw.Draw(img)

    # 1. Deep ocean & shallow turquoise reef rings
    for r in range(20, 0, -1):
        pad_x = int(20 + (20 - r) * 1.8)
        pad_y = int(16 + (20 - r) * 1.4)
        c_r = int(8 + (20 - r) * 1.5)
        c_g = int(35 + (20 - r) * 3.8)
        c_b = int(58 + (20 - r) * 4.5)
        draw.rounded_rectangle([pad_x, pad_y, w - pad_x, h - pad_y], radius=80, fill=(c_r, c_g, c_b, 255))

    # 2. 3D Island Cliff Extrusion (Drop Shadow + Rock Wall)
    land_pts = []
    cx, cy = w / 2, h / 2
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        wobble = 1.0 + 0.06 * math.sin(rad * 5) + 0.04 * math.cos(rad * 3)
        rx = (w * 0.435) * wobble
        ry = (h * 0.425) * wobble
        land_pts.append((cx + math.cos(rad) * rx, cy + math.sin(rad) * ry))

    shadow_pts = [(x + 8, y + 14) for (x, y) in land_pts]
    cliff_pts = [(x, y + 9) for (x, y) in land_pts]
    sand_pts = [(cx + (x - cx) * 0.985, cy + (y - cy) * 0.985) for (x, y) in land_pts]
    inland_pts = [(cx + (x - cx) * 0.94, cy + (y - cy) * 0.94) for (x, y) in land_pts]

    draw.polygon(shadow_pts, fill=(3, 12, 22, 190))
    draw.polygon(cliff_pts, fill=(48, 56, 68, 255))
    draw.polygon(land_pts, fill=(194, 178, 128, 255))
    draw.polygon(sand_pts, fill=(214, 198, 144, 255))
    draw.polygon(inland_pts, fill=(34, 78, 52, 255))

    # 3. 3D Biome Elevation Plateaus (with 3D cliff bases and top surfaces)
    biomes_3d = [
        # Florio Lush Meadow (Upper-Left & Center)
        {"cx": 290, "cy": 210, "rx": 185, "ry": 125, "cliff": (36, 74, 42), "top": (54, 122, 68), "hi": (78, 158, 90)},
        # Belusylva Deep Jungle (Bottom-Left)
        {"cx": 225, "cy": 430, "rx": 165, "ry": 115, "cliff": (20, 52, 38), "top": (28, 84, 56), "hi": (42, 112, 74)},
        # Maricopia Coral Lagoon (Bottom-Center)
        {"cx": 465, "cy": 485, "rx": 145, "ry": 85, "cliff": (18, 82, 108), "top": (28, 134, 168), "hi": (64, 182, 212)},
        # Durice Glacier Peaks (Top-Right)
        {"cx": 665, "cy": 155, "rx": 175, "ry": 105, "cliff": (74, 104, 138), "top": (168, 208, 238), "hi": (222, 242, 255)},
        # Voluca Volcanic Caldera (Mid/Bottom-Right)
        {"cx": 765, "cy": 385, "rx": 165, "ry": 125, "cliff": (58, 32, 28), "top": (98, 48, 38), "hi": (168, 68, 34)},
        # Aurus Ancient Ruins (Bottom-Right)
        {"cx": 670, "cy": 515, "rx": 120, "ry": 75, "cliff": (78, 68, 48), "top": (128, 112, 76), "hi": (164, 146, 102)},
    ]

    for b in biomes_3d:
        bx, by, brx, bry = b["cx"], b["cy"], b["rx"], b["ry"]
        # 3D Extruded Cliff Base
        draw.ellipse([bx - brx, by - bry + 10, bx + brx, by + bry + 10], fill=b["cliff"])
        # Main Biome Plateau
        draw.ellipse([bx - brx, by - bry, bx + brx, by + bry], fill=b["top"])
        # Upper 3D Terrace Highlight
        draw.ellipse([bx - brx * 0.72, by - bry * 0.72 - 4, bx + brx * 0.72, by + bry * 0.72 - 4], fill=b["hi"])

    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
    img.save(dest)
    print(f"[GENERATED 3D MAP ART] {dest}")


def download_file(url: str, dest: str, category: str = "default"):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        print(f"[OK] {dest}")
    except Exception as e:
        print(f"[WARN] Could not download {url} ({e}) -> Using fallback for {dest}")
        create_placeholder_png(dest, category=category, title=os.path.basename(dest))


def generate_boss_avatars():
    for filename, data in BOSS_AVATARS.items():
        path = os.path.join("assets/poachers", filename)
        img = Image.new("RGBA", (96, 96), data["bg"])
        draw = ImageDraw.Draw(img)
        draw.rectangle([2, 2, 93, 93], outline=data["fg"], width=3)
        draw.rectangle([6, 6, 89, 89], outline="#000000", width=1)
        draw.text((32, 28), data["initial"], fill=data["fg"])
        draw.text((14, 64), data["title"], fill="#ffffff")
        img.save(path)
        print(f"[GENERATED BOSS AVATAR] {path}")


def collect_wild_pokemon_files() -> set:
    files = {"1.png", "4.png", "7.png", "23.png", "215.png", "371.png"}

    def walk_evo(entry):
        if not entry:
            return
        spr = entry.get("sprite", "")
        if spr.startswith("/assets/pokemon/"):
            files.add(spr.split("/")[-1])
        if entry.get("evolves_to"):
            walk_evo(entry["evolves_to"])

    for biome_list in WILD_POKEDEX_150.values():
        for pk in biome_list:
            walk_evo(pk)
    return files


def main():
    for d in ASSET_DIRS:
        os.makedirs(d, exist_ok=True)

    generate_default_placeholders()
    generate_boss_avatars()
    generate_3d_archipelago_background()

    for fname, pid in SPRITE_MANIFEST["illumina"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/illumina", fname), category="illumina")
    for fname, pid in SPRITE_MANIFEST["poachers"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/poachers", fname), category="poachers")
    for fname, iid in SPRITE_MANIFEST["items"].items():
        download_file(ITEM_BASE + iid, os.path.join("assets/items", fname), category="items")

    for poke_file in sorted(collect_wild_pokemon_files()):
        front_dest = os.path.join("assets/pokemon", poke_file)
        back_dest = os.path.join("assets/pokemon_back", poke_file)
        download_file(POKE_BASE + poke_file, front_dest, category="pokemon")
        # Download back-sprite for POV battle animations; mirror front sprite if PokeAPI lacks a back sprite
        if not os.path.exists(back_dest) or os.path.getsize(back_dest) == 0:
            try:
                req = urllib.request.Request(POKE_BACK_BASE + poke_file, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=6) as resp, open(back_dest, "wb") as out:
                    out.write(resp.read())
                print(f"[OK BACK-SPRITE] {back_dest}")
            except Exception:
                if os.path.exists(front_dest):
                    im = Image.open(front_dest).transpose(Image.FLIP_LEFT_RIGHT)
                    im.save(back_dest)
                else:
                    create_placeholder_png(back_dest, category="pokemon_back", title=poke_file)

    print("All front sprites, POV back-sprites, 3D map art, and placeholders verified!")


if __name__ == "__main__":
    main()
