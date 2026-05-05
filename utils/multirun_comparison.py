"""
Build COMPARISON.md for Hydra multiruns that use tile_<N>/ subdirectories.

Used by ``scripts/write_multirun_comparison.py`` and optional Hydra ``on_multirun_end`` callback.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from omegaconf import DictConfig, OmegaConf

logger = logging.getLogger(__name__)

TILE_SUBDIR_RE = re.compile(r"^tile_(\d+)$")


def discover_tile_dirs(sweep_dir: Path) -> list[tuple[int, Path]]:
    pairs: list[tuple[int, Path]] = []
    for p in sorted(sweep_dir.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith(".") or p.name == "__pycache__":
            continue
        m = TILE_SUBDIR_RE.match(p.name)
        if m:
            pairs.append((int(m.group(1)), p))
    pairs.sort(key=lambda x: x[0])
    return pairs


def detect_image_basename(tile_dirs: list[Path]) -> str:
    for d in tile_dirs:
        pngs = sorted(d.glob("*.png"))
        if pngs:
            return pngs[0].name
        jpgs = sorted(d.glob("*.jpg")) + sorted(d.glob("*.jpeg"))
        if jpgs:
            return jpgs[0].name
    raise ValueError("No .png/.jpg images found inside tile_* folders; pass image_basename")


def md_table_chunk(sizes_rel: list[tuple[int, str]]) -> str:
    if not sizes_rel:
        return ""
    ts = sizes_rel
    header = "|" + "|".join(f" **`tile_size={u[0]}`** " for u in ts) + "|"
    sep = "|" + "|".join(":--:" for _ in ts) + "|"
    imgs = "|" + "|".join(f" ![tile {u[0]}]({u[1]}) " for u in ts) + "|"
    return "\n".join([header, sep, imgs, ""])


def build_markdown(
    sweep_dir: Path,
    tile_entries: list[tuple[int, Path]],
    image_basename: str,
    cols: int,
    title: str,
    *,
    regen_relative_sweep_hint: Path | None = None,
) -> str:
    lines: list[str] = [
        f"# {title}",
        "",
        f"Generated `{datetime.now(tz=UTC).isoformat()}` · sweep directory `{sweep_dir.name}/`",
        "",
        "## Gallery",
        "",
        "Paths below are relative to this file (`COMPARISON.md`) so previews resolve to "
        "`tile_<N>/…` outputs from the multirun.",
        "",
    ]

    rel_pairs: list[tuple[int, str]] = []
    for sz, td in tile_entries:
        rel = td.name + "/" + image_basename.replace("\\", "/")
        img_path = td / image_basename
        if not img_path.is_file():
            raise FileNotFoundError(f"Missing image for tile_size={sz}: {img_path}")
        rel_pairs.append((sz, rel))

    for i in range(0, len(rel_pairs), cols):
        chunk = rel_pairs[i : i + cols]
        lines.append(md_table_chunk(chunk))

    hint = regen_relative_sweep_hint or sweep_dir
    try:
        sweep_arg = hint.relative_to(Path.cwd())
    except ValueError:
        sweep_arg = hint
    regen = sweep_arg.as_posix()

    lines.extend(
        [
            "---",
            "",
            "## Regenerate",
            "",
            "```bash",
            f"python scripts/write_multirun_comparison.py {regen}",
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def write_multirun_comparison(
    sweep_dir: Path,
    *,
    cols: int = 3,
    image_basename: str | None = None,
    title: str = "Multirun comparison",
    output_path: Path | None = None,
) -> Path:
    """Write ``COMPARISON.md`` beneath ``sweep_dir``. Raises if validation fails."""
    sweep_dir = sweep_dir.resolve()
    if not sweep_dir.is_dir():
        raise NotADirectoryError(str(sweep_dir))

    discovered = discover_tile_dirs(sweep_dir)
    if not discovered:
        raise FileNotFoundError(f"No tile_<N> subdirectories under {sweep_dir}")

    dirs_only = [d for _, d in discovered]
    basename = image_basename or detect_image_basename(dirs_only)

    out_path = (output_path or (sweep_dir / "COMPARISON.md")).resolve()
    body = build_markdown(
        sweep_dir,
        discovered,
        basename,
        cols,
        title,
        regen_relative_sweep_hint=sweep_dir,
    )
    out_path.write_text(body, encoding="utf-8")
    return out_path


class MultirunComparisonHydraCallback:
    """Hydra callback: writes COMPARISON.md when a multirun sweep finishes."""

    def __init__(
        self,
        cols: int = 3,
        image_basename: str | None = None,
        title: str | None = None,
    ):
        self.cols = cols
        self.image_basename = image_basename
        self.title = title

    def on_multirun_end(self, config: DictConfig, **kwargs: object) -> None:
        title = (
            self.title
            if self.title is not None
            else "Multirun comparison (Hydra sweep)"
        )
        try:
            OmegaConf.resolve(config)
            sweep_raw = OmegaConf.select(config, "hydra.sweep.dir")
            if sweep_raw is None:
                logger.warning("multirun comparison callback: hydra.sweep.dir missing")
                return
            sweep_dir = Path(str(sweep_raw)).resolve()
            if not sweep_dir.is_dir():
                logger.warning("multirun comparison callback: sweep dir not found: %s", sweep_dir)
                return

            tiles = discover_tile_dirs(sweep_dir)
            if not tiles:
                logger.info(
                    "multirun comparison callback: no tile_<N>/ subdirs under %s; skipping",
                    sweep_dir,
                )
                return

            path = write_multirun_comparison(
                sweep_dir,
                cols=self.cols,
                image_basename=self.image_basename,
                title=title,
            )
            logger.info("multirun comparison callback: wrote %s", path)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "multirun comparison callback failed; sweep output is unaffected"
            )
