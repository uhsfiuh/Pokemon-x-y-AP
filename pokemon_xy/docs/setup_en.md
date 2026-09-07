# Pokémon X and Y Archipelago Setup Guide

This guide will walk you through setting up and playing a **Pokémon X and Y** Archipelago Multiworld game using BizHawk (Citra core) and the Archipelago BizHawk Client.

---

## 📋 Requirements

* **Archipelago**: v0.5.0 or newer.
* **Emulator**: BizHawk (v2.9.1 or newer recommended) with the N3DS (Citra) core enabled.
* **Game ROM**: A legitimate **Pokémon X** or **Pokémon Y** decrypted `.3ds` or `.cia` ROM.
* **Lua Connector**: `connector_pokemon_xy.lua` (included in the release).
* **APWorld Package**: `pokemon_x_and_y.apworld` (included in the release).

---

## ⚙️ Installation & Setup

### 1. Install the `.apworld` File
Copy `pokemon_x_and_y.apworld` into your Archipelago installation's `custom_worlds` folder:
* **Windows**: `C:\ProgramData\Archipelago\custom_worlds\` or inside your standalone Archipelago installation directory.

### 2. Generate a Multiworld Seed
1. Create or place a `pokemon_x_and_y.yaml` player file into your Archipelago `Players` directory.
2. Run `ArchipelagoGenerate.exe` to build your `.zip` multiworld seed.
3. Host the room locally via `ArchipelagoServer.exe` or upload the seed to [archipelago.gg](https://archipelago.gg).

---

## 🎮 How to Play & Connect

1. **Launch BizHawk**:
   * Open BizHawk and load your **Pokémon X** or **Pokémon Y** ROM.

2. **Open Lua Console**:
   * In BizHawk, navigate to `Tools -> Lua Console`.
   * Click `Script -> Open Script...` and select `connector_pokemon_xy.lua`.

3. **Launch Archipelago BizHawk Client**:
   * Open `ArchipelagoBizHawkClient.exe`.
   * Connect to your Archipelago server (e.g. `localhost:38281`).

4. **Enjoy your Multiworld!**:
   * The client will automatically connect to your BizHawk emulator and sync items and location checks bidirectionally in real-time.

---

## 🛠️ Helpful BizHawk Console Debug Commands

While running `connector_pokemon_xy.lua` in BizHawk, you can type the following helper functions directly into the Lua Console:

| Command | Description | Example |
| :--- | :--- | :--- |
| `give(item_id, count)` | Injects an item directly into your bag | `give(0x0011, 5)` *(Gives 5 Potions)* |
| `give_badge(num)` | Grants a specific Gym Badge (1..8) or all badges (`0`) | `give_badge(1)` *(Grants Bug Badge)* |
| `check_flag(flag_id)` | Manually sets an event flag in RAM and marks check | `check_flag(0x051A)` |
| `check_loc("name")` | Checks all locations matching search text | `check_loc("Route 2")` |
