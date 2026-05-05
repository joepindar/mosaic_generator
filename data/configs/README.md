# Configuration parameters

## Usage
We use YAML configuration files managed by [Hydra](https://hydra.cc/docs/intro/) to define various parameters to generating mosaics. 

To get started, consider using the following templates and adjust them to tailor the mosaic generation process according to your requirements. Save your modified `.yaml` file with a different name, and use it to execute the code as explained in the [usage](../../README.md#usage) section. 

You can run two types of hydra configs:
* [`default.yaml`](./default.yaml) has a list of parameters to run a single execution for mosaic generation.
* [`default_parallel.yaml`](./default_parallel.yaml) has additional hydra configurations to run multiple mosaic generations in parallel. Here you can list multiple values for a single parameter under the `hydra/sweeper/params` part of the `.yaml` file.
* Dedicated sweep YAMLs extend a preset plus multirun: e.g. [`multirun_hed_polygonal_distance_stripes_coffee_cup.yaml`](./multirun_hed_polygonal_distance_stripes_coffee_cup.yaml) (HED + `polygonal_tiles` + `distance_stripes`, `tile_size` sweep on `coffee_cup.png`, input-sized PNG). Run with `-m`; **`COMPARISON.md`** is emitted in the sweep output folder when the run finishes ([`utils/multirun_comparison.py`](../utils/multirun_comparison.py)). Rebuild with [`scripts/write_multirun_comparison.py`](../scripts/write_multirun_comparison.py) if needed. See repo [README](../../README.md#multirun-parameter-sweep).

## Parameters
Here you can find a list of the posible parameters with their explaination and possible values:
#### `image_path` 
- Type: String
- Description: Absolute or relative path to the input image.
- Example: `/path/to/image.jpg`

#### `output_folder`
- Type: String
- Description: Base folder where Hydra writes timestamped **`hydra.run.dir`** (single runs) and **`hydra.sweep.dir`** (multiruns). Defaults to **`outputs`** in [`default.yaml`](./default.yaml); the resolver uses **`outputs`** if the key is missing. Set to another path when you want artefacts elsewhere.
- Example: `outputs`

#### `edge_extraction_method`
- Type: String
- Description: Method to extract the edges.
- Options: `HED` (deep learning method), `diblasi`, `sobel`
- Example: `HED`

#### `tile_size`
- Type: Integer
- Description: Size in pixels of the tiles used to create the mosaic.
- Example: `10`

#### `coloring_method`
- Type: String
- Description: Coloring method for the mosaic. If specified as original, the original image colors will be used. If kmeans is specified, a clustering of the main colors will be obtained.
- Options: `original` (more colors), `kmeans`
- Example: `kmeans`

#### `num_colors`
- Type: Integer
- Description: Number of colors to extract. Applicable only when `coloring_method` is set to `kmeans`.
- Example: `5`

#### `resize_image`
- Type: Boolean
- Description: Whether to resize the input image to half its size.
- Example: `False`

#### `mosaic_height`
- Type: Integer
- Description: Desired mosaic height in centimeters of the saved mosaic.
- Example: `10`

#### `mosaic_width`
- Type: Integer
- Description: Desired mosaic width in centimeters of the saved mosaic.
- Example: `10`

#### `interactive_edge_modification`
- Type: Boolean
- Description: If `True`, an interactive window will open after extracting the edges in order to modify them.
Use the following keybindings to modify the edges:
*'c': Toggle between drawing and erasing mode.
*'+': Increase the size of the eraser.
*'-': Decrease the size of the eraser.
*'q': Finish the interactive correction process.
- Example: `False`

#### `save_intermediate_steps`
- Type: Boolean
- Description: If `True`, intermediate steps like images with the extracted edges and mosaic guides will be saved.
- Example: `False`

#### `edges_path`
- Type: String
- Description: Path to an image containing extracted edges. Useful for loading previously modified and saved edges. By default, `null` meaning no input file with edeges.
- Example: `null`

#### `output_dpi`
- Type: Integer
- Description: DPI used when saving the figure to PNG. Combined with `figsize` (derived from `mosaic_width`/`mosaic_height` in cm) this determines the output pixel resolution.
- Example: `96`

#### `match_output_to_input_pixels`
- Type: Boolean
- Description: If `True`, sets `mosaic_width`/`mosaic_height` so the saved PNG has the same pixel size as the input image at the configured `output_dpi`.
- Example: `True`

#### `figure_dpi`
- Type: Integer
- Description: Matplotlib figure DPI used during rendering. Defaults to `output_dpi`.
- Example: `192`

### Tile shape / appearance

These knobs control the post-processing pass that turns raw polygons into final tiles.

#### `shrink_tiles`
- Type: Boolean
- Description: If `True`, applies a random scale + small negative buffer to each tile to mimic stone irregularity.
- Example: `True`

#### `shrink_join_style`
- Type: Integer
- Description: Shapely `join_style` used by the negative buffer in the shrink step. `1` rounds corners (the original behaviour), `2` keeps mitred corners (recommended for the Roman-mosaic look), `3` bevels them.
- Example: `2`

#### `shrink_buffer_factor`
- Type: Float
- Description: Negative-buffer distance as a fraction of `half_tile_size`. Larger values shrink tiles more.
- Example: `0.03`

#### `convex_repair`
- Type: Boolean
- Description: If `True`, runs an article-style two-stage convex repair: (1) iteratively drops vertices whose removal *decreases* polygon area (spike removal); (2) replaces near-convex tiles with their convex hull when `area / hull.area >= convex_repair_threshold`. Smooths small concave bites left after overlap subtraction.
- Example: `True`

#### `convex_repair_threshold`
- Type: Float
- Description: Minimum `area / convex_hull.area` ratio required to apply the convex hull replacement (stage 2 of `convex_repair`). Lower values are more aggressive.
- Example: `0.92`

#### `spike_removal_passes`
- Type: Integer
- Description: Maximum number of greedy sweeps performed by stage 1 of `convex_repair`. Each sweep removes at most one *thin* spike vertex (see `spike_max_loss_fraction`). Tile polygons are short, so 3 is usually enough.
- Example: `3`

#### `spike_max_loss_fraction`
- Type: Float
- Description: Threshold for stage 1 of `convex_repair`. A vertex is removed only if its removal both decreases area (i.e. it sticks out) **and** the relative area loss is below this fraction (so the spike is thin). The article's rule is "the area must not change considerably". Setting this too high (e.g. > 0.2) lets the pass eat real corners and shred convex tiles into triangles.
- Example: `0.05`

#### `simplify_tolerance_factor`
- Type: Float
- Description: Polygon simplification tolerance as a fraction of `half_tile_size`. Larger values produce simpler, more polygonal tiles.
- Example: `0.05`

#### `skip_thin_polygons`
- Type: Boolean
- Description: If `True`, skips tile emission when only a very short section of the guideline has been traversed (mirrors the upstream algorithm). Helps avoid sliver/disc-shaped tiles.
- Example: `True`

#### `tile_edge_lw`
- Type: Float
- Description: Line width of each tile's outline in the rendered figure.
- Example: `0.3`

#### `tile_edge_color`
- Type: String
- Description: Matplotlib colour for the tile outline. Use `null` (or omit) to disable outlines.
- Example: `black`

#### `gap_guideline_method`
- Type: String
- Description: How to derive raster guidelines for the gap-filling passes (after edge chains are tiled). **`distance_stripes`** (default) builds offset contours from the distance transform to placed tiles, matching the approach described in [Beetz’s article](https://towardsdatascience.com/how-to-generate-roman-style-mosaics-with-python-11d5aa021b09/). Set to **`skeleton`** only if you explicitly want the older medial-axis-of-gaps behaviour from an earlier version of this fork.
- Options: `distance_stripes` (default), `skeleton` (opt-in legacy)
- Example: `distance_stripes`

#### `gap_chain_spacing_factor`
- Type: Float
- Description: For `distance_stripes`, spacing between gap guide stripes in units of **`half_tile × this factor`** (rounded to pixels). The legacy commented code used `0.5`.
- Example: `0.5`

#### `gap_tile_placement`
- Type: String
- Description: How tiles are placed once the gap guidelines have been built. **`square`** (default) drops axis-aligned squares of side `2 × half_tile` along each gap chain and clips them against neighbours — matches `place_tiles_into_gaps` from [Beetz’s upstream](https://github.com/yobeatz/mosaic) and produces the regular interior grid seen in the article. **`rotated`** uses the legacy curve-following placement (the same path used for the rim pass) and tends to swirl the interior fill.
- Options: `square` (default), `rotated`
- Example: `square`

#### `gap_tile_step_factor`
- Type: Float
- Description: Step between consecutive square placements along a gap chain, in units of `half_tile × this factor`. The article uses `2.0` (i.e. one tile width).
- Example: `2.0`

#### `coloring_sample`
- Type: String
- Description: How each tile's RGB colour is sampled from the source image.
  - `polygon_mean` (default, article-style): mean over pixels truly inside the polygon (uses `skimage.draw.polygon` to rasterise the tile shape).
  - `center`: single representative-point pixel — fastest, blockier look.
  - `bbox_mean`: legacy axis-aligned bounding-box mean. Includes pixels outside the tile, which can leak neighbour colours and is what this fork produced before.
- Options: `polygon_mean` (default), `center`, `bbox_mean`
- Example: `polygon_mean`

##
Got an idea of a parameter that might be relevant to use? [Open an issue](https://github.com/JavierCoronel/mosaic_generator/issues/new/choose) describing your idea!