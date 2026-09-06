-- ============================================================================
-- Pokémon X Archipelago BizHawk Connector (Vanilla Item Interceptor Build)
-- Location: Z:\ProgramData\Archipelago\data\lua\pokemon_x_connector.lua
-- Memory Domain: mainmemory (0x074... addresses)
-- ============================================================================

local script_dir = debug.getinfo(1, "S").source:match("@?(.*[/\\])") or ""
package.path = package.path .. ";" .. script_dir .. "?.lua;" .. "Z:/ProgramData/Archipelago/data/lua/?.lua;C:/ProgramData/Archipelago/data/lua/?.lua"

local base64 = require("base64")
local json   = require("json")

-- 1. Load BizHawk's native socket C binary from ./Lua/socket/core.dll
local function load_native_socket_core()
    local paths = {
        "./Lua/socket/core.dll",
        "Lua/socket/core.dll",
        "Z:/ProgramData/Archipelago/data/lua/x64/socket-windows-5-4.dll",
        "C:/ProgramData/Archipelago/data/lua/x64/socket-windows-5-4.dll",
    }

    for _, path in ipairs(paths) do
        local loader = package.loadlib(path, "luaopen_socket_core")
        if loader then
            print(string.format(">>> Successfully loaded socket C core from: %s", path))
            return loader()
        end
    end

    error("Could not find or load socket/core.dll C library.")
end

local core = load_native_socket_core()

-- 2. Create TCP Server socket using core.tcp() or core.bind()
local function bind_socket_server(host, port)
    if type(core.bind) == "function" then
        local server, err = core.bind(host, port)
        if server then
            if server.settimeout then server:settimeout(0) end
            return server
        end
    end

    if type(core.tcp) == "function" then
        local sock, err = core.tcp()
        if not sock then
            return nil, "core.tcp failed: " .. tostring(err)
        end
        
        sock:setoption("reuseaddr", true)
        local res, b_err = sock:bind(host, port)
        if not res then
            return nil, "bind failed: " .. tostring(b_err)
        end

        local l_res, l_err = sock:listen(5)
        if not l_res then
            return nil, "listen failed: " .. tostring(l_err)
        end

        sock:settimeout(0)
        return sock
    end

    return nil, "No valid socket creation method found on C core"
end

-- Verified Addresses in mainmemory domain
local BADGE_ADDRESS    = 0x074D86A0

-- Bag Pocket Layouts (mainmemory domain)
local POCKETS = {
    { addr = 0x074D5554, slots = 100, name = "Items" },
    { addr = 0x074D5B94, slots = 60,  name = "Key Items" },
    { addr = 0x074D5D14, slots = 110, name = "TM/HM" },
    { addr = 0x074D5EBC, slots = 60,  name = "Medicine" },
    { addr = 0x074D5FBC, slots = 70,  name = "Berries" },
}

-- Verified Event Flags Base Address matching Google Sheet / Locations.py
local EVENT_FLAGS_BASE = 0x074E86B8
local MONITORED_BYTES  = 375  -- 375 bytes * 8 = 3,000 total flags (covers up to 0x0BB8)

local SERVER_PORT = 43055
local server = nil
local client = nil

-- Bag Snapshot Helper
local function take_bag_snapshot()
    local snap = {}
    for p_idx, p in ipairs(POCKETS) do
        snap[p_idx] = {}
        for s = 0, p.slots - 1 do
            local addr = p.addr + (s * 4)
            local id  = mainmemory.read_u8(addr) + (mainmemory.read_u8(addr + 1) * 256)
            local cnt = mainmemory.read_u8(addr + 2) + (mainmemory.read_u8(addr + 3) * 256)
            snap[p_idx][s] = { id = id, cnt = cnt }
        end
    end
    return snap
end

-- Interceptor State
local pending_vanilla_removals = 0
local hold_ap_items            = false
local intercept_timer          = 0
local held_writes              = {}
local last_bag                 = take_bag_snapshot()

-- Release Held Archipelago Writes
local function release_held_writes()
    if #held_writes > 0 then
        print(string.format(">>> [RELEASING %d HELD ARCHIPELAGO WRITES TO BAG]", #held_writes))
        for _, req in ipairs(held_writes) do
            local addr = req["address"]
            local raw = base64.decode(req["value"])
            for i = 1, #raw do
                local val = (type(raw) == "table") and raw[i] or string.byte(raw, i)
                mainmemory.write_u8(addr + (i - 1), val)
            end
            print(string.format(">>> [ARCHIPELAGO ITEM DELIVERED] to 0x%08X", addr))
        end
        held_writes = {}
        last_bag = take_bag_snapshot()
    end
end

-- Table of flags that are actual randomized item checks (Item Balls, Gifts, Hidden Items)
local ITEM_CHECK_FLAGS = {
    [0x008D] = true, -- Shalour City - Exchanged a Sitrus Berry for a Leppa Berry with guy
    [0x008E] = true, -- Cyllage City - Received Destiny Knot from maid
    [0x0090] = true, -- Cyllage City - Received Whipped Dream / Sachet from man
    [0x0092] = true, -- Lumiose City (South Boulevard) - Received Luxury Ball (x5) from woman
    [0x0093] = true, -- Shalour City - Received Shoothe Bell from madame for showing her a Pokémon with good friendship
    [0x0097] = true, -- Shalour City - Received Eviolite from scientist for seeing at least 40 species in Coastal Pokédex
    [0x00A4] = true, -- Aquacorde Town - Received Potion from shopkeeper
    [0x00AA] = true, -- Coumarine City - Received Poké Toy from woman for answering her sound quiz first time
    [0x00B1] = true, -- Lumiose City (South Boulevard) - Received TM54 (False Swipe) from female scientist for seeing at least 20 species in Central Kalos Pokédex
    [0x00B2] = true, -- Camphrier Town - Received Berry Juice from girl
    [0x00B3] = true, -- Camphrier Town - Received Ultra Ball from man
    [0x00B4] = true, -- Camphrier Town - Received Full Heal from boy
    [0x00B5] = true, -- Camphrier Town - Received TM46 (Thief) from punk girl
    [0x00B7] = true, -- Coumarine City - Received Lucky Egg from woman for showing her a Pokémon with maximum friendship
    [0x00C6] = true, -- Lumiose City (South Boulevard) - Received Quick Claw from woman
    [0x00C7] = true, -- Lumiose City (South Boulevard) - Received Quick Ball (x3) from man
    [0x00D5] = true, -- Ambrette Town - Received the Douse Drive
    [0x00D7] = true, -- Santalune Forest - Received Poké Ball from Calem/Serena if interacted
    [0x00FE] = true, -- Lumiose City (South Boulevard) - Received Timer Ball (x3) from man
    [0x00FF] = true, -- Cyllage City - Received Persim Berry (x3) from girl for answering her quiz
    [0x0106] = true, -- Parfum Palace - Received Oran Berry from woman
    [0x0109] = true, -- Ambrette Town - Received TM94 (Rock Smash) from girl
    [0x010B] = true, -- Santalune City - Received Great Ball from boy
    [0x010D] = true, -- Lumiose City (Vernal Avenue) - Received Pearl String (x2) from madame for showing her a Furfrou that has kept the same trim for 15 days
    [0x010E] = true, -- Tower of Mastery - Received TM47 (Low Sweep) from ace trainer
    [0x011A] = true, -- Coumarine City - Received Good Rod from fisherman
    [0x011C] = true, -- Reflection Cave - Received Reveal Glass from female scientist for showing her a Tornadus / Thundurus / Landorus
    [0x011D] = true, -- Azure Bay - Received Ampharosite from old man
    [0x011E] = true, -- Ambrette Town - Received Aerodactylite from male scientist
    [0x0146] = true, -- Shalour City - Exchanged the Intriguing Stone for a Sun Stone with hiker
    [0x0191] = true, -- Ambrette Gate - Received Rocky Helmet from woman
    [0x0193] = true, -- Coumarine Gate - Received Black Sludge from punk guy
    [0x0195] = true, -- Coumarine City - Received Silk Scarf from old man
    [0x019B] = true, -- Coumarine City - Received Metronome from man
    [0x019C] = true, -- Route 12 - Received TM45 (Attract) from girl
    [0x019E] = true, -- Ambrette Town - Received TM96 (Nature Power) from woman
    [0x01A1] = true, -- Geosenge Town - Received TM66 (Payback) from old man
    [0x01A3] = true, -- Cyllage City - Received TM44 (Rest) from guy
    [0x01A4] = true, -- Cyllage City - Received TM88 (Sleep Talk) from girl
    [0x01A5] = true, -- Connecting Cave - Received TM21 (Frustration) from Backpacker
    [0x01AC] = true, -- Santalune City - Received X Attack (x3) and X Defense (x3) from old man
    [0x01AD] = true, -- Shalour City - Received Stardust (x5) from girl for helping her
    [0x01AE] = true, -- Geosenge Town - Received Everstone from female scientist
    [0x044D] = true, -- Route 13 - Found Power Plant Pass
    [0x044E] = true, -- Santalune City - Found Super Potion
    [0x044F] = true, -- Santalune City - Found Great Ball
    [0x0450] = true, -- Santalune City - Found Antidote
    [0x0451] = true, -- Route 4 - Found Honey (recurring)
    [0x0452] = true, -- Route 4 - Found Honey (recurring) (2)
    [0x0453] = true, -- Route 4 - Found Honey (recurring) (3)
    [0x0454] = true, -- Route 4 - Found Super Potion
    [0x0455] = true, -- Route 5 - Found Paralyze Heal
    [0x0456] = true, -- Route 5 - Found Super Potion
    [0x0457] = true, -- Camphrier Town - Found Antidote
    [0x0458] = true, -- Camphrier Town - Found Ether
    [0x0459] = true, -- Route 6 - Found Antidote
    [0x045A] = true, -- Route 6 - Found Tiny Mushroom
    [0x045B] = true, -- Parfum Palace - Found Rare Candy
    [0x045C] = true, -- Parfum Palace - Found X Sp. Atk
    [0x045D] = true, -- Parfum Palace - Found Pretty Wing (recurring)
    [0x045E] = true, -- Route 8 - Found Super Potion
    [0x045F] = true, -- Route 8 - Found Escape Rope
    [0x0460] = true, -- Route 8 - Found Pearl (recurring)
    [0x0461] = true, -- Route 8 - Found Ultra Ball
    [0x0462] = true, -- Route 8 - Found Heart Scale
    [0x0463] = true, -- Route 8 - Found Stardust (recurring)
    [0x0464] = true, -- Route 8 - Found Heart Scale (recurring)
    [0x0465] = true, -- Ambrette Town - Found Rare Candy
    [0x0466] = true, -- Ambrette Town - Found X Attack
    [0x0467] = true, -- Route 9 - Found Super Repel
    [0x0468] = true, -- Cyllage City - Found Ether
    [0x0469] = true, -- Cyllage City - Found Pearl
    [0x046A] = true, -- Cyllage City - Found X Speed
    [0x046B] = true, -- Cyllage City - Found Protein
    [0x046C] = true, -- Route 10 - Found Revive
    [0x046D] = true, -- Route 10 - Found Paralyze Heal
    [0x046E] = true, -- Route 10 - Found Burn Heal
    [0x046F] = true, -- Route 11 - Found Super Potion
    [0x0470] = true, -- Route 11 - Found Thunder Stone
    [0x0471] = true, -- Shalour City - Found X Sp. Atk
    [0x0472] = true, -- Shalour City - Found Stardust (recurring)
    [0x0473] = true, -- Shalour City - Found Max Repel
    [0x0474] = true, -- Route 12 - Found Honey (recurring)
    [0x0475] = true, -- Route 12 - Found Net Ball
    [0x0476] = true, -- Route 12 - Found Water Stone
    [0x0477] = true, -- Route 12 - Found Ice Heal
    [0x0478] = true, -- Azure Bay - Found Star Piece
    [0x0479] = true, -- Azure Bay - Found Hyper Potion
    [0x047A] = true, -- Azure Bay - Found Heart Scale
    [0x047B] = true, -- Coumarine City - Found Elixir
    [0x047C] = true, -- Coumarine City - Found Awakening
    [0x047D] = true, -- Coumarine City - Found Max Repel
    [0x047E] = true, -- Route 13 - Found Guard Spec.
    [0x047F] = true, -- Route 13 - Found Heat Rock
    [0x0480] = true, -- Route 13 - Found Nest Ball
    [0x0481] = true, -- Route 13 - Found Hyper Potion
    [0x0482] = true, -- Route 13 - Found PP Up
    [0x0483] = true, -- Route 13 - Found X Accuracy
    [0x0484] = true, -- Route 13 - Found Stardust
    [0x0485] = true, -- Route 13 - Found Fire Stone
    [0x0486] = true, -- Route 13 - Found Star Piece
    [0x0487] = true, -- Route 14 - Found Super Potion
    [0x0488] = true, -- Route 14 - Found Tiny Mushroom
    [0x0489] = true, -- Route 14 - Found Revive
    [0x048A] = true, -- Laverre City - Found Tiny Mushroom (recurring)
    [0x048B] = true, -- Laverre City - Found Leaf Stone
    [0x048C] = true, -- Laverre City - Found Ultra Ball
    [0x048D] = true, -- Poké Ball Factory - Found Dusk Ball
    [0x048E] = true, -- Poké Ball Factory - Found Burn Heal
    [0x048F] = true, -- Poké Ball Factory - Found Poké Ball
    [0x0490] = true, -- Poké Ball Factory - Found Hyper Potion
    [0x0491] = true, -- Route 15 - Found HP Up
    [0x0492] = true, -- Route 15 - Found Antidote
    [0x0493] = true, -- Route 15 - Found Tiny Mushroom
    [0x0494] = true, -- Route 15 - Found X Defense
    [0x0495] = true, -- Route 15 - Found Pretty Wing
    [0x0496] = true, -- Route 16 - Found Repel
    [0x0497] = true, -- Route 16 - Found Rare Candy
    [0x0498] = true, -- Route 16 - Found Big Mushroom
    [0x0499] = true, -- Route 16 - Found Max Revive
    [0x049A] = true, -- Dendemille Town - Found Heal Ball
    [0x049B] = true, -- Dendemille Town - Found X Speed
    [0x049C] = true, -- Dendemille Town - Found Nugget
    [0x049D] = true, -- Frost Cavern - Found Escape Rope
    [0x049E] = true, -- Frost Cavern - Found X Sp. Def
    [0x049F] = true, -- Frost Cavern - Found Ice Heal
    [0x04A0] = true, -- Frost Cavern - Found Dusk Ball
    [0x04A1] = true, -- Frost Cavern - Found Dire Hit
    [0x04A2] = true, -- Frost Cavern - Found Pearl
    [0x04A3] = true, -- Frost Cavern - Found Super Potion
    [0x04A4] = true, -- Frost Cavern - Found Ice Heal (2)
    [0x04A5] = true, -- Frost Cavern - Found Elixir
    [0x04A6] = true, -- Frost Cavern - Found PP Up
    [0x04A7] = true, -- Route 18 - Found Timer Ball
    [0x04A8] = true, -- Route 18 - Found Paralyze Heal
    [0x04A9] = true, -- Anistar City - Found Pretty Wing (recurring)
    [0x04AA] = true, -- Anistar City - Found Escape Rope
    [0x04AB] = true, -- Anistar City - Found Super Repel
    [0x04AC] = true, -- Anistar City - Found Sun Stone
    [0x04AD] = true, -- Route 19 - Found Poké Ball
    [0x04AE] = true, -- Route 19 - Found Ether
    [0x04AF] = true, -- Route 19 - Found Honey
    [0x04B0] = true, -- Route 19 - Found Super Potion
    [0x04B1] = true, -- Terminus Cave - Found Dusk Ball
    [0x04B2] = true, -- Terminus Cave - Found Hyper Potion
    [0x04B3] = true, -- Terminus Cave - Found Moon Stone
    [0x04B4] = true, -- Terminus Cave - Found Max Repel
    [0x04B5] = true, -- Terminus Cave - Found Iron
    [0x04B6] = true, -- Terminus Cave - Found Dire Hit
    [0x04B7] = true, -- Terminus Cave - Found Max Potion
    [0x04B8] = true, -- Terminus Cave - Found Big Nugget
    [0x04B9] = true, -- Terminus Cave - Found Normal Gem
    [0x04BA] = true, -- Couriway Town - Found Pretty Wing
    [0x04BB] = true, -- Couriway Town - Found Ether
    [0x04BC] = true, -- Couriway Town - Found Burn Heal
    [0x04BD] = true, -- Couriway Town - Found Prism Scale (recurring)
    [0x04BE] = true, -- Route 20 - Found Net Ball
    [0x04BF] = true, -- Route 20 - Found Antidote
    [0x04C0] = true, -- Route 20 - Found Damp Rock
    [0x04C1] = true, -- Route 20 - Found Escape Rope
    [0x04C2] = true, -- Route 20 - Found Timer Ball
    [0x04C3] = true, -- Snowbelle City - Found Icy Rock
    [0x04C4] = true, -- Snowbelle City - Found X Sp. Atk
    [0x04C5] = true, -- Snowbelle City - Found Full Heal
    [0x04C6] = true, -- Route 21 - Found Repeat Ball
    [0x04C7] = true, -- Route 21 - Found Antidote
    [0x04C8] = true, -- Route 21 - Found Mental Herb
    [0x04C9] = true, -- Route 21 - Found Tiny Mushroom
    [0x04CA] = true, -- Route 21 - Found Balm Mushroom
    [0x04CB] = true, -- Pokémon Village - Found Honey
    [0x04CC] = true, -- Pokémon Village - Found Pretty Wing
    [0x04CD] = true, -- Pokémon Village - Found Honey (2)
    [0x04CE] = true, -- Route 22 - Found Guard Spec.
    [0x04CF] = true, -- Route 22 - Found PP Up
    [0x04D0] = true, -- Route 22 - Found Pearl String
    [0x04D1] = true, -- Route 22 - Found Elixir
    [0x04D2] = true, -- Route 22 - Found Max Elixir
    [0x04D3] = true, -- Route 22 - Found Full Restore
    [0x04D4] = true, -- Victory Road - Found X Attack
    [0x04D5] = true, -- Victory Road - Found Full Heal
    [0x04D6] = true, -- Victory Road - Found Hyper Potion
    [0x04D7] = true, -- Victory Road - Found Ultra Ball
    [0x04D8] = true, -- Victory Road - Found Smooth Rock
    [0x04D9] = true, -- Victory Road - Found Revive
    [0x04DA] = true, -- Victory Road - Found Pretty Wing
    [0x04DB] = true, -- Victory Road - Found Escape Rope
    [0x04DC] = true, -- Victory Road - Found Max Repel
    [0x04DD] = true, -- Victory Road - Found X Defense
    [0x04DE] = true, -- Victory Road - Found Max Ether
    [0x04DF] = true, -- Victory Road - Found Star Piece
    [0x04E0] = true, -- Couriway Town - Found Poké Ball
    [0x04E1] = true, -- Kiloude City - Found Max Revive
    [0x04E2] = true, -- Kiloude City - Found PP Up
    [0x04E3] = true, -- Unknown Dungeon - Found Oval Stone (recurring)
    [0x051A] = true, -- Santalune Forest - Potion item ball disappeared
    [0x051B] = true, -- Santalune Forest - Poké Ball item ball disappeared
    [0x051C] = true, -- Route 3 - Super Potion item ball disappeared
    [0x051D] = true, -- Route 3 - Revive item ball disappeared
    [0x051E] = true, -- Route 3 - Dawn Stone item ball disappeared
    [0x051F] = true, -- Route 22 - Super Potion item ball disappeared
    [0x0520] = true, -- Route 22 - Elixir item ball disappeared
    [0x0521] = true, -- Route 22 - Draco Plate item ball disappeared
    [0x0522] = true, -- Route 4 - Great Ball item ball disappeared
    [0x0523] = true, -- Route 4 - Antidote item ball disappeared
    [0x0524] = true, -- Route 4 - Super Potion item ball disappeared
    [0x0525] = true, -- Route 4 - Repel item ball disappeared
    [0x0526] = true, -- Route 4 - Poison Barb item ball disappeared
    [0x0527] = true, -- Route 4 - Net Ball item ball disappeared
    [0x0528] = true, -- Route 4 - Ether item ball disappeared
    [0x0529] = true, -- Route 5 - Super Potion item ball disappeared
    [0x052A] = true, -- Route 5 - Super Potion item ball disappeared (2)
    [0x052B] = true, -- Route 5 - Great Ball item ball disappeared
    [0x052C] = true, -- Route 5 - TM01 (Hone Claws) item ball disappeared
    [0x052D] = true, -- Route 5 - X Attack item ball disappeared
    [0x052E] = true, -- Route 5 - Sharp Beak item ball disappeared
    [0x052F] = true, -- Route 6 - X Sp. Atk item ball disappeared
    [0x0530] = true, -- Route 6 - Antidote item ball disappeared
    [0x0531] = true, -- Route 6 - X Speed item ball disappeared
    [0x0532] = true, -- Route 6 - Paralyze Heal item ball disappeared
    [0x0533] = true, -- Route 6 - TM09 (Venosock) item ball disappeared
    [0x0534] = true, -- Route 6 - Awakening item ball disappeared
    [0x0535] = true, -- Route 6 - Super Repel item ball disappeared
    [0x0536] = true, -- Route 6 - Ultra Ball item ball disappeared
    [0x0537] = true, -- Route 7 - X Sp. Def item ball disappeared
    [0x0538] = true, -- Route 7 - PP Up item ball disappeared
    [0x0539] = true, -- Route 7 - Tiny Mushroom item ball disappeared
    [0x053A] = true, -- Route 7 - Silver Powder item ball disappeared
    [0x053B] = true, -- Connecting Cave - TM40 (Aerial Ace) item ball disappeared
    [0x053C] = true, -- Route 8 - HP Up item ball disappeared
    [0x053D] = true, -- Route 8 - Leaf Stone item ball disappeared
    [0x053E] = true, -- Route 8 - Water Stone item ball disappeared
    [0x053F] = true, -- Route 8 - Heart Scale item ball disappeared
    [0x0540] = true, -- Route 8 - TM19 (Roost) item ball disappeared
    [0x0541] = true, -- Route 9 - X Defense item ball disappeared
    [0x0542] = true, -- Route 9 - Paralyze Heal item ball disappeared
    [0x0543] = true, -- Route 9 - Fire Stone item ball disappeared
    [0x0544] = true, -- Route 9 - Dusk Ball item ball disappeared
    [0x0545] = true, -- Glittering Cave - Hard Stone item ball disappeared
    [0x0546] = true, -- Glittering Cave - TM65 (Shadow Claw) item ball disappeared
    [0x0547] = true, -- Route 10 - TM73 (Thunder Wave) item ball disappeared
    [0x0548] = true, -- Route 10 - Mind Plate item ball disappeared
    [0x0549] = true, -- Route 10 - X Accuracy item ball disappeared
    [0x054A] = true, -- Route 10 - Thunder Stone item ball disappeared
    [0x054B] = true, -- Route 11 - TM69 (Rock Polish) item ball disappeared
    [0x054C] = true, -- Route 11 - Hyper Potion item ball disappeared
    [0x054D] = true, -- Reflection Cave - Nest Ball item ball disappeared
    [0x054E] = true, -- Reflection Cave - Revive item ball disappeared
    [0x054F] = true, -- Reflection Cave - Moon Stone item ball disappeared
    [0x0550] = true, -- Reflection Cave - Black Belt item ball disappeared
    [0x0551] = true, -- Reflection Cave - Hyper Potion item ball disappeared
    [0x0552] = true, -- Reflection Cave - Escape Rope item ball disappeared
    [0x0553] = true, -- Reflection Cave - Iron item ball disappeared
    [0x0554] = true, -- Reflection Cave - Earth Plate item ball disappeared
    [0x0555] = true, -- Reflection Cave - TM74 (Gyro Ball) item ball disappeared
    [0x0556] = true, -- Route 12 - Sachet item ball disappeared
    [0x0557] = true, -- Route 12 - Shiny Stone item ball disappeared
    [0x0558] = true, -- Route 12 - Whipped Dream item ball disappeared
    [0x0559] = true, -- Parfum Palace - Guard Spec. item ball disappeared
    [0x055A] = true, -- Route 12 - Leftovers item ball disappeared
    [0x055B] = true, -- Azure Bay - Deep Sea Tooth item ball disappeared
    [0x055C] = true, -- Azure Bay - TM81 (X-Scissor) item ball disappeared
    [0x055D] = true, -- Azure Bay - Dive Ball item ball disappeared
    [0x055E] = true, -- Azure Bay - Big Pearl item ball disappeared
    [0x055F] = true, -- Azure Bay - Splash Plate item ball disappeared
    [0x0560] = true, -- Route 13 - Smooth Rock item ball disappeared
    [0x0561] = true, -- Route 13 - Burn Heal item ball disappeared
    [0x0562] = true, -- Route 13 - TM57 (Charge Beam) item ball disappeared
    [0x0563] = true, -- Route 13 - Flame Plate item ball disappeared
    [0x0564] = true, -- Route 13 - Sun Stone item ball disappeared
    [0x0565] = true, -- Route 13 - Rare Candy item ball disappeared
    [0x0566] = true, -- Route 14 - Cleanse Tag item ball disappeared
    [0x0567] = true, -- Route 14 - Big Mushroom item ball disappeared
    [0x0568] = true, -- Route 14 - Hyper Potion item ball disappeared
    [0x0569] = true, -- Route 14 - Damp Rock item ball disappeared
    [0x056A] = true, -- Route 14 - Spell Tag item ball disappeared
    [0x056B] = true, -- Route 14 - TM61 (Will-O-Wisp) item ball disappeared
    [0x056C] = true, -- Poké Ball Factory - Max Revive item ball disappeared
    [0x056D] = true, -- Poké Ball Factory - Max Ether item ball disappeared
    [0x056E] = true, -- Poké Ball Factory - Quick Ball item ball disappeared
    [0x056F] = true, -- Poké Ball Factory - Metal Coat item ball disappeared
    [0x0570] = true, -- Poké Ball Factory - Timer Ball item ball disappeared
    [0x0571] = true, -- Route 15 - Net Ball item ball disappeared
    [0x0572] = true, -- Route 15 - Revive item ball disappeared
    [0x0573] = true, -- Route 15 - Dire Hit item ball disappeared
    [0x0574] = true, -- Route 15 - PP Up item ball disappeared
    [0x0575] = true, -- Route 15 - Full Heal item ball disappeared
    [0x0576] = true, -- Route 15 - Protein item ball disappeared
    [0x0577] = true, -- Route 15 - Macho Brace item ball disappeared
    [0x0578] = true, -- Route 15 - Stone Plate item ball disappeared
    [0x0579] = true, -- Route 15 - TM97 (Dark Pulse) item ball disappeared
    [0x057A] = true, -- Route 16 - Rare Candy item ball disappeared
    [0x057B] = true, -- Route 16 - Max Potion item ball disappeared
    [0x057C] = true, -- Route 16 - Fist Plate item ball disappeared
    [0x057D] = true, -- Route 16 - Dive Ball item ball disappeared
    [0x057E] = true, -- Lost Hotel - Smoke Ball item ball disappeared
    [0x057F] = true, -- Lost Hotel - Twisted Spoon item ball disappeared
    [0x0580] = true, -- Lost Hotel - TM95 (Snarl) item ball disappeared
    [0x0581] = true, -- Lost Hotel - Dread Plate item ball disappeared
    [0x0582] = true, -- Lost Hotel - Protector item ball disappeared
    [0x0583] = true, -- Frost Cavern - Heart Scale item ball disappeared
    [0x0584] = true, -- Frost Cavern - TM71 (Stone Edge) item ball disappeared
    [0x0585] = true, -- Frost Cavern - Hyper Potion item ball disappeared
    [0x0586] = true, -- Frost Cavern - Ice Heal item ball disappeared
    [0x0587] = true, -- Frost Cavern - Max Repel item ball disappeared
    [0x0588] = true, -- Frost Cavern - Never-Melt Ice item ball disappeared
    [0x0589] = true, -- Frost Cavern - TM79 (Frost Breath) item ball disappeared
    [0x058A] = true, -- Frost Cavern - Ether item ball disappeared
    [0x058B] = true, -- Frost Cavern - Zinc item ball disappeared
    [0x058C] = true, -- Frost Cavern - Icy Rock item ball disappeared
    [0x058D] = true, -- Route 18 - Icicle Plate item ball disappeared
    [0x058E] = true, -- Route 18 - Calcium item ball disappeared
    [0x058F] = true, -- Route 18 - Rare Candy item ball disappeared
    [0x0590] = true, -- Route 19 - Hyper Potion item ball disappeared
    [0x0591] = true, -- Route 19 - PP Up item ball disappeared
    [0x0592] = true, -- Route 19 - X Defense item ball disappeared
    [0x0593] = true, -- Route 19 - Max Ether item ball disappeared
    [0x0594] = true, -- Terminus Cave - Star Piece item ball disappeared
    [0x0595] = true, -- Terminus Cave - Heat Rock item ball disappeared
    [0x0596] = true, -- Terminus Cave - Escape Rope item ball disappeared
    [0x0597] = true, -- Terminus Cave - Reaper Cloth item ball disappeared
    [0x0598] = true, -- Terminus Cave - Dusk Stone item ball disappeared
    [0x0599] = true, -- Terminus Cave - X Attack item ball disappeared
    [0x059A] = true, -- Terminus Cave - Elixir item ball disappeared
    [0x059B] = true, -- Terminus Cave - Full Heal item ball disappeared
    [0x059C] = true, -- Terminus Cave - Iron Plate item ball disappeared
    [0x059D] = true, -- Terminus Cave - TM30 (Shadow Ball) item ball disappeared
    [0x059E] = true, -- Terminus Cave - Griseous Orb item ball disappeared
    [0x059F] = true, -- Terminus Cave - Dragon Scale item ball disappeared
    [0x05A0] = true, -- Terminus Cave - TM31 (Brick Break) item ball disappeared
    [0x05A1] = true, -- Route 20 - Max Revive item ball disappeared
    [0x05A2] = true, -- Route 20 - HP Up item ball disappeared
    [0x05A3] = true, -- Route 20 - Rare Bone item ball disappeared
    [0x05A4] = true, -- Route 20 - PP Up item ball disappeared
    [0x05A5] = true, -- Route 20 - Toxic Plate item ball disappeared
    [0x05A6] = true, -- Route 20 - TM36 (Sludge Bomb) item ball disappeared
    [0x05A7] = true, -- Route 21 - Paralyze Heal item ball disappeared
    [0x05A8] = true, -- Route 21 - Protein item ball disappeared
    [0x05A9] = true, -- Route 21 - Meadow Plate item ball disappeared
    [0x05AA] = true, -- Route 21 - X Accuracy item ball disappeared
    [0x05AB] = true, -- Route 21 - TM53 (Energy Ball) item ball disappeared
    [0x05AC] = true, -- Pokémon Village - Max Ether item ball disappeared
    [0x05AD] = true, -- Pokémon Village - Full Restore item ball disappeared
    [0x05AE] = true, -- Pokémon Village - Pixie Plate item ball disappeared
    [0x05AF] = true, -- Pokémon Village - TM29 (Psychic) item ball disappeared
    [0x05B0] = true, -- Route 21 - Insect Plate item ball disappeared
    [0x05B1] = true, -- Route 21 - Elixir item ball disappeared
    [0x05B2] = true, -- Route 21 - TM22 (Solar Beam) item ball disappeared
    [0x05B3] = true, -- Route 21 - Rare Candy item ball disappeared
    [0x05B4] = true, -- Route 21 - Repeat Ball item ball disappeared
    [0x05B5] = true, -- Victory Road - Dusk Ball item ball disappeared
    [0x05B6] = true, -- Victory Road - TM03 (Psyshock) item ball disappeared
    [0x05B7] = true, -- Victory Road - Rare Candy item ball disappeared
    [0x05B8] = true, -- Victory Road - Carbos item ball disappeared
    [0x05B9] = true, -- Victory Road - PP Up item ball disappeared
    [0x05BA] = true, -- Victory Road - Zinc item ball disappeared
    [0x05BB] = true, -- Victory Road - Max Elixir item ball disappeared
    [0x05BC] = true, -- Victory Road - Dragon Fang item ball disappeared
    [0x05BD] = true, -- Victory Road - Full Restore item ball disappeared
    [0x05BE] = true, -- Victory Road - TM02 (Dragon Claw) item ball disappeared
    [0x05BF] = true, -- Camphrier Town - X Attack item ball disappeared
    [0x05C0] = true, -- Ambrette Town - Pearl item ball disappeared
    [0x05C1] = true, -- Cyllage City - Super Potion item ball disappeared
    [0x05C2] = true, -- Cyllage City - X Sp. Atk item ball disappeared
    [0x05C3] = true, -- Cyllage City - X Defense item ball disappeared
    [0x05C4] = true, -- Geosenge Town - Timer Ball item ball disappeared
    [0x05C5] = true, -- Coumarine City - Sky Plate item ball disappeared
    [0x05C6] = true, -- Laverre City - Ether item ball disappeared
    [0x05C7] = true, -- Dendemille Town - Big Root item ball disappeared
    [0x05C8] = true, -- Couriway Town - Rare Candy item ball disappeared
    [0x05C9] = true, -- Couriway Town - Max Potion item ball disappeared
    [0x05CA] = true, -- Couriway Town - TM80 (Rock Slide) item ball disappeared
    [0x05CB] = true, -- Snowbelle City - Full Restore item ball disappeared
    [0x05CC] = true, -- Route 7 - Heal Ball item ball disappeared
    [0x05CD] = true, -- Shabboneau Castle - Escape Rope item ball disappeared
    [0x05CE] = true, -- Parfum Palace - Ether item ball disappeared
    [0x05CF] = true, -- Parfum Palace - Amulet Coin item ball disappeared
    [0x05D0] = true, -- Parfum Palace - Antidote item ball disappeared
    [0x05D1] = true, -- Kalos Power Plant - Zap Plate item ball disappeared
    [0x05D2] = true, -- Lysandre Labs - Hyper Potion item ball disappeared
    [0x05D3] = true, -- Lysandre Labs - Black Glasses item ball disappeared
    [0x05D4] = true, -- Lysandre Labs - Revive item ball disappeared
    [0x05D5] = true, -- Lysandre Labs - Rare Candy item ball disappeared
    [0x05D6] = true, -- Chamber of Emptiness - Spooky Plate item ball disappeared
    [0x05D7] = true, -- Parfum Palace - Revive item ball disappeared
    [0x05D8] = true, -- Parfum Palace - Super Potion item ball disappeared
    [0x05D9] = true, -- Santalune Forest - Potion item ball disappeared (2)
    [0x05DA] = true, -- Shalour City - Max Ether item ball disappeared
    [0x05DB] = true, -- Kiloude City - Nugget item ball disappeared
    [0x05DC] = true, -- Route 14 - Rare Candy item ball disappeared
    [0x05DD] = true, -- Santalune Forest - Potion item ball disappeared (3)
    [0x05DE] = true, -- Santalune Forest - Antidote item ball disappeared
    [0x05DF] = true, -- Route 22 - TM26 (Earthquake) item ball disappeared
    [0x05E0] = true, -- Camphrier Town - Star Piece item ball disappeared
    [0x05E1] = true, -- Azure Bay - Deep Sea Scale item ball disappeared
    [0x05E2] = true, -- Terminus Cave - Adamant Orb item ball disappeared
    [0x05E3] = true, -- Terminus Cave - Lustrous Orb item ball disappeared
    [0x05E4] = true, -- Geosenge Town - Soft Sand item ball disappeared
    [0x05E5] = true, -- Route 7 - Miracle Seed item ball disappeared
    [0x05E6] = true, -- Glittering Cave - Escape Rope item ball disappeared
    [0x05E7] = true, -- Parfum Palace - HM01 (Cut) item ball disappeared
    [0x05E8] = true, -- Victory Road - Quick Ball item ball disappeared
    [0x0A76] = true, -- Coumarine City - Received Diploma for completing Central Kalos Pokédex (native) from Game Director
    [0x0A77] = true, -- Coumarine City - Received Diploma for completing Coastal Kalos Pokédex (native) from Game Director
    [0x0A78] = true, -- Coumarine City - Received Diploma for completing Mountain Kalos Pokédex (native) from Game Director
    [0x0A79] = true, -- Coumarine City - Received Diploma for completing all Kalos Pokédexes (native) from Game Director
    [0x0A7A] = true, -- Coumarine City - Received Diploma for completing Central Kalos Pokédex from Game Director
    [0x0A7B] = true, -- Coumarine City - Received Diploma for completing Coastal Kalos Pokédex from Game Director
    [0x0A7C] = true, -- Coumarine City - Received Diploma for completing Mountain Kalos Pokédex from Game Director
    [0x0A7D] = true, -- Coumarine City - Received Diploma for completing all Kalos Pokédexes from Game Director
    [0x0A7E] = true, -- Coumarine City - Received Diploma for completing National Pokédex from Game Director
    [0x0B90] = true, -- Camphrier Town - [Daily] Received Sweet Heart from maid
    [0x0BA5] = true, -- Ambrette Town - [Daily] Exchanged a Poké Ball for a Dive Ball with the punk guy
    [0x0BA6] = true, -- Lumiose City (South Boulevard) - [Daily] Received Rare Candy from male scientist for a chain length of at least 31 Pokémon with the Poké Radar
    [0x0BAC] = true, -- Ambrette Town - [Daily] Received Health Wing from woman for showing a Pokémon with a Speed stat equals or higher than requested
    [0x0BB3] = true, -- Coumarine City - [Daily] Picked the random berry from the empty stand
    [0x0BB7] = true, -- Camphrier Town - [Daily] Received a berry from man for showing him a Pokémon of the requested type
    [0x0BBD] = true, -- Lumiose City (South Boulevard) - [Daily] Received PP Max from male scientist for a chain length of 21-30 Pokémon with the Poké Radar
    [0x0BBE] = true, -- Lumiose City (South Boulevard) - [Daily] Received PP Up from male scientist for a chain length of 11-20 Pokémon with the Poké Radar
    [0x0BBF] = true, -- Lumiose City (South Boulevard) - [Daily] Received Ultra Ball from male scientist for a chain length of 1-10 Pokémon with the Poké Radar
    [0x0BC5] = true, -- Coumarine City - [Daily] Received Heart Scale from Tierno for showing him a Pokémon with the requested dance move
}

-- Comprehensive Location Definitions matching worlds/pokemon_y/Locations.py
local LOCATION_NAMES = {
    [0x008D] = "Shalour City - Exchanged a Sitrus Berry for a Leppa Berry with guy",
    [0x008E] = "Cyllage City - Received Destiny Knot from maid",
    [0x0090] = "Cyllage City - Received Whipped Dream / Sachet from man",
    [0x0092] = "Lumiose City (South Boulevard) - Received Luxury Ball (x5) from woman",
    [0x0093] = "Shalour City - Received Shoothe Bell from madame for showing her a Pokémon with good friendship",
    [0x0097] = "Shalour City - Received Eviolite from scientist for seeing at least 40 species in Coastal Pokédex",
    [0x00A4] = "Aquacorde Town - Received Potion from shopkeeper",
    [0x00AA] = "Coumarine City - Received Poké Toy from woman for answering her sound quiz first time",
    [0x00B1] = "Lumiose City (South Boulevard) - Received TM54 (False Swipe) from female scientist for seeing at least 20 species in Central Kalos Pokédex",
    [0x00B2] = "Camphrier Town - Received Berry Juice from girl",
    [0x00B3] = "Camphrier Town - Received Ultra Ball from man",
    [0x00B4] = "Camphrier Town - Received Full Heal from boy",
    [0x00B5] = "Camphrier Town - Received TM46 (Thief) from punk girl",
    [0x00B7] = "Coumarine City - Received Lucky Egg from woman for showing her a Pokémon with maximum friendship",
    [0x00C6] = "Lumiose City (South Boulevard) - Received Quick Claw from woman",
    [0x00C7] = "Lumiose City (South Boulevard) - Received Quick Ball (x3) from man",
    [0x00D5] = "Ambrette Town - Received the Douse Drive",
    [0x00D7] = "Santalune Forest - Received Poké Ball from Calem/Serena if interacted",
    [0x00FE] = "Lumiose City (South Boulevard) - Received Timer Ball (x3) from man",
    [0x00FF] = "Cyllage City - Received Persim Berry (x3) from girl for answering her quiz",
    [0x0106] = "Parfum Palace - Received Oran Berry from woman",
    [0x0109] = "Ambrette Town - Received TM94 (Rock Smash) from girl",
    [0x010B] = "Santalune City - Received Great Ball from boy",
    [0x010D] = "Lumiose City (Vernal Avenue) - Received Pearl String (x2) from madame for showing her a Furfrou that has kept the same trim for 15 days",
    [0x010E] = "Tower of Mastery - Received TM47 (Low Sweep) from ace trainer",
    [0x011A] = "Coumarine City - Received Good Rod from fisherman",
    [0x011C] = "Reflection Cave - Received Reveal Glass from female scientist for showing her a Tornadus / Thundurus / Landorus",
    [0x011D] = "Azure Bay - Received Ampharosite from old man",
    [0x011E] = "Ambrette Town - Received Aerodactylite from male scientist",
    [0x0146] = "Shalour City - Exchanged the Intriguing Stone for a Sun Stone with hiker",
    [0x0189] = "Lumiose City (Lysandre Cafe) - Team Flame Grunt M Battle",
    [0x018A] = "Lumiose City (Lysandre Cafe) - Team Flame Grunt F Battle",
    [0x0191] = "Ambrette Gate - Received Rocky Helmet from woman",
    [0x0193] = "Coumarine Gate - Received Black Sludge from punk guy",
    [0x0195] = "Coumarine City - Received Silk Scarf from old man",
    [0x019B] = "Coumarine City - Received Metronome from man",
    [0x019C] = "Route 12 - Received TM45 (Attract) from girl",
    [0x019E] = "Ambrette Town - Received TM96 (Nature Power) from woman",
    [0x01A1] = "Geosenge Town - Received TM66 (Payback) from old man",
    [0x01A3] = "Cyllage City - Received TM44 (Rest) from guy",
    [0x01A4] = "Cyllage City - Received TM88 (Sleep Talk) from girl",
    [0x01A5] = "Connecting Cave - Received TM21 (Frustration) from Backpacker",
    [0x01AC] = "Santalune City - Received X Attack (x3) and X Defense (x3) from old man",
    [0x01AD] = "Shalour City - Received Stardust (x5) from girl for helping her",
    [0x01AE] = "Geosenge Town - Received Everstone from female scientist",
    [0x0301] = "Victory Road (Entrance) - Ace Trainer Robbie Battle",
    [0x044D] = "Route 13 - Found Power Plant Pass",
    [0x044E] = "Santalune City - Found Super Potion",
    [0x044F] = "Santalune City - Found Great Ball",
    [0x0450] = "Santalune City - Found Antidote",
    [0x0451] = "Route 4 - Found Honey (recurring)",
    [0x0452] = "Route 4 - Found Honey (recurring) (2)",
    [0x0453] = "Route 4 - Found Honey (recurring) (3)",
    [0x0454] = "Route 4 - Found Super Potion",
    [0x0455] = "Route 5 - Found Paralyze Heal",
    [0x0456] = "Route 5 - Found Super Potion",
    [0x0457] = "Camphrier Town - Found Antidote",
    [0x0458] = "Camphrier Town - Found Ether",
    [0x0459] = "Route 6 - Found Antidote",
    [0x045A] = "Route 6 - Found Tiny Mushroom",
    [0x045B] = "Parfum Palace - Found Rare Candy",
    [0x045C] = "Parfum Palace - Found X Sp. Atk",
    [0x045D] = "Parfum Palace - Found Pretty Wing (recurring)",
    [0x045E] = "Route 8 - Found Super Potion",
    [0x045F] = "Route 8 - Found Escape Rope",
    [0x0460] = "Route 8 - Found Pearl (recurring)",
    [0x0461] = "Route 8 - Found Ultra Ball",
    [0x0462] = "Route 8 - Found Heart Scale",
    [0x0463] = "Route 8 - Found Stardust (recurring)",
    [0x0464] = "Route 8 - Found Heart Scale (recurring)",
    [0x0465] = "Ambrette Town - Found Rare Candy",
    [0x0466] = "Ambrette Town - Found X Attack",
    [0x0467] = "Route 9 - Found Super Repel",
    [0x0468] = "Cyllage City - Found Ether",
    [0x0469] = "Cyllage City - Found Pearl",
    [0x046A] = "Cyllage City - Found X Speed",
    [0x046B] = "Cyllage City - Found Protein",
    [0x046C] = "Route 10 - Found Revive",
    [0x046D] = "Route 10 - Found Paralyze Heal",
    [0x046E] = "Route 10 - Found Burn Heal",
    [0x046F] = "Route 11 - Found Super Potion",
    [0x0470] = "Route 11 - Found Thunder Stone",
    [0x0471] = "Shalour City - Found X Sp. Atk",
    [0x0472] = "Shalour City - Found Stardust (recurring)",
    [0x0473] = "Shalour City - Found Max Repel",
    [0x0474] = "Route 12 - Found Honey (recurring)",
    [0x0475] = "Route 12 - Found Net Ball",
    [0x0476] = "Route 12 - Found Water Stone",
    [0x0477] = "Route 12 - Found Ice Heal",
    [0x0478] = "Azure Bay - Found Star Piece",
    [0x0479] = "Azure Bay - Found Hyper Potion",
    [0x047A] = "Azure Bay - Found Heart Scale",
    [0x047B] = "Coumarine City - Found Elixir",
    [0x047C] = "Coumarine City - Found Awakening",
    [0x047D] = "Coumarine City - Found Max Repel",
    [0x047E] = "Route 13 - Found Guard Spec.",
    [0x047F] = "Route 13 - Found Heat Rock",
    [0x0480] = "Route 13 - Found Nest Ball",
    [0x0481] = "Route 13 - Found Hyper Potion",
    [0x0482] = "Route 13 - Found PP Up",
    [0x0483] = "Route 13 - Found X Accuracy",
    [0x0484] = "Route 13 - Found Stardust",
    [0x0485] = "Route 13 - Found Fire Stone",
    [0x0486] = "Route 13 - Found Star Piece",
    [0x0487] = "Route 14 - Found Super Potion",
    [0x0488] = "Route 14 - Found Tiny Mushroom",
    [0x0489] = "Route 14 - Found Revive",
    [0x048A] = "Laverre City - Found Tiny Mushroom (recurring)",
    [0x048B] = "Laverre City - Found Leaf Stone",
    [0x048C] = "Laverre City - Found Ultra Ball",
    [0x048D] = "Poké Ball Factory - Found Dusk Ball",
    [0x048E] = "Poké Ball Factory - Found Burn Heal",
    [0x048F] = "Poké Ball Factory - Found Poké Ball",
    [0x0490] = "Poké Ball Factory - Found Hyper Potion",
    [0x0491] = "Route 15 - Found HP Up",
    [0x0492] = "Route 15 - Found Antidote",
    [0x0493] = "Route 15 - Found Tiny Mushroom",
    [0x0494] = "Route 15 - Found X Defense",
    [0x0495] = "Route 15 - Found Pretty Wing",
    [0x0496] = "Route 16 - Found Repel",
    [0x0497] = "Route 16 - Found Rare Candy",
    [0x0498] = "Route 16 - Found Big Mushroom",
    [0x0499] = "Route 16 - Found Max Revive",
    [0x049A] = "Dendemille Town - Found Heal Ball",
    [0x049B] = "Dendemille Town - Found X Speed",
    [0x049C] = "Dendemille Town - Found Nugget",
    [0x049D] = "Frost Cavern - Found Escape Rope",
    [0x049E] = "Frost Cavern - Found X Sp. Def",
    [0x049F] = "Frost Cavern - Found Ice Heal",
    [0x04A0] = "Frost Cavern - Found Dusk Ball",
    [0x04A1] = "Frost Cavern - Found Dire Hit",
    [0x04A2] = "Frost Cavern - Found Pearl",
    [0x04A3] = "Frost Cavern - Found Super Potion",
    [0x04A4] = "Frost Cavern - Found Ice Heal (2)",
    [0x04A5] = "Frost Cavern - Found Elixir",
    [0x04A6] = "Frost Cavern - Found PP Up",
    [0x04A7] = "Route 18 - Found Timer Ball",
    [0x04A8] = "Route 18 - Found Paralyze Heal",
    [0x04A9] = "Anistar City - Found Pretty Wing (recurring)",
    [0x04AA] = "Anistar City - Found Escape Rope",
    [0x04AB] = "Anistar City - Found Super Repel",
    [0x04AC] = "Anistar City - Found Sun Stone",
    [0x04AD] = "Route 19 - Found Poké Ball",
    [0x04AE] = "Route 19 - Found Ether",
    [0x04AF] = "Route 19 - Found Honey",
    [0x04B0] = "Route 19 - Found Super Potion",
    [0x04B1] = "Terminus Cave - Found Dusk Ball",
    [0x04B2] = "Terminus Cave - Found Hyper Potion",
    [0x04B3] = "Terminus Cave - Found Moon Stone",
    [0x04B4] = "Terminus Cave - Found Max Repel",
    [0x04B5] = "Terminus Cave - Found Iron",
    [0x04B6] = "Terminus Cave - Found Dire Hit",
    [0x04B7] = "Terminus Cave - Found Max Potion",
    [0x04B8] = "Terminus Cave - Found Big Nugget",
    [0x04B9] = "Terminus Cave - Found Normal Gem",
    [0x04BA] = "Couriway Town - Found Pretty Wing",
    [0x04BB] = "Couriway Town - Found Ether",
    [0x04BC] = "Couriway Town - Found Burn Heal",
    [0x04BD] = "Couriway Town - Found Prism Scale (recurring)",
    [0x04BE] = "Route 20 - Found Net Ball",
    [0x04BF] = "Route 20 - Found Antidote",
    [0x04C0] = "Route 20 - Found Damp Rock",
    [0x04C1] = "Route 20 - Found Escape Rope",
    [0x04C2] = "Route 20 - Found Timer Ball",
    [0x04C3] = "Snowbelle City - Found Icy Rock",
    [0x04C4] = "Snowbelle City - Found X Sp. Atk",
    [0x04C5] = "Snowbelle City - Found Full Heal",
    [0x04C6] = "Route 21 - Found Repeat Ball",
    [0x04C7] = "Route 21 - Found Antidote",
    [0x04C8] = "Route 21 - Found Mental Herb",
    [0x04C9] = "Route 21 - Found Tiny Mushroom",
    [0x04CA] = "Route 21 - Found Balm Mushroom",
    [0x04CB] = "Pokémon Village - Found Honey",
    [0x04CC] = "Pokémon Village - Found Pretty Wing",
    [0x04CD] = "Pokémon Village - Found Honey (2)",
    [0x04CE] = "Route 22 - Found Guard Spec.",
    [0x04CF] = "Route 22 - Found PP Up",
    [0x04D0] = "Route 22 - Found Pearl String",
    [0x04D1] = "Route 22 - Found Elixir",
    [0x04D2] = "Route 22 - Found Max Elixir",
    [0x04D3] = "Route 22 - Found Full Restore",
    [0x04D4] = "Victory Road - Found X Attack",
    [0x04D5] = "Victory Road - Found Full Heal",
    [0x04D6] = "Victory Road - Found Hyper Potion",
    [0x04D7] = "Victory Road - Found Ultra Ball",
    [0x04D8] = "Victory Road - Found Smooth Rock",
    [0x04D9] = "Victory Road - Found Revive",
    [0x04DA] = "Victory Road - Found Pretty Wing",
    [0x04DB] = "Victory Road - Found Escape Rope",
    [0x04DC] = "Victory Road - Found Max Repel",
    [0x04DD] = "Victory Road - Found X Defense",
    [0x04DE] = "Victory Road - Found Max Ether",
    [0x04DF] = "Victory Road - Found Star Piece",
    [0x04E0] = "Couriway Town - Found Poké Ball",
    [0x04E1] = "Kiloude City - Found Max Revive",
    [0x04E2] = "Kiloude City - Found PP Up",
    [0x04E3] = "Unknown Dungeon - Found Oval Stone (recurring)",
    [0x051A] = "Santalune Forest - Potion item ball disappeared",
    [0x051B] = "Santalune Forest - Poké Ball item ball disappeared",
    [0x051C] = "Route 3 - Super Potion item ball disappeared",
    [0x051D] = "Route 3 - Revive item ball disappeared",
    [0x051E] = "Route 3 - Dawn Stone item ball disappeared",
    [0x051F] = "Route 22 - Super Potion item ball disappeared",
    [0x0520] = "Route 22 - Elixir item ball disappeared",
    [0x0521] = "Route 22 - Draco Plate item ball disappeared",
    [0x0522] = "Route 4 - Great Ball item ball disappeared",
    [0x0523] = "Route 4 - Antidote item ball disappeared",
    [0x0524] = "Route 4 - Super Potion item ball disappeared",
    [0x0525] = "Route 4 - Repel item ball disappeared",
    [0x0526] = "Route 4 - Poison Barb item ball disappeared",
    [0x0527] = "Route 4 - Net Ball item ball disappeared",
    [0x0528] = "Route 4 - Ether item ball disappeared",
    [0x0529] = "Route 5 - Super Potion item ball disappeared",
    [0x052A] = "Route 5 - Super Potion item ball disappeared (2)",
    [0x052B] = "Route 5 - Great Ball item ball disappeared",
    [0x052C] = "Route 5 - TM01 (Hone Claws) item ball disappeared",
    [0x052D] = "Route 5 - X Attack item ball disappeared",
    [0x052E] = "Route 5 - Sharp Beak item ball disappeared",
    [0x052F] = "Route 6 - X Sp. Atk item ball disappeared",
    [0x0530] = "Route 6 - Antidote item ball disappeared",
    [0x0531] = "Route 6 - X Speed item ball disappeared",
    [0x0532] = "Route 6 - Paralyze Heal item ball disappeared",
    [0x0533] = "Route 6 - TM09 (Venosock) item ball disappeared",
    [0x0534] = "Route 6 - Awakening item ball disappeared",
    [0x0535] = "Route 6 - Super Repel item ball disappeared",
    [0x0536] = "Route 6 - Ultra Ball item ball disappeared",
    [0x0537] = "Route 7 - X Sp. Def item ball disappeared",
    [0x0538] = "Route 7 - PP Up item ball disappeared",
    [0x0539] = "Route 7 - Tiny Mushroom item ball disappeared",
    [0x053A] = "Route 7 - Silver Powder item ball disappeared",
    [0x053B] = "Connecting Cave - TM40 (Aerial Ace) item ball disappeared",
    [0x053C] = "Route 8 - HP Up item ball disappeared",
    [0x053D] = "Route 8 - Leaf Stone item ball disappeared",
    [0x053E] = "Route 8 - Water Stone item ball disappeared",
    [0x053F] = "Route 8 - Heart Scale item ball disappeared",
    [0x0540] = "Route 8 - TM19 (Roost) item ball disappeared",
    [0x0541] = "Route 9 - X Defense item ball disappeared",
    [0x0542] = "Route 9 - Paralyze Heal item ball disappeared",
    [0x0543] = "Route 9 - Fire Stone item ball disappeared",
    [0x0544] = "Route 9 - Dusk Ball item ball disappeared",
    [0x0545] = "Glittering Cave - Hard Stone item ball disappeared",
    [0x0546] = "Glittering Cave - TM65 (Shadow Claw) item ball disappeared",
    [0x0547] = "Route 10 - TM73 (Thunder Wave) item ball disappeared",
    [0x0548] = "Route 10 - Mind Plate item ball disappeared",
    [0x0549] = "Route 10 - X Accuracy item ball disappeared",
    [0x054A] = "Route 10 - Thunder Stone item ball disappeared",
    [0x054B] = "Route 11 - TM69 (Rock Polish) item ball disappeared",
    [0x054C] = "Route 11 - Hyper Potion item ball disappeared",
    [0x054D] = "Reflection Cave - Nest Ball item ball disappeared",
    [0x054E] = "Reflection Cave - Revive item ball disappeared",
    [0x054F] = "Reflection Cave - Moon Stone item ball disappeared",
    [0x0550] = "Reflection Cave - Black Belt item ball disappeared",
    [0x0551] = "Reflection Cave - Hyper Potion item ball disappeared",
    [0x0552] = "Reflection Cave - Escape Rope item ball disappeared",
    [0x0553] = "Reflection Cave - Iron item ball disappeared",
    [0x0554] = "Reflection Cave - Earth Plate item ball disappeared",
    [0x0555] = "Reflection Cave - TM74 (Gyro Ball) item ball disappeared",
    [0x0556] = "Route 12 - Sachet item ball disappeared",
    [0x0557] = "Route 12 - Shiny Stone item ball disappeared",
    [0x0558] = "Route 12 - Whipped Dream item ball disappeared",
    [0x0559] = "Parfum Palace - Guard Spec. item ball disappeared",
    [0x055A] = "Route 12 - Leftovers item ball disappeared",
    [0x055B] = "Azure Bay - Deep Sea Tooth item ball disappeared",
    [0x055C] = "Azure Bay - TM81 (X-Scissor) item ball disappeared",
    [0x055D] = "Azure Bay - Dive Ball item ball disappeared",
    [0x055E] = "Azure Bay - Big Pearl item ball disappeared",
    [0x055F] = "Azure Bay - Splash Plate item ball disappeared",
    [0x0560] = "Route 13 - Smooth Rock item ball disappeared",
    [0x0561] = "Route 13 - Burn Heal item ball disappeared",
    [0x0562] = "Route 13 - TM57 (Charge Beam) item ball disappeared",
    [0x0563] = "Route 13 - Flame Plate item ball disappeared",
    [0x0564] = "Route 13 - Sun Stone item ball disappeared",
    [0x0565] = "Route 13 - Rare Candy item ball disappeared",
    [0x0566] = "Route 14 - Cleanse Tag item ball disappeared",
    [0x0567] = "Route 14 - Big Mushroom item ball disappeared",
    [0x0568] = "Route 14 - Hyper Potion item ball disappeared",
    [0x0569] = "Route 14 - Damp Rock item ball disappeared",
    [0x056A] = "Route 14 - Spell Tag item ball disappeared",
    [0x056B] = "Route 14 - TM61 (Will-O-Wisp) item ball disappeared",
    [0x056C] = "Poké Ball Factory - Max Revive item ball disappeared",
    [0x056D] = "Poké Ball Factory - Max Ether item ball disappeared",
    [0x056E] = "Poké Ball Factory - Quick Ball item ball disappeared",
    [0x056F] = "Poké Ball Factory - Metal Coat item ball disappeared",
    [0x0570] = "Poké Ball Factory - Timer Ball item ball disappeared",
    [0x0571] = "Route 15 - Net Ball item ball disappeared",
    [0x0572] = "Route 15 - Revive item ball disappeared",
    [0x0573] = "Route 15 - Dire Hit item ball disappeared",
    [0x0574] = "Route 15 - PP Up item ball disappeared",
    [0x0575] = "Route 15 - Full Heal item ball disappeared",
    [0x0576] = "Route 15 - Protein item ball disappeared",
    [0x0577] = "Route 15 - Macho Brace item ball disappeared",
    [0x0578] = "Route 15 - Stone Plate item ball disappeared",
    [0x0579] = "Route 15 - TM97 (Dark Pulse) item ball disappeared",
    [0x057A] = "Route 16 - Rare Candy item ball disappeared",
    [0x057B] = "Route 16 - Max Potion item ball disappeared",
    [0x057C] = "Route 16 - Fist Plate item ball disappeared",
    [0x057D] = "Route 16 - Dive Ball item ball disappeared",
    [0x057E] = "Lost Hotel - Smoke Ball item ball disappeared",
    [0x057F] = "Lost Hotel - Twisted Spoon item ball disappeared",
    [0x0580] = "Lost Hotel - TM95 (Snarl) item ball disappeared",
    [0x0581] = "Lost Hotel - Dread Plate item ball disappeared",
    [0x0582] = "Lost Hotel - Protector item ball disappeared",
    [0x0583] = "Frost Cavern - Heart Scale item ball disappeared",
    [0x0584] = "Frost Cavern - TM71 (Stone Edge) item ball disappeared",
    [0x0585] = "Frost Cavern - Hyper Potion item ball disappeared",
    [0x0586] = "Frost Cavern - Ice Heal item ball disappeared",
    [0x0587] = "Frost Cavern - Max Repel item ball disappeared",
    [0x0588] = "Frost Cavern - Never-Melt Ice item ball disappeared",
    [0x0589] = "Frost Cavern - TM79 (Frost Breath) item ball disappeared",
    [0x058A] = "Frost Cavern - Ether item ball disappeared",
    [0x058B] = "Frost Cavern - Zinc item ball disappeared",
    [0x058C] = "Frost Cavern - Icy Rock item ball disappeared",
    [0x058D] = "Route 18 - Icicle Plate item ball disappeared",
    [0x058E] = "Route 18 - Calcium item ball disappeared",
    [0x058F] = "Route 18 - Rare Candy item ball disappeared",
    [0x0590] = "Route 19 - Hyper Potion item ball disappeared",
    [0x0591] = "Route 19 - PP Up item ball disappeared",
    [0x0592] = "Route 19 - X Defense item ball disappeared",
    [0x0593] = "Route 19 - Max Ether item ball disappeared",
    [0x0594] = "Terminus Cave - Star Piece item ball disappeared",
    [0x0595] = "Terminus Cave - Heat Rock item ball disappeared",
    [0x0596] = "Terminus Cave - Escape Rope item ball disappeared",
    [0x0597] = "Terminus Cave - Reaper Cloth item ball disappeared",
    [0x0598] = "Terminus Cave - Dusk Stone item ball disappeared",
    [0x0599] = "Terminus Cave - X Attack item ball disappeared",
    [0x059A] = "Terminus Cave - Elixir item ball disappeared",
    [0x059B] = "Terminus Cave - Full Heal item ball disappeared",
    [0x059C] = "Terminus Cave - Iron Plate item ball disappeared",
    [0x059D] = "Terminus Cave - TM30 (Shadow Ball) item ball disappeared",
    [0x059E] = "Terminus Cave - Griseous Orb item ball disappeared",
    [0x059F] = "Terminus Cave - Dragon Scale item ball disappeared",
    [0x05A0] = "Terminus Cave - TM31 (Brick Break) item ball disappeared",
    [0x05A1] = "Route 20 - Max Revive item ball disappeared",
    [0x05A2] = "Route 20 - HP Up item ball disappeared",
    [0x05A3] = "Route 20 - Rare Bone item ball disappeared",
    [0x05A4] = "Route 20 - PP Up item ball disappeared",
    [0x05A5] = "Route 20 - Toxic Plate item ball disappeared",
    [0x05A6] = "Route 20 - TM36 (Sludge Bomb) item ball disappeared",
    [0x05A7] = "Route 21 - Paralyze Heal item ball disappeared",
    [0x05A8] = "Route 21 - Protein item ball disappeared",
    [0x05A9] = "Route 21 - Meadow Plate item ball disappeared",
    [0x05AA] = "Route 21 - X Accuracy item ball disappeared",
    [0x05AB] = "Route 21 - TM53 (Energy Ball) item ball disappeared",
    [0x05AC] = "Pokémon Village - Max Ether item ball disappeared",
    [0x05AD] = "Pokémon Village - Full Restore item ball disappeared",
    [0x05AE] = "Pokémon Village - Pixie Plate item ball disappeared",
    [0x05AF] = "Pokémon Village - TM29 (Psychic) item ball disappeared",
    [0x05B0] = "Route 21 - Insect Plate item ball disappeared",
    [0x05B1] = "Route 21 - Elixir item ball disappeared",
    [0x05B2] = "Route 21 - TM22 (Solar Beam) item ball disappeared",
    [0x05B3] = "Route 21 - Rare Candy item ball disappeared",
    [0x05B4] = "Route 21 - Repeat Ball item ball disappeared",
    [0x05B5] = "Victory Road - Dusk Ball item ball disappeared",
    [0x05B6] = "Victory Road - TM03 (Psyshock) item ball disappeared",
    [0x05B7] = "Victory Road - Rare Candy item ball disappeared",
    [0x05B8] = "Victory Road - Carbos item ball disappeared",
    [0x05B9] = "Victory Road - PP Up item ball disappeared",
    [0x05BA] = "Victory Road - Zinc item ball disappeared",
    [0x05BB] = "Victory Road - Max Elixir item ball disappeared",
    [0x05BC] = "Victory Road - Dragon Fang item ball disappeared",
    [0x05BD] = "Victory Road - Full Restore item ball disappeared",
    [0x05BE] = "Victory Road - TM02 (Dragon Claw) item ball disappeared",
    [0x05BF] = "Camphrier Town - X Attack item ball disappeared",
    [0x05C0] = "Ambrette Town - Pearl item ball disappeared",
    [0x05C1] = "Cyllage City - Super Potion item ball disappeared",
    [0x05C2] = "Cyllage City - X Sp. Atk item ball disappeared",
    [0x05C3] = "Cyllage City - X Defense item ball disappeared",
    [0x05C4] = "Geosenge Town - Timer Ball item ball disappeared",
    [0x05C5] = "Coumarine City - Sky Plate item ball disappeared",
    [0x05C6] = "Laverre City - Ether item ball disappeared",
    [0x05C7] = "Dendemille Town - Big Root item ball disappeared",
    [0x05C8] = "Couriway Town - Rare Candy item ball disappeared",
    [0x05C9] = "Couriway Town - Max Potion item ball disappeared",
    [0x05CA] = "Couriway Town - TM80 (Rock Slide) item ball disappeared",
    [0x05CB] = "Snowbelle City - Full Restore item ball disappeared",
    [0x05CC] = "Route 7 - Heal Ball item ball disappeared",
    [0x05CD] = "Shabboneau Castle - Escape Rope item ball disappeared",
    [0x05CE] = "Parfum Palace - Ether item ball disappeared",
    [0x05CF] = "Parfum Palace - Amulet Coin item ball disappeared",
    [0x05D0] = "Parfum Palace - Antidote item ball disappeared",
    [0x05D1] = "Kalos Power Plant - Zap Plate item ball disappeared",
    [0x05D2] = "Lysandre Labs - Hyper Potion item ball disappeared",
    [0x05D3] = "Lysandre Labs - Black Glasses item ball disappeared",
    [0x05D4] = "Lysandre Labs - Revive item ball disappeared",
    [0x05D5] = "Lysandre Labs - Rare Candy item ball disappeared",
    [0x05D6] = "Chamber of Emptiness - Spooky Plate item ball disappeared",
    [0x05D7] = "Parfum Palace - Revive item ball disappeared",
    [0x05D8] = "Parfum Palace - Super Potion item ball disappeared",
    [0x05D9] = "Santalune Forest - Potion item ball disappeared (2)",
    [0x05DA] = "Shalour City - Max Ether item ball disappeared",
    [0x05DB] = "Kiloude City - Nugget item ball disappeared",
    [0x05DC] = "Route 14 - Rare Candy item ball disappeared",
    [0x05DD] = "Santalune Forest - Potion item ball disappeared (3)",
    [0x05DE] = "Santalune Forest - Antidote item ball disappeared",
    [0x05DF] = "Route 22 - TM26 (Earthquake) item ball disappeared",
    [0x05E0] = "Camphrier Town - Star Piece item ball disappeared",
    [0x05E1] = "Azure Bay - Deep Sea Scale item ball disappeared",
    [0x05E2] = "Terminus Cave - Adamant Orb item ball disappeared",
    [0x05E3] = "Terminus Cave - Lustrous Orb item ball disappeared",
    [0x05E4] = "Geosenge Town - Soft Sand item ball disappeared",
    [0x05E5] = "Route 7 - Miracle Seed item ball disappeared",
    [0x05E6] = "Glittering Cave - Escape Rope item ball disappeared",
    [0x05E7] = "Parfum Palace - HM01 (Cut) item ball disappeared",
    [0x05E8] = "Victory Road - Quick Ball item ball disappeared",
    [0x06CD] = "Route 12 - Battled Youngster Aidan",
    [0x06CF] = "Santalune Forest - Battled Lass Lise",
    [0x06D2] = "Santalune Area - Bug Badge",
    [0x06E0] = "Route 8 (Cliffside) - Battled Sky Trainer Howe",
    [0x06E1] = "Shalour Area - Rumble Badge",
    [0x06E2] = "Coumarine Area - Plant Badge",
    [0x06E3] = "Lumiose Area - Voltage Badge",
    [0x06E4] = "Laverre Area - Fairy Badge",
    [0x06E5] = "Anistar Area - Psychic Badge",
    [0x06E6] = "Snowbelle Area - Iceberg Badge",
    [0x06E7] = "Reflection Cave (B1F) - Battled Ace Trainer Emil",
    [0x06E8] = "Lumiose City (Gym 4F) - Ace Trainer Mathis",
    [0x06E9] = "Lumiose City (Gym 4F) - Ace Trainer Maxim",
    [0x06EA] = "Lumiose City (Gym 4F) - Ace Trainer Rico",
    [0x06EB] = "Snowbelle City (Gym) - Ace Trainer Theo",
    [0x06EC] = "Snowbelle City (Gym) - Ace Trainer Viktor",
    [0x06F0] = "Santalune Forest - Battled Youngster Joey",
    [0x06F1] = "Route 2 - Battled Youngster Austin",
    [0x06F3] = "Santalune City (Gym) - Battled Youngster David",
    [0x06F4] = "Santalune City (Gym) - Battled Youngster Zachary",
    [0x06F5] = "Route 5 - Battled Youngster Keita",
    [0x06F6] = "Route 5 - Battled Youngster Anthony",
    [0x06F7] = "Route 6 - Battled Youngster Jacob",
    [0x06F8] = "Route 6 - Battled Youngster Tyler",
    [0x06F9] = "Santalune Forest - Battled Lass Anna",
    [0x06FA] = "Route 22 - Battled Lass Elin",
    [0x06FB] = "Route 22 - Battled Lass Elsa",
    [0x06FC] = "Santalune City (Gym) - Battled Lass Charlotte",
    [0x06FD] = "Route 3 - Battled Schoolboy Brighton",
    [0x06FE] = "Route 22 - Battled Schoolboy Rabbie",
    [0x0700] = "Route 3 - Battled Schoolgirl Bridget",
    [0x0701] = "Route 22 - Battled Schoolgirl Mackenzie",
    [0x0703] = "Route 3 - Battled Preschooler Oliver",
    [0x0704] = "Route 4 - Battled Preschooler Adrian",
    [0x0705] = "Route 3 - Battled Preschooler Ella",
    [0x0706] = "Route 4 - Battled Preschooler Mia",
    [0x0707] = "Route 22 - Battled Rising Star Loïc",
    [0x0708] = "Route 5 - Battled Rising Star Hamish",
    [0x0709] = "Route 22 - Battled Rising Star Louise",
    [0x070B] = "Cyllage City (Gym) - Battled Rising Star Manon",
    [0x070C] = "Cyllage City (Gym) - Battled Rising Star Didier",
    [0x070D] = "Route 22 - Battled Ace Trainer Adelbert",
    [0x070E] = "Route 22 - Battled Ace Trainer Hilde",
    [0x070F] = "Route 4 - Battled Poké Fan Gabe",
    [0x0710] = "Route 4 - Battled Poké Fan Agnes",
    [0x0711] = "Route 6 - Battled Poké Fan Family Jan & Erin",
    [0x0712] = "Route 4 - Battled Gardener Wheaton",
    [0x0713] = "Route 4 - Battled Gardener Fabian",
    [0x0714] = "Route 4 - Battled Gardener Grover",
    [0x0718] = "Cyllage Area - Cliff Badge",
    [0x0719] = "Route 6 - Battled Tourist Takemi",
    [0x071A] = "Route 6 - Battled Tourist Mari",
    [0x071B] = "Route 6 - Battled Tourist Eriko",
    [0x071C] = "Route 6 - Battled Tourist Hiroko",
    [0x071D] = "Route 10 - Battled Tourist Fumiko",
    [0x071E] = "Route 10 - Battled Tourist Tomoko",
    [0x071F] = "Shalour City (Gym) - Battled Roller Skater Shun",
    [0x0720] = "Shalour City (Gym) - Battled Roller Skater Rolanda",
    [0x0721] = "Route 5 - Battled Backpacker Heike",
    [0x0722] = "Route 6 - Battled Backpacker Jerome",
    [0x0723] = "Route 6 - Battled Backpacker Roderick",
    [0x0724] = "Route 5 - Battled Twins Faith & Joy",
    [0x0725] = "Route 6 - Battled Beauty Brigitte",
    [0x0726] = "Route 7 - Battled Artist Pierre",
    [0x0727] = "Route 7 - Battled Artist Georgia",
    [0x0728] = "Route 7 - Battled Artist Family Mona & Paolo",
    [0x072B] = "Connecting Cave - Battled Pokemon Breeder Mercy",
    [0x072C] = "Route 8 (Coast) - Battled Fisherman Wharton",
    [0x072D] = "Route 8 (Coast) - Battled Fisherman Shad",
    [0x072E] = "Azure Bay - Battled Fisherman Ewan",
    [0x072F] = "Route 8 (Coast) - Battled Swimmer ♀ Genevieve",
    [0x0730] = "Route 8 (Coast) - Battled Swimmer ♀ Marissa",
    [0x0731] = "Route 8 (Coast) - Battled Swimmer ♂ Ramses",
    [0x0732] = "Route 8 (Coast) - Battled Swimmer ♂ Estaban",
    [0x0734] = "Route 8 (Cliffside) - Battled Black Belt Cadoc",
    [0x0735] = "Cyllage City (Gym) - Battled Hiker Bernard",
    [0x0736] = "Cyllage City (Gym) - Battled Hiker Craig",
    [0x073A] = "Glittering Cave - Battled Team Flare Grunt",
    [0x073C] = "Route 10 - Battled Team Flare Grunt",
    [0x073D] = "Route 10 - Battled Psychic Sayid",
    [0x073E] = "Route 11 - Battled Brains & Brawn Frank & Sly",
    [0x073F] = "Route 11 - Battled Psychic Emanuel",
    [0x0740] = "Route 11 - Battled Battle Girl Gerardine",
    [0x0741] = "Route 8 (Coast) - Battled Sky Trainer Colm",
    [0x0742] = "Route 9 - Battled Sky Trainer Orion",
    [0x0743] = "Route 8 (Coast) - Battled Sky Trainer Aveza",
    [0x0744] = "Route 11 - Battled Sky Trainer Yvette",
    [0x0745] = "Coumarine City (Gym) - Battled Pokémon Ranger Brooke",
    [0x0746] = "Coumarine City (Gym) - Battled Pokémon Ranger Twiggy",
    [0x0747] = "Coumarine City (Gym) - Battled Pokémon Ranger Chaise",
    [0x0748] = "Coumarine City (Gym) - Battled Pokémon Ranger Maurice",
    [0x074D] = "Route 10 - Battled Team Flare Grunt",
    [0x0758] = "Reflection Cave (B1F) - Battled Honeymooners Yuu & Ami",
    [0x0759] = "Reflection Cave (B1F) - Battled Tourist Haruto",
    [0x075A] = "Reflection Cave (B1F) - Battled Tourist Monami",
    [0x075B] = "Reflection Cave (B1F) - Battled Psychic Franz",
    [0x075C] = "Reflection Cave (1F) - Battled Backpacker Lane",
    [0x075D] = "Reflection Cave (1F) - Battled Hiker Dunstan",
    [0x075E] = "Shalour City (Gym) - Battled Roller Skater Kate",
    [0x075F] = "Shalour City (Gym) - Battled Roller Skater Dash",
    [0x0760] = "Route 12 - Battled Backpacker Joren",
    [0x0761] = "Route 12 - Battled Fisherman Murray",
    [0x0762] = "Route 12 - Battled Pokémon Breeder Foster",
    [0x0763] = "Route 12 - Battled Pokémon Breeder Amala",
    [0x0764] = "Route 12 - Battled Swimmer ♂ Alessandro",
    [0x0765] = "Reflection Cave (1F) - Battled Ace Trainer Monique",
    [0x0768] = "Route 14 - Fairy Tale Girl Imogen",
    [0x0769] = "Route 14 - Hex Maniac Anina",
    [0x076A] = "Route 14 - Pokémon Ranger Melina",
    [0x076C] = "Route 14 - Pokémon Ranger Reed",
    [0x076D] = "Route 14 - Pokémon Ranger Nash",
    [0x076E] = "Reflection Cave (1F) - Battled Battle Girl Hedvig",
    [0x076F] = "Reflection Cave (B1F) - Battled Black Belt Igor",
    [0x0770] = "Route 5 - Battled Roller Skater Winnie",
    [0x0771] = "Route 5 - Battled Roller Skater Florin",
    [0x0774] = "Snowbelle City (Gym) - Ace Trainer Shannon",
    [0x0775] = "Snowbelle City (Gym) - Ace Trainer Imelda",
    [0x0776] = "Anistar City (Gym) - Psychic Paschal",
    [0x0777] = "Anistar City (Gym) - Psychic Harry",
    [0x0778] = "Anistar City (Gym) - Psychic Arthur",
    [0x077D] = "Power Plant - Team Flare Grunt M",
    [0x077E] = "Power Plant - Team Flare Grunt M",
    [0x077F] = "Power Plant - Team Flare Grunt F",
    [0x0780] = "Power Plant - Team Flare Grunt F",
    [0x0781] = "Power Plant - Team Flare Grunt F",
    [0x0782] = "Power Plant - Team Flare Grunt F",
    [0x07BF] = "Laverre City (Gym) - Furisode Girl Katherine",
    [0x07C1] = "Laverre City (Gym) - Furisode Girl Kali",
    [0x07C4] = "Laverre City (Gym) - Furisode Girl Blossom",
    [0x07C6] = "Laverre City (Gym) - Furisode Girl Linnea",
    [0x07FD] = "PokeBall Factory - Team Flare Grunt M",
    [0x07FE] = "PokeBall Factory - Team Flare Grunt M",
    [0x0801] = "Lysandre Lab - Team Flare Grunt M",
    [0x0802] = "Lysandre Lab - Team Flare Grunt M",
    [0x0803] = "Lysandre Lab - Team Flare Grunt M",
    [0x0807] = "PokeBall Factory - Team Flare Grunt F",
    [0x0808] = "PokeBall Factory - Team Flare Grunt F",
    [0x080A] = "Lysandre Lab - Team Flare Grunt F",
    [0x080B] = "Lysandre Lab - Team Flare Grunt F",
    [0x080C] = "Lysandre Lab - Team Flare Grunt F",
    [0x082D] = "Frost Cavern (1F) - Ace Trainer Cordelia",
    [0x0830] = "Route 21 - Ace Trainer Mireille",
    [0x0831] = "Frost Cavern (1F) - Ace Trainer Neil",
    [0x0834] = "Route 21 - Ace Trainer Evan",
    [0x0835] = "Route 19 - Hex Maniac Josette",
    [0x0836] = "Route 15 - Hex Maniac Luna",
    [0x0837] = "Route 15 - Hex Maniac Carrie",
    [0x0838] = "Route 16 - Hex Maniac Osanna",
    [0x0839] = "Anistar City (Gym) - Hex Maniac Melanie",
    [0x083A] = "Anistar City (Gym) - Hex Maniac Arachna",
    [0x083B] = "Frost Cavern (2F) - Black Belt Alonzo",
    [0x083C] = "Frost Cavern (3F) - Black Belt Kenji",
    [0x083D] = "Route 18 - Black Belt Yanis",
    [0x083E] = "Terminus Cave (B2F) - Black Belt Ricardo",
    [0x083F] = "Terminus Cave (B2F) - Black Belt Gunnar",
    [0x0840] = "Frost Cavern (Outside) - Artist Salvador",
    [0x0844] = "Terminus Cave (B1F) - Worker Dimitri",
    [0x0845] = "Terminus Cave (B1F) - Worker Narek",
    [0x0846] = "Terminus Cave (B1F) - Worker Yusif",
    [0x0847] = "Frost Cavern (2F) - Brains & Brawn Eoin & Wolf",
    [0x0848] = "Route 16 - Sky Trainer Gavin",
    [0x0849] = "Frost Cavern (Outside) - Sky Trainer Celso",
    [0x084A] = "Route 18 - Sky Trainer Jeremy",
    [0x084B] = "Azure Bay - Battled Sky Trainer Indra",
    [0x084C] = "Route 16 - Sky Trainer Clara",
    [0x084D] = "Frost Cavern (Outside) - Sky Trainer Era",
    [0x084E] = "Route 17 - Sky Trainer Anila",
    [0x084F] = "Route 19 - Sky Trainer Sera",
    [0x0850] = "Lost Hotel - Punk Girl Jeanne",
    [0x0851] = "Lost Hotel - Punk Guy Sid",
    [0x0852] = "Lost Hotel - Punk Guy Jaques",
    [0x0853] = "Lost Hotel - Punk Guy Slater",
    [0x0854] = "Lost Hotel - Punk Girl Cecile",
    [0x0855] = "Route 18 - Youngster Jayden",
    [0x0856] = "Route 16 - Fisherman Finn",
    [0x0857] = "Route 16 - Fisherman Seward",
    [0x0858] = "Route 16 - Fisherman Wade",
    [0x0859] = "Frost Cavern (2F) - Battle Girl Kinsey",
    [0x085A] = "Frost Cavern (3F) - Battle Girl Gabrielle",
    [0x085B] = "Route 18 - Battle Girl Justine",
    [0x085C] = "Terminus Cave (B2F) - Battle Girl Andrea",
    [0x085D] = "Terminus Cave (B2F) - Battle Girl Hailey",
    [0x085E] = "Route 19 - Swimmer F Coral",
    [0x085F] = "Route 15 - Mysterious Sisters Rune & Rime",
    [0x0860] = "Route 16 - Mysterious Sisters Achlys & Eos",
    [0x0862] = "Route 21 - Veteran Louis",
    [0x0864] = "Route 21 - Veteran Trisha",
    [0x0865] = "Route 18 - Lass Sara",
    [0x0866] = "Route 15 - Fairy Tale Girl Mahalyn",
    [0x0867] = "Route 16 - Fairy Tale Girl Alice",
    [0x0868] = "Route 19 - Fairy Tale Girl Lovelyn",
    [0x0869] = "Frost Cavern (1F) - Hiker Alain",
    [0x086A] = "Frost Cavern (2F) - Hiker Delmon",
    [0x086B] = "Frost Cavern (3F) - Hiker Brent",
    [0x086C] = "Frost Cavern (Outside) - Hiker Ross",
    [0x086F] = "Route 18 - Hiker Orestes",
    [0x0870] = "Terminus Cave (B1F) - Hiker Aaron",
    [0x0871] = "Terminus Cave (B1F) - Hiker Bergin",
    [0x0872] = "Route 16 - Roller Skater Olle",
    [0x0873] = "Route 16 - Roller Skater Jet",
    [0x0874] = "Route 21 - Ace Duo Elina & Sean",
    [0x0875] = "Terminus Cave (B2F) - Rangers Fern & Lee",
    [0x0876] = "Route 19 - Rangers Ivy & Orrick",
    [0x0877] = "Lost Hotel - Punk Couple Zoya & Asa",
    [0x0878] = "Route 15 - Pokémon Ranger Pedro",
    [0x0879] = "Route 15 - Pokémon Ranger Dean",
    [0x087A] = "Route 15 - Pokémon Ranger Silas",
    [0x087B] = "Route 15 - Pokémon Ranger Keith",
    [0x087C] = "Route 19 - Pokémon Ranger Shinobu",
    [0x087D] = "Route 19 - Pokémon Ranger Clementine",
    [0x087E] = "Route 19 - Pokémon Ranger Ambre",
    [0x0897] = "Route 4 - Battled Roller Skater Roland",
    [0x0898] = "Route 4 - Battled Roller Skater Calida",
    [0x0899] = "Lumiose City (Gym 2F) - Schoolboy Arno",
    [0x089A] = "Lumiose City (Gym 2F) - Schoolboy Sherlock",
    [0x089B] = "Lumiose City (Gym 2F) - Schoolboy Finnian",
    [0x089C] = "Lumiose City (Gym 3F) - Rising Star Estel",
    [0x089D] = "Lumiose City (Gym 3F) - Rising Star Nelly",
    [0x089E] = "Lumiose City (Gym 3F) - Rising Star Helene",
    [0x089F] = "Lumiose City (Gym 5F) - Poké Fan Abigail",
    [0x08A0] = "Lumiose City (Gym 5F) - Poké Fan Lydie",
    [0x08A1] = "Lumiose City (Gym 5F) - Poké Fan Tara",
    [0x08AC] = "Route 8 (Cliffside) - Battled Rising Star Rhys",
    [0x08AD] = "Route 8 (Cliffside) - Battled Rising Star Paulette",
    [0x08AE] = "Azure Bay - Battled Swimmer ♂ Kieran",
    [0x08AF] = "Azure Bay - Battled Swimmer ♀ Romy",
    [0x08B0] = "Route 10 - Battled Psychic Robert",
    [0x08D6] = "Azure Bay - Battled Sky Trainer Elata",
    [0x08D8] = "Azure Bay - Battled Swimmer ♀ Isla",
    [0x08DB] = "Victory Road (Inside 1) - Ace Trainer Alanza",
    [0x08DC] = "Victory Road (Inside 1) - Ace Trainer Bence",
    [0x08DD] = "Victory Road (Inside 1) - Black Belt Markus",
    [0x08DE] = "Victory Road (Inside 2) - Black Belt Ander",
    [0x08DF] = "Victory Road (Inside 1) - Battle Girl Veronique",
    [0x08E0] = "Victory Road (Inside 2) - Battle Girl Sigrid",
    [0x08E1] = "Victory Road (Outside 2) - Backpacker Farid",
    [0x08E2] = "Victory Road (Inside 2) - Psychic William",
    [0x08E3] = "Victory Road (Outside 3) - Hex Maniac Raziah",
    [0x08E4] = "Victory Road (Outside 3) - Fairy Tale Girl Corinne",
    [0x08E5] = "Victory Road (Inside 3) - Veteran Gerard",
    [0x08E6] = "Victory Road (Inside 4) - Veteran Timeo",
    [0x08E7] = "Victory Road (Inside 3) - Veteran Inga",
    [0x08E8] = "Victory Road (Inside 4) - Veteran Catrina",
    [0x08E9] = "Victory Road (Inside 4) - Veteran Gilles",
    [0x08EA] = "Victory Road (Inside 3) - Pokémon Ranger Ralf",
    [0x08EB] = "Victory Road (Inside 3) - Pokémon Ranger Petra",
    [0x08EC] = "Victory Road (Outside 4) - Ace Trainer Michele",
    [0x08ED] = "Victory Road (Outside 4) - Hiker Corwin",
    [0x08EE] = "Victory Road (Outside 4) - Artist Vincent",
    [0x08EF] = "Victory Road (Inside 2) - Brains & Brawn Arman & Hugo",
    [0x08F0] = "Route 16 - Pokémon Ranger Bjorn",
    [0x08F1] = "Route 16 - Pokémon Ranger Lee",
    [0x08F2] = "Lysandre Lab - Team Flare Grunt F",
    [0x08F6] = "Route 20 - Twins Nana & Nina",
    [0x08F7] = "Route 20 - Poké Fan Corey",
    [0x08F8] = "Route 20 - Poké Fan Roisin",
    [0x08F9] = "Route 20 - Fairy Tale Girl Wynne",
    [0x08FA] = "Route 20 - Hex Maniac Desdemona",
    [0x0927] = "Route 5 - Battled Rising Star Tyson",
    [0x0A50] = "Pokémon League - Champion Victory",
    [0x0A76] = "Coumarine City - Received Diploma for completing Central Kalos Pokédex (native) from Game Director",
    [0x0A77] = "Coumarine City - Received Diploma for completing Coastal Kalos Pokédex (native) from Game Director",
    [0x0A78] = "Coumarine City - Received Diploma for completing Mountain Kalos Pokédex (native) from Game Director",
    [0x0A79] = "Coumarine City - Received Diploma for completing all Kalos Pokédexes (native) from Game Director",
    [0x0A7A] = "Coumarine City - Received Diploma for completing Central Kalos Pokédex from Game Director",
    [0x0A7B] = "Coumarine City - Received Diploma for completing Coastal Kalos Pokédex from Game Director",
    [0x0A7C] = "Coumarine City - Received Diploma for completing Mountain Kalos Pokédex from Game Director",
    [0x0A7D] = "Coumarine City - Received Diploma for completing all Kalos Pokédexes from Game Director",
    [0x0A7E] = "Coumarine City - Received Diploma for completing National Pokédex from Game Director",
    [0x0B90] = "Camphrier Town - [Daily] Received Sweet Heart from maid",
    [0x0BA5] = "Ambrette Town - [Daily] Exchanged a Poké Ball for a Dive Ball with the punk guy",
    [0x0BA6] = "Lumiose City (South Boulevard) - [Daily] Received Rare Candy from male scientist for a chain length of at least 31 Pokémon with the Poké Radar",
    [0x0BAC] = "Ambrette Town - [Daily] Received Health Wing from woman for showing a Pokémon with a Speed stat equals or higher than requested",
    [0x0BB3] = "Coumarine City - [Daily] Picked the random berry from the empty stand",
    [0x0BB7] = "Camphrier Town - [Daily] Received a berry from man for showing him a Pokémon of the requested type",
    [0x0BBD] = "Lumiose City (South Boulevard) - [Daily] Received PP Max from male scientist for a chain length of 21-30 Pokémon with the Poké Radar",
    [0x0BBE] = "Lumiose City (South Boulevard) - [Daily] Received PP Up from male scientist for a chain length of 11-20 Pokémon with the Poké Radar",
    [0x0BBF] = "Lumiose City (South Boulevard) - [Daily] Received Ultra Ball from male scientist for a chain length of 1-10 Pokémon with the Poké Radar",
    [0x0BC5] = "Coumarine City - [Daily] Received Heart Scale from Tierno for showing him a Pokémon with the requested dance move",
}



-- Helper to determine if a triggered flag is an actual randomized item pickup location
local function is_item_check(flag_id)
    return ITEM_CHECK_FLAGS[flag_id] == true
end

-- Request Handlers Table matching Archipelago BizHawk Protocol
local request_handlers = {
    ["PING"] = function(req)
        return {type = "PONG"}
    end,
    ["SYSTEM"] = function(req)
        local sys = "N3DS"
        if emu and emu.getsystemid then
            sys = emu.getsystemid()
        end
        return {type = "SYSTEM_RESPONSE", value = sys}
    end,
    ["HASH"] = function(req)
        local h = "POKEMON_X"
        if gameinfo and gameinfo.getromhash then
            h = gameinfo.getromhash()
        end
        return {type = "HASH_RESPONSE", value = h}
    end,
    ["GUARD"] = function(req)
        return {type = "GUARD_RESPONSE", value = true, address = req["address"] or 0}
    end,
    ["LOCK"] = function(req)
        return {type = "LOCKED"}
    end,
    ["UNLOCK"] = function(req)
        return {type = "UNLOCKED"}
    end,
    ["MEMORY_SIZE"] = function(req)
        return {type = "MEMORY_SIZE_RESPONSE", value = 0x10000000}
    end,
    ["READ"] = function(req)
        local addr = req["address"]
        local size = req["size"]
        local bytes = {}
        for i = 0, size - 1 do
            table.insert(bytes, mainmemory.read_u8(addr + i))
        end
        return {type = "READ_RESPONSE", value = base64.encode(bytes)}
    end,
    ["WRITE"] = function(req)
        local addr = req["address"]
        
        -- Check if this write is targeting one of the bag pockets
        local is_bag_write = false
        for _, p in ipairs(POCKETS) do
            if addr >= p.addr and addr < (p.addr + p.slots * 4) then
                is_bag_write = true
                break
            end
        end

        -- If an item was just picked up, hold delivery until vanilla item is wiped!
        if is_bag_write and hold_ap_items then
            print(string.format(">>> [AP ITEM HELD] Bag write to 0x%08X held until vanilla item removed", addr))
            table.insert(held_writes, req)
            return {type = "WRITE_RESPONSE"}
        end

        local raw = base64.decode(req["value"])
        for i = 1, #raw do
            local val = (type(raw) == "table") and raw[i] or string.byte(raw, i)
            mainmemory.write_u8(addr + (i - 1), val)
        end
        return {type = "WRITE_RESPONSE"}
    end,
}

-- Initialize Server Socket directly
local function init_server()
    local s, err = bind_socket_server("127.0.0.1", SERVER_PORT)
    if s then
        server = s
        print(string.format(">>> Socket Server Listening on 127.0.0.1:%d", SERVER_PORT))
    else
        print(string.format("WARNING: Could not bind server to port %d: %s", SERVER_PORT, tostring(err)))
    end
end

init_server()

local checked = {}
local last_bytes = {}

for i = 0, MONITORED_BYTES - 1 do
    last_bytes[i] = mainmemory.read_u8(EVENT_FLAGS_BASE + i)
end

print("==============================================")
print(" Pokémon X Archipelago Connector Active")
print(" Memory Domain: mainmemory")
print(" Interceptor: AUTO-REMOVE VANILLA ITEMS")
print(" Status: LISTENING FOR CLIENT ON PORT 43055")
print("==============================================")

while true do
    -- Full Protocol Non-blocking TCP Socket Server Handling
    if server then
        if not client then
            local new_client, err = server:accept()
            if new_client then
                client = new_client
                if client.settimeout then client:settimeout(0) end
                print(">>> [ARCHIPELAGO BIZHAWK CLIENT CONNECTED!]")
            end
        else
            local line, err = client:receive("*l")
            if line then
                if line == "VERSION" then
                    client:send("1\n")
                else
                    local reqs = nil
                    local ok = pcall(function() reqs = json.decode(line) end)
                    if ok and type(reqs) == "table" then
                        local responses = {}
                        for _, req in ipairs(reqs) do
                            local req_type = req["type"]
                            local handler = request_handlers[req_type]
                            if handler then
                                table.insert(responses, handler(req))
                            else
                                table.insert(responses, {type = "ERROR", err = "Unknown type: " .. tostring(req_type)})
                            end
                        end
                        client:send(json.encode(responses) .. "\n")
                    end
                end
            elseif err == "closed" then
                print(">>> [ARCHIPELAGO BIZHAWK CLIENT DISCONNECTED]")
                client = nil
            end
        end
    end

    -- Real-Time Event Flag Location Check Monitor
    for i = 0, MONITORED_BYTES - 1 do
        local cur = mainmemory.read_u8(EVENT_FLAGS_BASE + i)
        local prev = last_bytes[i]
        if cur ~= prev then
            for bit = 0, 7 do
                local cur_bit  = math.floor(cur / (2 ^ bit)) % 2 == 1
                local prev_bit = math.floor(prev / (2 ^ bit)) % 2 == 1
                if cur_bit and not prev_bit then
                    local flag_id = (i * 8) + bit
                    if not checked[flag_id] then
                        checked[flag_id] = true
                        local loc_name = LOCATION_NAMES[flag_id]
                        if loc_name then
                            print(string.format(">>> [LOCATION CHECKED!] %s (Flag ID: 0x%04X)", loc_name, flag_id))
                        end

                        -- If this is an item pickup location, engage the vanilla interceptor!
                        if is_item_check(flag_id) then
                            pending_vanilla_removals = pending_vanilla_removals + 1
                            hold_ap_items = true
                            intercept_timer = 600 -- 10-second safety timeout
                            print(string.format(">>> [ITEM CHECK] Interceptor Active! Waiting for vanilla item... (Pending: %d)", pending_vanilla_removals))
                        end
                    end
                end
            end
            last_bytes[i] = cur
        end
    end

    -- Vanilla Item Interceptor & Remover Loop
    if pending_vanilla_removals > 0 then
        intercept_timer = intercept_timer - 1
        if intercept_timer <= 0 then
            print(">>> [INTERCEPT TIMEOUT] Safety reset: releasing hold.")
            pending_vanilla_removals = 0
            hold_ap_items = false
            release_held_writes()
        else
            for p_idx, pocket in ipairs(POCKETS) do
                for s = 0, pocket.slots - 1 do
                    local slot_addr = pocket.addr + (s * 4)
                    local cur_id = mainmemory.read_u8(slot_addr) + (mainmemory.read_u8(slot_addr + 1) * 256)
                    local cur_cnt = mainmemory.read_u8(slot_addr + 2) + (mainmemory.read_u8(slot_addr + 3) * 256)
                    local old = last_bag[p_idx][s]

                    if cur_id > 0 and (cur_id ~= old.id or cur_cnt > old.cnt) then
                        local diff = cur_cnt - (cur_id == old.id and old.cnt or 0)
                        print(string.format(">>> [VANILLA ITEM INTERCEPTED!] %s Pocket, Slot %d, Item ID %d (+%d)", pocket.name, s, cur_id, diff))

                        -- Remove the vanilla item from the slot
                        local restored_cnt = cur_cnt - diff
                        if restored_cnt <= 0 then
                            mainmemory.write_u8(slot_addr, 0)
                            mainmemory.write_u8(slot_addr + 1, 0)
                            mainmemory.write_u8(slot_addr + 2, 0)
                            mainmemory.write_u8(slot_addr + 3, 0)
                            print(string.format(">>> [VANILLA ITEM REMOVED] Cleared slot %d @ 0x%08X", s, slot_addr))
                        else
                            mainmemory.write_u8(slot_addr + 2, restored_cnt % 256)
                            mainmemory.write_u8(slot_addr + 3, math.floor(restored_cnt / 256))
                            print(string.format(">>> [VANILLA ITEM REDUCED] Slot %d restored to qty %d", s, restored_cnt))
                        end

                        pending_vanilla_removals = pending_vanilla_removals - 1
                        print(string.format(">>> [STATUS] Pending vanilla removals remaining: %d", pending_vanilla_removals))

                        if pending_vanilla_removals <= 0 then
                            pending_vanilla_removals = 0
                            hold_ap_items = false
                            print(">>> [ALL VANILLA ITEMS REMOVED] Delivering held Archipelago items now!")
                            release_held_writes()
                        end
                        break
                    end
                end
                if pending_vanilla_removals == 0 then break end
            end
        end
    else
        -- Keep baseline bag snapshot updated when not intercepting
        last_bag = take_bag_snapshot()
    end

    -- On-Screen Status Display
    gui.drawText(5, 5, "=== Pokémon X Archipelago Connector ===", "yellow", "black", 12)
    gui.drawText(5, 21, client and "Status: CONNECTED TO CLIENT" or "Status: LISTENING ON PORT 43055", client and "lime" or "yellow", "black", 11)
    if hold_ap_items then
        gui.drawText(5, 37, string.format("HOLD: Intercepting Vanilla Item (%d left)...", pending_vanilla_removals), "orange", "black", 11)
    end

    emu.frameadvance()
end
