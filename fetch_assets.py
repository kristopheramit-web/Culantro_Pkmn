# fetch_assets.py
import os
import urllib.request
from PIL import Image, ImageDraw

from lental_pokedex_data import WILD_POKEDEX_150

ASSET_DIRS = [
    "assets/map",
    "assets/roles",
    "assets/pokemon",
    "assets/illumina",
    "assets/poachers",
    "assets/items",
    "assets/placeholders",
    "downloads",
]

POKE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
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
    "illumina": {"bg": "#4a2500", "border": "#ffd166", "label": "BOSS"},
    "poachers": {"bg": "#4c111b", "border": "#f85149", "label": "SYND"},
    "items": {"bg": "#1b4332", "border": "#3fb950", "label": "ITEM"},
    "roles": {"bg": "#3c1e70", "border": "#bc8cff", "label": "ROLE"},
    "default": {"bg": "#21262d", "border": "#8b949e", "label": "TEMP"},
}

def create_placeholder_png(dest_path: str, category: str = "default", title: str = ""):
    """
    NOTE FOR FINAL POLISH:
    Generates a labeled default placeholder PNG when a real sprite asset is missing.
    Replace generated placeholder files with final custom pixel art before production release.
    """
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

def download_file(url: str, dest: str, category: str = "default"):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        print(f"[OK] {dest}")
    except Exception as e:
        print(f"[WARN] Could not download {url} ({e}) -> Generating default placeholder at {dest}")
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

    for fname, pid in SPRITE_MANIFEST["illumina"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/illumina", fname), category="illumina")
    for fname, pid in SPRITE_MANIFEST["poachers"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/poachers", fname), category="poachers")
    for fname, iid in SPRITE_MANIFEST["items"].items():
        download_file(ITEM_BASE + iid, os.path.join("assets/items", fname), category="items")

    for poke_file in sorted(collect_wild_pokemon_files()):
        download_file(POKE_BASE + poke_file, os.path.join("assets/pokemon", poke_file), category="pokemon")

    print("All assets and fallback placeholders verified!")

if __name__ == "__main__":
    main()
