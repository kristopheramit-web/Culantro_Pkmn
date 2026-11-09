# lental_online_server.py
import os
import json
import math
import time
import random
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from lental_boss_data import (
    ILLUMINA_POOL_60,
    CASINO_BOSSES,
    GRUNT_RADIO_INTRO,
    ILLUMINA_CALM_RADIO_TAUNTS,
)
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
import fetch_assets

app = FastAPI(title="Culantro Region Pokémon Board Game - drft.stream")

# Ensure asset directories and default placeholder PNGs exist on boot
for d in fetch_assets.ASSET_DIRS:
    os.makedirs(d, exist_ok=True)
fetch_assets.generate_default_placeholders()
fetch_assets.generate_boss_avatars()


@app.get("/assets/{category}/{filename}")
async def serve_asset_with_fallback(category: str, filename: str):
    """
    Serves the requested sprite from disk, or dynamically creates a labeled placeholder PNG
    if the file hasn't been downloaded yet so the browser never receives a 404 error.
    """
    safe_cat = os.path.basename(category)
    safe_file = os.path.basename(filename)
    target_path = os.path.join("assets", safe_cat, safe_file)
    if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
        fetch_assets.create_placeholder_png(target_path, category=safe_cat, title=safe_file)
    return FileResponse(target_path)


app.mount("/assets", StaticFiles(directory="assets"), name="assets")

JOIN_CODE = os.environ.get("LENTAL_JOIN_CODE", "CULANTRO2026")

ROLES = {
    "runner": {"name": "Runner", "desc": "+2 Movement on every die roll (Passive) | Sprint (+1 Step)"},
    "musician": {"name": "Musician", "desc": "Soothe Song: -5 Boss BP on your current node"},
    "nurse": {"name": "Nurse", "desc": "Field Triage: Revive & heal all partners on your node"},
    "fighter": {"name": "Fighter", "desc": "Battle Cry: +2 BP to all allies fighting on your node"},
    "researcher": {"name": "Researcher", "desc": "Field Analysis: +15 EXP to your lead partner"},
    "photographer": {"name": "Photographer", "desc": "Flash Stun: +10% bonus win odds on wheel spins"},
}

ITEMS_META = {
    "fluffruit": {
        "name": "Fluffruit",
        "sprite": "/assets/items/item_fluffruit.png",
        "desc": "Revives a fainted partner and grants +1.0 BP.",
    },
    "soothe_bell": {
        "name": "Soothe Bell",
        "sprite": "/assets/items/item_soothe_bell.png",
        "desc": "Calms an Illumina or Syndicate Boss (-4 Enemy BP on this node).",
    },
    "repel": {
        "name": "Super Repel",
        "sprite": "/assets/items/item_repel.png",
        "desc": "Clear path ahead: Immediately gain +3 movement steps.",
    },
    "knife": {
        "name": "Combat Knife",
        "sprite": "/assets/items/item_knife.png",
        "desc": "Grants +4.0 BP during your next Boss battle (auto-used in combat or click to equip).",
    },
    "grounding_anchor": {
        "name": "Grounding Anchor",
        "sprite": "/assets/items/item_illumina_orb.png",
        "desc": "Grounds Flying-type bosses and boosts team BP by 1.5x (or +3.5 BP vs non-Flying).",
    },
    "rare_candy": {
        "name": "Rare Candy",
        "sprite": "/assets/items/item_rare_candy.png",
        "desc": "Grants +25 EXP to your lead Pokémon, triggering level-up & evolution!",
    },
    "decoy": {
        "name": "Decoy Doll",
        "sprite": "/assets/items/item_decoy.png",
        "desc": "Protects your team from fainting if you lose a battle spin.",
    },
    "karate_trophy": {
        "name": "Karate Trophy",
        "sprite": "/assets/items/item_karate_trophy.png",
        "desc": "Permanently trains your lead Pokémon for +2.5 BP.",
    },
    "illumina_orb": {
        "name": "Illumina Orb",
        "sprite": "/assets/items/item_illumina_orb.png",
        "desc": "Weakens an Illumina Boss shield by -5 Enemy BP on your current node.",
    },
}


class GameState:
    def __init__(self):
        self.players: Dict[str, dict] = {}
        lib = load_library()
        first_rec = lib.get("classic_culantro") or generate_procedural_map(game_mode="long_mode")
        self.load_from_record(first_rec, preserve_players=False)

    def load_from_record(self, rec: dict, preserve_players: bool = True):
        self.map_id = rec["map_id"]
        self.map_name = rec["map_name"]
        self.created_at = rec.get("created_at", time.strftime("%Y-%m-%d %H:%M"))
        self.status = rec.get("status", "IN_PROGRESS")
        self.game_mode = rec.get("game_mode", "long_mode")
        self.active_boss_key = rec.get("active_boss_key", "Boss_Captain_B.Jack")
        self.commander_name = rec.get("commander_name", "Captain B.Jack")
        self.max_players = 6
        self.round_num = rec.get("round_num", 1)
        self.game_over_victory = self.status == "COMPLETED"
        self.amplification_star_active = rec.get("amplification_star_active", False)
        self.wave_tier_1_cleared = rec.get("wave_tier_1_cleared", False)
        self.wave_tier_2_cleared = rec.get("wave_tier_2_cleared", False)
        self.warden_defeated = rec.get("warden_defeated", False)
        self.map_shroud = rec.get("map_shroud", "NORMAL")
        self.nodes = json.loads(json.dumps(rec["nodes"]))

        if preserve_players and hasattr(self, "players") and self.players:
            for pl in self.players.values():
                pl["node"] = 0
                pl["moves_left"] = 0
                pl["rolled_this_round"] = False
                pl["ready_next_round"] = bool(pl.get("is_bot"))
                pl["ability_used_this_round"] = False
                for pk in pl.get("team", []):
                    pk["fainted"] = False
        else:
            self.players = {}

        self.photos: List[dict] = list(rec.get("photos", []))
        self.chat_log: List[dict] = [
            {
                "sender": "Professor Mirror",
                "msg": f"Welcome to {self.map_name}! Enter your Trainer Name at the top right and click 'Join / Edit' to begin.",
            }
        ]
        for g_msg in GRUNT_RADIO_INTRO:
            self.chat_log.append(dict(g_msg))
        self.last_wheel = {
            "spin_id": 0,
            "title": "Waiting for Battle",
            "win_prob": 0.5,
            "roll_val": 0.25,
            "result": "READY",
            "player_bp": 10.0,
            "enemy_bp": 10.0,
            "player_sprite": "/assets/pokemon/1.png",
            "enemy_sprite": "/assets/illumina/illumina_154.png",
        }
        self.persist()

    def persist(self):
        upsert_map_record(
            {
                "map_id": self.map_id,
                "map_name": self.map_name,
                "created_at": self.created_at,
                "status": "COMPLETED" if self.game_over_victory else "IN_PROGRESS",
                "game_mode": self.game_mode,
                "active_boss_key": self.active_boss_key,
                "round_num": self.round_num,
                "commander_name": self.commander_name,
                "amplification_star_active": self.amplification_star_active,
                "wave_tier_1_cleared": self.wave_tier_1_cleared,
                "wave_tier_2_cleared": self.wave_tier_2_cleared,
                "warden_defeated": self.warden_defeated,
                "map_shroud": self.map_shroud,
                "nodes": self.nodes,
                "photos": self.photos[-40:],
            }
        )

    def snap_photo(
        self,
        title: str,
        caption: str,
        stars: str,
        p_sprite: str,
        e_sprite: str,
        win_prob: float = 0.5,
        roll_val: float = 0.25,
        watermark: str = "Trainer",
    ):
        self.photos.append(
            {
                "id": len(self.photos) + 1,
                "round": self.round_num,
                "title": title,
                "caption": caption,
                "stars": stars,
                "player_sprite": p_sprite,
                "enemy_sprite": e_sprite,
                "win_prob": round(win_prob, 3),
                "roll_val": round(roll_val, 3),
                "watermark": watermark,
                "timestamp": time.strftime("%H:%M:%S"),
            }
        )
        self.persist()

    def record_wheel_spin(
        self,
        title: str,
        p_bp: float,
        e_bp: float,
        p_spr: str,
        e_spr: str,
        bonus_prob: float = 0.0,
        watermark: str = "Trainer",
    ) -> bool:
        win_p = min(0.92, max(0.08, (p_bp / max(1.0, (p_bp + e_bp))) + bonus_prob))
        roll = random.random()
        won = roll <= win_p
        self.last_wheel = {
            "spin_id": self.last_wheel["spin_id"] + 1,
            "title": title,
            "win_prob": round(win_p, 2),
            "roll_val": round(roll, 2),
            "result": "VICTORY" if won else "DEFEAT",
            "player_bp": round(p_bp, 1),
            "enemy_bp": round(e_bp, 1),
            "player_sprite": p_spr,
            "enemy_sprite": e_spr,
        }
        stars = "★★★★ DIAMOND" if won else "★★ SILVER"
        self.snap_photo(
            title,
            f"Faced {title} ({round(p_bp, 1)} BP vs {round(e_bp, 1)} BP) — {self.last_wheel['result']}",
            stars,
            p_spr,
            e_spr,
            win_p,
            roll,
            watermark,
        )
        return won

    def check_amplification_star_trigger(self):
        if self.amplification_star_active:
            return
        illumina_nodes = [nd for nd in self.nodes.values() if nd["type"] == "illumina"]
        calmed_count = sum(1 for nd in illumina_nodes if nd.get("boss", {}).get("calmed"))
        if calmed_count in ILLUMINA_CALM_RADIO_TAUNTS:
            for msg in ILLUMINA_CALM_RADIO_TAUNTS[calmed_count]:
                if msg not in self.chat_log:
                    self.chat_log.append(dict(msg))
        if illumina_nodes and calmed_count == len(illumina_nodes):
            self.amplification_star_active = True
            if self.game_mode == "long_mode":
                deploy_hexagram_wave(self.__dict__, "tier_1")
                self.chat_log.append(
                    {
                        "sender": "Team Syndicate Radio",
                        "msg": "Captain B.Jack, Lt. Deuce & Chief J.Pot have exited the Fortress to form Triangle Blockade Wave 1!",
                    }
                )
            else:
                self.chat_log.append(
                    {
                        "sender": "Team Syndicate Radio",
                        "msg": f"{self.commander_name}: All Illumina sanctuaries are calm?! The Fortress gates are open—come face me at Node 17!",
                    }
                )
            self.persist()

    def to_dict(self):
        return {
            "map_id": self.map_id,
            "map_name": self.map_name,
            "status": self.status,
            "game_mode": self.game_mode,
            "commander_name": self.commander_name,
            "game_over_victory": self.game_over_victory,
            "amplification_star_active": self.amplification_star_active,
            "warden_defeated": self.warden_defeated,
            "map_shroud": self.map_shroud,
            "max_players": self.max_players,
            "round_num": self.round_num,
            "nodes": self.nodes,
            "players": self.players,
            "chat_log": self.chat_log[-50:],
            "last_wheel": self.last_wheel,
            "photos": self.photos,
            "library": list(load_library().values()),
            "items_meta": ITEMS_META,
            "roles_meta": ROLES,
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
        if ws in CLIENTS:
            CLIENTS.remove(ws)


def check_level_up_and_evolution(state: GameState, player: dict, pokemon: dict):
    while pokemon.get("exp", 0) >= 25:
        pokemon["exp"] -= 25
        pokemon["level"] = pokemon.get("level", 1) + 1
        pokemon["bp"] = round(pokemon["bp"] + 1.2, 1)
        state.chat_log.append(
            {
                "sender": "Level Up!",
                "msg": f"{player['name']}'s {pokemon['name']} grew to Level {pokemon['level']} (BP {pokemon['bp']})!",
            }
        )
        if pokemon["level"] >= 3 and pokemon.get("evolves_to"):
            old_name = pokemon["name"]
            old_sprite = pokemon["sprite"]
            evo = pokemon["evolves_to"]
            pokemon["name"] = evo["name"]
            pokemon["bp"] = float(evo["bp"])
            pokemon["sprite"] = evo["sprite"]
            pokemon["evolves_to"] = evo.get("evolves_to")
            state.chat_log.append(
                {
                    "sender": "EVOLUTION!",
                    "msg": f"Congratulations! {player['name']}'s {old_name} evolved into {pokemon['name']} (BP {pokemon['bp']})!",
                }
            )
            state.snap_photo(
                f"Evolution: {old_name} → {pokemon['name']}",
                f"{player['name']} evolved {old_name} into {pokemon['name']}!",
                "★★★ GOLD",
                old_sprite,
                pokemon["sprite"],
                1.0,
                0.0,
                player["name"],
            )


def execute_boss_battle(state: GameState, pid: str) -> bool:
    p = state.players.get(pid)
    if not p:
        return False
    ndata = state.nodes[str(p["node"])]

    # In Long Mode, Node 17 (Fortress) is sealed until all 6 Illumina are calmed and Warden Croupier awakens Mega Darkrai
    if (
        str(p["node"]) == "17"
        and state.game_mode == "long_mode"
        and not state.warden_defeated
        and not ndata.get("syndicate_boss")
    ):
        state.chat_log.append(
            {
                "sender": "Fortress Security",
                "msg": "The Syndicate Citadel blast doors are sealed! Calm all 6 Illumina Sanctuaries and defeat the Syndicate officers surrounding the Fortress first!",
            }
        )
        return False

    boss = ndata.get("syndicate_boss") or ndata.get("boss")
    if not boss or boss.get("defeated") or boss.get("calmed"):
        state.chat_log.append(
            {"sender": "System", "msg": f"No active boss to fight at {ndata['name']}!"}
        )
        return False

    allies = [al for al in state.players.values() if al["node"] == p["node"]]
    fighter_present = any(al["role"] == "fighter" for al in allies)
    photog_present = any(al["role"] == "photographer" for al in allies)

    total_p_bp = 0.0
    lead_sprite = "/assets/pokemon/1.png"
    for al in allies:
        conscious = [pk for pk in al["team"] if not pk.get("fainted")]
        if conscious:
            best = max(conscious, key=lambda x: x["bp"])
            lead_sprite = best["sprite"]
            contrib = float(best["bp"]) + float(al.get("temp_bp_bonus", 0.0))
            al["temp_bp_bonus"] = 0.0
            if fighter_present:
                contrib += 2.0
            if "knife" in al["items"]:
                al["items"].remove("knife")
                contrib += 4.0
                state.chat_log.append(
                    {"sender": "Tactical Item", "msg": f"{al['name']} used Combat Knife (+4.0 BP)!"}
                )
            if "grounding_anchor" in al["items"] and boss.get("type") == "Flying":
                al["items"].remove("grounding_anchor")
                contrib *= 1.5
                state.chat_log.append(
                    {
                        "sender": "Tactical Item",
                        "msg": f"{al['name']} deployed Grounding Anchor! Flying boss grounded (1.5x BP)!",
                    }
                )
            total_p_bp += contrib

    if total_p_bp <= 0:
        state.chat_log.append(
            {
                "sender": "Battle",
                "msg": f"{p['name']}'s team is fainted! Visit an Outpost or use a Fluffruit/Nurse ability first.",
            }
        )
        return False

    team = boss.get("team", [])
    current_target = (
        team[0]
        if team
        else {
            "name": boss["name"],
            "bp": boss["bp"],
            "type": boss.get("type", "Normal"),
            "sprite": boss["sprite"],
        }
    )
    soothed_reduction = float(boss.get("soothed", 0))
    enemy_bp = max(4.0, float(current_target["bp"]) - soothed_reduction)
    bonus_prob = 0.10 if photog_present else 0.0

    won = state.record_wheel_spin(
        f"Vs {current_target['name']}",
        total_p_bp,
        enemy_bp,
        lead_sprite,
        current_target["sprite"],
        bonus_prob,
        p["name"],
    )

    if won:
        state.chat_log.append(
            {"sender": "Battle", "msg": f"VICTORY! {p['name']} overpowered {current_target['name']}!"}
        )
        if p["team"]:
            p["team"][0]["exp"] = p["team"][0].get("exp", 0) + 20
            check_level_up_and_evolution(state, p, p["team"][0])
        if len(p["items"]) < 6:
            reward_item = random.choice(list(ITEMS_META.keys()))
            p["items"].append(reward_item)
            state.chat_log.append(
                {
                    "sender": "Loot",
                    "msg": f"{p['name']} found a {ITEMS_META[reward_item]['name']}!",
                }
            )

        if team:
            team.pop(0)
            if team:
                state.chat_log.append(
                    {
                        "sender": boss["name"],
                        "msg": f"{boss.get('dialogue', {}).get('next_poke', 'Sending out next Pokémon!')} ({len(team)} left)",
                    }
                )
        if not team:
            boss["defeated"] = True
            was_syndicate_wave_boss = bool(ndata.get("syndicate_boss"))
            if was_syndicate_wave_boss:
                ndata["star_point_lit"] = boss["name"]
                ndata["syndicate_boss"] = None

            if ndata["type"] == "illumina" and not was_syndicate_wave_boss:
                boss["calmed"] = True
                state.chat_log.append(
                    {
                        "sender": "Sanctuary",
                        "msg": f"Illumina {boss['name']} at {ndata['name']} has been calmed!",
                    }
                )
                state.check_amplification_star_trigger()

            if was_syndicate_wave_boss and state.amplification_star_active:
                next_wave = check_and_advance_syndicate_wave(state.__dict__)
                if next_wave == "WAVE_2_SPAWNED":
                    state.chat_log.append(
                        {
                            "sender": "Syndicate Radio",
                            "msg": "Wave 1 defeated! Marshall Ace (NW) and Baron Roulette (NE) have exited the Fortress!",
                        }
                    )
                elif next_wave == "WAVE_3_SPAWNED":
                    state.chat_log.append(
                        {
                            "sender": "Syndicate Radio",
                            "msg": "The Enforcers fell! Supreme Warden Croupier has stepped out to the Southern approach!",
                        }
                    )
                elif next_wave == "DARKRAI_SPAWNED":
                    state.chat_log.append(
                        {
                            "sender": "CRITICAL ALERT",
                            "msg": "Warden Croupier activated the 6-point Amplification Star! Darkness shrouds the region as Super Illumina Mega Darkrai awakens on Node 17!",
                        }
                    )

            if boss.get("id") == "Super_Illumina_Mega_Darkrai" or (
                state.game_mode == "standard" and str(p["node"]) == "17"
            ):
                state.game_over_victory = True
                state.status = "COMPLETED"
                state.chat_log.append(
                    {
                        "sender": "VICTORY!",
                        "msg": f"{boss['name']} is defeated! The Culantro Region is saved!",
                    }
                )
    else:
        for al in allies:
            if "decoy" in al["items"]:
                al["items"].remove("decoy")
                state.chat_log.append(
                    {
                        "sender": "Tactical Item",
                        "msg": f"{al['name']}'s Decoy Doll absorbed the counterattack!",
                    }
                )
            else:
                for pk in al["team"]:
                    pk["fainted"] = True
                state.chat_log.append(
                    {
                        "sender": "Battle",
                        "msg": f"{current_target['name']} knocked out {al['name']}'s squad! Heal at an Outpost or use a Fluffruit.",
                    }
                )
    state.persist()
    return won


def process_ai_bot_turns(state: GameState):
    """
    Mathematical heuristic bot engine: rolls dice, navigates toward the nearest active
    Illumina or Syndicate Boss node, partners/trains on wild nodes, and engages bosses.
    """
    for pid, p in list(state.players.items()):
        if not p.get("is_bot"):
            continue

        for pk in p["team"]:
            pk["fainted"] = False

        base = random.randint(1, 6)
        p["moves_left"] = base + (2 if p["role"] == "runner" else 0)
        p["rolled_this_round"] = True

        goal_coords = []
        for nid, nd in state.nodes.items():
            if nid == "17" and state.game_mode == "long_mode" and not state.warden_defeated:
                continue
            b = nd.get("syndicate_boss") or nd.get("boss")
            if b and not b.get("defeated") and not b.get("calmed"):
                goal_coords.append((nd["x"], nd["y"]))

        while p["moves_left"] > 0:
            curr_node = state.nodes[str(p["node"])]
            edges = curr_node.get("edges", [])
            if not edges:
                break
            if goal_coords:
                gx, gy = goal_coords[0]
                target_nid = min(
                    edges,
                    key=lambda n: math.hypot(
                        state.nodes[str(n)]["x"] - gx, state.nodes[str(n)]["y"] - gy
                    ),
                )
            else:
                target_nid = random.choice(edges)
            p["node"] = int(target_nid)
            p["moves_left"] -= 1

        ndata = state.nodes[str(p["node"])]
        boss = ndata.get("syndicate_boss") or ndata.get("boss")
        if boss and not boss.get("defeated") and not boss.get("calmed"):
            if not (str(p["node"]) == "17" and state.game_mode == "long_mode" and not state.warden_defeated):
                execute_boss_battle(state, pid)
        elif ndata["type"] == "wild":
            w = random.choice(WILD_POKEDEX_150.get(ndata["region"], WILD_POKEDEX_150["Florio"]))
            if len(p["team"]) < 3:
                new_pk = dict(w)
                new_pk.update({"level": 1, "exp": 0, "fainted": False})
                p["team"].append(new_pk)
                state.chat_log.append(
                    {"sender": p["name"], "msg": f"[Bot] Partnered with wild {w['name']} at {ndata['name']}!"}
                )
            else:
                p["team"][0]["exp"] = p["team"][0].get("exp", 0) + 15
                check_level_up_and_evolution(state, p, p["team"][0])
        p["ready_next_round"] = True


def check_verify_join_code(supplied_code: Optional[str]) -> bool:
    if not supplied_code or supplied_code.strip() == "":
        return True
    return supplied_code.strip() == JOIN_CODE


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


async def handle_websocket_actions(ws: WebSocket, data: dict, state: GameState):
    action = data.get("action")
    pid = data.get("player_id")

    if action == "CHAT":
        msg_text = data.get("msg", "").strip()
        if msg_text:
            state.chat_log.append(
                {"sender": data.get("sender", "Trainer")[:20], "msg": msg_text[:220]}
            )

    elif action == "NEW_PROCEDURAL_MAP":
        if not check_verify_join_code(data.get("join_code")):
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        mode = data.get("game_mode", "long_mode")
        new_rec = generate_procedural_map(data.get("custom_title"), game_mode=mode)
        upsert_map_record(new_rec)
        state.load_from_record(new_rec, preserve_players=True)
        state.chat_log.append(
            {
                "sender": "System",
                "msg": f"Generated procedural Culantro map '{state.map_name}' ({mode.upper()})!",
            }
        )

    elif action == "LOAD_MAP":
        if not check_verify_join_code(data.get("join_code")):
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        lib = load_library()
        target_id = data.get("map_id")
        if target_id == "classic_culantro_fresh":
            fresh = {
                "map_id": "classic_culantro",
                "map_name": "Classic Culantro Region",
                "created_at": time.strftime("%Y-%m-%d %H:%M"),
                "status": "IN_PROGRESS",
                "game_mode": "long_mode",
                "round_num": 1,
                "commander_name": "Captain B.Jack",
                "nodes": get_classic_culantro_nodes(),
                "photos": [],
            }
            state.load_from_record(fresh, preserve_players=True)
        elif target_id in lib:
            state.load_from_record(lib[target_id], preserve_players=True)

    elif action == "DELETE_MAP":
        if not check_verify_join_code(data.get("join_code")):
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Incorrect Host Join Code!"}))
            return
        delete_map_record(data.get("map_id"))
        state.chat_log.append({"sender": "System", "msg": "Deleted map session from library."})

    elif action == "JOIN_OR_EDIT":
        if not check_verify_join_code(data.get("join_code")):
            await ws.send_text(
                json.dumps({"type": "ERROR", "msg": f"Invalid Join Code! Default is {JOIN_CODE}."})
            )
            return
        trainer_name = (data.get("name") or "Trainer").strip()[:18]
        role_key = data.get("role", "runner")
        if role_key not in ROLES:
            role_key = "runner"

        if pid not in state.players:
            starter = json.loads(json.dumps(random.choice(WILD_POKEDEX_150["Florio"][:4])))
            starter.update({"level": 1, "exp": 0, "fainted": False})
            state.players[pid] = {
                "id": pid,
                "name": trainer_name,
                "role": role_key,
                "is_bot": False,
                "node": 0,
                "moves_left": 0,
                "rolled_this_round": False,
                "ready_next_round": False,
                "ability_used_this_round": False,
                "temp_bp_bonus": 0.0,
                "team": [starter],
                "items": ["fluffruit", "grounding_anchor", "soothe_bell"],
            }
            state.chat_log.append(
                {
                    "sender": "System",
                    "msg": f"Trainer {trainer_name} ({ROLES[role_key]['name']}) arrived at Base Camp with {starter['name']}!",
                }
            )
        else:
            state.players[pid]["name"] = trainer_name
            state.players[pid]["role"] = role_key
            state.chat_log.append(
                {
                    "sender": "System",
                    "msg": f"{trainer_name} updated profile to [{ROLES[role_key]['name']}].",
                }
            )
        state.persist()

    elif action == "ADD_BOT":
        if len(state.players) >= state.max_players:
            await ws.send_text(
                json.dumps({"type": "ERROR", "msg": "Max party size (6 Rangers) reached!"})
            )
            return
        bot_num = sum(1 for pl in state.players.values() if pl.get("is_bot")) + 1
        bot_id = f"bot_{int(time.time()*1000) % 100000}_{bot_num}"
        bot_role = random.choice(list(ROLES.keys()))
        bot_name = f"Bot Ranger #{bot_num}"
        starter = json.loads(json.dumps(random.choice(WILD_POKEDEX_150["Florio"])))
        starter.update({"level": 1, "exp": 0, "fainted": False})
        state.players[bot_id] = {
            "id": bot_id,
            "name": bot_name,
            "role": bot_role,
            "is_bot": True,
            "node": 0,
            "moves_left": 0,
            "rolled_this_round": False,
            "ready_next_round": True,
            "ability_used_this_round": False,
            "temp_bp_bonus": 0.0,
            "team": [starter],
            "items": ["grounding_anchor", "fluffruit"],
        }
        state.chat_log.append(
            {
                "sender": "System",
                "msg": f"Mathematical Bot '{bot_name}' [{ROLES[bot_role]['name']}] joined the squad with {starter['name']}!",
            }
        )
        state.persist()

    elif action == "REMOVE_BOT":
        bot_ids = [k for k, v in state.players.items() if v.get("is_bot")]
        if bot_ids:
            removed = state.players.pop(bot_ids[-1])
            state.chat_log.append(
                {"sender": "System", "msg": f"Removed {removed['name']} from the party."}
            )
            state.persist()

    elif action == "ROLL_DICE":
        p = state.players.get(pid)
        if not p:
            await ws.send_text(
                json.dumps(
                    {
                        "type": "ERROR",
                        "msg": "Click 'Join / Edit' in the top-right bar first to join the game!",
                    }
                )
            )
            return
        if p["rolled_this_round"]:
            await ws.send_text(
                json.dumps(
                    {
                        "type": "ERROR",
                        "msg": "You already rolled this round! Click a green-ringed connected node on the map to move, or click 'Lock Turn'.",
                    }
                )
            )
            return
        base = random.randint(1, 6)
        bonus = 2 if p["role"] == "runner" else 0
        p["moves_left"] = base + bonus
        p["rolled_this_round"] = True
        state.chat_log.append(
            {
                "sender": p["name"],
                "msg": f"🎲 Rolled a {base}"
                + (f" (+2 Runner = {p['moves_left']} steps)!" if bonus else f" ({p['moves_left']} steps)!"),
            }
        )
        state.persist()

    elif action == "MOVE_NODE":
        p = state.players.get(pid)
        if not p:
            await ws.send_text(
                json.dumps({"type": "ERROR", "msg": "Join the game first before moving on the map!"})
            )
            return
        target = int(data.get("target_node", -1))
        if target == p["node"]:
            return
        if p["moves_left"] <= 0:
            await ws.send_text(
                json.dumps(
                    {"type": "ERROR", "msg": "No movement steps left! Roll Dice or Lock Turn."}
                )
            )
            return
        curr_edges = state.nodes[str(p["node"])]["edges"]
        if target in curr_edges:
            p["node"] = target
            p["moves_left"] -= 1
            ndata = state.nodes[str(target)]
            state.chat_log.append(
                {
                    "sender": p["name"],
                    "msg": f"Moved to {ndata['name']} ({p['moves_left']} steps left).",
                }
            )
            if ndata["type"] == "outpost":
                for pk in p["team"]:
                    pk["fainted"] = False
                if len(p["items"]) < 6:
                    ikey = random.choice(list(ITEMS_META.keys()))
                    p["items"].append(ikey)
                    state.chat_log.append(
                        {
                            "sender": p["name"],
                            "msg": f"🏥 Healed squad at {ndata['name']} & picked up {ITEMS_META[ikey]['name']}!",
                        }
                    )
                else:
                    state.chat_log.append(
                        {"sender": p["name"], "msg": f"🏥 Healed squad at {ndata['name']}! (Backpack full)"}
                    )
            state.persist()
        else:
            await ws.send_text(
                json.dumps(
                    {
                        "type": "ERROR",
                        "msg": "That node isn't directly connected to your current position!",
                    }
                )
            )

    elif action == "WILD_ENCOUNTER_ACTION":
        p = state.players.get(pid)
        if not p:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Join the game first!"}))
            return
        ndata = state.nodes[str(p["node"])]
        if ndata["type"] != "wild":
            await ws.send_text(
                json.dumps(
                    {
                        "type": "ERROR",
                        "msg": f"You are at {ndata['name']} ({ndata['type'].upper()}). Move to a purple WILD node to partner or spar with wild Pokémon!",
                    }
                )
            )
            return
        w = random.choice(WILD_POKEDEX_150.get(ndata["region"], WILD_POKEDEX_150["Florio"]))
        choice = data.get("mode", "catch")
        active_pk = p["team"][0]

        if choice == "catch":
            if len(p["team"]) < 3:
                state.record_wheel_spin(
                    f"Partner Encounter: {w['name']}",
                    float(active_pk["bp"]) + 3.0,
                    float(w["bp"]),
                    active_pk["sprite"],
                    w["sprite"],
                    0.20,
                    p["name"],
                )
                new_pk = json.loads(json.dumps(w))
                new_pk.update({"level": 1, "exp": 0, "fainted": False})
                p["team"].append(new_pk)
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": f"🔴 Ranger Styler locked on! Partnered up with wild {w['name']} (BP {w['bp']})!",
                    }
                )
            else:
                await ws.send_text(
                    json.dumps(
                        {
                            "type": "ERROR",
                            "msg": "Team is full (Max 3 partners)! Click '✕' next to a partner to release one, or click 'Battle for EXP' instead.",
                        }
                    )
                )
        elif choice == "battle":
            won = state.record_wheel_spin(
                f"Wild Spar vs {w['name']}",
                float(active_pk["bp"]) + 1.5,
                float(w["bp"]),
                active_pk["sprite"],
                w["sprite"],
                0.15,
                p["name"],
            )
            base_exp = {
                "Erratic": 30,
                "Fast": 25,
                "Medium Fast": 20,
                "Medium Slow": 18,
                "Slow": 15,
                "Fluctuating": 25,
            }.get(w.get("exp_group"), 20)
            if not won:
                base_exp = max(10, base_exp // 2)
            if p["role"] == "researcher":
                base_exp *= 2
            active_pk["exp"] = active_pk.get("exp", 0) + base_exp
            state.chat_log.append(
                {
                    "sender": p["name"],
                    "msg": f"⚔️ {active_pk['name']} sparred with wild {w['name']} (+{base_exp} EXP)!",
                }
            )
            check_level_up_and_evolution(state, p, active_pk)
        state.persist()

    elif action == "RELEASE_POKEMON":
        p = state.players.get(pid)
        idx = int(data.get("index", -1))
        if p and len(p["team"]) > 1 and 0 <= idx < len(p["team"]):
            rel = p["team"].pop(idx)
            state.chat_log.append(
                {"sender": p["name"], "msg": f"Released {rel['name']} back into the wild."}
            )
            state.persist()

    elif action == "USE_ABILITY_OR_ITEM":
        p = state.players.get(pid)
        if not p:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Join the game first!"}))
            return
        kind = data.get("kind", "")
        ndata = state.nodes[str(p["node"])]
        boss = ndata.get("syndicate_boss") or ndata.get("boss")

        if kind == "ROLE_ABILITY":
            if p.get("ability_used_this_round"):
                await ws.send_text(
                    json.dumps(
                        {"type": "ERROR", "msg": "You already used your Role Ability this round!"}
                    )
                )
                return
            role = p["role"]
            p["ability_used_this_round"] = True
            if role == "musician":
                if boss:
                    boss["soothed"] = boss.get("soothed", 0) + 5
                    state.chat_log.append(
                        {
                            "sender": p["name"],
                            "msg": f"🎵 Musician Melody soothed {boss['name']} (-5 BP)!",
                        }
                    )
                else:
                    p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 2.5
                    state.chat_log.append(
                        {"sender": p["name"], "msg": "🎵 Musician Melody inspired the squad (+2.5 BP)!"}
                    )
            elif role == "nurse":
                for al in state.players.values():
                    if al["node"] == p["node"]:
                        for pk in al["team"]:
                            pk["fainted"] = False
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": f"💉 Nurse Triage revived & healed all allies at {ndata['name']}!",
                    }
                )
            elif role == "runner":
                p["moves_left"] += 1
                state.chat_log.append(
                    {"sender": p["name"], "msg": "👟 Runner Sprint granted +1 extra step!"}
                )
            elif role == "fighter":
                p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 3.0
                state.chat_log.append(
                    {"sender": p["name"], "msg": "🥊 Fighter Battle Cry charged (+3.0 BP)!"}
                )
            elif role == "researcher":
                if p["team"]:
                    p["team"][0]["exp"] = p["team"][0].get("exp", 0) + 15
                    state.chat_log.append(
                        {
                            "sender": p["name"],
                            "msg": f"🔬 Researcher Field Study granted +15 EXP to {p['team'][0]['name']}!",
                        }
                    )
                    check_level_up_and_evolution(state, p, p["team"][0])
            elif role == "photographer":
                p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 2.0
                state.chat_log.append(
                    {"sender": p["name"], "msg": "📸 Photographer Flash calibrated (+2.0 BP & +10% Wheel Odds)!"}
                )
            state.persist()
            return

        if kind not in p["items"]:
            await ws.send_text(
                json.dumps({"type": "ERROR", "msg": "You don't have that item in your backpack!"})
            )
            return

        p["items"].remove(kind)
        item_name = ITEMS_META.get(kind, {}).get("name", kind)

        if kind == "fluffruit":
            for pk in p["team"]:
                pk["fainted"] = False
            p["team"][0]["bp"] = round(p["team"][0]["bp"] + 1.0, 1)
            state.chat_log.append(
                {
                    "sender": p["name"],
                    "msg": f"🍎 Used {item_name}: Revived squad & boosted {p['team'][0]['name']} (+1.0 BP)!",
                }
            )
        elif kind in ("soothe_bell", "illumina_orb"):
            reduction = 5 if kind == "illumina_orb" else 4
            if boss:
                boss["soothed"] = boss.get("soothed", 0) + reduction
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": f"🔔 Used {item_name}: Reduced {boss['name']}'s BP by -{reduction}!",
                    }
                )
            else:
                p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 3.0
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": f"🔔 Used {item_name}: Harmonized team aura (+3.0 BP for next battle)!",
                    }
                )
        elif kind == "repel":
            p["moves_left"] += 3
            state.chat_log.append(
                {"sender": p["name"], "msg": f"🧴 Used {item_name}: Gained +3 movement steps!"}
            )
        elif kind == "rare_candy":
            active_pk = p["team"][0]
            active_pk["exp"] = active_pk.get("exp", 0) + 25
            state.chat_log.append(
                {"sender": p["name"], "msg": f"🍬 Fed Rare Candy to {active_pk['name']} (+25 EXP)!"}
            )
            check_level_up_and_evolution(state, p, active_pk)
        elif kind == "karate_trophy":
            active_pk = p["team"][0]
            active_pk["bp"] = round(active_pk["bp"] + 2.5, 1)
            state.chat_log.append(
                {
                    "sender": p["name"],
                    "msg": f"🏆 Used Karate Trophy: {active_pk['name']}'s BP permanently increased to {active_pk['bp']}!",
                }
            )
        elif kind == "knife":
            p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 4.0
            state.chat_log.append(
                {"sender": p["name"], "msg": "🗡️ Equipped Combat Knife (+4.0 BP for next battle)!"}
            )
        elif kind == "grounding_anchor":
            if boss and boss.get("type") == "Flying":
                boss["soothed"] = boss.get("soothed", 0) + 6
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": f"⚓ Grounding Anchor slammed {boss['name']} out of the sky (-6 Boss BP)!",
                    }
                )
            else:
                p["temp_bp_bonus"] = p.get("temp_bp_bonus", 0.0) + 3.5
                state.chat_log.append(
                    {
                        "sender": p["name"],
                        "msg": "⚓ Anchored stance (+3.5 BP for next battle)!",
                    }
                )
        elif kind == "decoy":
            p["items"].append("decoy")
            state.chat_log.append(
                {
                    "sender": p["name"],
                    "msg": "🪆 Decoy Doll is active in your bag—it will automatically protect your squad if a battle spin fails!",
                }
            )
        state.persist()

    elif action == "FIGHT_BOSS":
        if not pid or pid not in state.players:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Join the game first!"}))
            return
        execute_boss_battle(state, pid)

    elif action == "READY_NEXT_ROUND":
        p = state.players.get(pid)
        if not p:
            await ws.send_text(json.dumps({"type": "ERROR", "msg": "Join the game first!"}))
            return
        p["ready_next_round"] = True
        state.chat_log.append(
            {"sender": p["name"], "msg": "✅ Locked turn and ready for the next round!"}
        )

        human_players = [pl for pl in state.players.values() if not pl.get("is_bot")]
        if human_players and all(pl.get("ready_next_round") for pl in human_players):
            process_ai_bot_turns(state)
            state.round_num += 1
            for pl in state.players.values():
                pl["rolled_this_round"] = False
                pl["ready_next_round"] = bool(pl.get("is_bot"))
                pl["ability_used_this_round"] = False
                pl["moves_left"] = 0
            state.chat_log.append(
                {
                    "sender": "Round Manager",
                    "msg": f"=== ROUND {state.round_num} STARTED! Roll your movement dice! ===",
                }
            )
        state.persist()


@app.get("/download/offline")
async def download_offline_binary(request: Request):
    ua = request.headers.get("user-agent", "").lower()
    is_android = "android" in ua or "wv" in ua or "aft" in ua
    filename = (
        "CulantroBoardGame_Offline.apk" if is_android else "CulantroBoardGame_Offline.exe"
    )
    filepath = os.path.join("downloads", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename, media_type="application/octet-stream")
    return FileResponse(
        "lental_offline_app.py", filename="lental_offline_app.py", media_type="text/x-python"
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    no_cache_headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    if os.path.exists("lental_ui.html"):
        with open("lental_ui.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), headers=no_cache_headers)
    return HTMLResponse(
        content="<h3>Frontend lental_ui.html not found.</h3>", headers=no_cache_headers
    )


if __name__ == "__main__":
    import uvicorn

    print("Starting Culantro Region Server v2.2 on http://0.0.0.0:8080 ...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
