# Mosaic Image Generator

This repository converts a photograph into an artistic mosaic. It derives from upstream work credited to [JavierCoronel/mosaic_generator](https://github.com/JavierCoronel/mosaic_generator) and, in turn, [yobeatz/mosaic](https://github.com/yobeatz/mosaic).

Raster inputs and outputs (`*.jpg`, `*.png`, etc.) are **gitignored** by default—use your own `image_path` in YAML or Hydra overrides.

## How it works

1. Load and preprocess an image.
2. Extract edges (`sobel`, `diblasi`, or `HED`).
3. Estimate guide chains from edge-distance contours.
4. Place polygon tiles along guides and iterate to fill gaps (defaults to **`distance_stripes`** gap guidelines; set `gap_guideline_method: skeleton` only to opt into medial-axis gap paths).
5. Colour tiles (`original`, `kmeans`, or `color_collection`).
6. Render and save a PNG with Matplotlib (`output_dpi` in config drives resolution).

## Requirements

- **Python**: 3.12
- **Dependencies**: `pip install -r requirements.txt` (includes `hydra-core` and `hydra-joblib-launcher` for optional parallel Hydra runs).
- **HED** (optional): if `edge_extraction_method: HED`, place `deploy.prototxt` and `hed_pretrained_bsds.caffemodel` beside `edges/hed.py` (see comments in [`edges/hed.py`](edges/hed.py)). Until then use `sobel` or `diblasi`.

## Installation

```bash
git clone https://github.com/joepindar/mosaic_generator.git
cd mosaic_generator
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3.12 -m pip install -r requirements.txt
```

Use matching `pip`/`python`: `python3.12 -m pip install -r requirements.txt`.

## Usage

Hydra resolves configs from **`data/configs/`**. The working directory during a run is the Hydra output directory; the mosaic PNG is written there with the **same basename** as `image_path` (see [`mosaic_generator.py`](mosaic/mosaic_generator.py) `save_mosaic`).

In **`default.yaml`**, **`output_folder`** is **`outputs`** (single and multirun). Each run lands under:

`outputs/<YYYY.MM.DD-HH-MM-SS>/<input_basename>.png`

Multirun sweep directories use the same base, e.g. `outputs/multirun_*_<timestamp>/…`. Override `output_folder` in YAML or on the CLI if you want a different location.

Override paths on the CLI, for example:

```bash
python3.12 main.py --config-name=default image_path=my_photo.jpg edge_extraction_method=sobel
```

### Config presets (tracked YAML)

| Config | Purpose |
|--------|---------|
| `default.yaml` | Single run; comments show all main keys (`mosaic_*` sizes are in **centimetres** for figure layout). |
| `default_parallel.yaml` | Multirun sweeps (requires `hydra-joblib-launcher` + `--multirun` / `-m`). |
| `match_input_size.yaml` | Sets `match_output_to_input_pixels: true` so output PNG dimensions match input pixels at `output_dpi` (default `96`). |
| `polygonal_tiles.yaml` | Roman-mosaic look: mitred negative buffer, two-stage convex repair, stronger simplify, finer tile outline. Compose with the others (e.g. `defaults: [match_input_size, polygonal_tiles]`). |
| `multirun_hed_polygonal_distance_stripes_coffee_cup.yaml` | Multirun **HED** + **`polygonal_tiles`** + **`distance_stripes`** (`tile_size`: 6…24 step 3) on `coffee_cup.png`; input-sized PNG output. Run with `-m` and Joblib launcher. |

### Multirun (parameter sweep)

```bash
python3.12 main.py --config-name=default_parallel --multirun
```

HED + Roman-style polygons + `distance_stripes` on `coffee_cup.png` (edit `hydra/sweeper/params/tile_size` in the YAML to change the sweep):

```bash
python3.12 main.py -m --config-name=multirun_hed_polygonal_distance_stripes_coffee_cup
```

After the sweep finishes, **`COMPARISON.md`** is written **automatically** in that sweep directory (Hydra `on_multirun_end` callback; see `hydra.callbacks` in the YAML). You can still refresh it manually:

```bash
python3.12 scripts/write_multirun_comparison.py outputs/multirun_hed_polygonal_coffee_cup_<timestamp>
```

Open `outputs/.../COMPARISON.md` next to the `tile_*` job folders (see `utils/multirun_comparison.py` and `scripts/write_multirun_comparison.py` for options).

`snap-to-input` runs are heavier for small `tile_size`; expect very long runtime for `tile_size=3`.

**Parallel workers (Joblib):** The sweep preset [`multirun_hed_polygonal_distance_stripes_coffee_cup.yaml`](data/configs/multirun_hed_polygonal_distance_stripes_coffee_cup.yaml) sets **`hydra.launcher.n_jobs: -1`** so all logical CPUs are used. Only add a CLI override such as `hydra.launcher.n_jobs=4` when you want to throttle load.

### Match input pixel dimensions

Use `match_input_size` (or `match_output_to_input_pixels: true` in your YAML). Figure width/height in cm are computed from image width × height and `output_dpi`; **`savefig` uses the same DPI** (`output_dpi` in [`config_resolver`](utils/config_resolver.py) / [`save_mosaic`](mosaic/mosaic_generator.py)).

## Headless / CI

Without a display backend, Matplotlib may need:

```bash
export MPLBACKEND=Agg
export MPLCONFIGDIR=/path/to/writable/dir
```

## Configuration reference

Structured parameter descriptions: [`data/configs/README.md`](data/configs/README.md). Supplement with:

- **`match_output_to_input_pixels`** — bool; derive mosaic figure size so pixel size matches image at `output_dpi`.
- **`output_dpi`** — int (default `96`); PNG resolution multiplier with Matplotlib figure size.

## Contributions

Issues and pull requests are welcome.

## License

This project is licensed under the [MIT License](LICENSE).
