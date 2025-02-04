#!/usr/bin/env -S uv run python

import asyncio
import sys
import termios
import tty
import random
import select
from dataclasses import dataclass


@dataclass(frozen=True)
class Conf:
    bar_width = 50


@dataclass
class State:
    bar_position = 0
    sparkle = False
    animation_active = True
    animate_direction = 1
    sparkle_char = "*"


conf = Conf()
state = State()

tasks: list[asyncio.Task] = []


async def handle_keypress():
    """Handle keypress events to reset the progress bar or toggle sparkle."""

    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == "a":
                state.animation_active = True
                state.sparkle = False
                while tasks:
                    tasks.pop().cancel()
                state.animate_direction = 0 if state.animate_direction == 1 else 1
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
        await asyncio.sleep(0.0)  # Yield control back to the event loop


async def reset_sparkle_char():
    """Reset the sparkle character back to '*' after 2 seconds."""
    await asyncio.sleep(2)
    state.sparkle_char = "*"


async def animate_to_position(target_position):
    """Animate the progress bar to the target position."""

    assert target_position >= 0 and target_position <= conf.bar_width

    step = 1 if target_position > state.bar_position else -1

    assert state.bar_position >= 0 and state.bar_position <= conf.bar_width

    while state.bar_position != target_position:
        state.bar_position = max(0, (min(conf.bar_width, state.bar_position + step)))
        await asyncio.sleep(0.02)

    state.animation_active = False
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
        sys.stdout.write("\r" + bar_str)
        sys.stdout.flush()

        if state.animation_active and state.bar_position < conf.bar_width:
            state.bar_position += 1
            if state.bar_position >= conf.bar_width:
                state.bar_position = conf.bar_width

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
