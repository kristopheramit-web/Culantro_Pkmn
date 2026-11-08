# fetch_assets.py
import os
import urllib.request
from PIL import Image, ImageDraw

ASSET_DIRS = [
    "assets/map", "assets/roles", "assets/pokemon",
    "assets/illumina", "assets/poachers", "assets/items", "downloads"
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
        "illumina_1005.png": "1005.png",
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
    }
}

BOSS_AVATARS = {
    "Boss_Captain_B.Jack.png": {"bg": "#2d3748", "fg": "#cbd5e0", "initial": "BJ", "title": "C. JACK"},
    "Boss_Lt._Deuce.png": {"bg": "#744210", "fg": "#f6ad55", "initial": "DE", "title": "LT. DEUCE"},
    "Boss_Chief_J.Pot.png": {"bg": "#975a16", "fg": "#ecc94b", "initial": "JP", "title": "JACKPOT"},
    "Boss_Marshall_Ace.png": {"bg": "#22543d", "fg": "#68d391", "initial": "AC", "title": "ACE"},
    "Boss_Baron_Roulette.png": {"bg": "#742a2a", "fg": "#fc8181", "initial": "BR", "title": "BARON"},
    "Boss_Warden_Croupier.png": {"bg": "#1a202c", "fg": "#e2e8f0", "initial": "WC", "title": "WARDEN"},
}

def download_file(url, dest):
    if os.path.exists(dest):
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp, open(dest, "wb") as out:
            out.write(resp.read())
        print(f"[OK] {dest}")
    except Exception as e:
        print(f"[WARN] Failed {url}: {e}")

def generate_boss_avatars():
    for filename, data in BOSS_AVATARS.items():
        img = Image.new("RGBA", (96, 96), data["bg"])
        draw = ImageDraw.Draw(img)
        draw.rectangle([2, 2, 93, 93], outline=data["fg"], width=3)
        draw.rectangle([6, 6, 89, 89], outline="#000000", width=1)
        draw.text((32, 28), data["initial"], fill=data["fg"])
        draw.text((16, 64), data["title"], fill="#ffffff")
        path = os.path.join("assets/poachers", filename)
        img.save(path)
        print(f"[GENERATED BOSS AVATAR] {path}")

def main():
    for d in ASSET_DIRS:
        os.makedirs(d, exist_ok=True)
    
    for fname, pid in SPRITE_MANIFEST["illumina"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/illumina", fname))
    for fname, pid in SPRITE_MANIFEST["poachers"].items():
        download_file(POKE_BASE + pid, os.path.join("assets/poachers", fname))
    for fname, iid in SPRITE_MANIFEST["items"].items():
        download_file(ITEM_BASE + iid, os.path.join("assets/items", fname))
        
    generate_boss_avatars()
    print("All assets downloaded and custom Casino Boss portraits generated!")

if __name__ == "__main__":
    main()
  
