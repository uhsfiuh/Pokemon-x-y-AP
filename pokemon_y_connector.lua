-- ============================================================================
-- Pokémon Y BizHawk Connector for Archipelago
-- Location: z:\Users\crazy\OneDrive\Desktop\code\POKEMONXYAP\pokemon_y_connector.lua
-- ============================================================================

local socket = nil
pcall(function() socket = require("socket") end)
if not socket then
    pcall(function() socket = require("socket.core") end)
end

local MEMORY_DOMAIN = "N3DS Extra RAM"

-- Memory Addresses
local ADDR_BAG_ITEMS   = 0x074D5554
local ADDR_MONEY       = 0x074D869C
local ADDR_BADGES      = 0x074D86A0
local EVENT_FLAGS_BASE = 0x074E86B8

local PORT = 43055
local UNIQUE_HANDSHAKE = "CLIENT_HANDSHAKE:POKEMON_Y_V1"

local server_socket = nil
local tcp_client = nil
local connection_active = false
local handshake_complete = false
local last_attempt = 0

-- Active Locations to Monitor
local LOCATIONS = {
    { name = "Route 4 - Great Ball", flag_id = 0x0522 },
    { name = "Route 4 - Repel",      flag_id = 0x0525 },
}

local checked_flags = {}

local function get_socket_func(func_name)
    if type(socket) == "table" then
        if socket[func_name] then return socket[func_name] end
        if type(socket.socket) == "table" and socket.socket[func_name] then
            return socket.socket[func_name]
        end
    end
    return nil
end

-- ============================================================================
-- RAM Writing Routines (Item Injection)
-- ============================================================================
function give_badge(badge_num)
    if badge_num < 1 or badge_num > 8 then return false end
    memory.usememorydomain(MEMORY_DOMAIN)
    local current_badges = mainmemory.read_u8(ADDR_BADGES)
    local badge_mask = (1 << (badge_num - 1))
    local new_badges = current_badges | badge_mask
    mainmemory.write_u8(ADDR_BADGES, new_badges)
    print(string.format("[RAM WRITER] Badge %d Granted! Badges 0x%02X -> 0x%02X", 
                        badge_num, current_badges, new_badges))
    return true
end

function add_money(amount)
    memory.usememorydomain(MEMORY_DOMAIN)
    local current_money = mainmemory.read_u32_le(ADDR_MONEY)
    local new_money = math.min(current_money + amount, 9999999)
    mainmemory.write_u32_le(ADDR_MONEY, new_money)
    print(string.format("[RAM WRITER] Money Updated! %d -> %d", current_money, new_money))
end

function give_bag_item(item_id, count)
    count = count or 1
    memory.usememorydomain(MEMORY_DOMAIN)
    local MAX_SLOTS = 100
    local target_slot_addr = nil
    
    for slot = 0, MAX_SLOTS - 1 do
        local slot_addr = ADDR_BAG_ITEMS + (slot * 4)
        local slot_item_id = mainmemory.read_u16_le(slot_addr)
        local slot_qty = mainmemory.read_u16_le(slot_addr + 2)
        
        if slot_item_id == item_id then
            local new_qty = math.min(slot_qty + count, 999)
            mainmemory.write_u16_le(slot_addr + 2, new_qty)
            print(string.format("[RAM WRITER] Stacked Item ID 0x%04X at Slot %d. Qty: %d -> %d", 
                                item_id, slot, slot_qty, new_qty))
            return true
        end
        
        if slot_item_id == 0 and not target_slot_addr then
            target_slot_addr = slot_addr
        end
    end
    
    if target_slot_addr then
        mainmemory.write_u16_le(target_slot_addr, item_id)
        mainmemory.write_u16_le(target_slot_addr + 2, count)
        print(string.format("[RAM WRITER] Added Item ID 0x%04X (Qty %d) to slot 0x%08X", 
                            item_id, count, target_slot_addr))
        return true
    end
    return false
end

-- ============================================================================
-- Protocol Verification
-- ============================================================================
function process_command(cmd)
    print("--------------------------------------------------")
    print(string.format("[AP Client -> Lua]: %s", cmd))
    
    -- Handshake Verification
    if cmd == UNIQUE_HANDSHAKE or cmd == "PING" or cmd:find("POKEMON_Y") or cmd:find("CONNECT") then
        handshake_complete = true
        connection_active = true
        print(">>> HANDSHAKE VERIFIED! PokemonYClient connected.")
        send_to_ap("LUA_HANDSHAKE_ACK:POKEMON_Y_V1")
        
    -- Process Item commands ONLY if Handshake is Verified
    elseif handshake_complete and cmd:find("GIVE_ITEM:") then
        local id_str = cmd:match("GIVE_ITEM:(%d+)")
        local ap_id = tonumber(id_str)
        if ap_id then
            if ap_id >= 200001 and ap_id <= 200008 then
                local badge_num = ap_id - 200000
                give_badge(badge_num)
                send_to_ap("ITEM_RECEIVED:" .. tostring(ap_id))
            else
                local success = give_bag_item(ap_id, 1)
                if success then
                    send_to_ap("ITEM_RECEIVED:" .. tostring(ap_id))
                end
            end
        end
    elseif not handshake_complete then
        print("[Lua Warning] Command ignored! Awaiting Handshake Verification.")
    end
    print("--------------------------------------------------")
end

-- ============================================================================
-- Socket Server & Client Management
-- ============================================================================
function manage_socket()
    if tcp_client then
        local line, err = tcp_client:receive("*l")
        if line and #line > 0 then
            process_command(line)
        elseif err == "closed" then
            print("[Lua Socket] AP Client disconnected.")
            tcp_client = nil
            connection_active = false
            handshake_complete = false
        end
        return
    end

    if not server_socket then
        local bind_func = get_socket_func("bind")
        if bind_func then
            pcall(function()
                local s, err = bind_func("127.0.0.1", PORT)
                if s then
                    server_socket = s
                    server_socket:settimeout(0.001)
                    print(string.format("[Lua Socket] Listening on 127.0.0.1:%d...", PORT))
                end
            end)
        end
    end

    if server_socket then
        local client, err = server_socket:accept()
        if client then
            tcp_client = client
            tcp_client:settimeout(0.001)
            print("[Lua Socket] Incoming connection... Awaiting Handshake Verification.")
            return
        end
    end
end

function send_to_ap(msg)
    print("[Lua -> AP Client]: " .. msg)
    if tcp_client then
        pcall(function() tcp_client:send(msg .. "\n") end)
    end
end

function get_flag_info(flag_id)
    local byte_offset = math.floor(flag_id / 8)
    local bit_in_byte = flag_id % 8
    local addr = EVENT_FLAGS_BASE + byte_offset
    local bit_mask = (1 << bit_in_byte)
    return addr, bit_mask, bit_in_byte
end

function is_flag_set(flag_id)
    memory.usememorydomain(MEMORY_DOMAIN)
    local addr, bit_mask, bit_in_byte = get_flag_info(flag_id)
    local val = mainmemory.read_u8(addr)
    local is_set = (val & bit_mask) ~= 0
    return is_set, addr, bit_in_byte
end

function monitor_locations()
    local hud_y = 5
    gui.drawText(5, hud_y, "=== Pokémon Y AP Connector ===", "yellow", "black", 12)
    hud_y = hud_y + 16

    if connection_active and handshake_complete then
        gui.drawText(5, hud_y, "AP Client: CONNECTED & VERIFIED", "lime", "black", 11)
    elseif tcp_client then
        gui.drawText(5, hud_y, "AP Client: AWAITING HANDSHAKE", "yellow", "black", 11)
    else
        gui.drawText(5, hud_y, "AP Client: DISCONNECTED (Port 43055)", "orange", "black", 11)
    end
    hud_y = hud_y + 16

    for i, loc in ipairs(LOCATIONS) do
        local is_set, addr, bit_in_byte = is_flag_set(loc.flag_id)
        local status_str = is_set and "CHECKED (SET)" or "UNCHECKED (0)"
        local status_color = is_set and "lime" or "white"
        
        gui.drawText(5, hud_y, string.format("[%d] %s: %s (Addr: 0x%08X Bit %d)", 
                     i, loc.name, status_str, addr, bit_in_byte), status_color, "black", 11)
        hud_y = hud_y + 14

        if is_set and not checked_flags[loc.flag_id] then
            checked_flags[loc.flag_id] = true
            print("--------------------------------------------------")
            print(string.format(">>> LOCATION CHECKED! %s", loc.name))
            print("--------------------------------------------------")
            if handshake_complete then
                send_to_ap("LOCATION_CHECKED:" .. loc.name)
            end
        end
    end
end

-- ============================================================================
-- Main Loop
-- ============================================================================
print("==============================================")
print(" Pokémon Y Archipelago Connector")
print(" Location: z:\\Users\\crazy\\OneDrive\\Desktop\\code\\POKEMONXYAP\\pokemon_y_connector.lua")
print("==============================================")

while true do
    manage_socket()
    monitor_locations()
    emu.frameadvance()
end
