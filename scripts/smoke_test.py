#!/usr/bin/env python3
"""Minimal end-to-end smoke test for mosaic generation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a smoke test for the mosaic generator.")
    parser.add_argument(
        "--image",
        default="coffee_cup.png",
        help="Path to an input image, relative to repository root.",
    )
    parser.add_argument(
        "--config-name",
        default="smoke_test",
        help="Hydra config name under data/configs (without .yaml).",
    )
    return parser.parse_args()


def latest_output_for(image_name: str, repo_root: Path) -> Path | None:
    outputs = repo_root / "outputs"
    if not outputs.is_dir():
        return None
    candidates = sorted(
        (p for p in outputs.rglob(image_name) if p.is_file()),
        key=lambda path: path.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    input_path = repo_root / args.image

    if not input_path.is_file():
        print(f"ERROR: input image not found: {input_path}", file=sys.stderr)
        return 1

    cmd = [
        sys.executable,
        "main.py",
        f"--config-name={args.config_name}",
        f"image_path={args.image}",
        "edge_extraction_method=sobel",
        "coloring_method=original",
        "interactive_edge_modification=false",
        "save_intermediate_steps=false",
    ]

    env = dict(os.environ)
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(repo_root / ".mplconfig")
    (repo_root / ".mplconfig").mkdir(exist_ok=True)

    print("Running:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=repo_root, check=False, env=env)
    if result.returncode != 0:
        print(f"ERROR: mosaic generation failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode

    output_image = latest_output_for(input_path.name, repo_root)
    if output_image is None:
        print("ERROR: no output image found under outputs/", file=sys.stderr)
        return 1

    if output_image.stat().st_size == 0:
        print(f"ERROR: output image is empty: {output_image}", file=sys.stderr)
        return 1

    print(f"Smoke test passed. Output image: {output_image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
