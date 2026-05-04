# Configuration parameters

## Usage
We use YAML configuration files managed by [Hydra](https://hydra.cc/docs/intro/) to define various parameters to generating mosaics. 

To get started, consider using the following templates and adjust them to tailor the mosaic generation process according to your requirements. Save your modified `.yaml` file with a different name, and use it to execute the code as explained in the [usage](../../README.md#usage) section. 

You can run two types of hydra configs:
* [`default.yaml`](./default.yaml) has a list of parameters to run a single execution for mosaic generation.
* [`default_parallel.yaml`](./default_parallel.yaml) has additional hydra configurations to run multiple mosaic generations in parallel. Here you can list multiple values for a single parameter under the `sweeper/params` part of the `.yaml` file.

## Parameters
Here you can find a list of the posible parameters with their explaination and possible values:
#### `image_path` 
- Type: String
- Description: Absolute or relative path to the input image.
- Example: `/path/to/image.jpg`

#### `output_folder`
- Type: String
- Description: Absolute or relative path to the output folder where generated mosaics will be saved.
- Example: `/path/to/folder`

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
- Description: If `True`, tiles whose area is at least `convex_repair_threshold` of their convex hull's area are replaced with the hull. Smooths out small concave bites left after overlap subtraction.
- Example: `True`

#### `convex_repair_threshold`
- Type: Float
- Description: Minimum `area / convex_hull.area` ratio required to apply the convex repair. Lower values are more aggressive.
- Example: `0.92`

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
- Description: How to derive raster guidelines for the gap-filling passes (after edge chains are tiled). `distance_stripes` builds offset contours from the distance transform to placed tiles, matching the approach described in [Beetz’s article](https://towardsdatascience.com/how-to-generate-roman-style-mosaics-with-python-11d5aa021b09/). `skeleton` uses the medial axis of free space (older behaviour in this fork).
- Options: `distance_stripes`, `skeleton`
- Example: `distance_stripes`

#### `gap_chain_spacing_factor`
- Type: Float
- Description: For `distance_stripes`, spacing between gap guide stripes in units of **`half_tile × this factor`** (rounded to pixels). The legacy commented code used `0.5`.
- Example: `0.5`

##
Got an idea of a parameter that might be relevant to use? [Open an issue](https://github.com/JavierCoronel/mosaic_generator/issues/new/choose) describing your idea!