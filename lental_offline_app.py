# lental_offline_app.py
import os
import time
import random
import tkinter as tk
from tkinter import messagebox, simpledialog

from lental_map_engine import (
    generate_procedural_map,
    load_library,
    upsert_map_record,
    delete_map_record,
    get_classic_culantro_nodes,
)
from lental_pokedex_data import WILD_POKEDEX_150

ROLES_LIST = [
    "Runner (+2 Move)", "Musician (-5 Boss BP)", "Nurse (Node Heal)",
    "Fighter (+2 Ally BP)", "Researcher (2x XP)", "Photographer (+10% Odds)"
]

class CulantroOfflineGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Culantro Region Board Game — Offline Couch Co-Op Edition")
        self.root.geometry("1200x720")
        self.root.configure(bg="#0d131a")

        lib = load_library()
        first_rec = lib.get("classic_culantro") or generate_procedural_map(game_mode="long_mode")
        self.players = []
        self.turn_idx = 0
        self.load_map_record(first_rec, prompt_players=False)
        self.setup_ui()
        self.open_map_library_dialog(startup=True)

    def load_map_record(self, rec: dict, prompt_players: bool = True):
        self.map_id = rec["map_id"]
        self.map_name = rec["map_name"]
        self.created_at = rec.get("created_at", time.strftime("%Y-%m-%d %H:%M"))
        self.status = rec.get("status", "IN_PROGRESS")
        self.game_mode = rec.get("game_mode", "long_mode")
        self.active_boss_key = rec.get("active_boss_key", "Boss_Captain_B.Jack")
        self.commander_name = rec.get("commander_name", "Captain B.Jack")
        self.round_num = rec.get("round_num", 1)
        self.nodes = {int(k): v for k, v in rec["nodes"].items()}
        self.photos = list(rec.get("photos", []))
        self.turn_idx = 0
        for pl in self.players:
            pl["node"] = 0
            pl["moves"] = 0
            pl["rolled"] = False
        if prompt_players and not self.players:
            self.prompt_player_setup()

    def save_current_session(self):
        upsert_map_record({
            "map_id": self.map_id,
            "map_name": self.map_name,
            "created_at": self.created_at,
            "status": self.status,
            "game_mode": self.game_mode,
            "active_boss_key": self.active_boss_key,
            "round_num": self.round_num,
            "commander_name": self.commander_name,
            "nodes": {str(k): v for k, v in self.nodes.items()},
            "photos": self.photos,
        })

    def snap_photo(self, title: str, caption: str, stars: str, watermark: str = "Offline Ranger"):
        self.photos.append({
            "id": len(self.photos) + 1,
            "round": self.round_num,
            "title": title,
            "caption": caption,
            "stars": stars,
            "watermark": watermark,
            "timestamp": time.strftime("%H:%M:%S")
        })
        self.save_current_session()

    def setup_ui(self):
        top = tk.Frame(self.root, bg="#161f2c", pady=8, padx=12)
        top.pack(fill=tk.X)
        self.lbl_turn = tk.Label(top, text="Culantro Region Offline", fg="#58a6ff", bg="#161f2c", font=("Segoe UI", 12, "bold"))
        self.lbl_turn.pack(side=tk.LEFT)

        tk.Button(top, text="📸 Highlights B-Roll", command=self.open_photo_album_dialog, bg="#b8860b", fg="white").pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="🗺️ Map Library", command=self.open_map_library_dialog, bg="#1f6feb", fg="white").pack(side=tk.RIGHT, padx=4)
        tk.Button(top, text="👥 Edit Players", command=self.prompt_player_setup, bg="#238636", fg="white").pack(side=tk.RIGHT, padx=4)

        mid = tk.Frame(self.root, bg="#0d131a")
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.canvas = tk.Canvas(mid, width=880, height=580, bg="#091e2c", highlightthickness=2, highlightbackground="#3d5a80")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        right = tk.Frame(mid, width=280, bg="#161f2c", padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        self.lbl_stats = tk.Label(right, text="", fg="#e6edf3", bg="#161f2c", justify=tk.LEFT, font=("Segoe UI", 9), wraplength=250)
        self.lbl_stats.pack(anchor="w", pady=(0, 10))

        btn_cfg = {"fill": tk.X, "pady": 3}
        tk.Button(right, text="1. Roll Movement Die", command=self.roll_die, bg="#238636", fg="white").pack(**btn_cfg)
        tk.Button(right, text="2. Partner Up (Wild)", command=lambda: self.wild_action("catch"), bg="#1f6feb", fg="white").pack(**btn_cfg)
        tk.Button(right, text="3. Battle for EXP & Evolution", command=lambda: self.wild_action("battle"), bg="#1f6feb", fg="white").pack(**btn_cfg)
        tk.Button(right, text="4. Fight Syndicate Boss", command=self.fight_boss, bg="#da3633", fg="white").pack(**btn_cfg)
        tk.Button(right, text="5. End My Turn", command=self.next_turn, bg="#d29922", fg="black").pack(**btn_cfg)

        self.lbl_banner = tk.Label(self.root, text="Welcome to the Culantro Region! Roll your die to begin.", fg="#ffd166", bg="#161f2c", pady=6, font=("Segoe UI", 11, "bold"))
        self.lbl_banner.pack(fill=tk.X, side=tk.BOTTOM)

    def open_map_library_dialog(self, startup=False):
        win = tk.Toplevel(self.root)
        win.title("Map Library — Procedural Generator")
        win.geometry("780x500")
        win.configure(bg="#131c27")
        win.grab_set()

        tk.Label(win, text="🗺️ Map Library & Procedural Generator", fg="#ffd166", bg="#131c27", font=("Segoe UI", 13, "bold")).pack(pady=8)
        top_bar = tk.Frame(win, bg="#131c27")
        top_bar.pack(fill=tk.X, padx=14, pady=4)

        mode_var = tk.StringVar(value="long_mode")
        tk.Label(top_bar, text="Mode:", fg="#fff", bg="#131c27").pack(side=tk.LEFT, padx=2)
        tk.OptionMenu(top_bar, mode_var, "standard", "long_mode").pack(side=tk.LEFT, padx=4)

        def create_new_proc():
            new_rec = generate_procedural_map(game_mode=mode_var.get())
            upsert_map_record(new_rec)
            self.load_map_record(new_rec, prompt_players=(not self.players))
            self.update_ui()
            win.destroy()

        tk.Button(top_bar, text="✨ Generate Procedural Map", command=create_new_proc, bg="#238636", fg="white", padx=8, pady=5).pack(side=tk.LEFT, padx=6)
        tk.Button(top_bar, text="🔄 Reset Classic", command=lambda: (self.load_map_record({"map_id":"classic_culantro","map_name":"Classic Culantro","status":"IN_PROGRESS","game_mode":"long_mode","commander_name":"Captain B.Jack","nodes":get_classic_culantro_nodes(),"photos":[]}, prompt_players=(not self.players)), self.update_ui(), win.destroy()), bg="#1f6feb", fg="white", padx=8, pady=5).pack(side=tk.LEFT)

        list_frame = tk.Frame(win, bg="#0d131a", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

        def populate_rows():
            for w in list_frame.winfo_children():
                w.destroy()
            lib = load_library()
            for mid, rec in lib.items():
                row = tk.Frame(list_frame, bg="#161f2c", pady=6, padx=8)
                row.pack(fill=tk.X, pady=3)
                info = f"{rec['map_name']} [{rec.get('status','IN_PROGRESS')}] (Mode: {rec.get('game_mode','long_mode').upper()})\nBoss: {rec.get('commander_name')} | Highlights: {len(rec.get('photos',[]))}"
                tk.Label(row, text=info, fg="white", bg="#161f2c", justify=tk.LEFT, font=("Segoe UI", 9)).pack(side=tk.LEFT)
                tk.Button(row, text="▶️ Play", command=lambda r=rec: (self.load_map_record(r, prompt_players=(not self.players)), self.update_ui(), win.destroy()), bg="#1f6feb", fg="white").pack(side=tk.RIGHT, padx=4)
                if mid != "classic_culantro":
                    tk.Button(row, text="🗑️ Delete", command=lambda m=mid: (delete_map_record(m), populate_rows()), bg="#da3633", fg="white").pack(side=tk.RIGHT, padx=4)

        populate_rows()
        if startup and not self.players:
            win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), self.prompt_player_setup()))

    def open_photo_album_dialog(self):
        win = tk.Toplevel(self.root)
        win.title(f"📸 Highlights B-Roll — {self.map_name}")
        win.geometry("700x480")
        win.configure(bg="#131c27")
        tk.Label(win, text=f"📸 Highlights B-Roll ({len(self.photos)} Captures)", fg="#ffd166", bg="#131c27", font=("Segoe UI", 13, "bold")).pack(pady=8)
        box = tk.Text(win, bg="#0d131a", fg="#e6edf3", font=("Consolas", 10), height=17, padx=10, pady=10)
        box.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)
        if not self.photos:
            box.insert(tk.END, "No B-Roll highlights captured yet!")
        else:
            for ph in self.photos:
                box.insert(tk.END, f"====================================================\n")
                box.insert(tk.END, f"Capture #{ph['id']} | {ph['stars']} | Round {ph['round']} ({ph['timestamp']})\n")
                box.insert(tk.END, f"TITLE:   {ph['title']}\n")
                box.insert(tk.END, f"CAPTION: {ph['caption']}\n")
                box.insert(tk.END, f"WATERMARK: © {ph['watermark']}\n")
        box.config(state=tk.DISABLED)

    def prompt_player_setup(self):
        count = simpledialog.askinteger("Player Count", "How many players (2 to 6)?", minvalue=2, maxvalue=6, initialvalue=4) or 4
        self.players = []
        for i in range(count):
            name = simpledialog.askstring("Player Name", f"Enter name for Player {i+1}:", initialvalue=f"Trainer {i+1}") or f"Trainer {i+1}"
            role = ROLES_LIST[i % len(ROLES_LIST)]
            starter = random.choice(WILD_POKEDEX_150["Florio"][:4])
            self.players.append({
                "name": name, "role": role, "node": 0, "moves": 0, "rolled": False,
                "team": [{"name": starter["name"], "bp": starter["bp"], "level": 1, "exp": 0, "evolves_to": starter.get("evolves_to"), "fainted": False}],
                "items": ["Grounding Anchor"]
            })
        self.turn_idx = 0
        self.update_ui()

    def current_player(self):
        return self.players[self.turn_idx]

    def roll_die(self):
        p = self.current_player()
        if p["rolled"]:
            return
        r = random.randint(1, 6)
        bonus = 2 if "Runner" in p["role"] else 0
        p["moves"] = r + bonus
        p["rolled"] = True
        self.lbl_banner.config(text=f"{p['name']} rolled a {r}" + (f" (+2 Runner = {p['moves']})!" if bonus else "!"))
        self.update_ui()

    def on_canvas_click(self, event):
        if not self.players:
            return
        p = self.current_player()
        if p["moves"] <= 0:
            return
        for nid, nd in self.nodes.items():
            if ((event.x - nd["x"])**2 + (event.y - nd["y"])**2) ** 0.5 <= 26:
                if nid in self.nodes[p["node"]]["edges"]:
                    p["node"] = nid
                    p["moves"] -= 1
                    if nd["type"] == "outpost":
                        for pk in p["team"]:
                            pk["fainted"] = False
                        if len(p["items"]) < 5:
                            p["items"].append("Grounding Anchor")
                        self.lbl_banner.config(text=f"{p['name']} resupplied at {nd['name']}!")
                    self.save_current_session()
                    self.update_ui()
                break

    def wild_action(self, mode):
        p = self.current_player()
        nd = self.nodes[p["node"]]
        if nd["type"] != "wild":
            return
        w = random.choice(WILD_POKEDEX_150.get(nd["region"], WILD_POKEDEX_150["Florio"]))
        if mode == "catch":
            if len(p["team"]) < 3:
                p["team"].append({"name": w["name"], "bp": w["bp"], "level": 1, "exp": 0, "evolves_to": w.get("evolves_to"), "fainted": False})
                self.lbl_banner.config(text=f"{p['name']} partnered up with wild {w['name']}!")
            else:
                self.lbl_banner.config(text="Team is full (Max 3 partners)!")
        else:
            active = p["team"][0]
            active["exp"] += 15
            self.lbl_banner.config(text=f"{active['name']} defeated wild {w['name']} and gained 15 EXP!")
            if active["exp"] >= 25 and active.get("evolves_to"):
                old = active["name"]
                evo = active["evolves_to"]
                active["name"] = evo["name"]
                active["bp"] = evo["bp"]
                active["evolves_to"] = evo.get("evolves_to")
                active["exp"] = 0
                self.snap_photo(f"EVOLUTION: {old} -> {active['name']}!", f"{p['name']} evolved {old} into {active['name']}!", "★★★ GOLD", p["name"])
        self.save_current_session()
        self.update_ui()

    def fight_boss(self):
        p = self.current_player()
        nd = self.nodes[p["node"]]
        boss = nd.get("syndicate_boss") or nd.get("boss")
        if not boss or boss.get("defeated"):
            return
        total_bp = sum(pk["bp"] for pk in p["team"] if not pk["fainted"])
        enemy_bp = float(boss["bp"])
        won = random.random() <= (total_bp / (total_bp + enemy_bp))
        if won:
            boss["defeated"] = True
            if nd.get("syndicate_boss"):
                nd["syndicate_boss"] = None
            self.snap_photo(f"DEFEATED {boss['name'].upper()}!", f"{p['name']} defeated {boss['name']}!", "★★★★ DIAMOND", p["name"])
            messagebox.showinfo("VICTORY!", f"You defeated {boss['name']}!")
        else:
            for pk in p["team"]:
                pk["fainted"] = True
            self.lbl_banner.config(text=f"{boss['name']} overpowered your team!")
        self.save_current_session()
        self.update_ui()

    def next_turn(self):
        self.turn_idx = (self.turn_idx + 1) % len(self.players)
        if self.turn_idx == 0:
            self.round_num += 1
            for pl in self.players:
                pl["rolled"] = False
                pl["moves"] = 0
        self.save_current_session()
        self.update_ui()

    def update_ui(self):
        if not self.players:
            return
        p = self.current_player()
        self.lbl_turn.config(text=f"{self.map_name} | ROUND {self.round_num} | TURN: {p['name']}")
        roster_txt = "\n\n".join([
            f"{'-> ' if idx==self.turn_idx else ''}{pl['name']}\n" + "".join([f"   • {pk['name']} (BP {pk['bp']}{' KO' if pk['fainted'] else ''})\n" for pk in pl["team"]]) + f"   📍 {self.nodes[pl['node']]['name']} | Steps: {pl['moves']}"
            for idx, pl in enumerate(self.players)
        ])
        self.lbl_stats.config(text=roster_txt)
        self.draw_map()

    def draw_map(self):
        self.canvas.delete("all")
        for nid, nd in self.nodes.items():
            for edge in nd["edges"]:
                t = self.nodes.get(edge)
                if t:
                    self.canvas.create_line(nd["x"], nd["y"], t["x"], t["y"], fill="#48cae4", width=2)
        for nid, nd in self.nodes.items():
            boss = nd.get("boss")
            color = "#1f6feb" if nd["type"] == "outpost" else ("#6e40c9" if nd["type"] == "wild" else "#d29922")
            if boss and boss.get("calmed"):
                color = "#238636"
            elif nd["type"] == "poacher_base":
                color = "#da3633"
            r = 20
            self.canvas.create_oval(nd["x"]-r, nd["y"]-r, nd["x"]+r, nd["y"]+r, fill=color, outline="white", width=2)
            label = f"{nd['name']}" + (f" ({boss['name']})" if boss else "")
            self.canvas.create_text(nd["x"], nd["y"]-26, text=label, fill="white", font=("Segoe UI", 8, "bold"))
        for idx, pl in enumerate(self.players):
            nd = self.nodes[pl["node"]]
            ox = nd["x"] - 14 + (idx * 7)
            self.canvas.create_oval(ox-5, nd["y"]-5, ox+5, nd["y"]+5, fill="#3fb950", outline="white")

if __name__ == "__main__":
    root = tk.Tk()
    app = CulantroOfflineGame(root)
    root.mainloop()
              
