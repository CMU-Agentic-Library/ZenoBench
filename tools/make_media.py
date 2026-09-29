"""README media from a rollout: a compressed MP4 and a small sped-up GIF.

    python tools/make_media.py runs/collect_fruits/run.mp4 media/tasks/collect_fruits
    # -> media/tasks/collect_fruits.mp4 (H.264, 854 px) + .gif (360 px, 8x speed)
    #    + result.json copied next to them when the run has one

Needs ffmpeg on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_stem")
    ap.add_argument("--speed", type=float, default=8.0, help="GIF speed-up")
    ap.add_argument("--gif-width", type=int, default=360)
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--mp4-speed", type=float, default=1.0, help="MP4 speed-up (long task videos)")
    args = ap.parse_args()
    src = Path(args.video)
    out = Path(args.out_stem)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", f"setpts=PTS/{args.mp4_speed},scale=854:-2", "-r", "30",
                    "-c:v", "libx264", "-crf", "28", "-preset", "slow", "-pix_fmt", "yuv420p",
                    str(out.with_suffix(".mp4"))], check=True)
    pal = out.with_suffix(".palette.png")
    vf = f"setpts=PTS/{args.speed},fps={args.fps},scale={args.gif_width}:-1:flags=lanczos"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-vf", vf + ",palettegen=max_colors=96",
                    str(pal)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-i", str(pal), "-lavfi",
                    vf + " [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4", str(out.with_suffix(".gif"))],
                   check=True)
    pal.unlink()
    res = src.parent / "result.json"
    if res.exists():
        shutil.copy(res, out.parent / (out.name + ".result.json"))
    for suf in (".mp4", ".gif"):
        p = out.with_suffix(suf)
        print(p, f"{p.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
