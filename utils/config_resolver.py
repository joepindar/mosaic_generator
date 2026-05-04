"""
config_resolver.py
Module to resolve the configuration parameters to obtain a mosaic.
Copyright (c) 2024 Javier Coronel
"""
import math
import logging
from pathlib import Path
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
            default_output_folder = Path(cfg.image_path).parent
            cfg.output_folder = cfg.get("output_folder", default_output_folder)

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
            cfg.simplify_tolerance_factor = cfg.get("simplify_tolerance_factor", 0.05)
            cfg.skip_thin_polygons = cfg.get("skip_thin_polygons", True)
            cfg.figure_dpi = cfg.get("figure_dpi", cfg.output_dpi)
            cfg.tile_edge_lw = cfg.get("tile_edge_lw", 0.3)
            cfg.tile_edge_color = cfg.get("tile_edge_color", "black")

            # Gap-fill guidelines (see mosaic_guides.MosaicGuides.get_gaps_from_polygons).
            cfg.gap_guideline_method = cfg.get("gap_guideline_method", "distance_stripes")
            cfg.gap_chain_spacing_factor = cfg.get("gap_chain_spacing_factor", 0.5)

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
