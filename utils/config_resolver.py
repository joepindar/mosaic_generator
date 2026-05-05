"""
config_resolver.py
Module to resolve the configuration parameters to obtain a mosaic.
Copyright (c) 2024 Javier Coronel
"""
import math
import logging
import numpy as np
from omegaconf import DictConfig, open_dict

from utils.image_handler import ImageHandler

logger = logging.getLogger("__main__." + __name__)


class ConfigResolver:
    """Class to resolve a the configuration parameters to obtain a mosaic"""

    def __init__(self):
        pass


    def resolve_config(self, cfg: DictConfig) -> DictConfig:
        """Set configuration parameters to default if they are not set

        Parameters
        ----------
        cfg : DictConfig
            A raw configuration file

        Returns
        -------
        DictConfig
            A resolved configuraiton dictionary
        """
        assert cfg.image_path, "An 'image_path' should be provided in the config"

        with open_dict(cfg):
            cfg.output_folder = cfg.get("output_folder", "outputs")

            cfg.edge_extraction_method = cfg.get("edge_extraction_method", "sobel")
            cfg.coloring_method = cfg.get("coloring_method", "original")

            if cfg.coloring_method == "kmeans":
                cfg.num_colors = cfg.get("num_colors", "8")
            else:
                cfg.num_colors = None

            cfg.resize_image = cfg.get("resize_image", False)

            cfg.interactive_edge_modification = cfg.get("interactive_edge_modification", False)
            cfg.save_intermediate_steps = cfg.get("save_intermediate_steps", False)

            cfg.edges_path = cfg.get("edges_path", None)
            cfg.output_dpi = cfg.get("output_dpi", 96)

            # Visual / shape post-processing knobs (see mosaic_tiles.MosaicTiles).
            cfg.shrink_tiles = cfg.get("shrink_tiles", True)
            cfg.shrink_buffer_factor = cfg.get("shrink_buffer_factor", 0.03)
            cfg.shrink_join_style = cfg.get("shrink_join_style", 2)
            cfg.convex_repair = cfg.get("convex_repair", False)
            cfg.convex_repair_threshold = cfg.get("convex_repair_threshold", 0.92)
            cfg.spike_removal_passes = cfg.get("spike_removal_passes", 3)
            cfg.spike_max_loss_fraction = cfg.get("spike_max_loss_fraction", 0.05)
            cfg.simplify_tolerance_factor = cfg.get("simplify_tolerance_factor", 0.05)
            cfg.skip_thin_polygons = cfg.get("skip_thin_polygons", True)
            cfg.figure_dpi = cfg.get("figure_dpi", cfg.output_dpi)
            cfg.tile_edge_lw = cfg.get("tile_edge_lw", 0.3)
            cfg.tile_edge_color = cfg.get("tile_edge_color", "black")

            # Gap-fill guidelines (see mosaic_guides.MosaicGuides.get_gaps_from_polygons).
            # Default is distance_stripes; skeleton is only used when explicitly set.
            gap_m = cfg.get("gap_guideline_method", "distance_stripes")
            if gap_m is None or (isinstance(gap_m, str) and not str(gap_m).strip()):
                gap_m = "distance_stripes"
            else:
                gap_m = str(gap_m).strip()
            if gap_m not in ("distance_stripes", "skeleton"):
                logger.warning(
                    "Invalid gap_guideline_method=%r; using distance_stripes (only 'skeleton' is supported as an alternate)",
                    gap_m,
                )
                gap_m = "distance_stripes"
            cfg.gap_guideline_method = gap_m
            cfg.gap_chain_spacing_factor = cfg.get("gap_chain_spacing_factor", 0.5)

            # How gap tiles are placed once the gap guidelines have been built.
            # `square` (default) matches the article / yobeatz upstream:
            # axis-aligned squares clipped against neighbours. `rotated` uses
            # the curve-following placement also used for the rim pass.
            gap_tp = cfg.get("gap_tile_placement", "square")
            if gap_tp not in ("square", "rotated"):
                logger.warning(
                    "Invalid gap_tile_placement=%r; using 'square'",
                    gap_tp,
                )
                gap_tp = "square"
            cfg.gap_tile_placement = gap_tp
            cfg.gap_tile_step_factor = cfg.get("gap_tile_step_factor", 2.0)

            # How tile colour is sampled from the input image.
            cs = cfg.get("coloring_sample", "polygon_mean")
            if cs not in ("polygon_mean", "bbox_mean", "center"):
                logger.warning(
                    "Invalid coloring_sample=%r; using 'polygon_mean'",
                    cs,
                )
                cs = "polygon_mean"
            cfg.coloring_sample = cs

            cfg.mosaic_width, cfg.mosaic_height = self._resolve_mosaic_dimensions(cfg=cfg)
            cfg.tile_size = self._resolve_tile_size(cfg=cfg)

        return cfg

    def _resolve_mosaic_dimensions(self, cfg: DictConfig) -> DictConfig:

        if cfg.get("match_output_to_input_pixels", False):
            logger.info("Sizing output figure to match input image pixel size (see output_dpi)...")
            image_handler = ImageHandler(cfg)
            image = image_handler.read_image()
            img_height, img_width, _ = image.shape
            dpi = cfg.get("output_dpi", 96)
            # figsize is in inches; savefig uses output_dpi -> pixels = inches * dpi = image pixels
            mosaic_width = img_width * 2.54 / dpi
            mosaic_height = img_height * 2.54 / dpi
            logger.info(
                "Resolved mosaic figure to ~%d x %d px at %d dpi (%.2f x %.2f cm)",
                img_width,
                img_height,
                dpi,
                mosaic_width,
                mosaic_height,
            )
            return mosaic_width, mosaic_height

        mosaic_width = cfg.get("mosaic_width", False)
        mosaic_height = cfg.get("mosaic_height", False)

        if not mosaic_width or not mosaic_height:
            logger.info("Desired mosaic dimensions not provided, estimating default size based on image size...")
            image_handler = ImageHandler(cfg)
            image = image_handler.read_image()

            img_height, img_width, _ = image.shape
            mag_order = math.floor(math.log(img_height,10))

            n=1
            mosaic_height = img_height
            while mosaic_height>15:
                mosaic_height = img_height/(mag_order*10*n)
                n+=1

            mosaic_width = img_width/(mag_order*10*(n-1))

        return mosaic_width, mosaic_height

    def _resolve_tile_size(self, cfg: DictConfig) -> DictConfig:

        tile_size = cfg.get("tile_size", False)

        if not tile_size:
            logger.info("Desired tile size not provided, estimating default size based on image size...")
            if cfg.get("match_output_to_input_pixels", False):
                tile_size = 10
            else:
                tile_size = np.min((cfg.mosaic_width, cfg.mosaic_height))

        return tile_size
