"""Rebuild all original Kage Village v2 meshes, foley and asset checksums."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    (base / 'assets' / 'audio').mkdir(parents=True, exist_ok=True)
    runpy.run_path(str(base / 'build_models_v2.py'), run_name='__main__')
    runpy.run_path(str(base / 'build_audio_v2.py'), run_name='__main__')