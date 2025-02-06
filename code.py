# Based on the original Adafruit code copyright 2023 Liz Clark for Adafruit Industries

import time
import random
import board
import audiocore
import audiobusio
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
import neopixel
import adafruit_lis3dh
import asyncio

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
SABER_COLOR = 3
CLASH_COLOR = WHITE

# enable external power pin
# provides power to the external components
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = Direction.OUTPUT
external_power.value = True

CLASH_SOUNDS = [
    "sounds/clash1.wav",
    "sounds/clash2.wav",
    "sounds/clash3.wav",
    "sounds/clash4.wav",
    "sounds/clash5.wav",
    "sounds/clash6.wav",
    "sounds/clash7.wav",
    "sounds/clash8.wav",
]

SWING_SOUNDS = [
    "sounds/swing1.wav",
    "sounds/swing2.wav",
    "sounds/swing3.wav",
    "sounds/swing4.wav",
    "sounds/swing5.wav",
    "sounds/swing6.wav",
    "sounds/swing7.wav",
    "sounds/swing8.wav",
]

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)


def play_sound(fname, loop=False):
    try:
        wave_file = open(fname, "rb")
        wave = audiocore.WaveFile(wave_file)
        audio.play(wave, loop=loop)
    except:  # noqa: E722
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

class State:
    def __init__(self):
        self.mode = M_OFF
        self.blade_length = 0

state = State()
tasks: list[asyncio.Task] = []

"""
while True:
    switch.update()
    switch2.update()

    if switch2.short_count == 1:
        brightness = not brightness
        pixels.brightness = 0.7 if brightness else 0.5
        play_wav("sounds/zz_march.wav", loop=False)

    # startup
    elif mode == 0:
        play_wav("sounds/0_on.wav", loop=False)
        for i in range(num_pixels // 2):
            pixels[i] = COLORS[SABER_COLOR]
            pixels[num_pixels - 1 - i] = COLORS[SABER_COLOR]
            pixels.show()
        time.sleep(1)
        play_wav("sounds/1_idle.wav", loop=True)
        mode = 1
    # default
    elif mode == 1:
        x, y, z = lis3dh.acceleration
        accel_total = x * x + z * z
        if lis3dh.tapped:
            mode = "hit"
        elif accel_total >= SWING_THRESHOLD:
            mode = "swing"
        if switch.short_count == 1:
            mode = 3
        if switch.long_press:
            audio.stop()
            play_wav("sounds/z_color.wav", loop=True)
            mode = 5
    # clash or move
    elif mode == "hit":
        audio.stop()
        play_wav(CLASH_SOUNDS[random.randint(0, len(CLASH_SOUNDS)) - 1])
        while audio.playing:
            pixels.fill(WHITE)
            pixels.show()
        pixels.fill(COLORS[SABER_COLOR])
        pixels.show()
        play_wav("sounds/1_idle.wav", loop=True)
        mode = 1
    elif mode == "swing":
        audio.stop()
        play_wav(SWING_SOUNDS[random.randint(0, len(SWING_SOUNDS)) - 1])
        while audio.playing:
            pixels.fill(COLORS[SABER_COLOR])
            pixels.show()
        pixels.fill(COLORS[SABER_COLOR])
        pixels.show()
        play_wav("sounds/1_idle.wav", loop=True)
        mode = 1
    # turn off
    elif mode == 3:
        audio.stop()
        play_wav("sounds/2_off.wav")
        for i in range(num_pixels // 2):
            pixels[num_pixels // 2 - 1 - i] = (0, 0, 0)
            pixels[num_pixels // 2 - 1 + i] = (0, 0, 0)
            pixels.show()
        time.sleep(1)
        external_power.value = False
        mode = 4
    # go to startup from off
    elif mode == 4:
        if switch.short_count == 1:
            external_power.value = True
            mode = 0
    # change color
    elif mode == 5:
        if switch.short_count == 1:
            SABER_COLOR = (SABER_COLOR + 1) % 6
            c = COLORS[SABER_COLOR]
            pixels.fill(COLORS[SABER_COLOR])
            pixels.show()
        if switch.long_press:
            play_wav("sounds/1_idle.wav", loop=True)
            pixels.fill(COLORS[SABER_COLOR])
            pixels.show()
            mode = 1
"""

async def animate_to_position(target_position):
    assert target_position >= 0 and target_position <= BLADE_LENGTH

    step = 1 if target_position > state.blade_length else -1

    if step > 0:
        play_sound("sounds/0_on.wav", False)
    else:
        play_sound("sounds/2_off.wav", False)

    assert state.blade_length >= 0 and state.blade_length <= BLADE_LENGTH

    while state.blade_length != target_position:
        state.blade_length = max(
            0, (min(BLADE_LENGTH, state.blade_length + step))
        )
        print(state.blade_length)
        await asyncio.sleep(0.025)

    state.mode = M_OFF if target_position == 0 else M_IDLE
    #if target_position == conf.blade_max_len:
    #    state.sparkle = True

    if state.mode == M_IDLE:
        play_sound("sounds/1_idle.wav", loop=True)
    else:
        audio.stop()


async def light_and_sounds():
    while True:
        color = COLORS[SABER_COLOR]
        if state.mode == M_IDLE:
            external_power.value = True
            pixels.fill(color)
            pixels.show()
        elif state.mode == M_POWERING_ON or state.mode == M_POWERING_OFF:
            external_power.value = True
            pixels.fill((0,0,0))
            for i in range(0, state.blade_length):
                pixels[i] = color
                pixels[NUM_PIXELS-1-i] = color
            pixels.show()
        elif state.mode == M_HIT or state.mode == M_SWING:
            external_power.value = True
            pixels.fill(CLASH_COLOR)
            pixels.show()
        else:
            external_power.value = False
        await asyncio.sleep(0.01)

async def reset_to_idle(wait):
    await asyncio.sleep(wait)
    state.mode = M_IDLE
    play_sound("sounds/1_idle.wav", loop=True)

async def handle_events():
    while True:
        switch.update()
        switch2.update()

        if state.mode not in [M_POWERING_ON, M_POWERING_OFF, M_OFF, M_CONFIGURE]:
            x, y, z = lis3dh.acceleration
            accel_total = x * x + z * z
            if lis3dh.tapped:
                state.mode = M_HIT
                # print("hit")
                play_sound(CLASH_SOUNDS[random.randint(0, len(CLASH_SOUNDS)) - 1])
                tasks.append(asyncio.create_task(reset_to_idle(0.5)))
            elif accel_total >= SWING_THRESHOLD:
                state.mode = M_SWING
                # print("swing")
                play_sound(SWING_SOUNDS[random.randint(0, len(SWING_SOUNDS)) - 1])
                tasks.append(asyncio.create_task(reset_to_idle(0.5)))

        if switch.short_count == 1:
            while tasks:
                tasks.pop().cancel()
            state.mode = M_POWERING_ON if state.mode in [M_OFF, M_POWERING_OFF] else M_POWERING_OFF
            tasks.append(
                asyncio.create_task(
                    animate_to_position(
                        0 if state.mode == M_POWERING_OFF else BLADE_LENGTH
                    )
                )
            )
        if switch.long_press:
            audio.stop()
            play_sound("sounds/z_color.wav", loop=True)
            state.mode = M_CONFIGURE

        await asyncio.sleep(0.0)


async def main():
    main_tasks = [
        asyncio.create_task(light_and_sounds()),
        asyncio.create_task(handle_events()),
    ]

    await asyncio.gather(*main_tasks)

if __name__ == "__main__":
    print("test")
    asyncio.run(main())
