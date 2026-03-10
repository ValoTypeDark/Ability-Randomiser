"""
Pokémon Ability Randomizer  –  with live theme switching
─────────────────────────────────────────────────────────
Abilities are loaded from  data/abilities.json  (relative to this script).
Run with --update-abilities to fetch fresh data from PokéAPI.
The app works fully offline once the cache exists.
"""

import json
import os
import random
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.request import urlopen, Request

try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.path.join(SCRIPT_DIR, "data")
ABILITIES_FILE = os.path.join(DATA_DIR, "abilities.json")
SETTINGS_FILE  = os.path.join(DATA_DIR, "settings.json")
AVATAR_FILE    = os.path.join(DATA_DIR, "avatar.png")
os.makedirs(DATA_DIR, exist_ok=True)

APP_TITLE    = "Pokémon Ability Randomizer"
POKEAPI_BASE = "https://pokeapi.co/api/v2"

VERSION    = "1.0.0"
GITHUB_API = "https://api.github.com/repos/ValoTypeDark/Ability-Randomiser/releases/latest"
GITHUB_RAW = "https://raw.githubusercontent.com/ValoTypeDark/Ability-Randomiser/refs/heads/main/pokemon_ability_randomizer.py"

GENERATIONS = ["GEN III", "GEN IV", "GEN V", "GEN VI", "GEN VII", "GEN VIII", "GEN IX"]
GEN_ORDER   = {g: i for i, g in enumerate(GENERATIONS)}

POKEAPI_GEN_MAP = {
    "generation-iii":  "GEN III", "generation-iv":   "GEN IV",
    "generation-v":    "GEN V",   "generation-vi":   "GEN VI",
    "generation-vii":  "GEN VII", "generation-viii": "GEN VIII",
    "generation-ix":   "GEN IX",
}

GAME_PRESETS = {
    "Ruby / Sapphire / Emerald":         "GEN III",
    "FireRed / LeafGreen":               "GEN III",
    "Diamond / Pearl / Platinum":        "GEN IV",
    "HeartGold / SoulSilver":            "GEN IV",
    "Black / White":                     "GEN V",
    "Black 2 / White 2":                 "GEN V",
    "X / Y":                             "GEN VI",
    "Omega Ruby / Alpha Sapphire":       "GEN VI",
    "Sun / Moon":                        "GEN VII",
    "Ultra Sun / Ultra Moon":            "GEN VII",
    "Sword / Shield":                    "GEN VIII",
    "Brilliant Diamond / Shining Pearl": "GEN IV",
    "Scarlet / Violet":                  "GEN IX",
    "Custom":                            None,
}

# Fixed per-generation colours (look good on every theme)
GEN_COLORS = {
    "GEN III": "#ff6b6b", "GEN IV": "#ffa94d", "GEN V":  "#ffe066",
    "GEN VI":  "#69db7c", "GEN VII": "#4dabf7", "GEN VIII": "#cc5de8",
    "GEN IX":  "#f783ac",
}

# ══════════════════════════════════════════════════════════════════════════════
#  Themes
#  Each theme is a flat colour-role → hex dict.  Roles:
#    bg_root/panel/field/result/banned  – backgrounds
#    fg_main/sub/accent1/accent2/accent3/banned  – foregrounds
#    roll_bg/hover  – roll button
#    profile_bg/rim  – profile card
# ══════════════════════════════════════════════════════════════════════════════

def _theme(bg_root, bg_panel, bg_field, bg_result, bg_banned,
           fg_main, fg_sub, acc1, acc2, acc3, fg_banned,
           roll_bg, roll_hover, profile_bg, profile_rim):
    """Build a theme dict from positional values."""
    return dict(
        bg_root=bg_root, bg_panel=bg_panel, bg_field=bg_field,
        bg_result=bg_result, bg_banned=bg_banned,
        fg_main=fg_main, fg_sub=fg_sub,
        fg_accent1=acc1, fg_accent2=acc2, fg_accent3=acc3, fg_banned=fg_banned,
        roll_bg=roll_bg, roll_hover=roll_hover,
        profile_bg=profile_bg, profile_rim=profile_rim,
    )

THEMES = {
    "Pokédex (Default)": _theme(
        "#1a1a2e", "#0f3460", "#16213e", "#071a2e", "#3a0a0a",
        "#f0f0f0", "#a0a8b8", "#f5a623", "#4fc3f7", "#f5a623", "#ff6b6b",
        "#e94560", "#c73048", "#0a2040", "#f5a623"),
    "🔥 Charizard": _theme(
        "#1a0800", "#2a1200", "#2a1200", "#0e0600", "#3a0000",
        "#fff0d0", "#c8956a", "#ff9500", "#ffcc44", "#ff9500", "#ff5555",
        "#cc3300", "#aa2200", "#1a0800", "#ff9500"),
    "🌿 Bulbasaur": _theme(
        "#0a1a0a", "#193519", "#112211", "#060e06", "#2a0808",
        "#e8f5e0", "#80b870", "#7ecf3f", "#b0e870", "#7ecf3f", "#ff7070",
        "#3a8c10", "#2d7008", "#081208", "#7ecf3f"),
    "💧 Blastoise": _theme(
        "#031520", "#0b3550", "#072030", "#020c18", "#2a0808",
        "#d8f4ff", "#6aadcc", "#30c0e0", "#80dff5", "#30c0e0", "#ff7070",
        "#0878b8", "#0660a0", "#021020", "#30c0e0"),
    "👻 Gengar": _theme(
        "#100618", "#280e40", "#1c0a2e", "#080010", "#2e0030",
        "#f0e0ff", "#9070b8", "#c060e8", "#e0a8ff", "#c060e8", "#ff6060",
        "#7818b8", "#6010a0", "#0c0418", "#c060e8"),
    "⚡ Pikachu": _theme(
        "#181400", "#3a3000", "#262000", "#0e0c00", "#2a0808",
        "#fff8cc", "#b8a840", "#f8d800", "#ffe860", "#f8d800", "#ff6060",
        "#c89800", "#a87800", "#121000", "#f8d800"),
    "❄️ Glaceon": _theme(
        "#060e18", "#102038", "#0a1828", "#04080e", "#2a0000",
        "#d8f0ff", "#7098b8", "#80d8ff", "#b8ecff", "#80d8ff", "#ff8888",
        "#2890c0", "#1878a8", "#040a14", "#80d8ff"),
    "🌙 Umbreon": _theme(
        "#080808", "#141414", "#0e0e0e", "#040404", "#280000",
        "#e8e8e8", "#707070", "#f8c800", "#3898d8", "#f8c800", "#ff6060",
        "#2060a0", "#184880", "#060606", "#f8c800"),
    "🌸 Sylveon": _theme(
        "#1e0818", "#3c1430", "#2a0e22", "#100510", "#2a0808",
        "#ffe8f8", "#c888b8", "#ff80c0", "#80d0ff", "#ff80c0", "#ff6060",
        "#c83080", "#a82060", "#180510", "#ff80c0"),
    "🖤 Team Rocket": _theme(
        "#0a0a0a", "#1a1a1a", "#111111", "#050505", "#200000",
        "#ffffff", "#888888", "#cc0000", "#ff4444", "#cc0000", "#ff6666",
        "#880000", "#660000", "#080808", "#cc0000"),
}

THEME_NAMES = list(THEMES.keys())


# ══════════════════════════════════════════════════════════════════════════════
#  PokeAPI helpers
# ══════════════════════════════════════════════════════════════════════════════

def _api_get(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "PokemonAbilityRandomizer/2.0"})
    with urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def fetch_all_abilities(progress_cb=None) -> list:
    index   = _api_get(f"{POKEAPI_BASE}/ability?limit=10000")
    entries = index["results"]
    total   = len(entries)
    abilities = []
    for i, entry in enumerate(entries, 1):
        try:
            data       = _api_get(entry["url"])
            generation = POKEAPI_GEN_MAP.get(data.get("generation", {}).get("name", ""))
            if generation is None:
                continue
            effect_text = "No effect description available."
            for ent in data.get("effect_entries", []):
                if ent.get("language", {}).get("name") == "en":
                    effect_text = ent.get("short_effect") or ent.get("effect", effect_text)
                    break
            display_name = entry["name"].replace("-", " ").title()
            for name_entry in data.get("names", []):
                if name_entry.get("language", {}).get("name") == "en":
                    display_name = name_entry["name"]
                    break
            abilities.append({
                "name": entry["name"], "display_name": display_name,
                "effect": effect_text, "generation": generation,
                "is_main_series": data.get("is_main_series", False),
            })
        except Exception:
            pass
        if progress_cb:
            progress_cb(i, total, entry["name"])
    abilities.sort(key=lambda a: a["display_name"].lower())
    return abilities


def save_abilities_json(abilities: list):
    with open(ABILITIES_FILE, "w", encoding="utf-8") as f:
        json.dump({"version": 2, "source": "PokeAPI",
                   "count": len(abilities), "abilities": abilities},
                  f, ensure_ascii=False, indent=2)


def load_abilities_json() -> list:
    if not os.path.exists(ABILITIES_FILE):
        return []
    with open(ABILITIES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("abilities", [])


# ══════════════════════════════════════════════════════════════════════════════
#  Main application
# ══════════════════════════════════════════════════════════════════════════════

class AbilityRandomizerApp:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x820")
        self.root.minsize(900, 600)

        self.abilities:          list = []
        self.filtered_abilities: list = []
        self.banned_abilities:   set  = set()
        self._rolled:            list = []
        self._user_name               = ""
        self._avatar_photo            = None

        self._theme_name = THEME_NAMES[0]
        self._t          = THEMES[self._theme_name]
        self._tw:        list = []   # [(widget, role), …] theme registry

        self.status_var           = tk.StringVar(value="Loading abilities…")
        self.draw_count_var       = tk.IntVar(value=3)
        self.search_var           = tk.StringVar()
        self.custom_ban_var       = tk.StringVar()
        self.include_banned_var   = tk.BooleanVar(value=False)
        self.main_series_only_var = tk.BooleanVar(value=True)
        self.generation_vars      = {g: tk.BooleanVar(value=True) for g in GENERATIONS}
        self.game_var             = tk.StringVar(value="Custom")
        self.theme_var            = tk.StringVar(value=self._theme_name)

        self._build_ui()
        self._apply_theme()
        self._load_abilities()
        self._load_settings()
        self._update_status()
        self._refresh_ability_views()
        self.root.after(100, self._maybe_first_launch)
        self.root.after(1500, self._check_for_update)

    # ══════════════════════════════════════════════════════════════════════════
    #  Theme engine
    # ══════════════════════════════════════════════════════════════════════════

    def _r(self, widget, role: str):
        """Register widget with a colour role and return it."""
        self._tw.append((widget, role))
        return widget

    def _switch_theme(self, _event=None):
        name = self.theme_var.get()
        if name in THEMES:
            self._theme_name = name
            self._t = THEMES[name]
            self._apply_theme()
            self._save_settings()

    def _apply_theme(self):
        t = self._t
        self.root.configure(bg=t["bg_root"])

        # Helpers for common button patterns
        def _btn(bg_key, fg_key, act_bg_key=None, act_fg_key="bg_root"):
            act_bg = t[act_bg_key or bg_key]
            return dict(bg=t[bg_key], fg=t[fg_key],
                        activebackground=act_bg, activeforeground=t[act_fg_key])

        for w, role in self._tw:
            try:
                if   role == "bg_root":         w.configure(bg=t["bg_root"])
                elif role == "bg_panel":        w.configure(bg=t["bg_panel"])
                elif role == "lbl_title":       w.configure(bg=t["bg_root"],  fg=t["fg_accent1"])
                elif role == "lbl_status":      w.configure(bg=t["bg_root"],  fg=t["fg_accent2"])
                elif role == "lbl_theme":       w.configure(bg=t["bg_root"],  fg=t["fg_sub"])
                elif role == "lbl_main":        w.configure(bg=t["bg_panel"], fg=t["fg_main"])
                elif role == "lbl_sub":         w.configure(bg=t["bg_panel"], fg=t["fg_sub"])
                elif role == "lbl_detail_title":w.configure(bg=t["bg_panel"], fg=t["fg_accent2"])
                elif role == "lf_accent1":      w.configure(bg=t["bg_panel"], fg=t["fg_accent1"])
                elif role == "lf_accent2":      w.configure(bg=t["bg_panel"], fg=t["fg_accent2"])
                elif role == "lf_banned":       w.configure(bg=t["bg_panel"], fg=t["fg_banned"])
                elif role == "lf_result":       w.configure(bg=t["bg_panel"], fg=t["fg_accent1"])
                elif role == "field":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"],
                                insertbackground=t["fg_main"])
                elif role == "field_search":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"],
                                insertbackground=t["fg_main"],
                                highlightbackground=t["fg_accent2"], highlightthickness=1)
                elif role == "field_ban":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"],
                                insertbackground=t["fg_main"],
                                highlightbackground=t["fg_banned"], highlightthickness=1)
                elif role == "spinbox":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"],
                                buttonbackground=t["bg_field"],
                                highlightbackground=t["fg_accent2"], highlightthickness=1)
                elif role == "listbox":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"],
                                selectbackground=t["fg_accent2"],
                                selectforeground=t["bg_root"])
                elif role == "listbox_banned":
                    w.configure(bg=t["bg_banned"], fg=t["fg_banned"],
                                selectbackground=t["fg_banned"],
                                selectforeground=t["bg_root"])
                elif role == "scrollbar":
                    w.configure(bg=t["bg_panel"], troughcolor=t["bg_field"])
                elif role == "btn_roll":
                    w.configure(**_btn("roll_bg", "fg_main", "roll_hover", "fg_main"))
                elif role == "btn_accent1":
                    w.configure(**_btn("bg_field", "fg_accent1", "fg_accent1"))
                elif role == "btn_accent2":
                    w.configure(**_btn("bg_field", "fg_accent2", "fg_accent2"))
                elif role == "btn_banned":
                    w.configure(**_btn("bg_field", "fg_banned", "fg_banned"))
                elif role == "btn_unban":
                    w.configure(bg=t["bg_field"], fg="#69db7c",
                                activebackground="#69db7c",
                                activeforeground=t["bg_root"])
                elif role == "btn_small":
                    w.configure(**_btn("bg_field", "fg_main", "fg_accent2"))
                elif role == "btn_dramatic":
                    w.configure(**_btn("profile_bg", "fg_accent1", "fg_accent1"))
                elif role == "check":
                    w.configure(bg=t["bg_panel"], fg=t["fg_main"],
                                selectcolor=t["bg_field"],
                                activebackground=t["bg_panel"],
                                activeforeground=t["fg_main"])
                elif role == "check_gen":
                    w.configure(bg=t["bg_panel"], selectcolor=t["bg_field"],
                                activebackground=t["bg_panel"])
                elif role == "result_text":
                    w.configure(bg=t["bg_result"], fg=t["fg_main"])
                    w.tag_configure("header",       foreground=t["fg_accent1"])
                    w.tag_configure("ability_name", foreground=t["fg_accent2"])
                    w.tag_configure("gen_tag",      foreground=t["fg_accent3"])
                    w.tag_configure("effect_text",  foreground=t["fg_main"])
                    w.tag_configure("divider",      foreground=t["bg_panel"])
                    w.tag_configure("meta",         foreground=t["fg_sub"])
                elif role == "detail_text":
                    w.configure(bg=t["bg_field"], fg=t["fg_main"])
                    w.tag_configure("key",          foreground=t["fg_accent3"])
                    w.tag_configure("val",          foreground=t["fg_main"])
                    w.tag_configure("banned_val",   foreground=t["fg_banned"])
                    w.tag_configure("effect_label", foreground=t["fg_accent2"])
                elif role == "profile_card":    w.configure(bg=t["profile_bg"])
                elif role == "lbl_welcome":     w.configure(bg=t["profile_bg"], fg=t["fg_accent1"])
                elif role == "lbl_welcome_sub": w.configure(bg=t["profile_bg"], fg=t["fg_sub"])
            except tk.TclError:
                pass

        # Re-colour banned rows in the ability listbox
        for idx, ability in enumerate(self.filtered_abilities):
            try:
                banned = ability["name"] in self.banned_abilities
                self.ability_listbox.itemconfig(
                    idx,
                    fg=t["fg_banned"] if banned else t["fg_main"],
                    bg=t["bg_banned"] if banned else t["bg_field"])
            except Exception:
                pass

        try:
            self._draw_avatar()
        except AttributeError:
            pass

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TCombobox",
                        fieldbackground=t["bg_field"], background=t["bg_field"],
                        foreground=t["fg_main"],
                        selectbackground=t["bg_field"], selectforeground=t["fg_main"],
                        arrowcolor=t["fg_main"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", t["bg_field"])],
                  foreground=[("readonly", t["fg_main"])],
                  selectbackground=[("readonly", t["bg_field"])],
                  selectforeground=[("readonly", t["fg_main"])])

    # ══════════════════════════════════════════════════════════════════════════
    #  Build UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self.root.columnconfigure(0, weight=0, minsize=315)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._build_header()

        left = self._r(tk.Frame(self.root), "bg_root")
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 4), pady=(0, 12))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)

        right = self._r(tk.Frame(self.root), "bg_root")
        right.grid(row=1, column=1, sticky="nsew", padx=(4, 12), pady=(0, 12))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=2)
        right.rowconfigure(2, weight=3)

        self._build_game_selector(left)
        self._build_roll_settings(left)
        self._build_ban_panel(left)
        self._build_profile_card(right)
        self._build_results_panel(right)
        self._build_ability_browser(right)

    def _build_header(self):
        hdr = self._r(tk.Frame(self.root, pady=10), "bg_root")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16)

        self._r(tk.Label(hdr, text="⚡ Pokémon Ability Randomizer",
                         font=("Segoe UI", 20, "bold")),
                "lbl_title").pack(side="left")

        theme_row = self._r(tk.Frame(hdr), "bg_root")
        theme_row.pack(side="left", padx=(20, 0))
        self._r(tk.Label(theme_row, text="Theme:", font=("Segoe UI", 9)),
                "lbl_theme").pack(side="left", padx=(0, 5))
        cb = ttk.Combobox(theme_row, textvariable=self.theme_var,
                          values=THEME_NAMES, state="readonly",
                          width=17, font=("Segoe UI", 9))
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", self._switch_theme)

        self._r(tk.Label(hdr, textvariable=self.status_var,
                         font=("Segoe UI", 9, "italic")),
                "lbl_status").pack(side="right", padx=8)

    def _build_game_selector(self, parent):
        pf = self._r(
            tk.LabelFrame(parent, text=" 🎮  Game Preset ",
                          font=("Segoe UI", 10, "bold"), relief="solid", bd=1, padx=10, pady=8),
            "lf_accent1")
        pf.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        pf.columnconfigure(0, weight=1)

        self._r(tk.Label(pf, text="Select your game to auto-set generations:",
                         font=("Segoe UI", 9)), "lbl_sub").grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(pf, textvariable=self.game_var,
                          values=list(GAME_PRESETS.keys()), state="readonly", width=30)
        cb.grid(row=1, column=0, sticky="ew", pady=(6, 6))
        cb.bind("<<ComboboxSelected>>", self._on_game_selected)

        self.update_btn = self._r(
            tk.Button(pf, text="🔄 Update from PokéAPI", command=self._start_api_update,
                      relief="flat", font=("Segoe UI", 9), padx=8, pady=4, cursor="hand2"),
            "btn_accent2")
        self.update_btn.grid(row=2, column=0, sticky="ew")

    def _build_roll_settings(self, parent):
        pf = self._r(
            tk.LabelFrame(parent, text=" 🎲  Roll Settings ",
                          font=("Segoe UI", 10, "bold"), relief="solid", bd=1, padx=10, pady=10),
            "lf_accent1")
        pf.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        pf.columnconfigure(1, weight=1)

        self._r(tk.Label(pf, text="Abilities to draw:", font=("Segoe UI", 10)),
                "lbl_main").grid(row=0, column=0, sticky="w")
        self._r(
            tk.Spinbox(pf, from_=1, to=99, textvariable=self.draw_count_var,
                       width=5, relief="flat", font=("Consolas", 12, "bold")),
            "spinbox").grid(row=0, column=1, sticky="w", padx=(10, 0))

        cf = self._r(tk.Frame(pf), "bg_panel")
        cf.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        for text, var in [("Allow cringe abilities in roll", self.include_banned_var),
                          ("Main-series abilities only",     self.main_series_only_var)]:
            self._r(
                tk.Checkbutton(cf, text=text, variable=var,
                               command=self._on_filter_changed, font=("Segoe UI", 9)),
                "check").pack(anchor="w", pady=1)

        gf = self._r(
            tk.LabelFrame(pf, text=" Generations ",
                          font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=6, pady=6),
            "lf_accent2")
        gf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for i, gen in enumerate(GENERATIONS):
            self._r(
                tk.Checkbutton(gf, text=gen, variable=self.generation_vars[gen],
                               command=self._on_filter_changed,
                               fg=GEN_COLORS[gen], font=("Segoe UI", 9, "bold")),
                "check_gen").grid(row=i // 4, column=i % 4, sticky="w", padx=4, pady=1)

        br = self._r(tk.Frame(gf), "bg_panel")
        br.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))
        for text, cmd in [("All", self.select_all_generations),
                          ("None", self.clear_all_generations)]:
            self._r(
                tk.Button(br, text=text, command=cmd, relief="flat",
                          font=("Segoe UI", 8), padx=8, pady=2, cursor="hand2"),
                "btn_small").pack(side="left", padx=(0, 4))

        self.roll_btn = self._r(
            tk.Button(pf, text="⚡  ROLL ABILITIES", command=self.roll_abilities,
                      relief="flat", font=("Segoe UI", 13, "bold"), padx=0, pady=10,
                      cursor="hand2"),
            "btn_roll")
        self.roll_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.dramatic_roll_btn = self._r(
            tk.Button(pf, text="🎭  ROLL DRAMATICALLY", command=self._roll_dramatically,
                      relief="flat", font=("Segoe UI", 10, "bold"), padx=0, pady=7,
                      cursor="hand2"),
            "btn_dramatic")
        self.dramatic_roll_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    def _build_ban_panel(self, parent):
        pf = self._r(
            tk.LabelFrame(parent, text=" 🚫  Cringe / Banned Abilities ",
                          font=("Segoe UI", 10, "bold"), relief="solid", bd=1, padx=10, pady=8),
            "lf_banned")
        pf.grid(row=3, column=0, sticky="nsew")
        pf.columnconfigure(0, weight=1)
        pf.rowconfigure(2, weight=1)

        self._r(tk.Label(pf, text="Type an ability name and press Add, or\n"
                         "select one in the browser below.",
                         font=("Segoe UI", 8), justify="left"),
                "lbl_sub").grid(row=0, column=0, sticky="w")

        er = self._r(tk.Frame(pf), "bg_panel")
        er.grid(row=1, column=0, sticky="ew", pady=(6, 6))
        er.columnconfigure(0, weight=1)

        self.custom_ban_entry = self._r(
            tk.Entry(er, textvariable=self.custom_ban_var, relief="flat", font=("Segoe UI", 10)),
            "field_ban")
        self.custom_ban_entry.grid(row=0, column=0, sticky="ew")
        self.custom_ban_entry.bind("<Return>", lambda _: self.add_ban_from_entry())

        for col, (text, cmd, role) in enumerate([
            ("Add",       self.add_ban_from_entry,  "btn_accent2"),
            ("Remove",    self.remove_selected_ban, "btn_accent1"),
            ("Clear All", self.clear_bans,          "btn_banned"),
        ], start=1):
            self._r(
                tk.Button(er, text=text, command=cmd, relief="flat",
                          font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2"),
                role).grid(row=0, column=col, padx=(4, 0))

        lf = self._r(tk.Frame(pf), "bg_panel")
        lf.grid(row=2, column=0, sticky="nsew")
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        self.ban_listbox = self._r(
            tk.Listbox(lf, relief="flat", font=("Segoe UI", 9),
                       selectmode=tk.EXTENDED, activestyle="none", height=8),
            "listbox_banned")
        self.ban_listbox.grid(row=0, column=0, sticky="nsew")
        scr = self._r(tk.Scrollbar(lf, orient="vertical", command=self.ban_listbox.yview),
                      "scrollbar")
        scr.grid(row=0, column=1, sticky="ns")
        self.ban_listbox.configure(yscrollcommand=scr.set)

    def _build_profile_card(self, parent):
        t    = self._t
        card = self._r(tk.Frame(parent, pady=6, padx=10), "profile_card")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self._avatar_size  = 56
        self.avatar_canvas = tk.Canvas(card, width=56, height=56,
                                       highlightthickness=0, cursor="hand2")
        self.avatar_canvas.configure(bg=t["profile_bg"])
        self.avatar_canvas.pack(side="left", padx=(0, 14))
        self.avatar_canvas.bind("<Button-1>", lambda _: self._pick_avatar())

        text_col = self._r(tk.Frame(card), "profile_card")
        text_col.pack(side="left", fill="y", expand=False)

        self.welcome_var = tk.StringVar(value="Welcome Back!")
        self.welcome_lbl = self._r(
            tk.Label(text_col, textvariable=self.welcome_var,
                     font=("Segoe UI", 15, "bold"), anchor="w"),
            "lbl_welcome")
        self.welcome_lbl.pack(anchor="w")
        self.welcome_lbl.bind("<Button-1>", lambda _: self._edit_name())
        self.welcome_lbl.configure(cursor="hand2")

        self._r(
            tk.Label(text_col,
                     text="Click your avatar to change it  •  Click your name to edit",
                     font=("Segoe UI", 8), anchor="w"),
            "lbl_welcome_sub").pack(anchor="w")

        self._draw_avatar()

    def _build_results_panel(self, parent):
        pf = self._r(
            tk.LabelFrame(parent, text=" ✨  Rolled Abilities ",
                          font=("Segoe UI", 10, "bold"), relief="solid", bd=1, padx=10, pady=8),
            "lf_result")
        pf.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        pf.columnconfigure(0, weight=3)
        pf.rowconfigure(0, weight=1)

        self.result_text = self._r(
            tk.Text(pf, wrap="word", relief="flat", font=("Consolas", 10), padx=8, pady=6),
            "result_text")
        self.result_text.grid(row=0, column=0, sticky="nsew")
        for tag, fnt in [
            ("header",       ("Segoe UI",  10, "bold")),
            ("ability_name", ("Consolas",  11, "bold")),
            ("gen_tag",      ("Consolas",   9)),
            ("effect_text",  ("Consolas",  10)),
            ("divider",      ("Consolas",  10)),
            ("meta",         ("Consolas",   9, "italic")),
        ]:
            self.result_text.tag_configure(tag, font=fnt)

        scr = self._r(tk.Scrollbar(pf, orient="vertical", command=self.result_text.yview),
                      "scrollbar")
        scr.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scr.set)

        self.result_text.configure(state="normal")
        self.result_text.insert("1.0",
            "Press ⚡ Roll Abilities to get started!\n\n"
            "Select your game, adjust the settings on the left,\n"
            "then roll to see your random abilities here.", "meta")
        self.result_text.configure(state="disabled")

        # Sidebar
        side = self._r(tk.Frame(pf, padx=6), "bg_panel")
        side.grid(row=0, column=2, sticky="nsew")
        side.rowconfigure(1, weight=1)

        self._r(tk.Label(side, text="Select to act on:", font=("Segoe UI", 8)),
                "lbl_sub").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.rolled_listbox = self._r(
            tk.Listbox(side, relief="flat", font=("Segoe UI", 9),
                       selectmode=tk.SINGLE, activestyle="none",
                       width=20, exportselection=False),
            "listbox")
        self.rolled_listbox.grid(row=1, column=0, sticky="nsew")
        scr2 = self._r(tk.Scrollbar(side, orient="vertical", command=self.rolled_listbox.yview),
                       "scrollbar")
        scr2.grid(row=1, column=1, sticky="ns")
        self.rolled_listbox.configure(yscrollcommand=scr2.set)

        bf = self._r(tk.Frame(side), "bg_panel")
        bf.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        bf.columnconfigure(0, weight=1)
        for row, (text, cmd, role) in enumerate([
            ("🚫  Ban",          self._ban_selected,  "btn_banned"),
            ("🎲  Reroll",       self._reroll_selected, "btn_accent2"),
            ("🚫🎲  Ban & Reroll", self._ban_and_reroll, "btn_accent1"),
        ]):
            pady = (0, 3) if row < 2 else 0
            self._r(
                tk.Button(bf, text=text, command=cmd, relief="flat",
                          font=("Segoe UI", 9, "bold"), padx=6, pady=5, cursor="hand2"),
                role).grid(row=row, column=0, sticky="ew", pady=pady)

    def _build_ability_browser(self, parent):
        pf = self._r(
            tk.LabelFrame(parent, text=" 📖  Ability Browser ",
                          font=("Segoe UI", 10, "bold"), relief="solid", bd=1, padx=10, pady=8),
            "lf_accent1")
        pf.grid(row=2, column=0, sticky="nsew")
        pf.columnconfigure(0, weight=1, minsize=200)
        pf.columnconfigure(1, weight=2)
        pf.rowconfigure(1, weight=1)

        sf = self._r(tk.Frame(pf), "bg_panel")
        sf.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        sf.columnconfigure(1, weight=1)
        self._r(tk.Label(sf, text="🔍 Search:", font=("Segoe UI", 9)),
                "lbl_main").grid(row=0, column=0, sticky="w")
        self._r(
            tk.Entry(sf, textvariable=self.search_var, relief="flat", font=("Segoe UI", 10)),
            "field_search").grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.search_var.trace_add("write", lambda *_: self._refresh_ability_views())

        lf = self._r(tk.Frame(pf), "bg_panel")
        lf.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        self.ability_listbox = self._r(
            tk.Listbox(lf, relief="flat", font=("Segoe UI", 9),
                       exportselection=False, activestyle="none"),
            "listbox")
        self.ability_listbox.grid(row=0, column=0, sticky="nsew")
        self.ability_listbox.bind("<<ListboxSelect>>", self.show_selected_ability)
        scr = self._r(tk.Scrollbar(lf, orient="vertical", command=self.ability_listbox.yview),
                      "scrollbar")
        scr.grid(row=0, column=1, sticky="ns")
        self.ability_listbox.configure(yscrollcommand=scr.set)

        df = self._r(tk.Frame(pf), "bg_panel")
        df.grid(row=1, column=1, sticky="nsew")
        df.columnconfigure(0, weight=1)
        df.rowconfigure(1, weight=1)

        self.detail_title_var = tk.StringVar(value="← Select an ability")
        self._r(
            tk.Label(df, textvariable=self.detail_title_var,
                     font=("Segoe UI", 14, "bold"), anchor="w"),
            "lbl_detail_title").grid(row=0, column=0, sticky="ew")

        self.detail_text = self._r(
            tk.Text(df, wrap="word", relief="flat", font=("Segoe UI", 10),
                    padx=8, pady=6, height=6),
            "detail_text")
        self.detail_text.grid(row=1, column=0, sticky="nsew", pady=(6, 6))
        for tag, fnt in [
            ("key",          ("Segoe UI",  9, "bold")),
            ("val",          ("Segoe UI", 10)),
            ("banned_val",   ("Segoe UI", 10, "bold")),
            ("effect_label", ("Segoe UI", 10, "bold")),
        ]:
            self.detail_text.tag_configure(tag, font=fnt)

        dt_scr = self._r(
            tk.Scrollbar(df, orient="vertical", command=self.detail_text.yview), "scrollbar")
        dt_scr.grid(row=1, column=1, sticky="ns", pady=(6, 6))
        self.detail_text.configure(yscrollcommand=dt_scr.set)

        br = self._r(tk.Frame(df), "bg_panel")
        br.grid(row=2, column=0, sticky="w")
        for text, cmd, role in [
            ("🚫 Ban (Cringe)", self.ban_selected_ability,   "btn_banned"),
            ("✅ Unban",        self.unban_selected_ability, "btn_unban"),
        ]:
            self._r(
                tk.Button(br, text=text, command=cmd, relief="flat",
                          font=("Segoe UI", 9), padx=10, pady=4, cursor="hand2"),
                role).pack(side="left", padx=(0, 8))

    # ══════════════════════════════════════════════════════════════════════════
    #  Avatar / profile
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_avatar(self):
        t    = self._t
        size = self._avatar_size
        self.avatar_canvas.configure(bg=t["profile_bg"])
        self.avatar_canvas.delete("all")
        if _PIL_OK and os.path.exists(AVATAR_FILE):
            try:
                img = Image.open(AVATAR_FILE).convert("RGBA").resize(
                    (size, size), Image.LANCZOS)
                self._avatar_photo = ImageTk.PhotoImage(img)
                self.avatar_canvas.create_image(0, 0, anchor="nw",
                                                image=self._avatar_photo)
                return
            except Exception:
                pass
        self.avatar_canvas.create_rectangle(
            0, 0, size, size, fill=self._lighten(t["profile_bg"], 30), outline="")
        self.avatar_canvas.create_text(
            size // 2, size // 2, text="📷", font=("Segoe UI", 18), fill=t["fg_sub"])

    @staticmethod
    def _lighten(hex_col: str, amount: int = 30) -> str:
        h = hex_col.lstrip("#")
        return "#{:02x}{:02x}{:02x}".format(
            min(255, int(h[0:2], 16) + amount),
            min(255, int(h[2:4], 16) + amount),
            min(255, int(h[4:6], 16) + amount))

    def _pick_avatar(self):
        path = filedialog.askopenfilename(
            title="Choose profile picture",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                       ("All files", "*.*")])
        if not path:
            return
        if not _PIL_OK:
            messagebox.showwarning(APP_TITLE,
                "Pillow is not installed.\n"
                "Install it with:  pip install Pillow\n"
                "Then restart the app to use custom avatars.")
            return
        try:
            img  = Image.open(path).convert("RGBA")
            w, h = img.size
            side = min(w, h)
            img  = img.crop(((w - side) // 2, (h - side) // 2,
                             (w + side) // 2, (h + side) // 2))
            img.save(AVATAR_FILE, "PNG")
            self._draw_avatar()
            self._save_settings()
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Could not load image:\n{e}")

    def _edit_name(self):
        t   = self._t
        dlg = tk.Toplevel(self.root)
        dlg.title("Edit name")
        dlg.resizable(False, False)
        dlg.configure(bg=t["bg_panel"])
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Your name:", bg=t["bg_panel"], fg=t["fg_main"],
                 font=("Segoe UI", 10)).grid(row=0, column=0, padx=14, pady=(14, 4), sticky="w")
        name_var = tk.StringVar(value=self._user_name)
        entry = tk.Entry(dlg, textvariable=name_var, bg=t["bg_field"], fg=t["fg_main"],
                         insertbackground=t["fg_main"], relief="flat",
                         font=("Segoe UI", 12), width=22,
                         highlightbackground=t["fg_accent1"], highlightthickness=1)
        entry.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="ew")
        entry.focus_set()
        entry.select_range(0, tk.END)

        def save(_e=None):
            name = name_var.get().strip()
            if name:
                self._user_name = name
                self.welcome_var.set(f"Welcome Back, {name}!")
                self._save_settings()
            dlg.destroy()

        entry.bind("<Return>", save)
        tk.Button(dlg, text="Save", command=save,
                  bg=t["roll_bg"], fg=t["fg_main"], relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=5,
                  activebackground=t["roll_hover"], cursor="hand2"
                  ).grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 14), sticky="ew")

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - dlg.winfo_reqwidth())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_reqheight()) // 2
        dlg.geometry(f"+{x}+{y}")

    def _maybe_first_launch(self):
        if self._user_name:
            return
        t   = self._t
        dlg = tk.Toplevel(self.root)
        dlg.title("Welcome! 👋")
        dlg.resizable(False, False)
        dlg.configure(bg=t["bg_panel"])
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Welcome to the\nPokémon Ability Randomizer!",
                 bg=t["bg_panel"], fg=t["fg_accent1"],
                 font=("Segoe UI", 14, "bold"), justify="center"
                 ).grid(row=0, column=0, columnspan=2, padx=24, pady=(18, 6))
        tk.Label(dlg, text="What's your name, Trainer?",
                 bg=t["bg_panel"], fg=t["fg_main"], font=("Segoe UI", 10)
                 ).grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 4))

        name_var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=name_var, bg=t["bg_field"], fg=t["fg_main"],
                         insertbackground=t["fg_main"], relief="flat",
                         font=("Segoe UI", 12), width=22,
                         highlightbackground=t["fg_accent1"], highlightthickness=1)
        entry.grid(row=2, column=0, columnspan=2, padx=24, pady=(0, 10), sticky="ew")
        entry.focus_set()

        avatar_path_var = tk.StringVar()

        def pick_pic():
            if not _PIL_OK:
                messagebox.showwarning(APP_TITLE,
                    "Pillow is not installed.\n"
                    "Install it with:  pip install Pillow\n"
                    "Custom avatars need Pillow – you can skip for now.", parent=dlg)
                return
            path = filedialog.askopenfilename(
                parent=dlg, title="Choose a profile picture",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                           ("All files", "*.*")])
            if path:
                avatar_path_var.set(path)
                pic_btn.configure(text="✅ Picture chosen!")

        pic_btn = tk.Button(dlg, text="📷  Choose profile picture  (optional)",
                            command=pick_pic,
                            bg=t["bg_field"], fg=t["fg_accent2"], relief="flat",
                            font=("Segoe UI", 9), padx=10, pady=5, cursor="hand2",
                            activebackground=t["fg_accent2"], activeforeground=t["bg_root"])
        pic_btn.grid(row=3, column=0, columnspan=2, padx=24, pady=(0, 14), sticky="ew")

        def confirm(_e=None):
            name = name_var.get().strip() or "Trainer"
            self._user_name = name
            self.welcome_var.set(f"Welcome, {name}!")
            if avatar_path_var.get() and _PIL_OK:
                try:
                    img  = Image.open(avatar_path_var.get()).convert("RGBA")
                    w, h = img.size
                    side = min(w, h)
                    img  = img.crop(((w - side) // 2, (h - side) // 2,
                                     (w + side) // 2, (h + side) // 2))
                    img.save(AVATAR_FILE, "PNG")
                except Exception:
                    pass
            self._draw_avatar()
            self._save_settings()
            dlg.destroy()

        entry.bind("<Return>", confirm)
        tk.Button(dlg, text="Let's go! ⚡", command=confirm,
                  bg=t["roll_bg"], fg=t["fg_main"], relief="flat",
                  font=("Segoe UI", 11, "bold"), padx=14, pady=8, cursor="hand2",
                  activebackground=t["roll_hover"]
                  ).grid(row=4, column=0, columnspan=2, padx=24, pady=(0, 18), sticky="ew")

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - dlg.winfo_reqwidth())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_reqheight()) // 2
        dlg.geometry(f"+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════════
    #  Data loading / API update
    # ══════════════════════════════════════════════════════════════════════════

    def _load_abilities(self):
        loaded = load_abilities_json()
        if loaded:
            self.abilities = loaded
            self.status_var.set(f"Loaded {len(self.abilities)} abilities from cache.")
        else:
            self.status_var.set("No ability cache found — use 'Update from PokéAPI' to fetch.")

    def _start_api_update(self):
        if not messagebox.askyesno(APP_TITLE,
                "This will fetch all abilities from PokéAPI.\n"
                "It may take 1–3 minutes depending on your connection.\n\nContinue?"):
            return
        self.update_btn.configure(state="disabled", text="⏳ Updating…")
        self.status_var.set("Connecting to PokéAPI…")

        def worker():
            try:
                def progress(cur, tot, name):
                    pct = int(cur / tot * 100)
                    self.root.after(0, lambda: self.status_var.set(
                        f"Fetching from PokéAPI… {cur}/{tot}  ({pct}%)  — {name}"))
                abilities = fetch_all_abilities(progress_cb=progress)
                save_abilities_json(abilities)
                self.root.after(0, lambda: self._on_update_complete(abilities))
            except Exception as e:
                self.root.after(0, lambda: self._on_update_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_complete(self, abilities):
        self.abilities = abilities
        self.update_btn.configure(state="normal", text="🔄 Update from PokéAPI")
        self._update_status()
        self._refresh_ability_views()
        messagebox.showinfo(APP_TITLE,
            f"Updated! {len(abilities)} abilities fetched and saved to data/abilities.json")

    def _on_update_error(self, msg):
        self.update_btn.configure(state="normal", text="🔄 Update from PokéAPI")
        self.status_var.set(f"Update failed: {msg}")
        messagebox.showerror(APP_TITLE, f"Failed to fetch from PokéAPI:\n{msg}")

    # ══════════════════════════════════════════════════════════════════════════
    #  Filters / settings
    # ══════════════════════════════════════════════════════════════════════════

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower().replace("_", "-").replace(" ", "-")

    def _display_name(self, internal: str) -> str:
        for a in self.abilities:
            if a["name"] == internal:
                return a["display_name"]
        return internal.replace("-", " ").title()

    def _selected_generations(self) -> set:
        return {g for g, v in self.generation_vars.items() if v.get()}

    def _get_visible_pool(self) -> list:
        sel  = self._selected_generations()
        pool = [a for a in self.abilities if a.get("generation") in sel]
        if self.main_series_only_var.get():
            pool = [a for a in pool if a.get("is_main_series", True)]
        return pool

    def _update_status(self):
        pool      = self._get_visible_pool()
        available = sum(1 for a in pool if a["name"] not in self.banned_abilities)
        self.status_var.set(
            f"{len(self.abilities)} abilities total  •  "
            f"{available} available  •  "
            f"{len(self.banned_abilities)} banned/cringe")

    def _on_filter_changed(self):
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()

    def select_all_generations(self):
        for g in GENERATIONS: self.generation_vars[g].set(True)
        self.game_var.set("Custom")
        self._on_filter_changed()

    def clear_all_generations(self):
        for g in GENERATIONS: self.generation_vars[g].set(False)
        self.game_var.set("Custom")
        self._on_filter_changed()

    def _on_game_selected(self, _event=None):
        max_gen = GAME_PRESETS.get(self.game_var.get())
        if max_gen is None:
            return
        max_idx = GEN_ORDER[max_gen]
        for gen in GENERATIONS:
            self.generation_vars[gen].set(GEN_ORDER[gen] <= max_idx)
        self._on_filter_changed()

    def _load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                p = json.load(f)
            self.banned_abilities = set(p.get("banned_abilities", []))
            self.include_banned_var.set(bool(p.get("include_banned", False)))
            self.main_series_only_var.set(bool(p.get("main_series_only", True)))
            game = p.get("selected_game", "Custom")
            self.game_var.set(game if game in GAME_PRESETS else "Custom")
            saved_gens = p.get("selected_generations")
            if saved_gens:
                saved_gens = set(saved_gens)
                for g in GENERATIONS:
                    self.generation_vars[g].set(g in saved_gens)
            saved_theme = p.get("theme", THEME_NAMES[0])
            if saved_theme in THEMES:
                self._theme_name = saved_theme
                self._t = THEMES[saved_theme]
                self.theme_var.set(saved_theme)
                self._apply_theme()
            saved_name = p.get("user_name", "")
            if saved_name:
                self._user_name = saved_name
                self.welcome_var.set(f"Welcome Back, {saved_name}!")
                self._draw_avatar()
        except Exception:
            pass

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "banned_abilities":     sorted(self.banned_abilities),
                    "include_banned":       self.include_banned_var.get(),
                    "main_series_only":     self.main_series_only_var.get(),
                    "selected_game":        self.game_var.get(),
                    "selected_generations": [g for g in GENERATIONS
                                            if self.generation_vars[g].get()],
                    "theme":                self._theme_name,
                    "user_name":            self._user_name,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  Ability list / detail
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_ability_views(self):
        t     = self._t
        query = self.search_var.get().strip().lower()
        self.filtered_abilities = [
            a for a in self._get_visible_pool()
            if query in a["display_name"].lower() or query in a["effect"].lower()
        ]
        self.ability_listbox.delete(0, tk.END)
        for ability in self.filtered_abilities:
            banned = ability["name"] in self.banned_abilities
            label  = f"  {'🚫 ' if banned else ''}{ability['display_name']}  [{ability['generation']}]"
            self.ability_listbox.insert(tk.END, label)
            if banned:
                self.ability_listbox.itemconfig(tk.END, fg=t["fg_banned"], bg=t["bg_banned"])
        self._refresh_ban_list()

    def show_selected_ability(self, _event=None):
        sel = self.ability_listbox.curselection()
        if not sel:
            return
        ability   = self.filtered_abilities[sel[0]]
        is_banned = ability["name"] in self.banned_abilities
        self.detail_title_var.set(ability["display_name"])
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        for key, val, tag in [
            ("Generation:  ", ability["generation"],                        "val"),
            ("Main series: ", "Yes" if ability["is_main_series"] else "No", "val"),
            ("Status:      ", "🚫 CRINGE / BANNED" if is_banned else "✅ Allowed",
             "banned_val" if is_banned else "val"),
        ]:
            self.detail_text.insert(tk.END, key, "key")
            self.detail_text.insert(tk.END, val + "\n", tag)
        self.detail_text.insert(tk.END, "\nEffect:\n", "effect_label")
        self.detail_text.insert(tk.END, ability["effect"] + "\n", "val")
        self.detail_text.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    #  Ban management
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_ban_list(self):
        self.ban_listbox.delete(0, tk.END)
        for name in sorted(self.banned_abilities, key=lambda n: self._display_name(n)):
            self.ban_listbox.insert(tk.END, f"  {self._display_name(name)}")

    def add_ban_from_entry(self):
        raw = self.custom_ban_var.get().strip()
        if not raw:
            return
        norm  = self._normalize_name(raw)
        match = next((a for a in self.abilities
                      if a["name"] == norm or a["display_name"].lower() == raw.lower()), None)
        self.banned_abilities.add(match["name"] if match else norm)
        self.custom_ban_var.set("")
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()

    def ban_selected_ability(self):
        sel = self.ability_listbox.curselection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select an ability in the browser first.")
            return
        self.banned_abilities.add(self.filtered_abilities[sel[0]]["name"])
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()
        self.show_selected_ability()

    def unban_selected_ability(self):
        sel = self.ability_listbox.curselection()
        if not sel:
            messagebox.showinfo(APP_TITLE, "Select an ability in the browser first.")
            return
        self.banned_abilities.discard(self.filtered_abilities[sel[0]]["name"])
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()
        self.show_selected_ability()

    def remove_selected_ban(self):
        sel = self.ban_listbox.curselection()
        if not sel:
            return
        name_map = {a["display_name"]: a["name"] for a in self.abilities}
        for dn in [self.ban_listbox.get(i).strip() for i in sel]:
            self.banned_abilities.discard(name_map.get(dn) or self._normalize_name(dn))
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()

    def clear_bans(self):
        if not self.banned_abilities:
            return
        if not messagebox.askyesno(APP_TITLE,
                f"Clear all {len(self.banned_abilities)} banned abilities?"):
            return
        self.banned_abilities.clear()
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    #  Roll
    # ══════════════════════════════════════════════════════════════════════════

    def _get_roll_pool(self):
        pool = self._get_visible_pool()
        if not self.include_banned_var.get():
            pool = [a for a in pool if a["name"] not in self.banned_abilities]
        return pool

    def _validate_roll(self):
        """Returns (count, pool) or (None, None) on validation failure."""
        if not self._selected_generations():
            messagebox.showerror(APP_TITLE, "Select at least one generation first.")
            return None, None
        try:
            count = int(self.draw_count_var.get())
        except Exception:
            messagebox.showerror(APP_TITLE, "Enter a valid number of abilities to draw.")
            return None, None
        pool = self._get_roll_pool()
        if not pool:
            messagebox.showerror(APP_TITLE, "No abilities available with the current filters.")
            return None, None
        if count < 1:
            messagebox.showerror(APP_TITLE, "Draw at least 1 ability.")
            return None, None
        if count > len(pool):
            messagebox.showerror(APP_TITLE,
                f"You asked for {count}, but only {len(pool)} abilities are available.")
            return None, None
        return count, pool

    def _sort_key(self, a):
        return (GEN_ORDER.get(a["generation"], 99), a["display_name"])

    def _render_results(self):
        rolled   = self._rolled
        gen_list = ", ".join(g.replace("GEN ", "Gen ") for g in GENERATIONS
                             if self.generation_vars[g].get())
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END,
            f"⚡  {len(rolled)} Abilit{'y' if len(rolled) == 1 else 'ies'} Rolled", "header")
        self.result_text.insert(tk.END, f"\n{'─'*52}\n", "divider")
        self.result_text.insert(tk.END, f"  Game:        {self.game_var.get()}\n", "meta")
        self.result_text.insert(tk.END, f"  Generations: {gen_list}\n", "meta")
        self.result_text.insert(tk.END,
            f"  Cringe incl: {'Yes' if self.include_banned_var.get() else 'No'}\n", "meta")
        self.result_text.insert(tk.END, f"{'─'*52}\n\n", "divider")
        for i, ability in enumerate(rolled, 1):
            self.result_text.insert(tk.END, f"  {i:>2}.  ", "meta")
            self.result_text.insert(tk.END, ability["display_name"], "ability_name")
            self.result_text.insert(tk.END, f"  [{ability['generation']}]\n", "gen_tag")
            self.result_text.insert(tk.END, f"       {ability['effect']}\n\n", "effect_text")
        self.result_text.see("1.0")
        self.result_text.configure(state="disabled")
        self.rolled_listbox.delete(0, tk.END)
        for ability in rolled:
            self.rolled_listbox.insert(tk.END, f"  {ability['display_name']}")

    def roll_abilities(self):
        count, pool = self._validate_roll()
        if count is None:
            return
        self._rolled = sorted(random.sample(pool, count), key=self._sort_key)
        self._render_results()
        self._update_status()

    def _roll_dramatically(self):
        count, pool = self._validate_roll()
        if count is None:
            return
        self._rolled = sorted(random.sample(pool, count), key=self._sort_key)
        self._update_status()
        self._dramatic_reveal(on_close=self._render_results)

    # ══════════════════════════════════════════════════════════════════════════
    #  Rolled ability actions (ban / reroll)
    # ══════════════════════════════════════════════════════════════════════════

    def _get_selected_rolled(self):
        """Return (index, ability) or (None, None) if nothing selected."""
        sel = self.rolled_listbox.curselection()
        if not sel or not self._rolled:
            messagebox.showinfo(APP_TITLE,
                "Select an ability from the list on the right first.")
            return None, None
        return sel[0], self._rolled[sel[0]]

    def _do_reroll(self, idx):
        """Replace self._rolled[idx]. Returns replacement or None if pool exhausted."""
        current = {a["name"] for a in self._rolled}
        pool    = [a for a in self._get_roll_pool() if a["name"] not in current]
        if not pool:
            self._rolled.pop(idx)
            self._render_results()
            return None
        replacement      = random.choice(pool)
        self._rolled[idx] = replacement
        self._rolled.sort(key=self._sort_key)
        self._render_results()
        new_idx = next((i for i, a in enumerate(self._rolled)
                        if a["name"] == replacement["name"]), 0)
        self.rolled_listbox.selection_clear(0, tk.END)
        self.rolled_listbox.selection_set(new_idx)
        self.rolled_listbox.see(new_idx)
        return replacement

    def _ban_selected(self):
        idx, target = self._get_selected_rolled()
        if target is None:
            return
        self.banned_abilities.add(target["name"])
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()
        self._render_results()

    def _reroll_selected(self):
        idx, target = self._get_selected_rolled()
        if target is None:
            return
        if self._do_reroll(idx) is None:
            messagebox.showinfo(APP_TITLE, "No replacement available with the current filters.")

    def _ban_and_reroll(self):
        idx, target = self._get_selected_rolled()
        if target is None:
            return
        self.banned_abilities.add(target["name"])
        self._save_settings()
        self._update_status()
        self._refresh_ability_views()
        if self._do_reroll(idx) is None:
            messagebox.showinfo(APP_TITLE,
                f"{target['display_name']} was banned.\n"
                "No replacement available with the current filters.")

    # ══════════════════════════════════════════════════════════════════════════
    #  Dramatic Reveal
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _lerp_colour(c1: str, c2: str, t: float) -> str:
        """Interpolate between two #rrggbb hex colours. t=0→c1, t=1→c2."""
        c1 = c1.lstrip("#"); c2 = c2.lstrip("#")
        r1, g1, b1 = int(c1[0:2],16), int(c1[2:4],16), int(c1[4:6],16)
        r2, g2, b2 = int(c2[0:2],16), int(c2[2:4],16), int(c2[4:6],16)
        t = max(0.0, min(1.0, t))
        return "#{:02x}{:02x}{:02x}".format(
            int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

    def _dramatic_reveal(self, on_close=None):
        """Window-sized per-card reveal with fade in/out between abilities."""
        if not self._rolled:
            messagebox.showinfo(APP_TITLE, "Roll some abilities first!")
            return

        t         = self._t
        BLACK     = "#000000"
        abilities = list(self._rolled)
        total     = len(abilities)
        STEPS, MS = 20, 16

        self.root.update_idletasks()
        W, H   = self.root.winfo_width(), self.root.winfo_height()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()

        scale      = min(W / 1200, H / 820)
        sz_counter = max(8,  int(11 * scale))
        sz_gen     = max(8,  int(11 * scale))
        sz_name    = max(14, int(42 * scale))
        sz_effect  = max(9,  int(13 * scale))
        sz_btn     = max(8,  int(10 * scale))
        wrap_name  = int(W * 0.80)
        wrap_eff   = int(W * 0.72)
        div_w      = int(W * 0.42)
        btn_pady   = max(4, int(8  * scale))
        btn_padx   = max(8, int(18 * scale))

        ov = tk.Toplevel(self.root)
        ov.title("🎭 Dramatic Reveal")
        ov.configure(bg=BLACK)
        ov.geometry(f"{W}x{H}+{rx}+{ry}")
        ov.resizable(False, False)
        ov.overrideredirect(True)
        ov.grab_set()

        counter_var = tk.StringVar()
        counter_lbl = tk.Label(ov, textvariable=counter_var, bg=BLACK, fg=BLACK,
                               font=("Segoe UI", sz_counter))
        counter_lbl.place(relx=0.5, rely=0.09, anchor="center")

        gen_var = tk.StringVar()
        gen_lbl = tk.Label(ov, textvariable=gen_var, bg=BLACK, fg=BLACK,
                           font=("Segoe UI", sz_gen, "italic"))
        gen_lbl.place(relx=0.5, rely=0.34, anchor="center")

        name_var = tk.StringVar()
        name_lbl = tk.Label(ov, textvariable=name_var, bg=BLACK, fg=BLACK,
                            font=("Segoe UI", sz_name, "bold"),
                            wraplength=wrap_name, justify="center")
        name_lbl.place(relx=0.5, rely=0.45, anchor="center")

        div_cv = tk.Canvas(ov, bg=BLACK, highlightthickness=0, height=2, width=div_w)
        div_cv.place(relx=0.5, rely=0.57, anchor="center")

        effect_var = tk.StringVar()
        effect_lbl = tk.Label(ov, textvariable=effect_var, bg=BLACK, fg=BLACK,
                              font=("Segoe UI", sz_effect),
                              wraplength=wrap_eff, justify="center")
        effect_lbl.place(relx=0.5, rely=0.67, anchor="center")

        btn_row = tk.Frame(ov, bg=BLACK)
        btn_row.place(relx=0.5, rely=0.90, anchor="center")

        idx_ref    = [0]
        fading_ref = [False]

        def apply_alpha(alpha):
            bg_c = self._lerp_colour(BLACK, t["bg_root"],    alpha)
            ov.configure(bg=bg_c)
            counter_lbl.configure(bg=bg_c, fg=self._lerp_colour(BLACK, t["fg_sub"],     alpha))
            gen_lbl.configure(    bg=bg_c, fg=self._lerp_colour(BLACK, t["fg_accent3"], alpha))
            name_lbl.configure(   bg=bg_c, fg=self._lerp_colour(BLACK, t["fg_accent1"], alpha))
            effect_lbl.configure( bg=bg_c, fg=self._lerp_colour(BLACK, t["fg_main"],    alpha))
            div_cv.configure(bg=bg_c)
            div_cv.delete("all")
            if alpha > 0:
                div_cv.create_line(0, 1, div_w, 1,
                                   fill=self._lerp_colour(BLACK, t["fg_accent2"], alpha), width=2)
            btn_row.configure(bg=bg_c)

        def fade_in(step=0, then=None):
            if not ov.winfo_exists(): return
            if step > STEPS:
                apply_alpha(1.0); fading_ref[0] = False
                if then: then()
                return
            apply_alpha(step / STEPS)
            ov.after(MS, lambda: fade_in(step + 1, then))

        def fade_out(step=0, then=None):
            if not ov.winfo_exists(): return
            if step > STEPS:
                apply_alpha(0.0)
                if then: then()
                return
            apply_alpha(1.0 - step / STEPS)
            ov.after(MS, lambda: fade_out(step + 1, then))

        def build_nav(i):
            for w in btn_row.winfo_children():
                w.destroy()
            bkw = dict(relief="flat", padx=btn_padx, pady=btn_pady, cursor="hand2")
            if i > 0:
                tk.Button(btn_row, text="◀  Previous", command=lambda: go(i - 1),
                          bg=t["bg_field"], fg=t["fg_main"],
                          activebackground=t["fg_accent2"], activeforeground=t["bg_root"],
                          font=("Segoe UI", sz_btn), **bkw).pack(side="left", padx=8)
            next_or_done = i < total - 1
            tk.Button(btn_row,
                      text="Next  ▶" if next_or_done else "✅  Done",
                      command=(lambda: go(i + 1)) if next_or_done else finish,
                      bg=t["roll_bg"], fg=t["fg_main"],
                      activebackground=t["roll_hover"], activeforeground=t["fg_main"],
                      font=("Segoe UI", sz_btn, "bold"), **bkw).pack(side="left", padx=8)
            tk.Button(btn_row, text="✕  Skip reveal", command=finish,
                      bg=t["bg_field"], fg=t["fg_sub"],
                      activebackground=t["fg_banned"], activeforeground=t["bg_root"],
                      font=("Segoe UI", sz_btn), **bkw).pack(side="left", padx=8)

        def load_card(i):
            a = abilities[i]
            idx_ref[0] = i
            counter_var.set(f"{i + 1}  /  {total}")
            gen_var.set(a["generation"])
            name_var.set(a["display_name"])
            effect_var.set(a["effect"])
            build_nav(i)

        def show_card(i):
            load_card(i)
            fading_ref[0] = True
            fade_in()

        def go(i):
            if fading_ref[0]: return
            fading_ref[0] = True
            fade_out(then=lambda: show_card(i))

        def finish():
            if fading_ref[0]: return
            fading_ref[0] = True
            def _close():
                if ov.winfo_exists():
                    ov.grab_release()
                    ov.destroy()
                if on_close:
                    on_close()
            fade_out(then=_close)

        def on_key(event):
            i = idx_ref[0]
            if event.keysym in ("Right", "space", "Return"):
                if i < total - 1: go(i + 1)
                else: finish()
            elif event.keysym == "Left" and i > 0:
                go(i - 1)
            elif event.keysym == "Escape":
                finish()

        ov.bind("<KeyPress>", on_key)
        ov.focus_set()
        show_card(0)

    # ══════════════════════════════════════════════════════════════════════════
    #  Auto-update
    # ══════════════════════════════════════════════════════════════════════════

    def _check_for_update(self):
        """Background thread: compare current VERSION against latest GitHub release tag."""
        def worker():
            try:
                req = Request(GITHUB_API,
                              headers={"User-Agent": "PokemonAbilityRandomizer/" + VERSION,
                                       "Accept": "application/vnd.github+json"})
                with urlopen(req, timeout=8) as r:
                    data = json.loads(r.read().decode())
                tag = data.get("tag_name", "").lstrip("v")
                if tag and tag != VERSION:
                    self.root.after(0, lambda: self._prompt_update(tag))
            except Exception:
                pass   # no internet, rate-limited, etc. — fail silently

        threading.Thread(target=worker, daemon=True).start()

    def _prompt_update(self, new_version: str):
        """Ask the user whether to download and install the new version."""
        if not messagebox.askyesno(
                APP_TITLE,
                f"A new version is available:  v{new_version}  (you have v{VERSION})\n\n"
                "Download and install it now?\n"
                "The app will restart automatically after updating.",
                icon="info"):
            return
        threading.Thread(target=self._download_and_replace, daemon=True).start()

    def _download_and_replace(self):
        """Download the new script to a temp file, swap on success, then restart."""
        import tempfile, shutil

        self.root.after(0, lambda: self.status_var.set("Downloading update…"))
        try:
            req = Request(GITHUB_RAW,
                          headers={"User-Agent": "PokemonAbilityRandomizer/" + VERSION})
            with urlopen(req, timeout=30) as r:
                new_src = r.read()

            script_path = os.path.abspath(__file__)
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py",
                                                dir=os.path.dirname(script_path))
            try:
                with os.fdopen(tmp_fd, "wb") as f:
                    f.write(new_src)
                shutil.move(tmp_path, script_path)
            except Exception:
                try: os.unlink(tmp_path)
                except Exception: pass
                raise

            self.root.after(0, self._restart_after_update)

        except Exception as e:
            self.root.after(0, lambda: (
                self.status_var.set("Update failed."),
                messagebox.showerror(APP_TITLE,
                    f"Update download failed:\n{e}\n\n"
                    "You can update manually at:\n"
                    "https://github.com/ValoTypeDark/Ability-Randomiser")))

    def _restart_after_update(self):
        """Inform the user then re-launch the script."""
        messagebox.showinfo(APP_TITLE, "Update installed!\n\nThe app will now restart.")
        self.root.destroy()
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--update-abilities" in sys.argv:
        print("Fetching abilities from PokéAPI…")
        def _cli_progress(cur, tot, name):
            print(f"\r  {cur}/{tot}  {name:<40}", end="", flush=True)
        _abilities = fetch_all_abilities(progress_cb=_cli_progress)
        print(f"\nSaving {len(_abilities)} abilities to {ABILITIES_FILE}")
        save_abilities_json(_abilities)
        print("Done.")
        sys.exit(0)

    root = tk.Tk()
    AbilityRandomizerApp(root)
    root.mainloop()
