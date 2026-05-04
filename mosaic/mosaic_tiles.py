"""
mosaic_tiles.py
Module to create and handle polygons that represent tiles for a mosaic.
Copyright (c) 2023 Javier Coronel
"""
import time
import random
from typing import List
import logging
import numpy as np
from shapely.geometry import LineString, Polygon, MultiPoint
from shapely.validation import make_valid
from shapely import affinity
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import patches

logger = logging.getLogger("__main__." + __name__)

RAND_SIZE = 0.15  # portion of tile size which is added or removed randomly during construction
MAX_ANGLE = 40  # 30...75 => max construction angle for tiles along roundings


class MosaicTiles:
    def __init__(self, config_parameters):
        self.config = config_parameters
        self.tile_size = config_parameters.tile_size
        self.tile_area = (self.tile_size) ** 2
        self.half_tile_size = self.tile_size // 2
        self.tile_size_tolerance = int(self.tile_size * RAND_SIZE)
        self.mosaic_height = 0
        self.mosaic_width = 0

        cfg_get = config_parameters.get
        self.shrink_tiles: bool = cfg_get("shrink_tiles", True)
        self.shrink_buffer_factor: float = cfg_get("shrink_buffer_factor", 0.03)
        # Shapely join style for negative buffer: 1=round, 2=mitre, 3=bevel.
        # Round (1) erodes corners into circular arcs and is the main reason
        # tiles appear "blobby" at small sizes.
        self.shrink_join_style: int = cfg_get("shrink_join_style", 2)
        self.convex_repair: bool = cfg_get("convex_repair", False)
        self.convex_repair_threshold: float = cfg_get("convex_repair_threshold", 0.92)
        self.simplify_tolerance_factor: float = cfg_get("simplify_tolerance_factor", 0.05)
        self.skip_thin_polygons: bool = cfg_get("skip_thin_polygons", True)
        self.figure_dpi: int = cfg_get("figure_dpi", cfg_get("output_dpi", 96))
        self.tile_edge_lw: float = cfg_get("tile_edge_lw", 0.3)
        self.tile_edge_color = cfg_get("tile_edge_color", "black")

    def place_tiles_along_guides(self, chains: List, angles: np.array, polygons: List = None) -> List:
        """Creates polygons (tiles) along guides

        Parameters
        ----------
        chains : List
            List of guides containing the chains along which the tiles need to be placed.
        angles : np.array
            Numpy array of shape (height, width) containing the angles of the guidelines.
        polygons : List, optional
            List of existing polygons (default is None).

        Returns
        -------
        List
            List containing all the polygon objects that represent the tiles of a mosaic
        """
        logger.info(f"Placing tiles along {len(chains)} guidelines")
        if polygons is None:
            polygons = []
        for chain in tqdm(chains):
            if len(chain) < 2:
                continue

            # consider existing polygons next to the new lane (reason: speed)
            search_area = LineString(np.array(chain)[:, ::-1]).buffer(2.1 * self.half_tile_size)
            preselected_nearby_polygons = [poly for poly in polygons if poly.intersects(search_area)]

            polygons = self.estimate_polygons_from_chain(chain, angles, polygons, preselected_nearby_polygons)

        return polygons

    def estimate_polygons_from_chain(
        self, list_of_points: List, angles: np.array, polygons: List, preselected_nearby_polygons: List
    ) -> List:
        """Creates a list of polygons by iterating along the points of a chain

        Parameters
        ----------
        list_of_points : List
            List of points that create a chain.
        angles : np.array
            Numpy array of shape (height, width) containing the angles of the points.
        polygons : List
            List of existing polygons
        preselected_nearby_polygons : List
            List of polygons that are close to the point

        Returns
        -------
        List
            List containing the polygon objects for a chain
        """
        for point_idx, point in enumerate(list_of_points):
            y_coord, x_coord = point
            angle = angles[y_coord, x_coord]

            if point_idx == 0:  # at the beginning save the first side of the future polygon
                random_tile_size = self.tile_size + (self.tile_size_tolerance * random.choice([-1, 1]))
                point_idx_start = point_idx
                point_angle_start = angle
                line_start = self._get_line_from_coords(x_coord, y_coord, point_angle_start)

            chain_ready = self._check_if_chain_ready_for_polygon(
                point_idx, point_idx_start, list_of_points, point_angle_start, angles, random_tile_size
            )

            if chain_ready:
                line = self._get_line_from_coords(x_coord, y_coord, angle)

                # Mirror upstream behaviour: a section thinner than ~3 points along the
                # guide produces near-degenerate polygons that round into specks during
                # post-processing. Advance the start anchor without emitting a tile.
                if self.skip_thin_polygons and (point_idx - point_idx_start) <= 2:
                    line_start = line
                    point_angle_start = angle
                    point_idx_start = point_idx
                    continue

                polygons, preselected_nearby_polygons = self._add_polygon(
                    line_start, line, polygons, preselected_nearby_polygons
                )

                line_start = line
                point_angle_start = angle
                point_idx_start = point_idx

        return polygons

    def _get_line_from_coords(self, x_coord: int, y_coord: int, angle: float):

        line = LineString([(x_coord, y_coord - self.half_tile_size), (x_coord, y_coord + self.half_tile_size)])
        line = affinity.rotate(line, -angle)

        return line

    @staticmethod
    def _check_if_chain_ready_for_polygon(
        point_idx: int,
        point_idx_start: int,
        chains: List,
        point_angle_start: float,
        angles: np.array,
        random_tile_size: int,
    ):
        # 1. end of point is reached
        if point_idx == len(chains) - 1:
            return True
        else:
            y_next, x_next = chains[point_idx + 1]
            angle_next_point = angles[y_next, x_next]
            angle_delta = angle_next_point - point_angle_start
            angle_delta = min(180 - abs(angle_delta), abs(angle_delta))
            # 2. with the NEXT point a large angle would be reached => draw now
            if angle_delta > MAX_ANGLE:
                return True
            # 3. goal width is reached
            if point_idx - point_idx_start == random_tile_size:
                return True
            return False

    def _add_polygon(
        self,
        line_start: LineString,
        current_line: LineString,
        polygons: List,
        preselected_nearby_polygons: List,
    ):

        # construct new tile
        polygon = MultiPoint(
            [line_start.coords[0], line_start.coords[1], current_line.coords[0], current_line.coords[1]]
        ).convex_hull

        # cut off areas that overlap with already existing tiles
        nearby_polygons = [
            poly for poly in preselected_nearby_polygons if polygon.buffer(0.02).disjoint(poly.buffer(0.02)) is False
        ]
        polygon = self._fit_in_polygon(polygon, nearby_polygons)

        # Sort out small tiles
        if polygon.area >= 0.08 * self.tile_area and polygon.geom_type == "Polygon" and polygon.is_valid:
            polygons += [polygon]
            preselected_nearby_polygons += [polygon]
            # self.plot_polygons(polygons)

        return polygons, preselected_nearby_polygons

    def _fit_in_polygon(self, polygon: Polygon, nearby_polygons: List):
        # Remove parts from polygon which overlap with existing ones:
        for p_there in nearby_polygons:
            polygon = polygon.difference(p_there)
        # only keep largest part if polygon consists of multiple fragments:
        if polygon.geom_type == "MultiPolygon":
            i_largest = np.argmax([p_i.area for p_i in polygon.geoms])
            polygon = polygon.geoms[i_largest]
        # remove pathologic polygons with holes (rare event):
        if polygon.geom_type not in ["MultiLineString", "LineString", "GeometryCollection"]:
            if polygon.interiors:  # check for attribute interiors if accessible
                polygon = Polygon(list(polygon.exterior.coords))

        return polygon

    def postprocess_polygons(self, polygons):

        logger.info("Posptrocessing mosaic")
        # complete_polygons = self.cut_tiles_outside_frame(polygons)
        if self.shrink_tiles:
            polygons = self._irregular_shrink(polygons)
        polygons = self._repair_tiles(polygons)
        if self.convex_repair:
            polygons = self._convexify_tiles(polygons)
        polygons = self._reduce_edge_count(polygons)
        polygons = self._drop_small_tiles(polygons)

        return polygons

    def _irregular_shrink(self, polygons):
        polygons_shrinked = []
        buffer_distance = -self.shrink_buffer_factor * self.half_tile_size
        for polygon in polygons:
            polygon = affinity.scale(polygon, xfact=random.uniform(0.85, 1), yfact=random.uniform(0.85, 1))
            # Mitred joins keep tile corners polygonal under negative buffering.
            polygon = polygon.buffer(buffer_distance, join_style=self.shrink_join_style)
            polygons_shrinked += [polygon]

        return polygons_shrinked

    def _convexify_tiles(self, polygons):
        """Replace nearly-convex tiles with their convex hull.

        After overlap subtraction tiles can end up with small concave bites that
        rasterize as fuzzy edges. Replacing the polygon with its convex hull when
        the area is already close to its hull's area (i.e. only a small spike or
        bite is being filled) restores the polygonal Roman-mosaic feel without
        meaningfully growing the tile into its neighbours.
        """
        polygons_new = []
        threshold = self.convex_repair_threshold
        for polygon in polygons:
            try:
                hull = polygon.convex_hull
                if (
                    hull.geom_type == "Polygon"
                    and hull.area > 0
                    and polygon.area / hull.area >= threshold
                ):
                    polygons_new.append(hull)
                else:
                    polygons_new.append(polygon)
            except Exception:  # pylint: disable=broad-except
                polygons_new.append(polygon)
        return polygons_new

    def _repair_tiles(self, polygons):
        # remove or correct strange polygons
        polygons_new = []
        for polygon in polygons:
            if polygon.geom_type == "MultiPolygon":
                for polygon_repaired in polygon.geoms:
                    polygons_new += [polygon_repaired]
            else:
                polygons_new += [polygon]

        polygons_new2 = []
        for polygon in polygons_new:
            if polygon.exterior.geom_type == "LinearRing":
                polygons_new2 += [polygon]

        return polygons_new2

    def _reduce_edge_count(self, polygons, tol=20):
        polygons_new = []
        # Configurable factor wins over the legacy "tol" inverse style.
        if self.simplify_tolerance_factor is not None:
            tolerance = self.half_tile_size * self.simplify_tolerance_factor
        else:
            tolerance = self.half_tile_size / tol
        for polygon in polygons:
            polygon = polygon.simplify(tolerance=tolerance)
            polygons_new += [polygon]
        return polygons_new

    def _drop_small_tiles(self, polygons, threshold=0.03):
        polygons_new = []
        counter = 0
        for polygon in polygons:
            if polygon.area > threshold * self.tile_area:
                polygons_new += [polygon]
            else:
                counter += 1
        return polygons_new

    def cut_tiles_outside_frame(self, polygons):
        # remove parts of tiles which are outside of the actual image
        t_0 = time.time()
        outer = Polygon(
            [
                (-3 * self.half_tile_size, -3 * self.half_tile_size),
                (self.mosaic_width + 3 * self.half_tile_size, -3 * self.half_tile_size),
                (self.mosaic_width + 3 * self.half_tile_size, self.mosaic_height + 3 * self.half_tile_size),
                (-3 * self.half_tile_size, self.mosaic_height + 3 * self.half_tile_size),
            ],
            holes=[
                [
                    (1, 1),
                    (self.mosaic_height - 1, 1),
                    (self.mosaic_height - 1, self.mosaic_width - 1),
                    (1, self.mosaic_width - 1),
                ],
            ],
        )
        polygons_cut = []
        counter = 0
        for polygon in polygons:
            x_coord, y_coord = list(polygon.representative_point().coords)[0]
            if (
                y_coord < 4 * self.half_tile_size
                or y_coord > self.mosaic_height - 4 * self.half_tile_size
                or x_coord < 4 * self.half_tile_size
                or x_coord > self.mosaic_width - 4 * self.half_tile_size
            ):
                polygon = make_valid(polygon).difference(make_valid(outer))  # => if outside image borders
                counter += 1
            if polygon.area >= 0.05 * self.tile_area and polygon.geom_type == "Polygon":
                x_exterior, y_exterior = polygon.exterior.xy
                x_coords_in_range = [self.check_coords_in_range(coord, 0, self.mosaic_width) for coord in x_exterior]
                y_coords_in_range = [self.check_coords_in_range(coord, 0, self.mosaic_height) for coord in y_exterior]

                polygon_is_in_valid_area = np.all(y_coords_in_range, x_coords_in_range)

                if polygon_is_in_valid_area:
                    polygons_cut += [polygon]
        logger.infof("Up to {counter} tiles beyond image borders were cut", f"{time.time()-t_0:.1f}s")
        return polygons_cut

    @staticmethod
    def check_coords_in_range(coords, lower_bound, higher_bound):
        if lower_bound <= coords < higher_bound:
            return True
        return False

    def plot_polygons(self, polygons, colors=None, background=None):

        # Turn interactive plotting off
        plt.ioff()
        logger.info("Plotting polygons for mosaic")
        fig, axes = plt.subplots(
            dpi=self.figure_dpi,
            figsize=(self.config.mosaic_width / 2.54, self.config.mosaic_height / 2.54),
        )
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        axes.invert_yaxis()
        axes.autoscale()
        axes.set_facecolor("slategray")

        edge_color_cfg = self.tile_edge_color
        edge_lw = self.tile_edge_lw

        for j, polygon in enumerate(tqdm(polygons)):

            if colors is not None:
                color = colors[j]
            else:
                color = "silver"

            corners = np.array(polygon.exterior.coords.xy).T
            tile = patches.Polygon(corners, edgecolor=edge_color_cfg, lw=edge_lw, facecolor=color)
            axes.add_patch(tile)

        if background is not None:
            axes.set_facecolor("antiquewhite")
        axes.margins(0)
        fig.canvas.draw()
        # plt.show()

        return fig
