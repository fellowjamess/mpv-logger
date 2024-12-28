local utils = require 'mp.utils'
local msg = require 'mp.msg'  -- MPV's logging module

-- Try to load socket library
local socket = require("socket")
if not socket then
    msg.error("Could not load socket library. Please ensure lua-socket is installed.")
    return
end

-- Configuration
local config = {
    server_url = "http://localhost:5000",
    update_interval = 30,
    min_play_time = 60
}

-- Debug function
local function debug_log(message, data)
    if data then
        msg.info(message .. ": " .. utils.format_json(data))
    else
        msg.info(message)
    end
end

local function get_hostname()
    -- Fallback to system command if socket.dns is not available
    local f = io.popen("/bin/hostname")
    if f then
        local hostname = f:read("*a")
        f:close()
        return hostname:gsub("^%s*(.-)%s*$", "%1") -- Trim whitespace
    end
    return "unknown"
end

-- Send progress update
local function send_update(data)
    debug_log("Attempting to send progress update", data)

    -- Create temporary file for curl output
    local temp_file = os.tmpname()
    local endpoint = "/track"  -- Use the correct endpoint

    local curl_cmd = string.format(
        'curl -X POST -H "Content-Type: application/json" -d \'%s\' %s%s -v > %s 2>&1',
        utils.format_json(data),
        config.server_url,
        endpoint,
        temp_file
    )

    debug_log("Executing curl command: " .. curl_cmd)

    -- Execute curl and capture output
    local success = os.execute(curl_cmd)

    -- Read the response
    local file = io.open(temp_file, "r")
    if file then
        local response = file:read("*all")
        file:close()
        os.remove(temp_file)
        debug_log("Curl response: " .. response)
    end

    if not success then
        debug_log("Failed to send update")
    else
        debug_log("Update sent successfully")
    end
end

-- Function to track progress periodically
local function track_progress()
    local last_time = 0
    local video_id = nil

    local function on_file_loaded()
        debug_log("File loaded event triggered")
        video_id = mp.get_property("media-title")  -- Unique identifier for the video

        -- Collecting initial media properties
        local path = mp.get_property("path")
        local title = mp.get_property("media-title")
        local total_duration = mp.get_property_number("duration")
        local current_time = mp.get_property_number("time-pos") or 0
        local file_format = mp.get_property("file-format")
        local video_format = mp.get_property("video-format")
        local audio_codec = mp.get_property("audio-codec-name")

        debug_log("Collected media properties:")
        debug_log("Path: " .. tostring(path))
        debug_log("Title: " .. tostring(title))
        debug_log("Total Duration: " .. tostring(total_duration))
        debug_log("Current Time: " .. tostring(current_time))

        local data = {
            filename = path,
            title = title,
            duration = current_time,
            total_duration = total_duration,
            format = file_format,
            video_format = video_format,
            audio_codec = audio_codec,
            timestamp = os.time(),
            hostname = get_hostname()
        }

        -- Send initial request to server
        send_update(data)
    end

    -- Periodically send progress updates
    local function on_idle()
        local total_duration = mp.get_property_number("duration")
        local current_time = mp.get_property_number("time-pos")

        if current_time and (current_time - last_time >= config.update_interval) then
            last_time = current_time

            local data = {
                id = video_id,
                duration = current_time,      -- Current playback position
                total_duration = total_duration,  -- Total length
                status = "playing"
            }

            send_update(data)
        end
    end

    -- Terminate event when media is closed
    local function on_file_terminated()
        local data = {
            id = video_id,
            duration = mp.get_property_number("duration"),
            status = "terminated"
        }
        send_update(data)
    end

    mp.register_event("file-loaded", on_file_loaded)
    mp.register_event("idle", on_idle)
    mp.register_event("file-terminated", on_file_terminated)
end

debug_log("Media tracker script loaded")
track_progress()
