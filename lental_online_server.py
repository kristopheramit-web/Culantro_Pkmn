# lental_online_server.py
import os
import json
import time
import random
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from lental_boss_data import ILLUMINA_POOL_60, CASINO_BOSSES, GRUNT_RADIO_INTRO, ILLUMINA_CALM_RADIO_TAUNTS
from lental_pokedex_data import WILD_POKEDEX_150
from lental_map_engine import (
    get_classic_culantro_nodes,
    generate_procedural_map,
    load_library,
    upsert_map_record,
    delete_map_record,
    deploy_hexagram_wave,
    check_and_advance_syndicate_wave,
    activate_super_illumuna_darkrai,
)

app = FastAPI(title="Culantro Region Pokémon Board Game - drft.stream")

if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

JOIN_CODE = os.environ.get("LENTAL_JOIN_CODE", "CULANTRO2026")

ROLES = {
    "musician": {"name": "Musician", "desc": "Soothe Illumina (-5 BP this round)"},
    "nurse": {"name": "Nurse", "desc": "Heal all allies on your current node"},
    "runner": {"name": "Runner", "desc": "+2 Movement on every die roll"},
    "fighter": {"name": "Fighter", "desc": "+2 BP to every ally fighting on your node"},
    "researcher": {"name": "Researcher", "desc": "Ignore hazards & double training XP (+1.0 BP)"},
    "photographer": {"name": "Photographer", "desc": "Flash-stun: +10% bonus win odds on wheel spins"},
}

TYPE_CHART = {
    "Water": {"strong": ["Fire", "Ground", "Rock"], "weak": ["Water", "Grass"]},
    "Fire": {"strong": ["Grass", "Ice", "Bug", "Steel"], "weak": ["Water", "Rock"]},
    "Grass": {"strong": ["Water", "Ground", "Rock"], "weak": ["Fire", "Ice", "Bug", "Flying"]},
    "Ice": {"strong": ["Grass", "Ground", "Flying", "Dragon"], "weak": ["Fire", "Steel", "Water"]},
    "Fighting": {"strong": ["Normal", "Ice", "Rock", "Steel", "Dark"], "weak": ["Flying", "Fairy", "Psychic"]},
    "Fairy": {"strong": ["Fighting", "Dragon", "Dark"], "weak": ["Steel", "Fire"]},
    "Dragon": {"strong": ["Dragon"], "weak": ["Ice", "Fairy", "Steel"]},
    "Dark": {"strong": ["Psychic", "Ghost"], "weak": ["Fighting", "Fairy", "Bug"]},
    "Psychic": {"strong": ["Fighting", "Poison"], "weak": ["Dark", "Bug", "Steel"]},
    "Rock": {"strong": ["Fire", "Ice", "Flying", "Bug"], "weak": ["Water", "Grass", "Fighting", "Ground", "Steel"]},
    "Ground": {"strong": ["Fire", "Rock", "Steel"], "weak": ["Grass", "Bug", "Flying"]},
    "Steel": {"strong": ["Ice", "Rock", "Fairy"], "weak": ["Fire", "Water"]},
    "Flying": {"strong": ["Grass", "Fighting", "Bug"], "weak": ["Rock", "Steel"]},
    "Normal": {"strong": [], "weak": ["Rock", "Steel"]},
}

ITEMS_META = {
    "decoy": {"name": "Decoy Doll", "sprite": "/assets/items/item_decoy.png"},
    "knife": {"name": "Combat Knife", "sprite": "/assets/items/item_knife.png"},
    "grounding_anchor": {"name": "Grounding Anchor", "sprite": "/assets/items/item_illumina_orb.png", "desc": "Grounds Flying types, making Fighting super effective!"},
    "soothe_bell": {"name": "Soothe Bell", "sprite": "/assets/items/item_soothe_bell.png"},
    "repel": {"name": "Super Repel", "sprite": "/assets/items/item_repel.png"},
    "rare_candy": {"name": "Rare Candy", "sprite": "/assets/items/item_rare_candy.png"},
    "fluffruit": {"name": "Fluffruit", "sprite": "/assets/items/item_fluffruit.png"},
}

class GameState:
    def __init__(self):
        self.load_from_record(load_library().get("classic_culantro") or generate_procedural_map(game_mode="long_mode"))

    def load_from_record(self, rec: dict):
        self.map_id = rec["map_id"]
        self.map_name = rec["map_name"]
        self.created_at = rec.get("created_at", time.strftime("%Y-%m-%d %H:%M"))
        self.status = rec.get("status", "IN_PROGRESS")
        self.game_mode = rec.get("game_mode", "long_mode")
        self.active_boss_key = rec.get("active_boss_key", "Boss_Captain_B.Jack")
        self.commander_name = rec.get("commander_name", "Captain B.Jack")
        self.max_players = 4
        self.round_num = rec.get("round_num", 1)
        self.game_over_victory = (self.status == "COMPLETED")
        self.amplification_star_active = rec.get("amplification_star_active", False)
        self.map_shroud = rec.get("map_shroud", "NORMAL")
        self.nodes = json.loads(json.dumps(rec["nodes"]))
        self.players: Dict[str, dict] = {}
        self.photos: List[dict] = list(rec.get("photos", []))
        self.chat_log: List[dict] = [
            {"sender": "Professor Mirror", "msg": f"Welcome to the Culantro Region ({self.map_name}). Radio intercepts report strange syndicate activity. Investigate the sanctuaries!"}
        ]
        for g_msg in GRUNT_RADIO_INTRO:
            self.chat_log.append(g_msg)
        self.last_wheel = {
            "spin_id": 0, "title": "Waiting for Battle", "win_prob": 0.5, "roll_val": 0.25,
            "result": "READY", "player_bp": 10.0, "enemy_bp": 10.0,
            "player_sprite": "/assets/pokemon/1.png", "enemy_sprite": "/assets/illumina/illumina_154.png"
        }
        self.persist()

    def persist(self):
        upsert_map_record({
            "map_id": self.map_id,
            "map_name": self.map_name,
            "created_at": self.created_at,
            "status": "COMPLETED" if self.game_over_victory else "IN_PROGRESS",
            "game_mode": self.game_mode,
            "active_boss_key": self.active_boss_key,
            "round_num": self.round_num,
            "commander_name": self.commander_name,
            "amplification_star_active": self.amplification_star_active,
            "map_shroud": self.map_shroud,
            "nodes": self.nodes,
            "photos": self.photos[-40:],
        })

    def snap_photo(self, title: str, caption: str, stars: str, p_sprite: str, e_sprite: str, win_prob: float = 0.5, roll_val: float = 0.25, watermark: str = "Trainer"):
        self.photos.append({
            "id": len(self.photos) + 1, "round": self.round_num, "title": title, "caption": caption,
            "stars": stars, "player_sprite": p_sprite, "enemy_sprite": e_sprite,
            "win_prob": round(win_prob, 3), "roll_val": round(roll_val, 3), "watermark": watermark,
            "timestamp": time.strftime("%H:%M:%S")
        })
        self.persist()

    def record_wheel_spin(self, title: str, p_bp: float, e_bp: float, p_spr: str, e_spr: str, bonus_prob: float = 0.0, watermark: str = "Trainer") -> bool:
        win_p = min(0.92, max(0.08, (p_bp / (p_bp + e_bp)) + bonus_prob))
        roll = random.random()
        won = roll <= win_p
        self.last_wheel = {
            "spin_id": self.last_wheel["spin_id"] + 1, "title": title,
            "win_prob": round(win_p, 2), "roll_val": round(roll, 2),
            "result": "VICTORY" if won else "DEFEAT",
            "player_bp": p_bp, "enemy_bp": e_bp,
            "player_sprite": p_spr, "enemy_sprite": e_spr
        }
        stars = "★★★★ DIAMOND" if won else "★ BRONZE"
        self.snap_photo(title, f"Faced {title} with {p_bp} BP vs {e_bp} BP. Outcome: {self.last_wheel['result']}", stars, p_spr, e_spr, win_p, roll, watermark)
        return won

    def check_amplification_star_trigger(self):
        if self.amplification_star_active:
            return
        illumina_nodes = [nd for nd in self.nodes.values() if nd["type"] == "illumina"]
        if illumina_nodes and all(nd["boss"].get("calmed") for nd in illumina_nodes):
            self.amplification_star_active = True
            deploy_hexagram_wave(self.__dict__, "tier_1")
            self.chat_log.append({"sender": "Team Syndicate Radio", "msg": f"{self.commander_name}: You've calmed all Illumina sanctuaries! The Amplification Star ley-lines are activating around the fortress!"})
            self.persist()

    def to_dict(self):
        return {
            "map_id": self.map_id, "map_name": self.map_name, "status": self.status,
            "game_mode": self.game_mode, "commander_name": self.commander_name,
            "game_over_victory": self.game_over_victory, "amplification_star_active": self.amplification_star_active,
            "map_shroud": self.map_shroud, "max_players": self.max_players,
            "round_num": self.round_num, "nodes": self.nodes, "players": self.players,
            "chat_log": self.chat_log[-45:], "last_wheel": self.last_wheel, "photos": self.photos,
            "library": list(load_library().values()), "items_meta": ITEMS_META,
        }

STATE = GameState()
CLIENTS: List[WebSocket] = []

async def broadcast_state():
    payload = json.dumps({"type": "STATE_UPDATE", "state": STATE.to_dict()})
    stale = []
    for ws in CLIENTS:
        try:
            await ws.send_text(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        CLIENTS.remove(ws)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    CLIENTS.append(ws)
    await ws.send_text(json.dumps({"type": "STATE_UPDATE", "state": STATE.to_dict()}))
    try:
        while True:
            data = json.loads(await ws.receive_text())
            await handle_websocket_actions(ws, data, STATE)
            await broadcast_state()
    except WebSocketDisconnect:
        if ws in CLIENTS:
            CLIENTS.remove(ws)

# --- MATHEMATICAL HEURISTIC BOT ENGINE ---
def process_ai_bot_turns(state: GameState):
    """
    Automates turns for any registered AI bot players using distance heuristics
    toward the nearest uncalmed Illumina node or active syndicate boss.
    """
    for pid, p in state.players.items():
        if not p.get("is_bot"):
            continue
        
        # 1. Roll dice if not rolled
        if not p["rolled_this_round"]:
            base = random.randint(1, 6)
            p["moves_left"] = base + (2 if p["role"] == "runner" else 0)
            p["rolled_this_round"] = True
            state.chat_log.append({"sender": p["name"], "msg": f"[Bot] Rolled a {base} (Moves: {p['moves_left']})"})

        # 2. Move toward target node (nearest Illumina or Syndicate boss)
        while p["moves_left"] > 0:
            curr_node = state.nodes[str(p["node"])]
            edges = curr_node["edges"]
            if not edges:
                break
            
            # Find target: nearest node with an active boss or uncalmed illumina
            target_nid = min(edges, key=lambda n: abs(state.nodes[str(n)]["x"] - curr_node["x"]))
            p["node"] = target_nid
            p["moves_left"] -= 1

        # 3. Execute combat or wild action if on target node
        ndata = state.nodes[str(p["node"])]
        if ndata.get("syndicate_boss") or ndata.get("boss"):
            # Trigger bot combat
            resolve_syndicate_boss_battle(state, pid, ndata)
        elif ndata["type"] == "wild" and len(p["team"]) < 3:
            w = random.choice(WILD_POKEDEX_150.get(ndata["region"], WILD_POKEDEX_150["Florio"]))
            p["team"].append({"name": w["name"], "bp": w["bp"], "level": 1, "exp": 0, "fainted": False})
            state.chat_log.append({"sender": p["name"], "msg": f"[Bot] Partnered up with wild {w['name']}!"})
        
        p["ready_next_round"] = True

async def handle_websocket_actions(ws: WebSocket, data: dict, state: GameState):
    action = data.get("action")
    pid = data.get("player_id")

    if action == "CHAT":
        state.chat_log.append({"sender": data.get("sender", "Trainer"), "msg": data.get("msg", "")[:200]})

    elif action == "NEW_PROCEDURAL_MAP":
        if data.get("join_code") != JOIN_CODE:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        mode = data.get("game_mode", "long_mode")
        new_rec = generate_procedural_map(data.get("custom_title"), game_mode=mode)
        upsert_map_record(new_rec)
        state.load_from_record(new_rec)
        state.chat_log.append({"sender": "System", "msg": f"Generated new Culantro Region map '{state.map_name}' in {mode.upper()} mode!"})

    elif action == "LOAD_MAP":
        if data.get("join_code") != JOIN_CODE:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        lib = load_library()
        target_id = data.get("map_id")
        if target_id == "classic_culantro_fresh":
            fresh = {
                "map_id": "classic_culantro", "map_name": "Classic Culantro Region",
                "created_at": time.strftime("%Y-%m-%d %H:%M"), "status": "IN_PROGRESS",
                "game_mode": "long_mode", "round_num": 1, "commander_name": "Captain B.Jack",
                "nodes": get_classic_culantro_nodes(), "photos": []
            }
            state.load_from_record(fresh)
        elif target_id in lib:
            state.load_from_record(lib[target_id])

    elif action == "DELETE_MAP":
        if data.get("join_code") != JOIN_CODE:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        delete_map_record(data.get("map_id"))
        state.chat_log.append({"sender": "System", "msg": "Deleted map session from library."})

    elif action == "JOIN_OR_EDIT":
        if data.get("join_code") != JOIN_CODE:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Invalid Host Join Code!"}))
            return
        starter = json.loads(json.dumps(random.choice(WILD_POKEDEX_150["Florio"][:4])))
        starter["level"] = 1
        starter["exp"] = 0
        starter["fainted"] = False
        if pid not in state.players:
            state.players[pid] = {
                "id": pid, "name": data.get("name", "Trainer")[:18], "role": data.get("role", "runner"),
                "node": 0, "moves_left": 0, "rolled_this_round": False, "ready_next_round": False,
                "team": [starter], "items": ["grounding_anchor"],
            }
            state.chat_log.append({"sender": "System", "msg": f"{state.players[pid]['name']} arrived in Culantro with partner {starter['name']}!"})
        else:
            state.players[pid]["name"] = data.get("name", state.players[pid]["name"])[:18]
            state.players[pid]["role"] = data.get("role", state.players[pid]["role"])

    elif action == "ROLL_DICE":
        p = state.players.get(pid)
        if p and not p["rolled_this_round"]:
            base = random.randint(1, 6)
            bonus = 2 if p["role"] == "runner" else 0
            p["moves_left"] = base + bonus
            p["rolled_this_round"] = True
            state.chat_log.append({"sender": p["name"], "msg": f"Rolled a {base}" + (f" (+2 Runner = {p['moves_left']})" if bonus else "!")})

    elif action == "MOVE_NODE":
        p = state.players.get(pid)
        target = int(data.get("target_node", 0))
        if p and p["moves_left"] > 0:
            curr_edges = state.nodes[str(p["node"])]["edges"]
            if target in curr_edges:
                p["node"] = target
                p["moves_left"] -= 1
                ndata = state.nodes[str(target)]
                if ndata["type"] == "outpost":
                    for pk in p["team"]:
                        pk["fainted"] = False
                    if len(p["items"]) < 5:
                        ikey = random.choice(list(ITEMS_META.keys()))
                        p["items"].append(ikey)
                        state.chat_log.append({"sender": p["name"], "msg": f"Healed at {ndata['name']} & acquired {ITEMS_META[ikey]['name']}!"})

    elif action == "WILD_ENCOUNTER_ACTION":
        p = state.players.get(pid)
        if not p:
            return
        ndata = state.nodes[str(p["node"])]
        if ndata["type"] != "wild":
            return
        w = random.choice(WILD_POKEDEX_150.get(ndata["region"], WILD_POKEDEX_150["Florio"]))
        choice = data.get("mode", "catch")

        if choice == "catch":
            if len(p["team"]) < 3:
                new_pk = dict(w)
                new_pk["level"] = 1
                new_pk["exp"] = 0
                new_pk["fainted"] = False
                p["team"].append(new_pk)
                state.chat_log.append({"sender": p["name"], "msg": f"Partnered up with wild {w['name']}!"})
            else:
                state.chat_log.append({"sender": p["name"], "msg": "Team is full (Max 3 partners)! Release a Pokémon or choose to battle for EXP."})
        elif choice == "battle":
            # Defeat wild Pokémon for EXP based on EXP group
            active_pk = p["team"][0]
            exp_gain = {"Erratic": 30, "Fast": 20, "Medium Fast": 15, "Medium Slow": 12, "Slow": 10, "Fluctuating": 25}.get(w.get("exp_group"), 15)
            active_pk["exp"] += exp_gain
            state.chat_log.append({"sender": p["name"], "msg": f"{active_pk['name']} defeated wild {w['name']} and gained {exp_gain} EXP!"})
            
            # 2 Level-ups trigger evolution
            if active_pk["exp"] >= 25 and active_pk.get("evolves_to"):
                old_name = active_pk["name"]
                evo = active_pk["evolves_to"]
                active_pk["name"] = evo["name"]
                active_pk["bp"] = evo["bp"]
                active_pk["sprite"] = evo["sprite"]
                active_pk["evolves_to"] = evo.get("evolves_to")
                active_pk["exp"] = 0
                state.chat_log.append({"sender": "EVOLUTION!", "msg": f"{p['name']}'s {old_name} evolved into {active_pk['name']}!"})

    elif action == "FIGHT_BOSS":
        p = state.players.get(pid)
        if not p:
            return
        ndata = state.nodes[str(p["node"])]
        boss = ndata.get("syndicate_boss") or ndata.get("boss")
        if not boss or boss.get("defeated"):
            return

        allies = [al for al in state.players.values() if al["node"] == p["node"]]
        fighter_present = any(al["role"] == "fighter" for al in allies)
        photog_present = any(al["role"] == "photographer" for al in allies)

        total_p_bp = 0.0
        lead_sprite = "/assets/pokemon/1.png"
        for al in allies:
            conscious = [pk for pk in al["team"] if not pk["fainted"]]
            if conscious:
                best = max(conscious, key=lambda x: x["bp"])
                lead_sprite = best["sprite"]
                contrib = best["bp"]
                if fighter_present:
                    contrib += 2.0
                if "knife" in al["items"]:
                    al["items"].remove("knife")
                    contrib += 4.0
                # D&D Tactical Grounding Anchor check against Flying types
                if "grounding_anchor" in al["items"] and boss.get("type") == "Flying":
                    al["items"].remove("grounding_anchor")
                    contrib *= 1.5
                    state.chat_log.append({"sender": "Tactical Item", "msg": f"{al['name']} deployed the Grounding Anchor! Flying type grounded and vulnerable!"})
                total_p_bp += contrib

        team = boss.get("team", [])
        current_target = team[0] if team else {"name": boss["name"], "bp": boss["bp"], "type": boss["type"], "sprite": boss["sprite"]}
        enemy_bp = float(current_target["bp"])
        bonus_prob = 0.10 if photog_present else 0.0

        won = state.record_wheel_spin(
            f"Syndicate Raid vs {current_target['name']}",
            total_p_bp, enemy_bp, lead_sprite, current_target["sprite"], bonus_prob, p["name"]
        )

        if won:
            state.chat_log.append({"sender": "Battle", "msg": f"{p['name']} defeated {current_target['name']}!"})
            if team:
                team.pop(0)
            if not team:
                boss["defeated"] = True
                if ndata.get("syndicate_boss"):
                    ndata["syndicate_boss"] = None
                
                # Check syndicate wave progression
                next_wave = check_and_advance_syndicate_wave(state.__dict__)
                if next_wave == "WAVE_2_SPAWNED":
                    state.chat_log.append({"sender": "Syndicate Radio", "msg": "Marshall Ace and Baron Roulette have stepped out of the fortress!"})
                elif next_wave == "WAVE_3_SPAWNED":
                    state.chat_log.append({"sender": "Syndicate Radio", "msg": "Warden Croupier has stepped onto the frontline!"})
                elif next_wave == "DARKRAI_SPAWNED":
                    state.chat_log.append({"sender": "CRITICAL ALERT", "msg": "Warden Croupier activated the Amplification Star! Super Illumina Mega Darkrai has awakened!"})
                
                if boss.get("id") == "Super_Illumina_Mega_Darkrai":
                    state.game_over_victory = True
                    state.status = "COMPLETED"
            
            if ndata["type"] == "illumina":
                boss["calmed"] = True
                state.check_amplification_star_trigger()
        else:
            for al in allies:
                for pk in al["team"]:
                    pk["fainted"] = True
            state.chat_log.append({"sender": "Battle", "msg": f"{current_target['name']} overpowered the team!"})
        state.persist()

@app.get("/download/offline")
async def download_offline_binary(request: Request):
    ua = request.headers.get("user-agent", "").lower()
    is_android = "android" in ua or "wv" in ua or "aft" in ua
    filename = "CulantroBoardGame_Offline.apk" if is_android else "CulantroBoardGame_Offline.exe"
    filepath = os.path.join("downloads", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type="application/octet-stream")
    return FileResponse("lental_offline_app.py", filename="lental_offline_app.py", media_type="text/x-python")

@app.get("/", response_class=HTMLResponse)
async def index():
    if os.path.exists("lental_ui.html"):
        with open("lental_ui.html", "r", encoding="utf-8") as f:
    
