import wave
from pathlib import Path

paths = sorted(Path(".").glob("sounds/*.wav"))

print("sound_lenghts = {")
for path in paths:
    with wave.open(str(path), "r") as f:
        frames = f.getnframes()
        rate = f.getframerate()
        assert f.getnchannels() == 1
        duration = frames / float(rate)
        assert rate == 22050
        print(f'  "{path.name}": {duration:.2f},')
print("}")
