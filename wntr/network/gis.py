"""
Geographic and shape functionality
"""

import os.path
import warnings

import pandas as pd
import numpy as np

try:
    from shapely.geometry import LineString, Point, shape

    has_shapely = True
except ModuleNotFoundError:
    has_shapely = False

try:
    import geopandas as gpd

    has_geopandas = True
except ModuleNotFoundError:
    gpd = None
    has_geopandas = False


class WaterNetworkGIS:
    def __init__(self, wn, crs: str = "", pump_as_point_geometry=True, valve_as_point_geometry=True) -> None:
        """
        Water network model as GeoPandas and Shapely objects with attributes

        Parameters
        ----------
        wn : WaterNetworkModel
            the water network
        crs : str, optional
            coordinate reference string, by default ""
        pump_as_point_geometry : bool, optional
            create pumps as points (True) or lines (False), by default True
        valve_as_point_geometry : bool, optional
            create valves as points (True) or lines (False), by default True

        Raises
        ------
        ModuleNotFoundError
            if missing either shapely or geopandas
        """
        if not has_shapely or not has_geopandas:
            raise ModuleNotFoundError("Cannot do WNTR geometry without shapely and geopandas")
        self.crs = crs
        self.pump_as_point_geometry = pump_as_point_geometry
        self.valve_as_point_geometry = valve_as_point_geometry
        self._wn = wn
        self.junctions = None
        self.tanks = None
        self.reservoirs = None
        self.pipes = None
        self.pumps = None
        self.valves = None
        self.reset_data()

    def reset_data(
        self, crs: str = None, pump_as_point_geometry: bool = None, valve_as_point_geometry: bool = None,
    ) -> None:
        """
        Reset the data in the geometry with new options (will delete any attributes previously added)

        Parameters
        ----------
        crs : str, optional
            the coordinate reference system, such as by default None (use internal object attribute value).
            If set, this will update the object's internal attribute
        pump_as_point_geometry : bool, optional
            create pumps as points (True) or lines (False), by default None (use internal object attribute value).
            If set, this will update the object's internal attribute
        valve_as_point_geometry : bool, optional
            create valves as points (True) or lines (False), by default None (use internal object attribute value).
            If set, this will update the object's internal attribute
        """
        if crs is not None:
            self.crs = crs
        if pump_as_point_geometry is not None:
            self.pump_as_point_geometry = pump_as_point_geometry
        if valve_as_point_geometry is not None:
            self.valve_as_point_geometry = valve_as_point_geometry
        crs = self.crs
        pumps_as_points = self.pump_as_point_geometry
        valves_as_points = self.valve_as_point_geometry
        wn = self._wn

        data = list()
        geometry = list()
        for node_name in wn.junction_name_list:
            node = wn.get_node(node_name)
            g = Point(node.coordinates)
            dd = dict(
                name=node.name,
                type=node.node_type,
                elevation=node.elevation,
                tag=node.tag,
                initial_quality=node.initial_quality,
                base_demand=node.base_demand,
            )
            data.append(dd)
            geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.junctions = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        data = list()
        geometry = list()
        for node_name in wn.tank_name_list:
            node = wn.get_node(node_name)
            g = Point(node.coordinates)
            dd = dict(
                name=node.name,
                type=node.node_type,
                elevation=node.elevation,
                tag=node.tag,
                initial_quality=node.initial_quality,
                initial_level=node.init_level,
            )
            data.append(dd)
            geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.tanks = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        data = list()
        geometry = list()
        for node_name in wn.reservoir_name_list:
            node = wn.get_node(node_name)
            g = Point(node.coordinates)
            dd = dict(
                name=node.name,
                type=node.node_type,
                elevation=node.base_head,
                tag=node.tag,
                initial_quality=node.initial_quality,
                base_head=node.base_head,
            )
            data.append(dd)
            geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.reservoirs = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        data = list()
        geometry = list()
        for link_name in wn.valve_name_list:
            ls = list()
            link = wn.get_link(link_name)
            ls.append(link.start_node.coordinates)
            for v in link.vertices:
                ls.append(v)
            ls.append(link.end_node.coordinates)
            g = LineString(ls)
            g2 = Point(link.start_node.coordinates)
            dd = dict(
                name=link.name,
                type=link.link_type,
                valve_type=link.valve_type,
                tag=link.tag,
                initial_status=link.initial_status,
                initial_setting=link.initial_setting,
            )
            data.append(dd)
            if valves_as_points:
                geometry.append(g2)
            else:
                geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.valves = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        data = list()
        geometry = list()
        for link_name in wn.pump_name_list:
            ls = list()
            link = wn.get_link(link_name)
            ls.append(link.start_node.coordinates)
            for v in link.vertices:
                ls.append(v)
            ls.append(link.end_node.coordinates)
            g = LineString(ls)
            g2 = Point(link.start_node.coordinates)
            dd = dict(
                name=link.name,
                type=link.link_type,
                pump_type=link.pump_type,
                tag=link.tag,
                initial_status=link.initial_status,
                initial_setting=link.initial_setting,
            )
            data.append(dd)
            if pumps_as_points:
                geometry.append(g2)
            else:
                geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.pumps = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

        data = list()
        geometry = list()
        for link_name in wn.pipe_name_list:
            ls = list()
            link = wn.get_link(link_name)
            ls.append(link.start_node.coordinates)
            for v in link.vertices:
                ls.append(v)
            ls.append(link.end_node.coordinates)
            g = LineString(ls)
            dd = dict(
                name=link.name,
                type=link.link_type,
                tag=link.tag,
                initial_status=link.initial_status,
                length=link.length,
                diameter=link.diameter,
                roughness=link.roughness,
                cv=link.cv,
            )
            data.append(dd)
            geometry.append(g)
        df = pd.DataFrame(data)
        if len(df) > 0:
            df.set_index("name", inplace=True)
        self.pipes = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    def add_node_attributes(self, values, name):
        """
        Add attributes to the nodes of the network geometry.

        Parameters
        ----------
        values : dict or Series or row of a DataFrame
            [description]
        name : str
            [description]
        """
        for node_name, value in values.items():
            node = self._wn.get_node(node_name)
            if str(node.node_type).lower() == "junction":
                if name not in self.junctions.columns:
                    self.junctions[name] = np.nan
                self.junctions.loc[node_name, name] = value
            if str(node.node_type).lower() == "tank":
                if name not in self.tanks.columns:
                    self.tanks[name] = np.nan
                self.tanks.loc[node_name, name] = value
            if str(node.node_type).lower() == "reservoir":
                if name not in self.reservoirs.columns:
                    self.reservoirs[name] = np.nan
                self.reservoirs.loc[node_name, name] = value

    def add_link_attributes(self, values, name):
        """
        Add attributes the links of the network geometry.

        Parameters
        ----------
        values : dict or Series or row of a DataFrame
            [description]
        name : [type]
            [description]
        """
        for link_name, value in values.items():
            link = self._wn.get_link(link_name)
            if str(link.link_type).lower() == "pipe":
                if name not in self.pipes.columns:
                    self.pipes[name] = np.nan
                self.pipes.loc[link_name, name] = value
            if str(link.link_type).lower() == "valve":
                if name not in self.valves.columns:
                    self.valves[name] = np.nan
                self.valves.loc[link_name, name] = value
            if str(link.link_type).lower() == "pump":
                if name not in self.pumps.columns:
                    self.pumps[name] = np.nan
                self.pumps.loc[link_name, name] = value

    def write(self, prefix: str, path: str = None, suffix: str = None, driver="GeoJSON") -> None:
        """
        Write the Geometry object to GIS file(s) with names constructed from parameters.

        The file name is of the format

            [ ``{path}/`` ] ``{prefix}_$elementType`` [ ``_{suffix}`` ] ``.$extensionByDriver``

        where parameters surrounded by brackets "[]" are optional parameters and the ``$`` indicates
        parts of the filename determined by the function. One file will be created for each type of
        network element (junctions, pipes, etc.) assuming that the element exists in the network;
        i.e., blank files will not be created. Drivers available are any of the geopandas valid
        drivers.


        Parameters
        ----------
        prefix : str
            the filename prefix, will have the element type (junctions, valves) appended
        path : str, optional
            the path to write the file, by default None (current directory)
        suffix : str, optional
            if desired, an indicator such as the timestep or other string, by default None
        driver : str, optional
            one of the geopandas drivers (use :code:`None` for ESRI shapefile folders), by default "GeoJSON",
        """
        if path is None:
            path = "."
        if suffix is None:
            suffix = ""
        prefix = os.path.join(path, prefix)
        if driver is None or driver == "":
            extension = ""
        else:
            extension = "." + driver.lower()
        if len(self.junctions) > 0:
            self.junctions.to_file(
                prefix + "_junctions" + suffix + extension, driver=driver,
            )
        if len(self.tanks) > 0:
            self.tanks.to_file(
                prefix + "_tanks" + suffix + extension, driver=driver,
            )
        if len(self.reservoirs) > 0:
            self.reservoirs.to_file(
                prefix + "_reservoirs" + suffix + extension, driver=driver,
            )
        if len(self.pipes) > 0:
            self.pipes.to_file(
                prefix + "_pipes" + suffix + extension, driver=driver,
            )
        if len(self.pumps) > 0:
            self.pumps.to_file(
                prefix + "_pumps" + suffix + extension, driver=driver,
            )
        if len(self.valves) > 0:
            self.valves.to_file(
                prefix + "_valves" + suffix + extension, driver=driver,
            )
    

def snap_points_to_points(points1, points2):
    pass

def snap_points_to_lines(points, lines):
    pass

def _intersect(elements, polygons, column):
   
    isinstance(polygons, gpd.GeoDataFrame)
    
    intersects = gpd.sjoin(elements, polygons, op='intersects')
    
    n = intersects.groupby('name')[column].count()
    val_sum = intersects.groupby('name')[column].sum()
    val_min = intersects.groupby('name')[column].min()
    val_max = intersects.groupby('name')[column].max()
    val_average = intersects.groupby('name')[column].mean()
    
    polygon_indices = intersects.groupby('name')['index_right'].apply(list)
    polygon_values = intersects.groupby('name')[column].apply(list)

    stats = pd.DataFrame(index=elements.index, data={'N': n,
                                                     'Sum': val_sum,
                                                     'Min': val_min, 
                                                     'Max': val_max, 
                                                     'Average': val_average,
                                                     'Polygons': polygon_indices,
                                                     'Values': polygon_values})
    return stats


def intersect_points_with_polygons(points, polygons, column):
    
    isinstance(points, gpd.GeoDataFrame)
    assert (points['geometry'].geom_type).isin(['Point']).all()
    isinstance(polygons, gpd.GeoDataFrame)
    assert (polygons['geometry'].geom_type).isin(['Polygon', 'MultiPolygon']).all()
    isinstance(column, str)
    assert column in polygons.columns
    
    stats = _intersect(points, polygons, column)
    return stats

def intersect_lines_with_polygons(lines, polygons, column, return_weighted_average=True):
    
    isinstance(lines, gpd.GeoDataFrame)
    assert (lines['geometry'].geom_type).isin(['LineString', 'MultiLineString']).all()
    isinstance(polygons, gpd.GeoDataFrame)
    assert (polygons['geometry'].geom_type).isin(['Polygon', 'MultiPolygon']).all()
    isinstance(column, str)
    assert column in polygons.columns
    isinstance(return_weighted_average, bool)
    
    stats = _intersect(lines, polygons, column)
    
    if return_weighted_average:
        stats['Weighted Average'] = 0
        line_length = lines.length
        for i in polygons.index:
            polygon = gpd.GeoDataFrame(polygons.loc[[i],:], crs=None)
            clip = gpd.clip(lines, polygon) # you might be able to downselect lines using stats['Polygons'] to speed up clip
            
            if len(clip.index) > 0:
                val = float(polygon[column])
                
                weighed_val = clip.length/line_length[clip.index]*val
                assert (weighed_val <= val).all()
                stats.loc[clip.index, 'Weighted Average'] = stats.loc[clip.index, 'Weighted Average'] + weighed_val
                
        stats['Weighted Average'] = stats['Weighted Average']/stats['N']
    
    return stats