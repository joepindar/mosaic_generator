#!/usr/bin/env python3
"""Write COMPARISON.md inside a Hydra multirun sweep directory.

Expects subdirectories named ``tile_<N>/`` (Hydra ``subdir: tile_${tile_size}`` pattern). The same
logic runs automatically via ``hydra.callbacks.multirun_comparison`` for configs that define it.

Example:

    python scripts/write_multirun_comparison.py outputs/multirun_hed_polygonal_coffee_cup_2026.05.05-07-13-41
    python scripts/write_multirun_comparison.py outputs/some_sweep -i result.png --cols 4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root import (script run as python scripts/write_multirun_comparison.py …)
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils.multirun_comparison import write_multirun_comparison  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Write COMPARISON.md for a Hydra tile_* multirun folder.")
    ap.add_argument(
        "sweep_dir",
        type=Path,
        help="Hydra multirun sweep directory (contains tile_<N>/ subfolders)",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Markdown output path (default: <sweep_dir>/COMPARISON.md)",
    )
    ap.add_argument(
        "-i",
        "--image",
        default=None,
        help="Image filename inside each tile_* folder (default: first .png found)",
    )
    ap.add_argument(
        "--cols",
        type=int,
        default=3,
        help="Number of images per table row (default: 3)",
    )
    ap.add_argument(
        "--title",
        default="Multirun comparison",
        help="Document title (default: Multirun comparison)",
    )
    args = ap.parse_args()

    try:
        out = write_multirun_comparison(
            args.sweep_dir,
            cols=args.cols,
            image_basename=args.image,
            title=args.title,
            output_path=args.output,
        )
        print(f"Wrote {out}")
    except (OSError, ValueError, FileNotFoundError) as e:
        raise SystemExit(str(e)) from e


if __name__ == "__main__":
    main()
