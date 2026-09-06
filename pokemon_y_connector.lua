-- ============================================================================
-- Pokémon X & Y Archipelago BizHawk Connector (Vanilla Item Interceptor Build)
-- Location: Z:\ProgramData\Archipelago\data\lua\pokemon_y_connector.lua
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

-- Helper to determine if a triggered flag is an item pickup location
local function is_item_check(flag_id)
    local non_item_flags = {
        [0x06D2] = true, -- Bug Badge
        [0x0718] = true, -- Cliff Badge
        [0x06E1] = true, -- Rumble Badge
        [0x06E2] = true, -- Plant Badge
        [0x06E3] = true, -- Voltage Badge
        [0x06E4] = true, -- Fairy Badge
        [0x06E5] = true, -- Psychic Badge
        [0x06E6] = true, -- Iceberg Badge
        [0x0600] = true, -- Champion Victory
        [0x0A52] = true, -- Can access Pokédex
    }
    if non_item_flags[flag_id] then
        return false
    end
    -- Pure trainer battle flag ranges (e.g. 0x06F0 - 0x06FF)
    if flag_id >= 0x06F0 and flag_id <= 0x06FF then
        return false
    end
    return true
end

-- Comprehensive Location Definitions matching worlds/pokemon_y/Locations.py
local LOCATION_NAMES = {
    [0x06D2] = "Santalune Area - Bug Badge",
    [0x0718] = "Cyllage Area - Cliff Badge",
    [0x06E1] = "Shalour Area - Rumble Badge",
    [0x06E2] = "Coumarine Area - Plant Badge",
    [0x06E3] = "Lumiose Area - Voltage Badge",
    [0x06E4] = "Laverre Area - Fairy Badge",
    [0x06E5] = "Anistar Area - Psychic Badge",
    [0x06E6] = "Snowbelle Area - Iceberg Badge",
    [0x0600] = "Pokémon League - Champion Victory",

    [0x051A] = "Santalune Forest - Potion item ball (1)",
    [0x051B] = "Santalune Forest - Poké Ball item ball",
    [0x051C] = "Route 3 - Super Potion item ball",
    [0x051D] = "Route 3 - Revive item ball",
    [0x051E] = "Route 3 - Dawn Stone item ball",
    [0x051F] = "Route 22 - Super Potion item ball",
    [0x0520] = "Route 22 - Elixir item ball",
    [0x0521] = "Route 22 - Draco Plate item ball",
    [0x05D9] = "Santalune Forest - Potion item ball (2)",
    [0x05DD] = "Santalune Forest - Potion item ball (3)",
    [0x05DE] = "Santalune Forest - Antidote item ball",
    [0x00D7] = "Santalune Forest - Received Poké Ball from Calem/Serena",
    [0x00A4] = "Aquacorde Town - Received Potion from shopkeeper",
    [0x0A52] = "Aquacorde Town - Can access Pokédex",
    [0x06F1] = "Route 2 - Battled Youngster Austin",
}

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
        local h = "POKEMON_Y"
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
print(" Pokémon X/Y Archipelago Connector Active")
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
                        else
                            print(string.format(">>> [EVENT FLAG SET] Flag ID: 0x%04X", flag_id))
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
    gui.drawText(5, 5, "=== Pokémon X/Y Archipelago Connector ===", "yellow", "black", 12)
    gui.drawText(5, 21, client and "Status: CONNECTED TO CLIENT" or "Status: LISTENING ON PORT 43055", client and "lime" or "yellow", "black", 11)
    if hold_ap_items then
        gui.drawText(5, 37, string.format("HOLD: Intercepting Vanilla Item (%d left)...", pending_vanilla_removals), "orange", "black", 11)
    end

    emu.frameadvance()
end
