# Lightsaber Build

Based on https://learn.adafruit.com/lightsaber-rp2040/overview

- Install `adafruit-circuitpython-adafruit_feather_rp2040_prop_maker-en_US-9.2.4.uf2`
- Run `uv run circup install adafruit_debouncer neopixel adafruit_lis3dh adafruit_ticks colorsys audiomp3`
- Connect via `screen /dev/ttyACM0 115200`

Download via yt-dlp

```
ffmpeg -i duel_begins_soundtrack.mp4 -b:a 128K -vn duel_begins.mp3

# Use the following to make a WAV file compatible with CircuitPython:
# (see https://github.com/adafruit/Adafruit_CircuitPython_CircuitPlayground/issues/97)
ffmpeg -i clonewars.mp3 -f wav -bitexact -acodec pcm_s16le -ac 1 -ar 22050 sounds/zz_clonewars.wav
```
