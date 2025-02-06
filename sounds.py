import wave
from pathlib import Path

paths = sorted(Path(".").glob("sounds/*.wav"))

print("sound_lenghts = {")
for path in paths:
    with wave.open(str(path), "r") as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        print(f'  "{path.name}": {duration:.2f},')
print("}")
