# Lightsaber Build

Based on https://learn.adafruit.com/lightsaber-rp2040/overview

I have re-done the CAD based on the original design, but with some modifications:

- Fits arcylic blade with 3 cm diameter (instead of 1 inch)
- Uses a 18650 battery with battery holder that is screwed onto a 3D printed insert
- Houses a 4 cm diameter speaker in the pommel

The CAD files can be found [in this onshapce document](https://cad.onshape.com/documents/32c2602e3ec2143ee914f82c/w/424b6ddb0cde132faabc46b4/e/2112e8064fa2641e1ce7c5a6?renderMode=0&uiState=67d6a57c4432c4612150b57f)

## Bill of materials

I've changed some aspects compared to the original design, in particular:

- [Speaker](https://www.amazon.de/dp/B00NQ0LHNA): 4 Ohm, 3W round speaker with 40 mm diameter
- [Momentary Push buttons](https://www.amazon.de/dp/B0BK3829XL): 16 mm diameter
- [On/Off button](https://www.amazon.de/dp/B0C3BYF7SM): 16 mm diameter (better: normally open, only closed when pushed down)
- [Acrylic tube](https://www.amazon.de/dp/B08FP8P12B): 30/26 mm

## Setup

- Install `adafruit-circuitpython-adafruit_feather_rp2040_prop_maker-en_US-9.2.4.uf2`
- Run `uv run circup install adafruit_debouncer neopixel adafruit_lis3dh adafruit_ticks colorsys audiomp3`
- Connect via `screen /dev/ttyACM0 115200`

## More notes

Videos can be downloaded via `yt-dlp`.
To extract the audio track, use 

```bash
ffmpeg -i duel_begins_soundtrack.mp4 -b:a 128K -vn duel_begins.mp3
```

To create WAV files that are compatible with CircuitPython
(see https://github.com/adafruit/Adafruit_CircuitPython_CircuitPlayground/issues/97)

```bash
ffmpeg -i clonewars.mp3 -f wav -bitexact -acodec pcm_s16le -ac 1 -ar 22050 sounds/zz_clonewars.wav
```
