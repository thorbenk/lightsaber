#!/usr/bin/env -S uv run python

import asyncio
import sys
import termios
import tty
import random
import select
from dataclasses import dataclass
import just_playback
from enum import Enum
from colorama import Fore

playback = just_playback.Playback()


@dataclass(frozen=True)
class Conf:
    bar_width = 50


class Mode(Enum):
    OFF = 0
    POWERING_ON = 1
    POWERING_OFF = 2
    ON = 3
    CONFIGURE = 4


@dataclass
class State:
    bar_position = 0
    sparkle = False
    mode: Mode = Mode.OFF
    animate_direction = 1
    sparkle_char = "*"
    color: int = 0


conf = Conf()
state = State()

tasks: list[asyncio.Task] = []

clash_sounds = [
    "sounds/clash1.wav",
    "sounds/clash2.wav",
    "sounds/clash3.wav",
    "sounds/clash4.wav",
    "sounds/clash5.wav",
    "sounds/clash6.wav",
    "sounds/clash7.wav",
    "sounds/clash8.wav",
]

swing_sounds = [
    "sounds/swing1.wav",
    "sounds/swing2.wav",
    "sounds/swing3.wav",
    "sounds/swing4.wav",
    "sounds/swing5.wav",
    "sounds/swing6.wav",
    "sounds/swing7.wav",
    "sounds/swing8.wav",
]

colors = [
    Fore.RED,
    Fore.GREEN,
    Fore.YELLOW,
    Fore.WHITE,
    Fore.BLUE,
]


def play_sound(fname: str, loop: bool):
    playback.load_file(fname)
    playback.play()
    playback.loop_at_end(loop)


async def clash():
    playback.stop()
    i = random.randint(0, len(clash_sounds) - 1)
    play_sound(clash_sounds[i], False)


async def swing():
    playback.stop()
    i = random.randint(0, len(swing_sounds) - 1)
    play_sound(swing_sounds[i], False)


async def configure_mode_start_stop():
    if state.mode != Mode.CONFIGURE:
        state.mode = Mode.CONFIGURE
        playback.stop()
        play_sound("sounds/z_color.wav", False)
    else:
        playback.stop()
        state.mode = Mode.ON


async def configure_next():
    state.color = (state.color + 1) % len(colors)


async def handle_keypress():
    """Handle keypress events to reset the progress bar or toggle sparkle."""

    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == "a":
                state.sparkle = False
                while tasks:
                    tasks.pop().cancel()
                state.animate_direction = 0 if state.animate_direction == 1 else 1
                state.mode = (
                    Mode.POWERING_OFF
                    if state.animate_direction == 0
                    else Mode.POWERING_ON
                )
                tasks.append(
                    asyncio.create_task(
                        animate_to_position(
                            0 if state.animate_direction == 0 else conf.bar_width
                        )
                    )
                )
            elif key == "b":
                state.sparkle_char = "o"
                asyncio.create_task(reset_sparkle_char())
            elif key == "c":
                state.sparkle_char = "x"
                asyncio.create_task(reset_sparkle_char())
            elif key == "x":
                asyncio.create_task(clash())
            elif key == "s":
                asyncio.create_task(swing())
            elif key == "t":
                asyncio.create_task(configure_mode_start_stop())
            elif key == "n":
                state.color = (state.color + 1) % len(colors)
        await asyncio.sleep(0.0)  # Yield control back to the event loop


async def reset_sparkle_char():
    """Reset the sparkle character back to '*' after 2 seconds."""
    await asyncio.sleep(2)
    state.sparkle_char = "*"


async def animate_to_position(target_position):
    """Animate the progress bar to the target position."""

    assert target_position >= 0 and target_position <= conf.bar_width

    step = 1 if target_position > state.bar_position else -1

    if step > 0:
        play_sound("sounds/0_on.wav", False)
    else:
        play_sound("sounds/2_off.wav", False)

    assert state.bar_position >= 0 and state.bar_position <= conf.bar_width

    while state.bar_position != target_position:
        state.bar_position = max(0, (min(conf.bar_width, state.bar_position + step)))
        await asyncio.sleep(0.025)

    state.mode = Mode.OFF if target_position == 0 else Mode.ON
    if target_position == conf.bar_width:
        state.sparkle = True


async def progress_bar():
    while True:
        assert state.bar_position >= 0 and state.bar_position <= conf.bar_width, (
            f"bar_position={state.bar_position}, bar_width={conf.bar_width}"
        )
        bar = ["#"] * state.bar_position + [" "] * (conf.bar_width - state.bar_position)

        if state.sparkle:
            for i in range(state.bar_position):
                if random.random() < 0.1:  # 10% chance to sparkle
                    bar[i] = state.sparkle_char

        bar_str = "[" + "".join(bar) + "]"
        assert len(bar_str) == conf.bar_width + 2
        sys.stdout.write("\r" + colors[state.color] + bar_str + Fore.RESET)
        sys.stdout.flush()

        if not playback.playing and state.mode == Mode.ON:
            play_sound("sounds/1_idle.wav", True)
        elif playback.playing and state.bar_position == 0:
            playback.stop()

        await asyncio.sleep(0.05)


async def main():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        # Disable echo
        new_settings = termios.tcgetattr(fd)
        new_settings[3] = new_settings[3] & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)

        # Start the initial animation to 100%
        tasks.append(asyncio.create_task(animate_to_position(conf.bar_width)))

        main_tasks = [
            asyncio.create_task(progress_bar()),
            asyncio.create_task(handle_keypress()),
        ]

        await asyncio.gather(*main_tasks)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
