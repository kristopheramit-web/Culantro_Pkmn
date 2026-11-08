# lental_boss_data.py
# Contains the 62 Illumina Pokemon (BST > 520), 6 Casino Syndicate Bosses (3-Pokemon Teams), and Radio Comms.

ILLUMINA_POOL_60 = [
    # Original 6 Lental Classics (BST 525 - 680)
    {"id": 154, "name": "Meganium", "bst": 525, "type": "Grass", "sprite": "/assets/illumina/illumina_154.png"},
    {"id": 350, "name": "Milotic", "bst": 540, "type": "Water", "sprite": "/assets/illumina/illumina_350.png"},
    {"id": 10127, "name": "Wishiwashi (School)", "bst": 620, "type": "Water", "sprite": "/assets/illumina/illumina_10127.png"},
    {"id": 637, "name": "Volcarona", "bst": 550, "type": "Fire", "sprite": "/assets/illumina/illumina_637.png"},
    {"id": 208, "name": "Steelix (Mega-Glow)", "bst": 610, "type": "Steel", "sprite": "/assets/illumina/illumina_208.png"},
    {"id": 716, "name": "Xerneas", "bst": 680, "type": "Fairy", "sprite": "/assets/illumina/illumina_716.png"},
    # Gen 1 Apex & Legends
    {"id": 6, "name": "Charizard", "bst": 534, "type": "Fire", "sprite": "/assets/illumina/illumina_6.png"},
    {"id": 9, "name": "Blastoise", "bst": 530, "type": "Water", "sprite": "/assets/illumina/illumina_9.png"},
    {"id": 59, "name": "Arcanine", "bst": 555, "type": "Fire", "sprite": "/assets/illumina/illumina_59.png"},
    {"id": 130, "name": "Gyarados", "bst": 540, "type": "Water", "sprite": "/assets/illumina/illumina_130.png"},
    {"id": 131, "name": "Lapras", "bst": 535, "type": "Ice", "sprite": "/assets/illumina/illumina_131.png"},
    {"id": 143, "name": "Snorlax", "bst": 540, "type": "Normal", "sprite": "/assets/illumina/illumina_143.png"},
    {"id": 149, "name": "Dragonite", "bst": 600, "type": "Dragon", "sprite": "/assets/illumina/illumina_149.png"},
    {"id": 150, "name": "Mewtwo", "bst": 680, "type": "Psychic", "sprite": "/assets/illumina/illumina_150.png"},
    # Gen 2 - Gen 3 Apex & Legends
    {"id": 248, "name": "Tyranitar", "bst": 600, "type": "Rock", "sprite": "/assets/illumina/illumina_248.png"},
    {"id": 249, "name": "Lugia", "bst": 680, "type": "Psychic", "sprite": "/assets/illumina/illumina_249.png"},
    {"id": 250, "name": "Ho-Oh", "bst": 680, "type": "Fire", "sprite": "/assets/illumina/illumina_250.png"},
    {"id": 373, "name": "Salamence", "bst": 600, "type": "Dragon", "sprite": "/assets/illumina/illumina_373.png"},
    {"id": 376, "name": "Metagross", "bst": 600, "type": "Steel", "sprite": "/assets/illumina/illumina_376.png"},
    {"id": 384, "name": "Rayquaza", "bst": 680, "type": "Dragon", "sprite": "/assets/illumina/illumina_384.png"},
    {"id": 445, "name": "Garchomp", "bst": 600, "type": "Ground", "sprite": "/assets/illumina/illumina_445.png"},
    {"id": 635, "name": "Hydreigon", "bst": 600, "type": "Dark", "sprite": "/assets/illumina/illumina_635.png"},
    {"id": 983, "name": "Kingambit", "bst": 550, "type": "Dark", "sprite": "/assets/illumina/illumina_983.png"},
    {"id": 998, "name": "Baxcalibur", "bst": 600, "type": "Dragon", "sprite": "/assets/illumina/illumina_998.png"},
    {"id": 1005, "name": "Roaring Moon", "bst": 590, "type": "Dragon", "sprite": "/assets/illumina/illumina_1005.png"},
]

GRUNT_RADIO_INTRO = [
    {"sender": "Grunt 1 [RADIO INTERCEPT]", "msg": "I have managed to intercept the radio frequency of the group exploring the Culantro Region."},
    {"sender": "Grunt 2 [RADIO INTERCEPT]", "msg": "Good. The syndicate wants to make it clear what we do to trespassers."},
    {"sender": "Grunt 1 [RADIO INTERCEPT]", "msg": "Locking onto their transponders. Let's agitate the Illumina targets!"}
]

ILLUMINA_CALM_RADIO_TAUNTS = {
    1: [{"sender": "Grunt 1 [RADIO INTERCEPT]", "msg": "Wait... they actually calmed the first Illumina Pokémon?!"}],
    2: [{"sender": "Grunt 2 [RADIO INTERCEPT]", "msg": "Another sanctuary has gone quiet! Command, are you seeing this?"}],
    3: [
        {"sender": "Grunt 1 [RADIO INTERCEPT]", "msg": "That's THREE Illumina targets cleansed!"},
        {"sender": "Lt. Deuce [RADIO INTERCEPT]", "msg": "Grunts, intercept them head-on! Nobody compromises our profits!"}
    ],
    4: [{"sender": "Chief J.Pot [RADIO INTERCEPT]", "msg": "Four sanctuaries back online?! Marshall Ace, get your weapons ready!"}],
    5: [{"sender": "Baron Roulette [RADIO INTERCEPT]", "msg": "Let them reach the final sanctuary. Our trap at the Amplification Star citadel is set."}]
}

CASINO_BOSSES = {
    "Boss_Captain_B.Jack": {
        "id": "Boss_Captain_B.Jack", "name": "Captain B.Jack", "full_title": "Captain Black Jack", "tier": 1,
        "sprite": "/assets/poachers/Boss_Captain_B.Jack.png",
        "appearance": "Heavy black-and-olive combat military attire with tactical webbing and a beret.",
        "team": [
            {"name": "Kingambit", "bp": 16, "type": "Steel", "sprite": "/assets/illumina/illumina_983.png"},
            {"name": "Hydreigon", "bp": 18, "type": "Dark", "sprite": "/assets/illumina/illumina_635.png"},
            {"name": "Tyranitar", "bp": 20, "type": "Rock", "sprite": "/assets/illumina/illumina_248.png"},
        ],
        "dialogue": {
            "intro": "Captain B.Jack: You calmed the Illumina Pokémon? For interfering with our military operation, I will make you pay!",
            "next_poke": "Captain B.Jack: My hand is still sitting on twenty-one! Send in the next unit!",
            "defeat": "Captain B.Jack: Bust...?! Fall back to high command!"
        }
    },
    "Boss_Lt._Deuce": {
        "id": "Boss_Lt._Deuce", "name": "Lt. Deuce", "full_title": "Lieutenant Deuce", "tier": 1,
        "sprite": "/assets/poachers/Boss_Lt._Deuce.png",
        "appearance": "Sharp desert-spec combat military fatigues, ballistic goggles, and dual shoulder holsters.",
        "team": [
            {"name": "Haxorus", "bp": 15, "type": "Dragon", "sprite": "/assets/illumina/illumina_635.png"},
            {"name": "Metagross", "bp": 18, "type": "Steel", "sprite": "/assets/illumina/illumina_376.png"},
            {"name": "Salamence", "bp": 20, "type": "Dragon", "sprite": "/assets/illumina/illumina_373.png"},
        ],
        "dialogue": {
            "intro": "Lt. Deuce: You disrupted our lures, so my strike squad is wiping your team off the map!",
            "next_poke": "Lt. Deuce: Double down—deploying my next armored unit!",
            "defeat": "Lt. Deuce: My perimeter is breached!"
        }
    },
    "Boss_Chief_J.Pot": {
        "id": "Boss_Chief_J.Pot", "name": "Chief J.Pot", "full_title": "Chief Jackpot", "tier": 1,
        "sprite": "/assets/poachers/Boss_Chief_J.Pot.png",
        "appearance": "Gold-trimmed syndicate riot armor with a heavy utility trench coat.",
        "team": [
            {"name": "Aggron", "bp": 16, "type": "Steel", "sprite": "/assets/illumina/illumina_208.png"},
            {"name": "Kommo-o", "bp": 18, "type": "Fighting", "sprite": "/assets/illumina/illumina_635.png"},
            {"name": "Garchomp", "bp": 20, "type": "Ground", "sprite": "/assets/illumina/illumina_445.png"},
        ],
        "dialogue": {
            "intro": "Chief J.Pot: Every Illumina Pokémon you calmed cost me millions—cashing out on your hides!",
            "next_poke": "Chief J.Pot: Let's raise the stakes!",
            "defeat": "Chief J.Pot: My vault is dry?!"
        }
    },
    "Boss_Marshall_Ace": {
        "id": "Boss_Marshall_Ace", "name": "Marshall Ace", "full_title": "Marshall Ace", "tier": 2,
        "sprite": "/assets/poachers/Boss_Marshall_Ace.png",
        "appearance": "Towering brawler wearing woodland camo trousers and a tight white singlet accentuating his muscles.",
        "team": [
            {"name": "Slaking", "bp": 18, "type": "Normal", "sprite": "/assets/illumina/illumina_143.png"},
            {"name": "Baxcalibur", "bp": 20, "type": "Ice", "sprite": "/assets/illumina/illumina_998.png"},
            {"name": "Roaring Moon", "bp": 22, "type": "Dragon", "sprite": "/assets/illumina/illumina_1005.png"},
        ],
        "dialogue": {
            "intro": "Marshall Ace: You flattened our field officers? Step up and face raw muscle!",
            "next_poke": "Marshall Ace: Let's see your bones handle this beast!",
            "defeat": "Marshall Ace: Nobody out-muscles an Ace!"
        }
    },
    "Boss_Baron_Roulette": {
        "id": "Boss_Baron_Roulette", "name": "Baron Roulette", "full_title": "Baron Roulette", "tier": 2,
        "sprite": "/assets/poachers/Boss_Baron_Roulette.png",
        "appearance": "Modern rich aristocrat in a tailored crimson velvet suit, silk cravat, and platinum cufflinks.",
        "team": [
            {"name": "Goodra", "bp": 18, "type": "Dragon", "sprite": "/assets/illumina/illumina_373.png"},
            {"name": "Volcarona", "bp": 20, "type": "Fire", "sprite": "/assets/illumina/illumina_637.png"},
            {"name": "Dragapult", "bp": 22, "type": "Ghost", "sprite": "/assets/illumina/illumina_384.png"},
        ],
        "dialogue": {
            "intro": "Baron Roulette: Red or black—your luck ends on this spin.",
            "next_poke": "Baron Roulette: Allow me to place a far deadlier wager!",
            "defeat": "Baron Roulette: Preposterous! My calculations were flawless!"
        }
    },
    "Boss_Warden_Croupier": {
        "id": "Boss_Warden_Croupier", "name": "Warden Croupier", "full_title": "Supreme Warden Croupier", "tier": 3,
        "sprite": "/assets/poachers/Boss_Warden_Croupier.png",
        "appearance": "Battle-scarred senior warlord with thick iron-grey facial hair and a scarred trench coat.",
        "team": [
            {"name": "Tyranitar (Apex)", "bp": 21, "type": "Rock", "sprite": "/assets/illumina/illumina_248.png"},
            {"name": "Garchomp (Apex)", "bp": 23, "type": "Ground", "sprite": "/assets/illumina/illumina_445.png"},
            {"name": "Rayquaza (Shackled)", "bp": 26, "type": "Dragon", "sprite": "/assets/illumina/illumina_384.png"},
        ],
        "dialogue": {
            "intro": "Warden Croupier: LISTEN TO ME, YOU INSECTS. You ruined years of extraction. There will be no mercy!",
            "next_poke": "Warden Croupier: YOU THINK BLEEDING ONE TITAN MEANS ANYTHING?!",
            "defeat": "Warden Croupier: CURSE YOU ALL! My empire... slipping away...!"
        }
    }
}
