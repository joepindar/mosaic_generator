# Mosaic Image Generator

This repository converts a photograph into an artistic mosaic. It derives from upstream work credited to **Javier Coronel** (`JavierCoronel/mosaic_generator`) and, in turn, [yobeatz/mosaic](https://github.com/yobeatz/mosaic).

Example before/after images are referenced in upstream docs (`data/donkey_original.jpg` / `data/donkey_mosaic.jpg`). Those binaries are usually **not** committed here because common image formats are listed in `.gitignore`; supply your own `image_path` in the YAML or via Hydra overrides.

## How it works

1. Load and preprocess an image.
2. Extract edges (`sobel`, `diblasi`, or `HED`).
3. Estimate guide chains from edge-distance contours.
4. Place polygon tiles along guides and iterate to fill gaps.
5. Colour tiles (`original`, `kmeans`, or `color_collection`).
6. Render and save a PNG with Matplotlib (`output_dpi` in config drives resolution).

## Requirements

- **Python**: 3.10+ recommended (development also uses 3.12).
- **Dependencies**: `pip install -r requirements.txt` (includes `hydra-core` and `hydra-joblib-launcher` for optional parallel Hydra runs).
- **HED** (optional): if `edge_extraction_method: HED`, place `deploy.prototxt` and `hed_pretrained_bsds.caffemodel` beside `edges/hed.py` (see comments in [`edges/hed.py`](edges/hed.py)). Until then use `sobel` or `diblasi`.

## Installation

```bash
git clone https://github.com/joepindar/mosaic_generator.git
cd mosaic_generator
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Use matching `pip`/`python`: `python3 -m pip install -r requirements.txt`

## Usage

Hydra resolves configs from **`data/configs/`**. The working directory during a run is the Hydra output directory; the mosaic PNG is written there with the **same basename** as `image_path` (see [`mosaic_generator.py`](mosaic/mosaic_generator.py) `save_mosaic`).

In **`default.yaml`**, `output_folder` is `data/` and each run lands under:

`data/<YYYY.MM.DD-HH-MM-SS>/<input_basename>.png`

Override paths on the CLI, for example:

```bash
python3 main.py --config-name=default image_path=my_photo.jpg edge_extraction_method=sobel
```

### Config presets (tracked YAML)

| Config | Purpose |
|--------|---------|
| `default.yaml` | Single run; comments show all main keys (`mosaic_*` sizes are in **centimetres** for figure layout). |
| `default_parallel.yaml` | Multirun sweeps (requires `hydra-joblib-launcher` + `--multirun` / `-m`). |
| `match_input_size.yaml` | Sets `match_output_to_input_pixels: true` so output PNG dimensions match input pixels at `output_dpi` (default `96`). |
| `parallel_tile_sweep_match_input.yaml` | Multirun with `tile_size: 3,6,…,18` plus input-sized output (`match_input_size` defaults). |
| `smoke_test.yaml` | Overrides for a quick Sobel/original smoke run (expects a local sample image — see Smoke test). |

### Multirun (parameter sweep)

```bash
python3 main.py --config-name=default_parallel --multirun
```

For the tile-size sweep with input-sized output:

```bash
python3 main.py -m --config-name=parallel_tile_sweep_match_input
```

`snap-to-input` runs are heavier for small `tile_size`; expect very long runtime for `tile_size=3`.

### Match input pixel dimensions

Use `match_input_size` (or `match_output_to_input_pixels: true` in your YAML). Figure width/height in cm are computed from image width × height and `output_dpi`; **`savefig` uses the same DPI** (`output_dpi` in [`config_resolver`](utils/config_resolver.py) / [`save_mosaic`](mosaic/mosaic_generator.py)).

## Headless / CI

Without a display backend, Matplotlib may need:

```bash
export MPLBACKEND=Agg
export MPLCONFIGDIR=/path/to/writable/dir
```

`scripts/smoke_test.py` sets `MPLBACKEND` and `.mplconfig` under the repo when run.

## Smoke test

[`scripts/smoke_test.py`](scripts/smoke_test.py) runs Hydra with `data/configs/smoke_test.yaml` (writes under `outputs/`).

**Sample image**: by default this looks for `coffee_cup.png` in the repo root. Raster images such as `.png` are **gitignored**, so clones need to add their own file or force-add one for tests.

```bash
python3 scripts/smoke_test.py
python3 scripts/smoke_test.py --image my_picture.png --config-name=smoke_test
```

Pass checks by finding the newest matching file under **`outputs/`** (including nested multirun dirs).

## Configuration reference

Structured parameter descriptions: [`data/configs/README.md`](data/configs/README.md). Supplement with:

- **`match_output_to_input_pixels`** — bool; derive mosaic figure size so pixel size matches image at `output_dpi`.
- **`output_dpi`** — int (default `96`); PNG resolution multiplier with Matplotlib figure size.

## Contributions

Issues and pull requests are welcome.

## License

This project is licensed under the [MIT License](LICENSE).
