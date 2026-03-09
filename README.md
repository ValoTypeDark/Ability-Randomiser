# ⚡ Pokémon Ability Randomizer

A desktop app for randomly drawing Pokémon abilities: useful for nuzlockes, challenge runs, or just messing around. Built with Python and tkinter, works fully offline once the ability cache is set up.

---

## Features

- **Roll abilities** from any combination of generations (Gen III–IX)
- **Game presets**: select a game and generations are auto-set to match
- **Dramatic Reveal mode**: roll abilities and have them unveiled one by one with a full-window fade-in animation
- **Ban / Cringe list**: mark abilities you never want to see in rolls
- **Ban & Reroll**: ban a rolled ability mid-session and immediately replace it
- **Ability browser**: search and browse the full ability list with effect descriptions
- **Profile card**: set your trainer name and avatar
- **10 themes**: Pokédex, Charizard, Bulbasaur, Blastoise, Gengar, Pikachu, Glaceon, Umbreon, Sylveon, Team Rocket
- **Persistent settings**: bans, theme, generations, and profile are saved between sessions

---

## Requirements

- Python 3.8+
- tkinter (included with most Python installations)
- **Optional:** [Pillow](https://pypi.org/project/Pillow/) for custom profile avatars

```
pip install Pillow
```

---

## Setup

### 1. Get the ability data if you just downloaded the PY (zip contains up-to-date Abilities)

The app needs a local ability cache to work. You have two options:

**Option A: Fetch from PokéAPI (recommended)**

Run the app, then click **🔄 Update from PokéAPI** in the Game Preset panel. This fetches all abilities and saves them to `data/abilities.json`. Takes 1–3 minutes depending on your connection.

Or from the command line:

```
python pokemon_ability_randomizer.py --update-abilities
```

**Option B: Use an existing cache**

Place a valid `abilities.json` file in the `data/` folder next to the script. The expected format is:

```json
{
  "version": 2,
  "source": "PokeAPI",
  "count": 307,
  "abilities": [
    {
      "name": "adaptability",
      "display_name": "Adaptability",
      "effect": "Powers up moves of the same type.",
      "generation": "GEN IV",
      "is_main_series": true
    }
  ]
}
```

### 2. Run the app

```
python pokemon_ability_randomizer.py
```

---

## File structure

```
pokemon_ability_randomizer.py
data/
  abilities.json      ← ability cache (created on first update)
  settings.json       ← auto-saved preferences
  avatar.png          ← your profile picture (created when you set one)
```

All data files are stored relative to the script, so the whole folder is portable.

---

## How to use

### Rolling abilities

1. Select a **game preset** or manually tick generations in Roll Settings
2. Set the number of abilities to draw with the spinbox
3. Click **⚡ ROLL ABILITIES** for an instant roll, or **🎭 ROLL DRAMATICALLY** for the reveal mode
4. Rolled abilities appear in the results panel with their generation and effect

### Dramatic Reveal

Clicking **🎭 ROLL DRAMATICALLY** rolls your abilities then overlays the main window with a full-screen card for each one. The ability fades in, you read it, then press **Next** (or `→` / `Space`) to move on. When you close or finish, the normal results panel populates as usual.

Keyboard shortcuts during reveal:

| Key | Action |
|-----|--------|
| `→` / `Space` / `Enter` | Next ability (or Done on last) |
| `←` | Previous ability |
| `Esc` | Skip reveal |

### Banning abilities

- Right-click (or use the browser's **🚫 Ban** button) to mark an ability as cringe/banned
- Banned abilities are excluded from rolls by default
- Tick **Allow cringe abilities in roll** to include them anyway
- To ban a rolled ability mid-session, select it in the sidebar and click **🚫 Ban** or **🚫🎲 Ban & Reroll**

### Ability browser

The browser at the bottom-right shows all abilities matching your current generation/filter settings. Use the search box to filter by name or effect text. Clicking an ability shows its full details and lets you ban or unban it.

---

## Settings

Settings are saved automatically to `data/settings.json` whenever you change them. This includes:

- Banned abilities list
- Selected game and generations
- Main-series only toggle
- Include banned in roll toggle
- Active theme
- Trainer name

---

## Themes

Switch themes using the dropdown in the header. The theme is applied live and saved for next time.

| Theme | Vibe |
|-------|------|
| Pokédex (Default) | Dark navy with gold and electric blue |
| 🔥 Charizard | Deep orange and ember |
| 🌿 Bulbasaur | Dark green and lime |
| 💧 Blastoise | Deep blue and aqua |
| 👻 Gengar | Dark purple and lavender |
| ⚡ Pikachu | Dark yellow and gold |
| ❄️ Glaceon | Icy blue and frost |
| 🌙 Umbreon | Near-black with ring gold |
| 🌸 Sylveon | Dark pink and ribbon blue |
| 🖤 Team Rocket | Black and villain red |

---

## Troubleshooting

**"No ability cache found"**: Run `--update-abilities` or click Update from PokéAPI to generate the cache.

**Avatar doesn't load**: Install Pillow (`pip install Pillow`) and restart the app.

**tkinter not found**: On Linux you may need to install it separately: `sudo apt install python3-tk`

**PokéAPI update fails**: The fetch requires an internet connection. The app works fine offline once the cache exists.
