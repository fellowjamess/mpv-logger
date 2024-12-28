# Python-Lua MPV Media History Project

This project is designed to log and display media history from MPV using a combination of Python and Lua scripts. It leverages MPV’s ability to run Lua scripts alongside Python for enhanced media information tracking, such as file name, format, device details, and playback progress.

## Features
- Logs media information (e.g., duration, format, video/audio codec) from MPV playback.
- Displays the progress of the media being played.
- Outputs a clear history view with information such as watched time and device/IP details.

## Requirements
- Python 3.x
- MPV media player
- Lua

## Installation

### Step 1: Install Dependencies
Ensure you have the necessary dependencies:

1. Install MPV:

   On Arch, use the following:

   ```bash
   sudo pacman -S mpv
