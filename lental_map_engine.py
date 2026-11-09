# lental_map_engine.py
import os
import json
import math
import time
import uuid
import random
from typing import Dict, List, Optional

from lental_boss_data import ILLUMINA_POOL_60, CASINO_BOSSES
from lental_pokedex_data import WILD_POKEDEX_150

LIBRARY_FILE = "maps_library.json"

CULANTRO_PREFIXES = [
    "Culantro", "Amazonia", "Cordillera", "Orinoco", "Pantanal", "Tierra",
    "Patagonia", "Guiana", "Yucatan", "Antillean", "Arawak", "Carib"
]
CULANTRO_SUFFIXES = [
    "Archipelago", "Isles", "Atoll", "Expanse", "Sanctuary", "Reeflands", "Cluster"
]

BIOME_METADATA = [
    {"region": "Florio", "outpost": "Florio Field Lab", "sanctuary": "Blossom Glade"},
    {"region": "Belusylva", "outpost": "Canopy Outpost", "sanctuary": "Emerald Lagoon"},
    {"region": "Maricopia", "outpost": "Atoll Dock", "sanctuary": "Abyssal Grotto"},
    {"region": "Durice", "outpost": "Glacier Station", "sanctuary": "Permafrost Vault"},
    {"region": "Voluca", "outpost": "Caldera Camp", "sanctuary": "Fireflow Core"},
    {"region": "Aurus", "outpost": "Relic Outpost", "sanctuary": "Astral Altar"},
]

OUTPOST_SPRITES = [
    "/assets/items/item_fluffruit.png", "/assets/items/item_soothe_bell.png",
    "/assets/items/item_repel.png", "/assets/items/item_knife.png", "/assets/items/item_rare_candy.png"
]

def ensure_bidirectional_edges(nodes: Dict[str, dict]):
    """Guarantees that if node A connects to node B, node B also connects back to node A."""
    for nid, nd in nodes.items():
        clean_edges = []
        for target in nd.get("edges", []):
            t_int = int(target)
            if str(t_int) in nodes and t_int != int(nid) and t_int not in clean_edges:
                clean_edges.append(t_int)
        nd["edges"] = clean_edges

    for nid, nd in nodes.items():
        n_int = int(nid)
        for target in list(nd["edges"]):
            t_edges = nodes[str(target)]["edges"]
            if n_int not in t_edges:
                t_edges.append(n_int)

def get_classic_culantro_nodes() -> Dict[str, dict]:
    nodes = {
        "0": {"name": "Base Camp Outpost", "region": "Florio", "type": "outpost", "x": 460, "y": 300, "edges": [1, 2, 4, 7, 10, 13], "sprite": "/assets/items/item_fluffruit.png"},
        "1": {"name": "Florio Nature Park", "region": "Florio", "type": "wild", "x": 230, "y": 200, "edges": [0, 2, 3, 5], "sprite": "/assets/pokemon/1.png"},
        "2": {"name": "Florio Research Lab", "region": "Florio", "type": "outpost", "x": 320, "y": 115, "edges": [0, 1, 3, 5, 10], "sprite": "/assets/items/item_soothe_bell.png"},
        "3": {"name": "Florio Sanctuary", "region": "Florio", "type": "illumina", "x": 115, "y": 115, "edges": [1, 2, 5], "boss": {"name": "Meganium", "bp": 14, "type": "Grass", "sprite": "/assets/illumina/illumina_154.png", "calmed": False, "decoy": False, "soothed": 0}},
        "4": {"name": "Belusylva Jungle", "region": "Belusylva", "type": "wild", "x": 240, "y": 420, "edges": [0, 5, 6, 8], "sprite": "/assets/pokemon/23.png"},
        "5": {"name": "Belusylva Outpost", "region": "Belusylva", "type": "outpost", "x": 130, "y": 300, "edges": [1, 2, 3, 4, 6], "sprite": "/assets/items/item_repel.png"},
        "6": {"name": "Belusylva Pond", "region": "Belusylva", "type": "illumina", "x": 115, "y": 505, "edges": [4, 5, 8], "boss": {"name": "Milotic", "bp": 16, "type": "Water", "sprite": "/assets/illumina/illumina_350.png", "calmed": False, "decoy": False, "soothed": 0}},
        "7": {"name": "Maricopia Reef", "region": "Maricopia", "type": "wild", "x": 460, "y": 465, "edges": [0, 8, 9, 13], "sprite": "/assets/pokemon/7.png"},
        "8": {"name": "Maricopia Outpost", "region": "Maricopia", "type": "outpost", "x": 325, "y": 535, "edges": [4, 6, 7, 9], "sprite": "/assets/items/item_knife.png"},
        "9": {"name": "Culantro Seafloor", "region": "Maricopia", "type": "illumina", "x": 575, "y": 545, "edges": [7, 8, 16], "boss": {"name": "Wishiwashi", "bp": 13, "type": "Water", "sprite": "/assets/illumina/illumina_10127.png", "calmed": False, "decoy": False, "soothed": 0}},
        "10": {"name": "Durice Snowfields", "region": "Durice", "type": "wild", "x": 575, "y": 140, "edges": [0, 2, 11, 13, 17], "sprite": "/assets/pokemon/215.png"},
        "11": {"name": "Durice Ice Caves", "region": "Durice", "type": "wild", "x": 720, "y": 85, "edges": [10, 12, 13, 17], "sprite": "/assets/pokemon/371.png"},
        "12": {"name": "Durice Cavern", "region": "Durice", "type": "illumina", "x": 765, "y": 215, "edges": [11, 13, 14, 17], "boss": {"name": "Steelix", "bp": 13, "type": "Steel", "sprite": "/assets/illumina/illumina_208.png", "calmed": False, "decoy": False, "soothed": 0}},
        "13": {"name": "Voluca Badlands", "region": "Voluca", "type": "wild", "x": 650, "y": 325, "edges": [0, 7, 10, 11, 12, 14, 15, 17], "sprite": "/assets/pokemon/4.png"},
        "14": {"name": "Voluca Outpost", "region": "Voluca", "type": "outpost", "x": 800, "y": 360, "edges": [12, 13, 15, 17], "sprite": "/assets/items/item_rare_candy.png"},
        "15": {"name": "Fireflow Crater", "region": "Voluca", "type": "illumina", "x": 855, "y": 500, "edges": [13, 14, 16, 17], "boss": {"name": "Volcarona", "bp": 15, "type": "Fire", "sprite": "/assets/illumina/illumina_637.png", "calmed": False, "decoy": False, "soothed": 0}},
        "16": {"name": "Aurus Ruins", "region": "Aurus", "type": "illumina", "x": 700, "y": 555, "edges": [9, 15, 17], "boss": {"name": "Xerneas", "bp": 17, "type": "Fairy", "sprite": "/assets/illumina/illumina_716.png", "calmed": False, "decoy": False, "soothed": 0}},
        "17": {"name": "Team Syndicate Fortress", "region": "Syndicate HQ", "type": "poacher_base", "x": 870, "y": 105, "edges": [10, 11, 12, 13, 14, 15, 16], "boss": {
            "id": "Boss_Captain_B.Jack",
            "name": "Captain B.Jack",
            "full_name": "Captain Black Jack",
            "tier": 1,
            "bp": 20,
            "type": "Flying",
            "sprite": "/assets/poachers/Boss_Captain_B.Jack.png",
            "team": list(CASINO_BOSSES["Boss_Captain_B.Jack"]["team"]),
            "dialogue": CASINO_BOSSES["Boss_Captain_B.Jack"]["dialogue"],
            "defeated": False
        }},
    }
    ensure_bidirectional_edges(nodes)
    return nodes

def generate_procedural_map(seed_str: Optional[str] = None, game_mode: str = "long_mode") -> dict:
    if not seed_str:
        seed_str = f"{random.choice(CULANTRO_PREFIXES)} {random.choice(CULANTRO_SUFFIXES)} #{random.randint(100, 999)}"
    rng = random.Random(seed_str)

    cx, cy = rng.choice([(480, 305), (420, 290), (520, 320)])
    nodes: Dict[str, dict] = {
        "0": {"name": "Culantro Base Camp", "region": "Florio", "type": "outpost", "x": cx, "y": cy, "edges": [], "sprite": "/assets/items/item_fluffruit.png"}
    }

    pool = list(ILLUMINA_POOL_60)
    rng.shuffle(pool)
    chosen_illumina, used_types = [], set()
    for cand in pool:
        if cand["type"] not in used_types or len(chosen_illumina) >= 4:
            chosen_illumina.append(dict(cand))
            used_types.add(cand["type"])
        if len(chosen_illumina) == 6:
            break

    bp_curve = [13, 13, 14, 15, 16, 17]
    rng.shuffle(bp_curve)
    for idx, boss in enumerate(chosen_illumina):
        boss.update({"bp": bp_curve[idx], "calmed": False, "decoy": False, "soothed": 0})

    active_boss_key = "Boss_Captain_B.Jack"
    boss_meta = CASINO_BOSSES[active_boss_key]

    biomes = list(BIOME_METADATA)
    rng.shuffle(biomes)

    session_biome_wilds = {}
    water_count = 0

    for b in biomes:
        reg = b["region"]
        raw_list = WILD_POKEDEX_150.get(reg, WILD_POKEDEX_150["Florio"])
        sub = list(raw_list)
        rng.shuffle(sub)
        session_biome_wilds[reg] = sub[:7]

    ang_offset = rng.uniform(0, math.pi / 3)

    # Ring 1: Nodes 1..6 (Land dominant: <20% water nodes)
    for i in range(6):
        nid = str(i + 1)
        ang = ang_offset + i * (math.pi / 3) + rng.uniform(-0.12, 0.12)
        rx = int(cx + math.cos(ang) * rng.randint(135, 165))
        ry = int(cy + math.sin(ang) * rng.randint(105, 130))
        b = biomes[i]

        is_water_biome = (b["region"] == "Maricopia" and water_count < 2)
        if is_water_biome:
            water_count += 1
            ntype = "wild"
        else:
            ntype = "outpost" if (i % 2 == 1) else "wild"

        wild_choice = rng.choice(session_biome_wilds[b["region"]]) if ntype == "wild" else None
        nodes[nid] = {
            "name": b["outpost"] if ntype == "outpost" else (wild_choice["name"] if wild_choice else b["sanctuary"]),
            "region": b["region"],
            "type": ntype,
            "x": max(85, min(895, rx)),
            "y": max(75, min(535, ry)),
            "edges": [0],
            "sprite": OUTPOST_SPRITES[i % len(OUTPOST_SPRITES)] if ntype == "outpost" else (wild_choice["sprite"] if wild_choice else "/assets/pokemon/7.png")
        }
        nodes["0"]["edges"].append(i + 1)

    for i in range(1, 7):
        nxt = 1 if i == 6 else i + 1
        nodes[str(i)]["edges"].append(nxt)

    # Ring 2: Nodes 7..12 (Connected to Ring 1)
    ring2_types = ["wild", "outpost", "wild", "outpost", "illumina", "illumina"]
    rng.shuffle(ring2_types)
    ill_idx = 0
    for i in range(6):
        nid = str(i + 7)
        ang = ang_offset + (i + 0.5) * (math.pi / 3) + rng.uniform(-0.10, 0.10)
        rx = int(cx + math.cos(ang) * rng.randint(250, 290))
        ry = int(cy + math.sin(ang) * rng.randint(175, 205))
        b = biomes[i]
        ntype = ring2_types[i]
        r1_a = i + 1
        r1_b = 1 if i == 5 else i + 2
        nd = {
            "name": f"{b['region']} {b['sanctuary']}" if ntype == "illumina" else (b["outpost"] if ntype == "outpost" else rng.choice(session_biome_wilds[b["region"]])["name"]),
            "region": b["region"],
            "type": ntype,
            "x": max(80, min(900, rx)),
            "y": max(70, min(540, ry)),
            "edges": [r1_a, r1_b],
        }
        if ntype == "illumina":
            nd["boss"] = chosen_illumina[ill_idx]
            ill_idx += 1
        else:
            nd["sprite"] = rng.choice(OUTPOST_SPRITES) if ntype == "outpost" else rng.choice(session_biome_wilds[b["region"]])["sprite"]
        nodes[nid] = nd

    # Ring 3: Nodes 13..16 (Illumina Sanctuaries connected to Ring 2)
    outer_angles = [0.25, 0.95, 1.85, 2.75, 3.85, 5.05]
    rng.shuffle(outer_angles)
    for j in range(4):
        nid = str(13 + j)
        ang = outer_angles[j]
        rx = int(cx + math.cos(ang) * rng.randint(355, 405))
        ry = int(cy + math.sin(ang) * rng.randint(215, 245))
        b = biomes[(j + 2) % 6]
        r2_link = 7 + (j % 6)
        r2_link2 = 7 + ((j + 1) % 6)
        nodes[nid] = {
            "name": f"{b['region']} {b['sanctuary']}",
            "region": b["region"],
            "type": "illumina",
            "x": max(75, min(905, rx)),
            "y": max(65, min(545, ry)),
            "edges": [r2_link, r2_link2],
            "boss": chosen_illumina[ill_idx],
        }
        ill_idx += 1

    # Node 17: Team Syndicate Fortress with 6 guaranteed encircling nodes
    p_ang = outer_angles[4]
    fx = max(85, min(895, int(cx + math.cos(p_ang) * 395)))
    fy = max(75, min(535, int(cy + math.sin(p_ang) * 235)))

    fortress_neighbors = [11, 12, 13, 14, 15, 16]
    nodes["17"] = {
        "name": "Team Syndicate Fortress",
        "region": "Syndicate HQ",
        "type": "poacher_base",
        "x": fx,
        "y": fy,
        "edges": fortress_neighbors,
        "boss": {
            "id": active_boss_key,
            "name": boss_meta["name"],
            "full_name": boss_meta["full_title"],
            "tier": boss_meta["tier"],
            "bp": max(pk["bp"] for pk in boss_meta["team"]),
            "type": boss_meta["team"][0]["type"],
            "sprite": boss_meta["sprite"],
            "appearance": boss_meta["appearance"],
            "team": [dict(pk) for pk in boss_meta["team"]],
            "dialogue": boss_meta["dialogue"],
            "defeated": False,
        },
    }

    ensure_bidirectional_edges(nodes)

    return {
        "map_id": "map_" + uuid.uuid4().hex[:8],
        "map_name": seed_str,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "status": "IN_PROGRESS",
        "game_mode": game_mode,
        "round_num": 1,
        "active_boss_key": active_boss_key,
        "commander_name": boss_meta["full_title"],
        "illumina_summary": ", ".join(b["name"] for b in chosen_illumina),
        "nodes": nodes,
        "photos": [],
    }

def load_library() -> Dict[str, dict]:
    if not os.path.exists(LIBRARY_FILE):
        classic = {
            "map_id": "classic_culantro",
            "map_name": "Classic Culantro Region",
            "created_at": "Preset",
            "status": "IN_PROGRESS",
            "game_mode": "long_mode",
            "round_num": 1,
            "active_boss_key": "Boss_Captain_B.Jack",
            "commander_name": "Captain B.Jack & Kingambit",
            "illumina_summary": "Meganium, Milotic, Wishiwashi, Steelix, Volcarona, Xerneas",
            "nodes": get_classic_culantro_nodes(),
            "photos": [],
        }
        save_library({"classic_culantro": classic})
        return {"classic_culantro": classic}
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            lib = json.load(f)
            for rec in lib.values():
                if "nodes" in rec:
                    ensure_bidirectional_edges(rec["nodes"])
            return lib
    except Exception:
        return {}

def save_library(lib: Dict[str, dict]):
    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(lib, f, indent=2)

def upsert_map_record(record: dict):
    lib = load_library()
    lib[record["map_id"]] = record
    save_library(lib)

def delete_map_record(map_id: str) -> bool:
    lib = load_library()
    if map_id in lib and map_id != "classic_culantro":
        del lib[map_id]
        save_library(lib)
        return True
    return False

HEXAGRAM_WAVES = {
    "tier_1": [
        {"boss_key": "Boss_Captain_B.Jack", "pos": "North"},
        {"boss_key": "Boss_Lt._Deuce", "pos": "West"},
        {"boss_key": "Boss_Chief_J.Pot", "pos": "East"},
    ],
    "tier_2": [
        {"boss_key": "Boss_Marshall_Ace", "pos": "North-West"},
        {"boss_key": "Boss_Baron_Roulette", "pos": "North-East"},
    ],
    "tier_3": [
        {"boss_key": "Boss_Warden_Croupier", "pos": "South"},
    ],
}

def deploy_hexagram_wave(map_record: dict, wave_name: str):
    fortress_edges = map_record["nodes"]["17"]["edges"]
    assignments = HEXAGRAM_WAVES.get(wave_name, [])
    for idx, slot in enumerate(assignments):
        if idx < len(fortress_edges):
            target_nid = str(fortress_edges[idx])
            boss_meta = CASINO_BOSSES[slot["boss_key"]]
            map_record["nodes"][target_nid]["syndicate_boss"] = {
                "id": slot["boss_key"],
                "name": boss_meta["name"],
                "full_name": boss_meta["full_title"],
                "tier": boss_meta["tier"],
                "bp": max(pk["bp"] for pk in boss_meta["team"]),
                "type": boss_meta["team"][0]["type"],
                "sprite": boss_meta["sprite"],
                "appearance": boss_meta["appearance"],
                "team": [dict(pk) for pk in boss_meta["team"]],
                "dialogue": boss_meta["dialogue"],
                "defeated": False,
                "tactical_position": slot["pos"],
            }

def check_and_advance_syndicate_wave(map_record: dict) -> str:
    all_nodes = map_record["nodes"].values()
    active_syndicate_bosses = [
        nd.get("syndicate_boss")
        for nd in all_nodes
        if nd.get("syndicate_boss") and not nd["syndicate_boss"].get("defeated")
    ]
    if not active_syndicate_bosses:
        if not map_record.get("wave_tier_1_cleared"):
            map_record["wave_tier_1_cleared"] = True
            deploy_hexagram_wave(map_record, "tier_2")
            return "WAVE_2_SPAWNED"
        elif not map_record.get("wave_tier_2_cleared"):
            map_record["wave_tier_2_cleared"] = True
            deploy_hexagram_wave(map_record, "tier_3")
            return "WAVE_3_SPAWNED"
        elif not map_record.get("warden_defeated"):
            map_record["warden_defeated"] = True
            activate_super_illumuna_darkrai(map_record)
            return "DARKRAI_SPAWNED"
    return "IN_PROGRESS"

def activate_super_illumuna_darkrai(map_record: dict):
    map_record["map_shroud"] = "DARKNESS_SHROUD"
    fortress_node = map_record["nodes"]["17"]
    fortress_node["name"] = "Amplification Star Mega Darkrai Citadel"
    fortress_node["boss"] = {
        "id": "Super_Illumina_Mega_Darkrai",
        "name": "Mega Darkrai (Super Illumina)",
        "full_name": "Super Illumina Mega Darkrai [Amplification Star]",
        "bp": 29.0,
        "type": "Dark",
        "sprite": "/assets/illumina/illumina_darkrai_mega.png",
        "shadowy_theme": True,
        "calmed": False,
        "defeated": False,
        "dialogue": {
            "intro": "Warden Croupier [RADIO VOICEOVER]: My defeat was merely the final spark! The Amplification Star has fully channeled the primordial shadow into Mega Darkrai!",
            "defeat": "Mega Darkrai dissolves into starlight as the shadow over the Culantro Region lifts forever!",
        },
    }
