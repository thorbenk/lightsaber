# Based on the original Adafruit code copyright 2023 Liz Clark for Adafruit Industries

import random
import board
import audiocore
import audiobusio
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import adafruit_lis3dh
import asyncio
from adafruit_ticks import ticks_ms, ticks_add, ticks_less
import colorsys
from audiomp3 import MP3Decoder

# CUSTOMIZE SENSITIVITY HERE: smaller numbers = more sensitive to motion
HIT_THRESHOLD = 120
SWING_THRESHOLD = 130

RED = (255, 0, 0)
YELLOW = (125, 255, 0)
GREEN = (0, 255, 0)
CYAN = (0, 125, 255)
BLUE = (0, 0, 255)
PURPLE = (125, 0, 255)
WHITE = (255, 255, 255)
COLORS = [RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE]
CLASH_EXTRA_WHITE = 32

# enable external power pin
# provides power to the external components
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT

CLASH_SOUNDS = [
    "clash1.wav",
    "clash2.wav",
    "clash3.wav",
    "clash4.wav",
    "clash5.wav",
    "clash6.wav",
    "clash7.wav",
    "clash8.wav",
]

SWING_SOUNDS = [
    "swing1.wav",
    "swing2.wav",
    "swing3.wav",
    "swing4.wav",
    "swing5.wav",
    "swing6.wav",
    "swing7.wav",
    "swing8.wav",
]

sound_lenghts = {
    "0_on.wav": 1.72,
    "1_idle.wav": 2.02,
    "2_off.wav": 1.27,
    "clash1.wav": 1.00,
    "clash2.wav": 1.00,
    "clash3.wav": 1.00,
    "clash4.wav": 0.67,
    "clash5.wav": 0.67,
    "clash6.wav": 0.85,
    "clash7.wav": 0.67,
    "clash8.wav": 0.88,
    "swing1.wav": 0.70,
    "swing2.wav": 0.70,
    "swing3.wav": 0.65,
    "swing4.wav": 0.70,
    "swing5.wav": 0.67,
    "swing6.wav": 1.15,
    "swing7.wav": 1.00,
    "swing8.wav": 0.70,
    "z_color.wav": 6.00,
    "zz_march.wav": 9.65,
    "zz_clonewars.wav": 18.56,
}

mp3_files = ["sounds/zz_duel_begins.mp3"]

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mp3 = open(mp3_files[0], 'rb')
mp3_decoder = MP3Decoder(mp3)

def play_sound(fname, loop=False):
    try:
        fname="sounds/" + fname
        wave_file = open(fname, "rb")
        print(fname)
        wave = audiocore.WaveFile(wave_file)
        audio.stop()
        audio.play(wave, loop=loop)
    except Exception as e:  # noqa: E722
        print(e)
        return

def play_sound_mp3(fname, loop=False):
    try:
        fname="sounds/" + fname
        mp3_decoder.file = open(fname, "rb")
        print(fname)
        audio.stop()
        audio.play(mp3_decoder, loop=loop)
    except Exception as e:  # noqa: E722
        print(e)
        return


# button 1
b1pin = DigitalInOut(board.D13)
b1pin.direction = Direction.INPUT
b1pin.pull = Pull.UP
switch = Button(b1pin, long_duration_ms=1000)
switch_state = False

# button 2
b2pin = DigitalInOut(board.D12)
b2pin.direction = Direction.INPUT
b2pin.pull = Pull.UP
switch2 = Button(b2pin, long_duration_ms=1000)
brightness = True

# external neopixels
NUM_PIXELS = 38
BLADE_LENGTH = NUM_PIXELS // 2
pixels = neopixel.NeoPixel(
    board.EXTERNAL_NEOPIXELS, NUM_PIXELS, auto_write=False, pixel_order="GRBW"
)
pixels.brightness = 0.7

# onboard LIS3DH
i2c = board.I2C()
int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
# Accelerometer Range (can be 2_G, 4_G, 8_G, 16_G)
lis3dh.range = adafruit_lis3dh.RANGE_2_G
lis3dh.set_tap(1, HIT_THRESHOLD)

M_OFF = 0
M_POWERING_OFF = 1
M_POWERING_ON = 2
M_IDLE = 3
M_HIT = 4
M_SWING = 5
M_CONFIGURE = 6
M_HERO = 7


class State:
    def __init__(self):
        self.mode = M_OFF
        self.blade_length = 0
        self.color_idx = 0
        self.tick = ticks_ms()
        self.first_hue = 0


state = State()
tasks: list[asyncio.Task] = []


async def animate_to_position(target_position):
    assert target_position >= 0 and target_position <= BLADE_LENGTH

    if state.mode == M_POWERING_ON:
        external_power.value = 1

    step = 1 if target_position > state.blade_length else -1

    if step > 0:
        play_sound("0_on.wav", False)
    else:
        play_sound("2_off.wav", False)

    assert state.blade_length >= 0 and state.blade_length <= BLADE_LENGTH

    while state.blade_length != target_position:
        state.blade_length = max(0, (min(BLADE_LENGTH, state.blade_length + step)))
        await asyncio.sleep(0.025)

    state.mode = M_OFF if target_position == 0 else M_IDLE
    # if target_position == conf.blade_max_len:
    #    state.sparkle = True

    if state.mode == M_IDLE:
        play_sound("1_idle.wav", loop=True)
    else:
        audio.stop()
        external_power.value = 0


async def light_and_sounds():
    while True:
        hues = state.color_idx >= len(COLORS)
        color = COLORS[state.color_idx] if not hues else WHITE
        if state.mode == M_IDLE or state.mode == M_HERO:
            if not hues:
                pixels.fill(color)
                pixels.show()
            else:
                if not ticks_less(ticks_ms(), state.tick):
                    c = colorsys.hsv_to_rgb(state.first_hue / 255.0, 1.0, 1.0)
                    pixels.fill((int(255 * c[0]), int(255 * c[1]), int(255 * c[2])))
                    state.tick = ticks_add(ticks_ms(), 50)
                    state.first_hue = (state.first_hue + 1) % 255
                    pixels.show()
        elif state.mode == M_POWERING_ON or state.mode == M_POWERING_OFF:
            pixels.fill((0, 0, 0))
            for i in range(0, state.blade_length):
                pixels[i] = color
                pixels[NUM_PIXELS - 1 - i] = color
            pixels.show()
        elif state.mode == M_HIT or state.mode == M_SWING:
            pixels.fill(color+ (CLASH_EXTRA_WHITE,))
            pixels.show()
        elif state.mode == M_CONFIGURE:
            pixels.fill(color)
            pixels.show()
        else:
            pass
        await asyncio.sleep(0.01)


async def reset_to_idle(wait):
    await asyncio.sleep(wait)
    state.mode = M_IDLE
    play_sound("1_idle.wav", loop=True)


async def handle_events():
    while True:
        switch.update()
        switch2.update()

        if state.mode == M_IDLE:
            x, y, z = lis3dh.acceleration
            accel_total = x * x + z * z
            if lis3dh.tapped:
                state.mode = M_HIT
                print("hit")
                idx = random.randint(0, len(CLASH_SOUNDS)) - 1
                snd = CLASH_SOUNDS[idx]
                play_sound(snd)
                tasks.append(asyncio.create_task(reset_to_idle(sound_lenghts[snd])))
            elif accel_total >= SWING_THRESHOLD:
                state.mode = M_SWING
                print("swing")
                idx = random.randint(0, len(SWING_SOUNDS)) - 1
                snd = SWING_SOUNDS[idx]
                play_sound(snd)
                tasks.append(asyncio.create_task(reset_to_idle(sound_lenghts[snd])))

        if switch.short_count == 1:
            if state.mode != M_CONFIGURE:
                while tasks:
                    tasks.pop().cancel()
                state.mode = (
                    M_POWERING_ON
                    if state.mode in [M_OFF, M_POWERING_OFF]
                    else M_POWERING_OFF
                )
                tasks.append(
                    asyncio.create_task(
                        animate_to_position(
                            0 if state.mode == M_POWERING_OFF else BLADE_LENGTH
                        )
                    )
                )
            else:
                state.color_idx = (state.color_idx + 1) % (len(COLORS) + 1)
        if switch.long_press:
            print("configure")
            if state.mode == M_CONFIGURE:
                tasks.append(asyncio.create_task(reset_to_idle(0.0)))
            else:
                play_sound("z_color.wav", loop=True)
                state.mode = M_CONFIGURE

        if switch2.short_count == 1:
            audio.stop()
            state.mode = M_HERO
            if state.color_idx == 0:
                play_sound("zz_march.wav")
                tasks.append(asyncio.create_task(reset_to_idle(9.75)))
            if state.color_idx == 1:
                play_sound_mp3("zz_duel_begins.mp3")
                tasks.append(asyncio.create_task(reset_to_idle(14.4)))
            else:
                play_sound("zz_clonewars.wav")
                tasks.append(asyncio.create_task(reset_to_idle(18.56)))

        await asyncio.sleep(0.0)


async def main():
    main_tasks = [
        asyncio.create_task(light_and_sounds()),
        asyncio.create_task(handle_events()),
    ]

    await asyncio.gather(*main_tasks)


if __name__ == "__main__":
    asyncio.run(main())
