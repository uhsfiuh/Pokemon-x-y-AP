--[[
    Pokémon Y Archipelago Connector
    Merged connector: implements connector_bizhawk_generic protocol (port 43055)
    so ArchipelagoBizHawkClient.exe can connect, while using N3DS Extra RAM mainmemory
    addressing for verified Pokémon Y addresses.
]]

local SCRIPT_VERSION = 1
local DEBUG = false

-- BizHawk version check
local bizhawk_version = client.getversion()
local bizhawk_major, bizhawk_minor = bizhawk_version:match("(%d+)%.(%d+)")
bizhawk_major = tonumber(bizhawk_major)
bizhawk_minor = tonumber(bizhawk_minor)

local lua_major, lua_minor = _VERSION:match("Lua (%d+)%.(%d+)")
lua_major = tonumber(lua_major)
lua_minor = tonumber(lua_minor)

if lua_major > 5 or (lua_major == 5 and lua_minor >= 3) then
    require("lua_5_3_compat")
end

local base64 = require("base64")
local socket = require("socket")
local json   = require("json")

-- ============================================================================
-- Pokémon Y Memory Configuration (N3DS Extra RAM domain via mainmemory)
-- ============================================================================
local MEMORY_DOMAIN    = "N3DS Extra RAM"
local ADDR_BAG_ITEMS   = 0x074D5554
local ADDR_MONEY       = 0x074D869C
local ADDR_BADGES      = 0x074D86A0
local EVENT_FLAGS_BASE = 0x074E86B8

-- Badge AP item IDs: 200001 = Bug Badge ... 200008 = Iceberg Badge
local BADGE_ID_BASE = 200001
local BADGE_COUNT   = 8

-- Locations to monitor (flag_id → location name)
local LOCATIONS = {
    { name = "FE_D12R0104_ITEMGET_01", flag_id = 0x008C },
    { name = "Shalour City - Exchanged a Sitrus Berry for a Leppa Berry with guy", flag_id = 0x008D },
    { name = "Cyllage City - Received Destiny Knot from maid", flag_id = 0x008E },
    { name = "FE_C03R0801_ITEMGET_01", flag_id = 0x008F },
    { name = "Cyllage City - Received Whipped Dream / Sachet from man", flag_id = 0x0090 },
    { name = "FE_C03R0901_ITEMGET_01", flag_id = 0x0091 },
    { name = "Lumiose City (South Boulevard) - Received Luxury Ball (x5) from woman", flag_id = 0x0092 },
    { name = "Shalour City - Received Shoothe Bell from madame for showing her a Pokémon with good friendship", flag_id = 0x0093 },
    { name = "FE_T06R0301_ITEMGET_01", flag_id = 0x0094 },
    { name = "FE_T05R0201_ITEMGET_01", flag_id = 0x0096 },
    { name = "Shalour City - Received Eviolite from scientist for seeing at least 40 species in Coastal Pokédex", flag_id = 0x0097 },
    { name = "FE_D07_ITEMGET_01", flag_id = 0x0098 },
    { name = "FE_D07_ITEMGET_02", flag_id = 0x0099 },
    { name = "Aquacorde Town - Received Potion from shopkeeper", flag_id = 0x00A4 },
    { name = "FE_C08R0401_ITEMGET_01", flag_id = 0x00A6 },
    { name = "Coumarine City - Received Poké Toy from woman for answering her sound quiz first time", flag_id = 0x00AA },
    { name = "Lumiose City (South Boulevard) - Received TM54 (False Swipe) from female scientist for seeing at least 20 species in Central Kalos Pokédex", flag_id = 0x00B1 },
    { name = "Camphrier Town - Received Berry Juice from girl", flag_id = 0x00B2 },
    { name = "Camphrier Town - Received Ultra Ball from man", flag_id = 0x00B3 },
    { name = "Camphrier Town - Received Full Heal from boy", flag_id = 0x00B4 },
    { name = "Camphrier Town - Received TM46 (Thief) from punk girl", flag_id = 0x00B5 },
    { name = "FE_T06R0101_ITEMGET_01", flag_id = 0x00B6 },
    { name = "Coumarine City - Received Lucky Egg from woman for showing her a Pokémon with maximum friendship", flag_id = 0x00B7 },
    { name = "FE_C09R0101_ITEMGET_01", flag_id = 0x00BB },
    { name = "FE_C09R0201_ITEMGET_01", flag_id = 0x00BD },
    { name = "FE_T03R0401_ITEMGET_01", flag_id = 0x00C5 },
    { name = "Lumiose City (South Boulevard) - Received Quick Claw from woman", flag_id = 0x00C6 },
    { name = "Lumiose City (South Boulevard) - Received Quick Ball (x3) from man", flag_id = 0x00C7 },
    { name = "FE_C06_ITEMGET_02", flag_id = 0x00D4 },
    { name = "Ambrette Town - Received the Douse Drive", flag_id = 0x00D5 },
    { name = "FE_PLR0801_ITEMGET_01", flag_id = 0x00D6 },
    { name = "Santalune Forest - Received Poké Ball from Calem/Serena if interacted", flag_id = 0x00D7 },
    { name = "Lumiose City (South Boulevard) - Received Timer Ball (x3) from man", flag_id = 0x00FE },
    { name = "Cyllage City - Received Persim Berry (x3) from girl for answering her quiz", flag_id = 0x00FF },
    { name = "FE_C02R1101_ITEMGET_01", flag_id = 0x0100 },
    { name = "FE_C02R1103_ITEMGET_01", flag_id = 0x0101 },
    { name = "FE_C02R1203_ITEMGET_01", flag_id = 0x0102 },
    { name = "FE_C02R1203_ITEMGET_02", flag_id = 0x0103 },
    { name = "FE_C02R1401_ITEMGET_01", flag_id = 0x0104 },
    { name = "FE_C02R3602_ITEMGET_01", flag_id = 0x0105 },
    { name = "Parfum Palace - Received Oran Berry from woman", flag_id = 0x0106 },
    { name = "Ambrette Town - Received TM94 (Rock Smash) from girl", flag_id = 0x0109 },
    { name = "FE_C08P0101_ITEMGET_01", flag_id = 0x010A },
    { name = "Santalune City - Received Great Ball from boy", flag_id = 0x010B },
    { name = "FE_C09R0601_ITEMGET_01", flag_id = 0x010C },
    { name = "Lumiose City (Vernal Avenue) - Received Pearl String (x2) from madame for showing her a Furfrou that has kept the same trim for 15 days", flag_id = 0x010D },
    { name = "Tower of Mastery - Received TM47 (Low Sweep) from ace trainer", flag_id = 0x010E },
    { name = "FE_C02R0701_ITEMGET_01", flag_id = 0x0117 },
    { name = "FE_C02R3105_ITEMGET_01", flag_id = 0x0119 },
    { name = "Coumarine City - Received Good Rod from fisherman", flag_id = 0x011A },
    { name = "Reflection Cave - Received Reveal Glass from female scientist for showing her a Tornadus / Thundurus / Landorus", flag_id = 0x011C },
    { name = "Azure Bay - Received Ampharosite from old man", flag_id = 0x011D },
    { name = "Ambrette Town - Received Aerodactylite from male scientist", flag_id = 0x011E },
    { name = "FE_C09_ITEMGET_01", flag_id = 0x0121 },
    { name = "FE_C09R1001_ITEMGET_01", flag_id = 0x0123 },
    { name = "FE_C09R1001_ITEMGET_02", flag_id = 0x0124 },
    { name = "FE_C09R0401_ITEMGET_01", flag_id = 0x0125 },
    { name = "FE_C09R0501_ITEMGET_01", flag_id = 0x0126 },
    { name = "FE_C02R3401_ITEMGET_01", flag_id = 0x0127 },
    { name = "FE_C02R3401_ITEMGET_02", flag_id = 0x0128 },
    { name = "FE_C02R3401_ITEMGET_03", flag_id = 0x0129 },
    { name = "FE_D06R0103_ITEMGET_01", flag_id = 0x012A },
    { name = "FE_C02GYM0101_ITEMGET_01", flag_id = 0x012F },
    { name = "FE_FLD_MEGASTONE_GET_01", flag_id = 0x0130 },
    { name = "FE_FLD_MEGASTONE_GET_02", flag_id = 0x0131 },
    { name = "FE_FLD_MEGASTONE_GET_03", flag_id = 0x0132 },
    { name = "FE_FLD_MEGASTONE_GET_04", flag_id = 0x0133 },
    { name = "FE_FLD_MEGASTONE_GET_05", flag_id = 0x0134 },
    { name = "FE_FLD_MEGASTONE_GET_06", flag_id = 0x0135 },
    { name = "FE_FLD_MEGASTONE_GET_07", flag_id = 0x0136 },
    { name = "FE_FLD_MEGASTONE_GET_08", flag_id = 0x0137 },
    { name = "FE_FLD_MEGASTONE_GET_09", flag_id = 0x0138 },
    { name = "FE_FLD_MEGASTONE_GET_10", flag_id = 0x0139 },
    { name = "FE_FLD_MEGASTONE_GET_11", flag_id = 0x013A },
    { name = "FE_FLD_MEGASTONE_GET_12", flag_id = 0x013B },
    { name = "FE_C09_ITEMGET_02", flag_id = 0x013E },
    { name = "Shalour City - Exchanged the Intriguing Stone for a Sun Stone with hiker", flag_id = 0x0146 },
    { name = "FE_T06R0201_ITEMGET_01", flag_id = 0x0147 },
    { name = "FE_C01_ITEMGET_01", flag_id = 0x018F },
    { name = "Ambrette Gate - Received Rocky Helmet from woman", flag_id = 0x0191 },
    { name = "Coumarine Gate - Received Black Sludge from punk guy", flag_id = 0x0193 },
    { name = "Coumarine City - Received Silk Scarf from old man", flag_id = 0x0195 },
    { name = "Coumarine City - Received Metronome from man", flag_id = 0x019B },
    { name = "Route 12 - Received TM45 (Attract) from girl", flag_id = 0x019C },
    { name = "FE_C08R0601_ITEMGET_01", flag_id = 0x019D },
    { name = "Ambrette Town - Received TM96 (Nature Power) from woman", flag_id = 0x019E },
    { name = "FE_R14_ITEMGET_01", flag_id = 0x019F },
    { name = "FE_D12R0104_ITEMGET_02", flag_id = 0x01A0 },
    { name = "Geosenge Town - Received TM66 (Payback) from old man", flag_id = 0x01A1 },
    { name = "Cyllage City - Received TM44 (Rest) from guy", flag_id = 0x01A3 },
    { name = "Cyllage City - Received TM88 (Sleep Talk) from girl", flag_id = 0x01A4 },
    { name = "Connecting Cave - Received TM21 (Frustration) from Backpacker", flag_id = 0x01A5 },
    { name = "FE_D15R0101_ITEMGET_01", flag_id = 0x01A7 },
    { name = "Santalune City - Received X Attack (x3) and X Defense (x3) from old man", flag_id = 0x01AC },
    { name = "Shalour City - Received Stardust (x5) from girl for helping her", flag_id = 0x01AD },
    { name = "Geosenge Town - Received Everstone from female scientist", flag_id = 0x01AE },
    { name = "FE_C06_ITEMGET_01", flag_id = 0x01DF },
    { name = "FE_T05P0101_ITEMGET_01", flag_id = 0x01E0 },
    { name = "FE_T05R0301_ITEMGET_01", flag_id = 0x01E1 },
    { name = "FE_R16R0101_ITEMGET_01", flag_id = 0x01E2 },
    { name = "FE_T05R0401_ITEMGET_01", flag_id = 0x01E4 },
    { name = "Route 13 - Found Power Plant Pass", flag_id = 0x044D },
    { name = "Santalune City - Found Super Potion", flag_id = 0x044E },
    { name = "Santalune City - Found Great Ball", flag_id = 0x044F },
    { name = "Santalune City - Found Antidote", flag_id = 0x0450 },
    { name = "Route 4 - Found Honey (recurring)", flag_id = 0x0451 },
    { name = "Route 4 - Found Honey (recurring) (2)", flag_id = 0x0452 },
    { name = "Route 4 - Found Honey (recurring) (3)", flag_id = 0x0453 },
    { name = "Route 4 - Found Super Potion", flag_id = 0x0454 },
    { name = "Route 5 - Found Paralyze Heal", flag_id = 0x0455 },
    { name = "Route 5 - Found Super Potion", flag_id = 0x0456 },
    { name = "Camphrier Town - Found Antidote", flag_id = 0x0457 },
    { name = "Camphrier Town - Found Ether", flag_id = 0x0458 },
    { name = "Route 6 - Found Antidote", flag_id = 0x0459 },
    { name = "Route 6 - Found Tiny Mushroom", flag_id = 0x045A },
    { name = "Parfum Palace - Found Rare Candy", flag_id = 0x045B },
    { name = "Parfum Palace - Found X Sp. Atk", flag_id = 0x045C },
    { name = "Parfum Palace - Found Pretty Wing (recurring)", flag_id = 0x045D },
    { name = "Route 8 - Found Super Potion", flag_id = 0x045E },
    { name = "Route 8 - Found Escape Rope", flag_id = 0x045F },
    { name = "Route 8 - Found Pearl (recurring)", flag_id = 0x0460 },
    { name = "Route 8 - Found Ultra Ball", flag_id = 0x0461 },
    { name = "Route 8 - Found Heart Scale", flag_id = 0x0462 },
    { name = "Route 8 - Found Stardust (recurring)", flag_id = 0x0463 },
    { name = "Route 8 - Found Heart Scale (recurring)", flag_id = 0x0464 },
    { name = "Ambrette Town - Found Rare Candy", flag_id = 0x0465 },
    { name = "Ambrette Town - Found X Attack", flag_id = 0x0466 },
    { name = "Route 9 - Found Super Repel", flag_id = 0x0467 },
    { name = "Cyllage City - Found Ether", flag_id = 0x0468 },
    { name = "Cyllage City - Found Pearl", flag_id = 0x0469 },
    { name = "Cyllage City - Found X Speed", flag_id = 0x046A },
    { name = "Cyllage City - Found Protein", flag_id = 0x046B },
    { name = "Route 10 - Found Revive", flag_id = 0x046C },
    { name = "Route 10 - Found Paralyze Heal", flag_id = 0x046D },
    { name = "Route 10 - Found Burn Heal", flag_id = 0x046E },
    { name = "Route 11 - Found Super Potion", flag_id = 0x046F },
    { name = "Route 11 - Found Thunder Stone", flag_id = 0x0470 },
    { name = "Shalour City - Found X Sp. Atk", flag_id = 0x0471 },
    { name = "Shalour City - Found Stardust (recurring)", flag_id = 0x0472 },
    { name = "Shalour City - Found Max Repel", flag_id = 0x0473 },
    { name = "Route 12 - Found Honey (recurring)", flag_id = 0x0474 },
    { name = "Route 12 - Found Net Ball", flag_id = 0x0475 },
    { name = "Route 12 - Found Water Stone", flag_id = 0x0476 },
    { name = "Route 12 - Found Ice Heal", flag_id = 0x0477 },
    { name = "Azure Bay - Found Star Piece", flag_id = 0x0478 },
    { name = "Azure Bay - Found Hyper Potion", flag_id = 0x0479 },
    { name = "Azure Bay - Found Heart Scale", flag_id = 0x047A },
    { name = "Coumarine City - Found Elixir", flag_id = 0x047B },
    { name = "Coumarine City - Found Awakening", flag_id = 0x047C },
    { name = "Coumarine City - Found Max Repel", flag_id = 0x047D },
    { name = "Route 13 - Found Guard Spec.", flag_id = 0x047E },
    { name = "Route 13 - Found Heat Rock", flag_id = 0x047F },
    { name = "Route 13 - Found Nest Ball", flag_id = 0x0480 },
    { name = "Route 13 - Found Hyper Potion", flag_id = 0x0481 },
    { name = "Route 13 - Found PP Up", flag_id = 0x0482 },
    { name = "Route 13 - Found X Accuracy", flag_id = 0x0483 },
    { name = "Route 13 - Found Stardust", flag_id = 0x0484 },
    { name = "Route 13 - Found Fire Stone", flag_id = 0x0485 },
    { name = "Route 13 - Found Star Piece", flag_id = 0x0486 },
    { name = "Route 14 - Found Super Potion", flag_id = 0x0487 },
    { name = "Route 14 - Found Tiny Mushroom", flag_id = 0x0488 },
    { name = "Route 14 - Found Revive", flag_id = 0x0489 },
    { name = "Laverre City - Found Tiny Mushroom (recurring)", flag_id = 0x048A },
    { name = "Laverre City - Found Leaf Stone", flag_id = 0x048B },
    { name = "Laverre City - Found Ultra Ball", flag_id = 0x048C },
    { name = "Poké Ball Factory - Found Dusk Ball", flag_id = 0x048D },
    { name = "Poké Ball Factory - Found Burn Heal", flag_id = 0x048E },
    { name = "Poké Ball Factory - Found Poké Ball", flag_id = 0x048F },
    { name = "Poké Ball Factory - Found Hyper Potion", flag_id = 0x0490 },
    { name = "Route 15 - Found HP Up", flag_id = 0x0491 },
    { name = "Route 15 - Found Antidote", flag_id = 0x0492 },
    { name = "Route 15 - Found Tiny Mushroom", flag_id = 0x0493 },
    { name = "Route 15 - Found X Defense", flag_id = 0x0494 },
    { name = "Route 15 - Found Pretty Wing", flag_id = 0x0495 },
    { name = "Route 16 - Found Repel", flag_id = 0x0496 },
    { name = "Route 16 - Found Rare Candy", flag_id = 0x0497 },
    { name = "Route 16 - Found Big Mushroom", flag_id = 0x0498 },
    { name = "Route 16 - Found Max Revive", flag_id = 0x0499 },
    { name = "Dendemille Town - Found Heal Ball", flag_id = 0x049A },
    { name = "Dendemille Town - Found X Speed", flag_id = 0x049B },
    { name = "Dendemille Town - Found Nugget", flag_id = 0x049C },
    { name = "Frost Cavern - Found Escape Rope", flag_id = 0x049D },
    { name = "Frost Cavern - Found X Sp. Def", flag_id = 0x049E },
    { name = "Frost Cavern - Found Ice Heal", flag_id = 0x049F },
    { name = "Frost Cavern - Found Dusk Ball", flag_id = 0x04A0 },
    { name = "Frost Cavern - Found Dire Hit", flag_id = 0x04A1 },
    { name = "Frost Cavern - Found Pearl", flag_id = 0x04A2 },
    { name = "Frost Cavern - Found Super Potion", flag_id = 0x04A3 },
    { name = "Frost Cavern - Found Ice Heal (2)", flag_id = 0x04A4 },
    { name = "Frost Cavern - Found Elixir", flag_id = 0x04A5 },
    { name = "Frost Cavern - Found PP Up", flag_id = 0x04A6 },
    { name = "Route 18 - Found Timer Ball", flag_id = 0x04A7 },
    { name = "Route 18 - Found Paralyze Heal", flag_id = 0x04A8 },
    { name = "Anistar City - Found Pretty Wing (recurring)", flag_id = 0x04A9 },
    { name = "Anistar City - Found Escape Rope", flag_id = 0x04AA },
    { name = "Anistar City - Found Super Repel", flag_id = 0x04AB },
    { name = "Anistar City - Found Sun Stone", flag_id = 0x04AC },
    { name = "Route 19 - Found Poké Ball", flag_id = 0x04AD },
    { name = "Route 19 - Found Ether", flag_id = 0x04AE },
    { name = "Route 19 - Found Honey", flag_id = 0x04AF },
    { name = "Route 19 - Found Super Potion", flag_id = 0x04B0 },
    { name = "Terminus Cave - Found Dusk Ball", flag_id = 0x04B1 },
    { name = "Terminus Cave - Found Hyper Potion", flag_id = 0x04B2 },
    { name = "Terminus Cave - Found Moon Stone", flag_id = 0x04B3 },
    { name = "Terminus Cave - Found Max Repel", flag_id = 0x04B4 },
    { name = "Terminus Cave - Found Iron", flag_id = 0x04B5 },
    { name = "Terminus Cave - Found Dire Hit", flag_id = 0x04B6 },
    { name = "Terminus Cave - Found Max Potion", flag_id = 0x04B7 },
    { name = "Terminus Cave - Found Big Nugget", flag_id = 0x04B8 },
    { name = "Terminus Cave - Found Normal Gem", flag_id = 0x04B9 },
    { name = "Couriway Town - Found Pretty Wing", flag_id = 0x04BA },
    { name = "Couriway Town - Found Ether", flag_id = 0x04BB },
    { name = "Couriway Town - Found Burn Heal", flag_id = 0x04BC },
    { name = "Couriway Town - Found Prism Scale (recurring)", flag_id = 0x04BD },
    { name = "Route 20 - Found Net Ball", flag_id = 0x04BE },
    { name = "Route 20 - Found Antidote", flag_id = 0x04BF },
    { name = "Route 20 - Found Damp Rock", flag_id = 0x04C0 },
    { name = "Route 20 - Found Escape Rope", flag_id = 0x04C1 },
    { name = "Route 20 - Found Timer Ball", flag_id = 0x04C2 },
    { name = "Snowbelle City - Found Icy Rock", flag_id = 0x04C3 },
    { name = "Snowbelle City - Found X Sp. Atk", flag_id = 0x04C4 },
    { name = "Snowbelle City - Found Full Heal", flag_id = 0x04C5 },
    { name = "Route 21 - Found Repeat Ball", flag_id = 0x04C6 },
    { name = "Route 21 - Found Antidote", flag_id = 0x04C7 },
    { name = "Route 21 - Found Mental Herb", flag_id = 0x04C8 },
    { name = "Route 21 - Found Tiny Mushroom", flag_id = 0x04C9 },
    { name = "Route 21 - Found Balm Mushroom", flag_id = 0x04CA },
    { name = "Pokémon Village - Found Honey", flag_id = 0x04CB },
    { name = "Pokémon Village - Found Pretty Wing", flag_id = 0x04CC },
    { name = "Pokémon Village - Found Honey (2)", flag_id = 0x04CD },
    { name = "Route 22 - Found Guard Spec.", flag_id = 0x04CE },
    { name = "Route 22 - Found PP Up", flag_id = 0x04CF },
    { name = "Route 22 - Found Pearl String", flag_id = 0x04D0 },
    { name = "Route 22 - Found Elixir", flag_id = 0x04D1 },
    { name = "Route 22 - Found Max Elixir", flag_id = 0x04D2 },
    { name = "Route 22 - Found Full Restore", flag_id = 0x04D3 },
    { name = "Victory Road - Found X Attack", flag_id = 0x04D4 },
    { name = "Victory Road - Found Full Heal", flag_id = 0x04D5 },
    { name = "Victory Road - Found Hyper Potion", flag_id = 0x04D6 },
    { name = "Victory Road - Found Ultra Ball", flag_id = 0x04D7 },
    { name = "Victory Road - Found Smooth Rock", flag_id = 0x04D8 },
    { name = "Victory Road - Found Revive", flag_id = 0x04D9 },
    { name = "Victory Road - Found Pretty Wing", flag_id = 0x04DA },
    { name = "Victory Road - Found Escape Rope", flag_id = 0x04DB },
    { name = "Victory Road - Found Max Repel", flag_id = 0x04DC },
    { name = "Victory Road - Found X Defense", flag_id = 0x04DD },
    { name = "Victory Road - Found Max Ether", flag_id = 0x04DE },
    { name = "Victory Road - Found Star Piece", flag_id = 0x04DF },
    { name = "Couriway Town - Found Poké Ball", flag_id = 0x04E0 },
    { name = "Kiloude City - Found Max Revive", flag_id = 0x04E1 },
    { name = "Kiloude City - Found PP Up", flag_id = 0x04E2 },
    { name = "Unknown Dungeon - Found Oval Stone (recurring)", flag_id = 0x04E3 },
    { name = "Santalune Forest - Potion item ball disappeared", flag_id = 0x051A },
    { name = "Santalune Forest - Poké Ball item ball disappeared", flag_id = 0x051B },
    { name = "Route 3 - Super Potion item ball disappeared", flag_id = 0x051C },
    { name = "Route 3 - Revive item ball disappeared", flag_id = 0x051D },
    { name = "Route 3 - Dawn Stone item ball disappeared", flag_id = 0x051E },
    { name = "Route 22 - Super Potion item ball disappeared", flag_id = 0x051F },
    { name = "Route 22 - Elixir item ball disappeared", flag_id = 0x0520 },
    { name = "Route 22 - Draco Plate item ball disappeared", flag_id = 0x0521 },
    { name = "Route 4 - Great Ball item ball disappeared", flag_id = 0x0522 },
    { name = "Route 4 - Antidote item ball disappeared", flag_id = 0x0523 },
    { name = "Route 4 - Super Potion item ball disappeared", flag_id = 0x0524 },
    { name = "Route 4 - Repel item ball disappeared", flag_id = 0x0525 },
    { name = "Route 4 - Poison Barb item ball disappeared", flag_id = 0x0526 },
    { name = "Route 4 - Net Ball item ball disappeared", flag_id = 0x0527 },
    { name = "Route 4 - Ether item ball disappeared", flag_id = 0x0528 },
    { name = "Route 5 - Super Potion item ball disappeared", flag_id = 0x0529 },
    { name = "Route 5 - Super Potion item ball disappeared (2)", flag_id = 0x052A },
    { name = "Route 5 - Great Ball item ball disappeared", flag_id = 0x052B },
    { name = "Route 5 - TM01 (Hone Claws) item ball disappeared", flag_id = 0x052C },
    { name = "Route 5 - X Attack item ball disappeared", flag_id = 0x052D },
    { name = "Route 5 - Sharp Beak item ball disappeared", flag_id = 0x052E },
    { name = "Route 6 - X Sp. Atk item ball disappeared", flag_id = 0x052F },
    { name = "Route 6 - Antidote item ball disappeared", flag_id = 0x0530 },
    { name = "Route 6 - X Speed item ball disappeared", flag_id = 0x0531 },
    { name = "Route 6 - Paralyze Heal item ball disappeared", flag_id = 0x0532 },
    { name = "Route 6 - TM09 (Venosock) item ball disappeared", flag_id = 0x0533 },
    { name = "Route 6 - Awakening item ball disappeared", flag_id = 0x0534 },
    { name = "Route 6 - Super Repel item ball disappeared", flag_id = 0x0535 },
    { name = "Route 6 - Ultra Ball item ball disappeared", flag_id = 0x0536 },
    { name = "Route 7 - X Sp. Def item ball disappeared", flag_id = 0x0537 },
    { name = "Route 7 - PP Up item ball disappeared", flag_id = 0x0538 },
    { name = "Route 7 - Tiny Mushroom item ball disappeared", flag_id = 0x0539 },
    { name = "Route 7 - Silver Powder item ball disappeared", flag_id = 0x053A },
    { name = "Connecting Cave - TM40 (Aerial Ace) item ball disappeared", flag_id = 0x053B },
    { name = "Route 8 - HP Up item ball disappeared", flag_id = 0x053C },
    { name = "Route 8 - Leaf Stone item ball disappeared", flag_id = 0x053D },
    { name = "Route 8 - Water Stone item ball disappeared", flag_id = 0x053E },
    { name = "Route 8 - Heart Scale item ball disappeared", flag_id = 0x053F },
    { name = "Route 8 - TM19 (Roost) item ball disappeared", flag_id = 0x0540 },
    { name = "Route 9 - X Defense item ball disappeared", flag_id = 0x0541 },
    { name = "Route 9 - Paralyze Heal item ball disappeared", flag_id = 0x0542 },
    { name = "Route 9 - Fire Stone item ball disappeared", flag_id = 0x0543 },
    { name = "Route 9 - Dusk Ball item ball disappeared", flag_id = 0x0544 },
    { name = "Glittering Cave - Hard Stone item ball disappeared", flag_id = 0x0545 },
    { name = "Glittering Cave - TM65 (Shadow Claw) item ball disappeared", flag_id = 0x0546 },
    { name = "Route 10 - TM73 (Thunder Wave) item ball disappeared", flag_id = 0x0547 },
    { name = "Route 10 - Mind Plate item ball disappeared", flag_id = 0x0548 },
    { name = "Route 10 - X Accuracy item ball disappeared", flag_id = 0x0549 },
    { name = "Route 10 - Thunder Stone item ball disappeared", flag_id = 0x054A },
    { name = "Route 11 - TM69 (Rock Polish) item ball disappeared", flag_id = 0x054B },
    { name = "Route 11 - Hyper Potion item ball disappeared", flag_id = 0x054C },
    { name = "Reflection Cave - Nest Ball item ball disappeared", flag_id = 0x054D },
    { name = "Reflection Cave - Revive item ball disappeared", flag_id = 0x054E },
    { name = "Reflection Cave - Moon Stone item ball disappeared", flag_id = 0x054F },
    { name = "Reflection Cave - Black Belt item ball disappeared", flag_id = 0x0550 },
    { name = "Reflection Cave - Hyper Potion item ball disappeared", flag_id = 0x0551 },
    { name = "Reflection Cave - Escape Rope item ball disappeared", flag_id = 0x0552 },
    { name = "Reflection Cave - Iron item ball disappeared", flag_id = 0x0553 },
    { name = "Reflection Cave - Earth Plate item ball disappeared", flag_id = 0x0554 },
    { name = "Reflection Cave - TM74 (Gyro Ball) item ball disappeared", flag_id = 0x0555 },
    { name = "Route 12 - Sachet item ball disappeared", flag_id = 0x0556 },
    { name = "Route 12 - Shiny Stone item ball disappeared", flag_id = 0x0557 },
    { name = "Route 12 - Whipped Dream item ball disappeared", flag_id = 0x0558 },
    { name = "Parfum Palace - Guard Spec. item ball disappeared", flag_id = 0x0559 },
    { name = "Route 12 - Leftovers item ball disappeared", flag_id = 0x055A },
    { name = "Azure Bay - Deep Sea Tooth item ball disappeared", flag_id = 0x055B },
    { name = "Azure Bay - TM81 (X-Scissor) item ball disappeared", flag_id = 0x055C },
    { name = "Azure Bay - Dive Ball item ball disappeared", flag_id = 0x055D },
    { name = "Azure Bay - Big Pearl item ball disappeared", flag_id = 0x055E },
    { name = "Azure Bay - Splash Plate item ball disappeared", flag_id = 0x055F },
    { name = "Route 13 - Smooth Rock item ball disappeared", flag_id = 0x0560 },
    { name = "Route 13 - Burn Heal item ball disappeared", flag_id = 0x0561 },
    { name = "Route 13 - TM57 (Charge Beam) item ball disappeared", flag_id = 0x0562 },
    { name = "Route 13 - Flame Plate item ball disappeared", flag_id = 0x0563 },
    { name = "Route 13 - Sun Stone item ball disappeared", flag_id = 0x0564 },
    { name = "Route 13 - Rare Candy item ball disappeared", flag_id = 0x0565 },
    { name = "Route 14 - Cleanse Tag item ball disappeared", flag_id = 0x0566 },
    { name = "Route 14 - Big Mushroom item ball disappeared", flag_id = 0x0567 },
    { name = "Route 14 - Hyper Potion item ball disappeared", flag_id = 0x0568 },
    { name = "Route 14 - Damp Rock item ball disappeared", flag_id = 0x0569 },
    { name = "Route 14 - Spell Tag item ball disappeared", flag_id = 0x056A },
    { name = "Route 14 - TM61 (Will-O-Wisp) item ball disappeared", flag_id = 0x056B },
    { name = "Poké Ball Factory - Max Revive item ball disappeared", flag_id = 0x056C },
    { name = "Poké Ball Factory - Max Ether item ball disappeared", flag_id = 0x056D },
    { name = "Poké Ball Factory - Quick Ball item ball disappeared", flag_id = 0x056E },
    { name = "Poké Ball Factory - Metal Coat item ball disappeared", flag_id = 0x056F },
    { name = "Poké Ball Factory - Timer Ball item ball disappeared", flag_id = 0x0570 },
    { name = "Route 15 - Net Ball item ball disappeared", flag_id = 0x0571 },
    { name = "Route 15 - Revive item ball disappeared", flag_id = 0x0572 },
    { name = "Route 15 - Dire Hit item ball disappeared", flag_id = 0x0573 },
    { name = "Route 15 - PP Up item ball disappeared", flag_id = 0x0574 },
    { name = "Route 15 - Full Heal item ball disappeared", flag_id = 0x0575 },
    { name = "Route 15 - Protein item ball disappeared", flag_id = 0x0576 },
    { name = "Route 15 - Macho Brace item ball disappeared", flag_id = 0x0577 },
    { name = "Route 15 - Stone Plate item ball disappeared", flag_id = 0x0578 },
    { name = "Route 15 - TM97 (Dark Pulse) item ball disappeared", flag_id = 0x0579 },
    { name = "Route 16 - Rare Candy item ball disappeared", flag_id = 0x057A },
    { name = "Route 16 - Max Potion item ball disappeared", flag_id = 0x057B },
    { name = "Route 16 - Fist Plate item ball disappeared", flag_id = 0x057C },
    { name = "Route 16 - Dive Ball item ball disappeared", flag_id = 0x057D },
    { name = "Lost Hotel - Smoke Ball item ball disappeared", flag_id = 0x057E },
    { name = "Lost Hotel - Twisted Spoon item ball disappeared", flag_id = 0x057F },
    { name = "Lost Hotel - TM95 (Snarl) item ball disappeared", flag_id = 0x0580 },
    { name = "Lost Hotel - Dread Plate item ball disappeared", flag_id = 0x0581 },
    { name = "Lost Hotel - Protector item ball disappeared", flag_id = 0x0582 },
    { name = "Frost Cavern - Heart Scale item ball disappeared", flag_id = 0x0583 },
    { name = "Frost Cavern - TM71 (Stone Edge) item ball disappeared", flag_id = 0x0584 },
    { name = "Frost Cavern - Hyper Potion item ball disappeared", flag_id = 0x0585 },
    { name = "Frost Cavern - Ice Heal item ball disappeared", flag_id = 0x0586 },
    { name = "Frost Cavern - Max Repel item ball disappeared", flag_id = 0x0587 },
    { name = "Frost Cavern - Never-Melt Ice item ball disappeared", flag_id = 0x0588 },
    { name = "Frost Cavern - TM79 (Frost Breath) item ball disappeared", flag_id = 0x0589 },
    { name = "Frost Cavern - Ether item ball disappeared", flag_id = 0x058A },
    { name = "Frost Cavern - Zinc item ball disappeared", flag_id = 0x058B },
    { name = "Frost Cavern - Icy Rock item ball disappeared", flag_id = 0x058C },
    { name = "Route 18 - Icicle Plate item ball disappeared", flag_id = 0x058D },
    { name = "Route 18 - Calcium item ball disappeared", flag_id = 0x058E },
    { name = "Route 18 - Rare Candy item ball disappeared", flag_id = 0x058F },
    { name = "Route 19 - Hyper Potion item ball disappeared", flag_id = 0x0590 },
    { name = "Route 19 - PP Up item ball disappeared", flag_id = 0x0591 },
    { name = "Route 19 - X Defense item ball disappeared", flag_id = 0x0592 },
    { name = "Route 19 - Max Ether item ball disappeared", flag_id = 0x0593 },
    { name = "Terminus Cave - Star Piece item ball disappeared", flag_id = 0x0594 },
    { name = "Terminus Cave - Heat Rock item ball disappeared", flag_id = 0x0595 },
    { name = "Terminus Cave - Escape Rope item ball disappeared", flag_id = 0x0596 },
    { name = "Terminus Cave - Reaper Cloth item ball disappeared", flag_id = 0x0597 },
    { name = "Terminus Cave - Dusk Stone item ball disappeared", flag_id = 0x0598 },
    { name = "Terminus Cave - X Attack item ball disappeared", flag_id = 0x0599 },
    { name = "Terminus Cave - Elixir item ball disappeared", flag_id = 0x059A },
    { name = "Terminus Cave - Full Heal item ball disappeared", flag_id = 0x059B },
    { name = "Terminus Cave - Iron Plate item ball disappeared", flag_id = 0x059C },
    { name = "Terminus Cave - TM30 (Shadow Ball) item ball disappeared", flag_id = 0x059D },
    { name = "Terminus Cave - Griseous Orb item ball disappeared", flag_id = 0x059E },
    { name = "Terminus Cave - Dragon Scale item ball disappeared", flag_id = 0x059F },
    { name = "Terminus Cave - TM31 (Brick Break) item ball disappeared", flag_id = 0x05A0 },
    { name = "Route 20 - Max Revive item ball disappeared", flag_id = 0x05A1 },
    { name = "Route 20 - HP Up item ball disappeared", flag_id = 0x05A2 },
    { name = "Route 20 - Rare Bone item ball disappeared", flag_id = 0x05A3 },
    { name = "Route 20 - PP Up item ball disappeared", flag_id = 0x05A4 },
    { name = "Route 20 - Toxic Plate item ball disappeared", flag_id = 0x05A5 },
    { name = "Route 20 - TM36 (Sludge Bomb) item ball disappeared", flag_id = 0x05A6 },
    { name = "Route 21 - Paralyze Heal item ball disappeared", flag_id = 0x05A7 },
    { name = "Route 21 - Protein item ball disappeared", flag_id = 0x05A8 },
    { name = "Route 21 - Meadow Plate item ball disappeared", flag_id = 0x05A9 },
    { name = "Route 21 - X Accuracy item ball disappeared", flag_id = 0x05AA },
    { name = "Route 21 - TM53 (Energy Ball) item ball disappeared", flag_id = 0x05AB },
    { name = "Pokémon Village - Max Ether item ball disappeared", flag_id = 0x05AC },
    { name = "Pokémon Village - Full Restore item ball disappeared", flag_id = 0x05AD },
    { name = "Pokémon Village - Pixie Plate item ball disappeared", flag_id = 0x05AE },
    { name = "Pokémon Village - TM29 (Psychic) item ball disappeared", flag_id = 0x05AF },
    { name = "Route 21 - Insect Plate item ball disappeared", flag_id = 0x05B0 },
    { name = "Route 21 - Elixir item ball disappeared", flag_id = 0x05B1 },
    { name = "Route 21 - TM22 (Solar Beam) item ball disappeared", flag_id = 0x05B2 },
    { name = "Route 21 - Rare Candy item ball disappeared", flag_id = 0x05B3 },
    { name = "Route 21 - Repeat Ball item ball disappeared", flag_id = 0x05B4 },
    { name = "Victory Road - Dusk Ball item ball disappeared", flag_id = 0x05B5 },
    { name = "Victory Road - TM03 (Psyshock) item ball disappeared", flag_id = 0x05B6 },
    { name = "Victory Road - Rare Candy item ball disappeared", flag_id = 0x05B7 },
    { name = "Victory Road - Carbos item ball disappeared", flag_id = 0x05B8 },
    { name = "Victory Road - PP Up item ball disappeared", flag_id = 0x05B9 },
    { name = "Victory Road - Zinc item ball disappeared", flag_id = 0x05BA },
    { name = "Victory Road - Max Elixir item ball disappeared", flag_id = 0x05BB },
    { name = "Victory Road - Dragon Fang item ball disappeared", flag_id = 0x05BC },
    { name = "Victory Road - Full Restore item ball disappeared", flag_id = 0x05BD },
    { name = "Victory Road - TM02 (Dragon Claw) item ball disappeared", flag_id = 0x05BE },
    { name = "Camphrier Town - X Attack item ball disappeared", flag_id = 0x05BF },
    { name = "Ambrette Town - Pearl item ball disappeared", flag_id = 0x05C0 },
    { name = "Cyllage City - Super Potion item ball disappeared", flag_id = 0x05C1 },
    { name = "Cyllage City - X Sp. Atk item ball disappeared", flag_id = 0x05C2 },
    { name = "Cyllage City - X Defense item ball disappeared", flag_id = 0x05C3 },
    { name = "Geosenge Town - Timer Ball item ball disappeared", flag_id = 0x05C4 },
    { name = "Coumarine City - Sky Plate item ball disappeared", flag_id = 0x05C5 },
    { name = "Laverre City - Ether item ball disappeared", flag_id = 0x05C6 },
    { name = "Dendemille Town - Big Root item ball disappeared", flag_id = 0x05C7 },
    { name = "Couriway Town - Rare Candy item ball disappeared", flag_id = 0x05C8 },
    { name = "Couriway Town - Max Potion item ball disappeared", flag_id = 0x05C9 },
    { name = "Couriway Town - TM80 (Rock Slide) item ball disappeared", flag_id = 0x05CA },
    { name = "Snowbelle City - Full Restore item ball disappeared", flag_id = 0x05CB },
    { name = "Route 7 - Heal Ball item ball disappeared", flag_id = 0x05CC },
    { name = "Shabboneau Castle - Escape Rope item ball disappeared", flag_id = 0x05CD },
    { name = "Parfum Palace - Ether item ball disappeared", flag_id = 0x05CE },
    { name = "Parfum Palace - Amulet Coin item ball disappeared", flag_id = 0x05CF },
    { name = "Parfum Palace - Antidote item ball disappeared", flag_id = 0x05D0 },
    { name = "Kalos Power Plant - Zap Plate item ball disappeared", flag_id = 0x05D1 },
    { name = "Lysandre Labs - Hyper Potion item ball disappeared", flag_id = 0x05D2 },
    { name = "Lysandre Labs - Black Glasses item ball disappeared", flag_id = 0x05D3 },
    { name = "Lysandre Labs - Revive item ball disappeared", flag_id = 0x05D4 },
    { name = "Lysandre Labs - Rare Candy item ball disappeared", flag_id = 0x05D5 },
    { name = "Chamber of Emptiness - Spooky Plate item ball disappeared", flag_id = 0x05D6 },
    { name = "Parfum Palace - Revive item ball disappeared", flag_id = 0x05D7 },
    { name = "Parfum Palace - Super Potion item ball disappeared", flag_id = 0x05D8 },
    { name = "Santalune Forest - Potion item ball disappeared (2)", flag_id = 0x05D9 },
    { name = "Shalour City - Max Ether item ball disappeared", flag_id = 0x05DA },
    { name = "Kiloude City - Nugget item ball disappeared", flag_id = 0x05DB },
    { name = "Route 14 - Rare Candy item ball disappeared", flag_id = 0x05DC },
    { name = "Santalune Forest - Potion item ball disappeared (3)", flag_id = 0x05DD },
    { name = "Santalune Forest - Antidote item ball disappeared", flag_id = 0x05DE },
    { name = "Route 22 - TM26 (Earthquake) item ball disappeared", flag_id = 0x05DF },
    { name = "Camphrier Town - Star Piece item ball disappeared", flag_id = 0x05E0 },
    { name = "Azure Bay - Deep Sea Scale item ball disappeared", flag_id = 0x05E1 },
    { name = "Terminus Cave - Adamant Orb item ball disappeared", flag_id = 0x05E2 },
    { name = "Terminus Cave - Lustrous Orb item ball disappeared", flag_id = 0x05E3 },
    { name = "Geosenge Town - Soft Sand item ball disappeared", flag_id = 0x05E4 },
    { name = "Route 7 - Miracle Seed item ball disappeared", flag_id = 0x05E5 },
    { name = "Glittering Cave - Escape Rope item ball disappeared", flag_id = 0x05E6 },
    { name = "Parfum Palace - HM01 (Cut) item ball disappeared", flag_id = 0x05E7 },
    { name = "Victory Road - Quick Ball item ball disappeared", flag_id = 0x05E8 },
    { name = "Coumarine City - Received Diploma for completing Central Kalos Pokédex (native) from Game Director", flag_id = 0x0A76 },
    { name = "Coumarine City - Received Diploma for completing Coastal Kalos Pokédex (native) from Game Director", flag_id = 0x0A77 },
    { name = "Coumarine City - Received Diploma for completing Mountain Kalos Pokédex (native) from Game Director", flag_id = 0x0A78 },
    { name = "Coumarine City - Received Diploma for completing all Kalos Pokédexes (native) from Game Director", flag_id = 0x0A79 },
    { name = "Coumarine City - Received Diploma for completing Central Kalos Pokédex from Game Director", flag_id = 0x0A7A },
    { name = "Coumarine City - Received Diploma for completing Coastal Kalos Pokédex from Game Director", flag_id = 0x0A7B },
    { name = "Coumarine City - Received Diploma for completing Mountain Kalos Pokédex from Game Director", flag_id = 0x0A7C },
    { name = "Coumarine City - Received Diploma for completing all Kalos Pokédexes from Game Director", flag_id = 0x0A7D },
    { name = "Coumarine City - Received Diploma for completing National Pokédex from Game Director", flag_id = 0x0A7E },
    { name = "Camphrier Town - [Daily] Received Sweet Heart from maid", flag_id = 0x0B90 },
    { name = "Ambrette Town - [Daily] Exchanged a Poké Ball for a Dive Ball with the punk guy", flag_id = 0x0BA5 },
    { name = "Lumiose City (South Boulevard) - [Daily] Received Rare Candy from male scientist for a chain length of at least 31 Pokémon with the Poké Radar", flag_id = 0x0BA6 },
    { name = "Ambrette Town - [Daily] Received Health Wing from woman for showing a Pokémon with a Speed stat equals or higher than requested", flag_id = 0x0BAC },
    { name = "TMFLG_C06_ITEMGET_01", flag_id = 0x0BAE },
    { name = "TMFLG_C06_ITEMGET_02", flag_id = 0x0BAF },
    { name = "Coumarine City - [Daily] Picked the random berry from the empty stand", flag_id = 0x0BB3 },
    { name = "Camphrier Town - [Daily] Received a berry from man for showing him a Pokémon of the requested type", flag_id = 0x0BB7 },
    { name = "TMFLG_C02R2701_ITEMGET_01", flag_id = 0x0BBC },
    { name = "Lumiose City (South Boulevard) - [Daily] Received PP Max from male scientist for a chain length of 21-30 Pokémon with the Poké Radar", flag_id = 0x0BBD },
    { name = "Lumiose City (South Boulevard) - [Daily] Received PP Up from male scientist for a chain length of 11-20 Pokémon with the Poké Radar", flag_id = 0x0BBE },
    { name = "Lumiose City (South Boulevard) - [Daily] Received Ultra Ball from male scientist for a chain length of 1-10 Pokémon with the Poké Radar", flag_id = 0x0BBF },
    { name = "Coumarine City - [Daily] Received Heart Scale from Tierno for showing him a Pokémon with the requested dance move", flag_id = 0x0BC5 },
}

local checked_flags  = {}
local prev_bag_snap  = {}

-- ============================================================================
-- Generic Connector Protocol (port 43055 for ArchipelagoBizHawkClient.exe)
-- ============================================================================
local SOCKET_PORT_FIRST     = 43055
local SOCKET_PORT_RANGE_SIZE = 5
local SOCKET_PORT_LAST      = SOCKET_PORT_FIRST + SOCKET_PORT_RANGE_SIZE

local STATE_NOT_CONNECTED = 0
local STATE_CONNECTED     = 1

local server        = nil
local ap_socket     = nil
local current_state = STATE_NOT_CONNECTED
local timeout_timer = 0
local message_timer = 0
local message_interval = 0
local prev_time     = 0
local current_time  = 0
local locked        = false
local rom_hash      = nil

-- Queue implementation
local function queue_push(self, value) self[self.right] = value; self.right = self.right + 1 end
local function queue_is_empty(self) return self.right == self.left end
local function queue_shift(self)
    local value = self[self.left]; self[self.left] = nil; self.left = self.left + 1; return value
end
local function new_queue()
    local q = {left = 1, right = 1}
    return setmetatable(q, {__index = {is_empty = queue_is_empty, push = queue_push, shift = queue_shift}})
end
local message_queue = new_queue()

local function lock()   locked = true;  ap_socket:settimeout(2) end
local function unlock() locked = false; ap_socket:settimeout(0) end

-- ============================================================================
-- Pokémon Y RAM Routines (N3DS Extra RAM domain via mainmemory)
-- ============================================================================
-- Pocket RAM Base Addresses (Official Bulbapedia Gen VI Pocket Layout)
local POCKET_ITEMS    = 0x074D5554
local POCKET_KEY      = 0x074D5B94
local POCKET_TM       = 0x074D5D14
local POCKET_MEDICINE = 0x074D5EBC
local POCKET_BERRIES  = 0x074D5FBC

local function read_bag_snapshot()
    memory.usememorydomain(MEMORY_DOMAIN)
    local snap = {}
    local pockets = {
        {base = POCKET_ITEMS, slots = 100},
        {base = POCKET_KEY, slots = 60},
        {base = POCKET_TM, slots = 110},
        {base = POCKET_MEDICINE, slots = 60},
        {base = POCKET_BERRIES, slots = 70}
    }
    for _, pocket in ipairs(pockets) do
        for slot = 0, pocket.slots - 1 do
            local addr    = pocket.base + (slot * 4)
            local item_id = mainmemory.read_u16_le(addr)
            local qty     = mainmemory.read_u16_le(addr + 2)
            if item_id ~= 0 then
                snap[item_id] = (snap[item_id] or 0) + qty
            end
        end
    end
    return snap
end

local function remove_item_from_bag(item_id)
    memory.usememorydomain(MEMORY_DOMAIN)
    local pockets = {
        {base = POCKET_ITEMS, slots = 100},
        {base = POCKET_KEY, slots = 60},
        {base = POCKET_TM, slots = 110},
        {base = POCKET_MEDICINE, slots = 60},
        {base = POCKET_BERRIES, slots = 70}
    }
    for _, pocket in ipairs(pockets) do
        for slot = 0, pocket.slots - 1 do
            local addr    = pocket.base + (slot * 4)
            local slot_id = mainmemory.read_u16_le(addr)
            if slot_id == item_id then
                local qty = mainmemory.read_u16_le(addr + 2)
                if qty > 1 then
                    mainmemory.write_u16_le(addr + 2, qty - 1)
                else
                    -- Shift all subsequent slots left to compact the pocket array
                    for s = slot, pocket.slots - 2 do
                        local curr_addr = pocket.base + (s * 4)
                        local next_addr = pocket.base + ((s + 1) * 4)
                        local next_id   = mainmemory.read_u16_le(next_addr)
                        local next_qty  = mainmemory.read_u16_le(next_addr + 2)

                        mainmemory.write_u16_le(curr_addr,     next_id)
                        mainmemory.write_u16_le(curr_addr + 2, next_qty)

                        if next_id == 0 then break end
                    end
                    -- Zero out the last slot in the pocket
                    local last_addr = pocket.base + ((pocket.slots - 1) * 4)
                    mainmemory.write_u16_le(last_addr,     0)
                    mainmemory.write_u16_le(last_addr + 2, 0)
                end
                print(string.format("[PokéY] Removed vanilla pickup item 0x%04X from bag (compacted pocket)", item_id))
                return true
            end
        end
    end
    return false
end

local function give_badge(badge_num)
    if badge_num < 1 or badge_num > BADGE_COUNT then return false end
    memory.usememorydomain(MEMORY_DOMAIN)
    local current = mainmemory.read_u8(ADDR_BADGES)
    local new_val = current | (1 << (badge_num - 1))
    mainmemory.write_u8(ADDR_BADGES, new_val)
    print(string.format("[PokéY] Badge %d granted! 0x%02X -> 0x%02X", badge_num, current, new_val))
    return true
end

local function get_pocket_base(item_id, category)
    -- 1. Key Items Pocket: (700..730, 450..465)
    if (item_id >= 700 and item_id <= 730) or (item_id >= 450 and item_id <= 465) or category == "Key Items" or category == "KeyItems" then
        return POCKET_KEY, 60
    end

    -- 2. TMs & HMs Pocket: HMs (328..332) and TMs (333..424, 692..699)
    if (item_id >= 328 and item_id <= 424) or (item_id >= 692 and item_id <= 699) then
        return POCKET_TM, 110
    end

    -- 3. Medicine Pocket: Potions, Status Heals, Revives, Vitamins, Drinks, Herbs (17..54)
    if (item_id >= 17 and item_id <= 54) then
        return POCKET_MEDICINE, 60
    end

    -- 4. Berries Pocket: All Berries (149..212)
    if category == "Berries" or (item_id >= 149 and item_id <= 212) then
        return POCKET_BERRIES, 70
    end

    -- 5. Items Pocket: General Items, Poké Balls (1..16), Evolutionary Stones, Held Items, Mega Stones
    return POCKET_ITEMS, 100
end

local function give_bag_item(item_id, count, category)
    count = count or 1
    memory.usememorydomain(MEMORY_DOMAIN)
    local pocket_base, max_slots = get_pocket_base(item_id, category)

    local empty_slot_addr = nil
    for slot = 0, max_slots - 1 do
        local addr     = pocket_base + (slot * 4)
        local slot_id  = mainmemory.read_u16_le(addr)
        local slot_qty = mainmemory.read_u16_le(addr + 2)
        if slot_id == item_id then
            local new_qty = math.min(slot_qty + count, 999)
            mainmemory.write_u16_le(addr + 2, new_qty)
            local msg = string.format("Received AP Item 0x%04X (qty %d)", item_id, new_qty)
            print(string.format("[PokéY Thought] 🎁 AP ITEM RECEIVED: 0x%04X (stacked qty -> %d). Baseline snapshot updated.", item_id, new_qty))
            gui.addmessage(msg)

            -- Update prev_bag_snap immediately to match full RAM state
            prev_bag_snap = read_bag_snapshot()
            return true
        end
        if slot_id == 0 and not empty_slot_addr then
            empty_slot_addr = addr
        end
    end
    if empty_slot_addr then
        mainmemory.write_u16_le(empty_slot_addr,     item_id)
        mainmemory.write_u16_le(empty_slot_addr + 2, count)
        local msg = string.format("Received AP Item 0x%04X (qty %d)", item_id, count)
        print(string.format("[PokéY Thought] 🎁 AP ITEM RECEIVED: 0x%04X (new slot qty %d). Baseline snapshot updated.", item_id, count))
        gui.addmessage(msg)

        -- Update prev_bag_snap immediately to match full RAM state
        prev_bag_snap = read_bag_snapshot()
        return true
    end
    return false
end

-- ============================================================================
-- Manual Debug Console Commands (Type directly into BizHawk Lua Console)
-- Usage:
--   give(0x0011, 5)     -> Injects 5 Potions (0x0011) into your bag
--   check_flag(0x051A)  -> Manually sets event flag 0x051A in RAM and checks it
--   check_loc("Route 2") -> Manually checks all locations containing "Route 2"
-- ============================================================================
function give(item_id, count, category)
    count = count or 1
    if give_bag_item(item_id, count, category) then
        print(string.format("[PokéY Manual] 🎁 Manually injected item 0x%04X (qty %d) into bag!", item_id, count))
        gui.addmessage(string.format("Manual Item: 0x%04X x%d", item_id, count))
    else
        print(string.format("[PokéY Manual] ❌ Failed to inject item 0x%04X (pocket full).", item_id))
    end
end

function check_flag(flag_id)
    memory.usememorydomain(MEMORY_DOMAIN)
    local byte_offset = math.floor(flag_id / 8)
    local bit_in_byte = flag_id % 8
    local addr        = EVENT_FLAGS_BASE + byte_offset
    local val         = mainmemory.read_u8(addr) or 0
    local new_val     = val | (1 << bit_in_byte)
    mainmemory.write_u8(addr, new_val)

    checked_flags[flag_id] = true
    print(string.format("[PokéY Manual] 🔍 Manually set event flag 0x%04X in RAM & marked checked.", flag_id))
    gui.addmessage(string.format("Manual Flag Check: 0x%04X", flag_id))
end

function check_loc(search)
    local count = 0
    for _, loc in ipairs(LOCATIONS) do
        if string.find(string.lower(loc.name), string.lower(search)) then
            check_flag(loc.flag_id)
            count = count + 1
        end
    end
    if count == 0 then
        print(string.format("[PokéY Manual] ⚠️ No locations found matching '%s'.", search))
    end
end

function give_badge(badge_num)
    memory.usememorydomain(MEMORY_DOMAIN)
    if badge_num == nil or badge_num == 0 or badge_num > 8 then
        mainmemory.write_u8(ADDR_BADGES, 0xFF)
        print("[PokéY Manual] 🎖️ Granted ALL 8 Gym Badges in RAM!")
        gui.addmessage("Manual Badges: ALL 8 Granted!")
    else
        local current = mainmemory.read_u8(ADDR_BADGES) or 0
        local new_val = current | (1 << (badge_num - 1))
        mainmemory.write_u8(ADDR_BADGES, new_val)
        print(string.format("[PokéY Manual] 🎖️ Granted Gym Badge %d in RAM!", badge_num))
        gui.addmessage(string.format("Manual Badge: %d Granted!", badge_num))
    end
end

-- Export to global environment for BizHawk Console input
_G.give        = give
_G.give_badge  = give_badge
_G.check_flag  = check_flag
_G.check_loc   = check_loc

local function is_flag_set(flag_id)
    memory.usememorydomain(MEMORY_DOMAIN)
    local byte_offset = math.floor(flag_id / 8)
    local bit_in_byte = flag_id % 8
    local addr        = EVENT_FLAGS_BASE + byte_offset
    local val         = mainmemory.read_u8(addr) or 0
    return (val & (1 << bit_in_byte)) ~= 0, addr, bit_in_byte
end

-- ============================================================================
-- Generic Connector Request Handlers (Intercept N3DS Extra RAM for mainmemory)
-- ============================================================================
local request_handlers = {
    ["PING"] = function(req)
        return {type = "PONG"}
    end,

    ["SYSTEM"] = function(req)
        return {type = "SYSTEM_RESPONSE", value = emu.getsystemid()}
    end,

    ["PREFERRED_CORES"] = function(req)
        local preferred_cores = client.getconfig().PreferredCores
        local iter = preferred_cores.Keys:GetEnumerator()
        local val = {}
        while iter:MoveNext() do
            val[iter.Current] = preferred_cores[iter.Current]
        end
        return {type = "PREFERRED_CORES_RESPONSE", value = val}
    end,

    ["HASH"] = function(req)
        return {type = "HASH_RESPONSE", value = rom_hash}
    end,

    ["MEMORY_SIZE"] = function(req)
        return {type = "MEMORY_SIZE_RESPONSE", value = memory.getmemorydomainsize(req["domain"])}
    end,

    ["GUARD"] = function(req)
        local expected = base64.decode(req["expected_data"])
        local actual   = memory.read_bytes_as_array(req["address"], #expected, req["domain"])
        local valid    = true
        for i, byte in ipairs(actual) do
            if byte ~= expected[i] then valid = false; break end
        end
        return {type = "GUARD_RESPONSE", value = valid, address = req["address"]}
    end,

    ["LOCK"] = function(req)
        lock()
        return {type = "LOCKED"}
    end,

    ["UNLOCK"] = function(req)
        unlock()
        return {type = "UNLOCKED"}
    end,

    ["READ"] = function(req)
        memory.usememorydomain(MEMORY_DOMAIN)
        if req["reads"] ~= nil then
            local results = {}
            for i, read_req in ipairs(req["reads"]) do
                local addr  = read_req[1]
                local size  = read_req[2]
                local bytes = {}
                for b = 0, size - 1 do
                    bytes[b + 1] = mainmemory.read_u8(addr + b) or 0
                end
                results[i] = base64.encode(bytes)
            end
            return {type = "READ_RESPONSE", value = results}
        else
            local addr  = req["address"]
            local size  = req["size"]
            local bytes = {}
            for b = 0, size - 1 do
                bytes[b + 1] = mainmemory.read_u8(addr + b) or 0
            end
            return {type = "READ_RESPONSE", value = base64.encode(bytes)}
        end
    end,

    ["WRITE"] = function(req)
        local data = base64.decode(req["value"])
        if req["domain"] == MEMORY_DOMAIN then
            memory.usememorydomain(MEMORY_DOMAIN)
            for i, byte in ipairs(data) do
                mainmemory.write_u8(req["address"] + i - 1, byte)
            end
        else
            memory.write_bytes_as_array(req["address"], data, req["domain"])
        end
        return {type = "WRITE_RESPONSE"}
    end,

    ["GIVE_ITEM"] = function(req)
        local item_id  = req["item_id"]
        local count    = req["count"] or 1
        local category = req["category"]
        local success  = give_bag_item(item_id, count, category)
        return {type = "GIVE_ITEM_RESPONSE", value = success}
    end,

    ["DISPLAY_MESSAGE"] = function(req)
        message_queue:push(req["message"])
        return {type = "DISPLAY_MESSAGE_RESPONSE"}
    end,

    ["SET_MESSAGE_INTERVAL"] = function(req)
        message_interval = req["value"]
        return {type = "SET_MESSAGE_INTERVAL_RESPONSE"}
    end,

    ["default"] = function(req)
        return {type = "ERROR", err = "Unknown command: " .. req["type"]}
    end,
}

local function process_request(req)
    local handler = request_handlers[req["type"]] or request_handlers["default"]
    return handler(req)
end

local function send_receive()
    local message, err = ap_socket:receive()
    if err == "closed" then
        if current_state == STATE_CONNECTED then
            print("[PokéY] ArchipelagoBizHawkClient disconnected")
        end
        current_state = STATE_NOT_CONNECTED
        return
    elseif err == "timeout" then
        unlock(); return
    elseif err ~= nil then
        print(err); current_state = STATE_NOT_CONNECTED; unlock(); return
    end

    timeout_timer = 5
    if DEBUG then print("Recv: " .. message) end

    if message == "VERSION" then
        ap_socket:send(tostring(SCRIPT_VERSION) .. "\n")
    else
        local res  = {}
        local data = json.decode(message)
        local failed_guard = nil
        for i, req in ipairs(data) do
            if failed_guard ~= nil then
                res[i] = failed_guard
            else
                local ok, response = pcall(process_request, req)
                if ok then
                    res[i] = response
                    if response["type"] == "GUARD_RESPONSE" and not response["value"] then
                        failed_guard = response
                    end
                else
                    if type(response) ~= "string" then response = "Unknown error" end
                    res[i] = {type = "ERROR", err = response}
                end
            end
        end
        ap_socket:send(json.encode(res) .. "\n")
    end
end

local function initialize_server()
    local port = SOCKET_PORT_FIRST
    local res, err
    server, err = socket.socket.tcp4()
    while res == nil and port <= SOCKET_PORT_LAST do
        res, err = server:bind("localhost", port)
        if res == nil and err ~= "address already in use" then
            print(err); return
        end
        if res == nil then port = port + 1 end
    end
    if port > SOCKET_PORT_LAST then
        print("Too many connector instances running. Exiting."); return
    end
    server:listen(0)
    server:settimeout(0)
    print(string.format("[PokéY] Listening for ArchipelagoBizHawkClient on port %d", port))
end

local prev_flags = {}

local function scan_event_flags()
    memory.usememorydomain(MEMORY_DOMAIN)
    local current_flags = {}
    for i = 0, 255 do
        current_flags[i] = mainmemory.read_u8(EVENT_FLAGS_BASE + i)
    end

    if #prev_flags > 0 then
        for i = 0, 255 do
            local old_b = prev_flags[i] or 0
            local new_b = current_flags[i] or 0
            if old_b ~= new_b then
                local diff = new_b & (~old_b)
                if diff ~= 0 then
                    for bit = 0, 7 do
                        if (diff & (1 << bit)) ~= 0 then
                            local flag_id = (i * 8) + bit
                            print(string.format("[PokéY Flag Detector] NEW FLAG SET: 0x%04X (offset +0x%02X bit %d)", flag_id, i, bit))
                        end
                    end
                end
            end
        end
    end
    prev_flags = current_flags
end

local pending_item_removals = 0
local bag_initialized       = false

local function monitor_locations()
    scan_event_flags()

    local current_bag_snap = read_bag_snapshot()

    -- First frame: establish baseline bag and location state.
    -- Any location already found in RAM prior to turning on the script is marked checked and ignored.
    if not bag_initialized then
        bag_initialized = true
        prev_bag_snap = current_bag_snap

        local pre_existing_count = 0
        for _, loc in ipairs(LOCATIONS) do
            if is_flag_set(loc.flag_id) then
                checked_flags[loc.flag_id] = true
                pre_existing_count = pre_existing_count + 1
            end
        end
        print(string.format("[PokéY Thought] 🔒 INITIALIZED BASELINE: Ignored %d location(s) already found prior to script startup.", pre_existing_count))
        return
    end

    -- Detect newly checked locations
    for _, loc in ipairs(LOCATIONS) do
        local is_set = is_flag_set(loc.flag_id)
        if is_set and not checked_flags[loc.flag_id] then
            checked_flags[loc.flag_id] = true
            local msg = "Location checked: " .. loc.name
            print(string.format("[PokéY Thought] 🔍 LOCATION CHECKED: '%s' (Flag 0x%04X set). Queuing 1 pending vanilla removal (Total pending: %d)", loc.name, loc.flag_id, pending_item_removals + 1))
            gui.addmessage(msg)
            pending_item_removals = pending_item_removals + 1
        end
    end

    -- Check for unexpected vanilla bag increases every frame.
    -- AP items are baseline-updated in prev_bag_snap by give_bag_item, so they are never touched.
    for item_id, qty in pairs(current_bag_snap) do
        local prev_qty = prev_bag_snap[item_id] or 0
        if qty > prev_qty then
            local added = qty - prev_qty
            print(string.format("[PokéY Thought] 🎒 BAG INCREASE DETECTED: Item 0x%04X quantity changed (%d -> %d, +%d)", item_id, prev_qty, qty, added))
            if pending_item_removals > 0 then
                print(string.format("[PokéY Thought] 🗑️ PENDING REMOVAL ACTIVE (%d pending). Removing vanilla item 0x%04X from bag...", pending_item_removals, item_id))
                for _ = 1, added do
                    if remove_item_from_bag(item_id) then
                        pending_item_removals = math.max(0, pending_item_removals - 1)
                        print(string.format("[PokéY Thought] ✅ Vanilla item 0x%04X removed & pocket compacted. (Remaining pending: %d)", item_id, pending_item_removals))
                    end
                end
            else
                print(string.format("[PokéY Thought] ℹ️ Bag increase for 0x%04X ignored because no pending location removals exist (e.g. shop/gift).", item_id))
            end
        end
    end

    prev_bag_snap = current_bag_snap
end

-- ============================================================================
-- Main Loop
-- ============================================================================
print("==============================================")
print(" Pokémon Y Archipelago Connector")
print(" Serves ArchipelagoBizHawkClient on port 43055")
print("==============================================")

if bizhawk_major < 2 or (bizhawk_major == 2 and bizhawk_minor < 7) then
    print("Must use BizHawk 2.7.0 or newer")
else
    if emu.getsystemid() == "NULL" then
        print("No ROM loaded. Please load Pokémon Y.")
        while emu.getsystemid() == "NULL" do emu.frameadvance() end
    end

    rom_hash = gameinfo.getromhash()
    print("ROM hash: " .. (rom_hash or "unknown"))

    local function main()
        while true do
            if server == nil then initialize_server() end

            current_time  = socket.socket.gettime()
            timeout_timer = timeout_timer - (current_time - prev_time)
            message_timer = message_timer - (current_time - prev_time)
            prev_time     = current_time

            if message_timer <= 0 and not message_queue:is_empty() then
                gui.addmessage(message_queue:shift())
                message_timer = message_interval
            end

            if current_state == STATE_NOT_CONNECTED then
                if emu.framecount() % 30 == 0 then
                    local c = server:accept()
                    if c then
                        print("[PokéY] ArchipelagoBizHawkClient connected!")
                        current_state = STATE_CONNECTED
                        ap_socket     = c
                        server:close()
                        server        = nil
                        ap_socket:settimeout(0)
                    end
                end
            else
                repeat send_receive() until not locked
                if timeout_timer <= 0 then
                    print("[PokéY] Client timed out")
                    current_state = STATE_NOT_CONNECTED
                end
            end

            monitor_locations()
            coroutine.yield()
        end
    end

    event.onexit(function()
        print("-- Connector stopping --")
        if server ~= nil then server:close() end
    end)

    local co = coroutine.create(main)
    local function tick()
        local ok, err = coroutine.resume(co)
        if not ok and err ~= "cannot resume dead coroutine" then
            print("ERROR: " .. err)
            if server ~= nil then server:close() end
            co = coroutine.create(main)
        end
    end

    event.onframeend(tick)
    while true do emu.frameadvance() end
end
