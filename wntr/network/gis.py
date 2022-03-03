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
#        if len(df) > 0:
#            df.set_index("name", inplace=True)
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
#        if len(df) > 0:
#            df.set_index("name", inplace=True)
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
                start_node=link.start_node.name, # keep start and end node names attached to links
                end_node=link.end_node.name,
#                start_node_coordinates=link.start_node.coordinates,
#                end_node_coordinates=link.end_node.coordinates,
                length=link.length,
                diameter=link.diameter,
                roughness=link.roughness,
                cv=link.cv,
            )
            data.append(dd)
            geometry.append(g)
        df = pd.DataFrame(data)
#        if len(df) > 0:
#            df.set_index("name", inplace=True)
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
                
    def snap_to_line(self, points, tolerance, lines='pipes', find_node=False):
        """
        Returns new points with coordinates snapped to the nearest lines.

        Parameters
        ----------
        points : GeoPandas GeoDataFrame
            A pandas.DataFrame object with a 'geometry' column populated by 
            'POINT' geometries.
        tolerance : float, optional
            the maximum allowable distance (in the line coordinate system) 
            between a point and nearby line to move the point to the line.
        lines : str or GeoPandas GeoDataFrame
            A pandas.DataFrame object with a 'geometry' column populated by 
            'LINESTRING' or 'MULTILINESTRING' geometries.
        """   
        if lines=='pipes':
            lines = self.pipes

#        # determine how far to look around each point for lines
#        bbox = points.bounds + [-tolerance, -tolerance, tolerance, tolerance]       
#        # determine which links are close to each point
#        hits = bbox.apply(lambda row: list(lines.loc[list(lines.sindex.intersection(row))]['name']), axis=1)        
#        closest = pd.DataFrame({
#            # index of points table
#            "valve": np.repeat(hits.index, hits.apply(len)),
#            # name of link
#            "name": np.concatenate(hits.values)
#            })
#        # Merge the closest dataframe with the lines dataframe on the line names
#        closest = pd.merge(closest,lines, on="name")
#        # rename the line "name" column header to "link"
#        closest = closest.rename(columns={"name":"link"})
#        # Join back to the original points to get their geometry
#        # rename the point geometry as "point"
#        closest = closest.join(points.geometry.rename("points"), on="valve")
#        # Convert back to a GeoDataFrame, so we can do spatial ops
#        closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=lines.crs)    
#        # Calculate distance between the point and nearby links
#        closest["snap_dist"] = closest.geometry.distance(gpd.GeoSeries(closest.points, crs=lines.crs))
#        # Sort on ascending snap distance, so that closest goes to top
#        closest = closest.sort_values(by=["snap_dist"])        
#        # group by the index of the points and take the first, which is the closest line
#        closest = closest.groupby("valve").first()        
#        # construct a GeoDataFrame of the closest lines
#        closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=lines.crs)
#        # position of nearest point from start of the line
#        pos = closest.geometry.project(gpd.GeoSeries(closest.points))        
#        # get new point location geometry
#        snapped_points = closest.geometry.interpolate(pos)
#        snapped_points = gpd.GeoDataFrame(data=closest.link,geometry=snapped_points, crs=lines.crs)
#        self.closest = closest
#        self.snapped_point_to_line = snapped_points 
        
        sjoin_points = points.sjoin_nearest(lines, how="left", max_distance=tolerance)
        sjoin_points = sjoin_points.rename(columns={"name":"link"})
        sjoin_points = gpd.GeoDataFrame(sjoin_points, geometry="geometry")
#        for point in sjoin_points.index:
#            points_link = sjoin_points.loc[point].link
#            pt_coord = sjoin_points.loc[point].geometry
#            linestring = lines.loc[lines['name'] == points_link].geometry
#            print('point:', point, 'linestring_project:', str(linestring.project(pt_coord, normalized=True)))
            
            
#        sjoin_points.geometry = sjoin_points["node_geom"]
#        sjoin_points.drop(columns=["node_geom", "type", "initial_quality", "base_demand",
        
        
#        sjoin_points["link"] = sjoin_points["index_right"]
#        if find_node:    
#            sjoin_points = sjoin_points[["index_right", "start_node", "end_node", "geometry"]]
#            # find nearest node to the point (between the start and end nodes for the link)
#            for row in sjoin_points:
#                link_name = sjoin_points.loc[row]['link']
#                link = self._wn.get_link(link_name)
#                start_node_coordinate = link.start_node.coordinates
#                end_node_coordinate = link.end_node.coordinates
                
        # else:
        #     sjoin_points = sjoin_points[["index_right", "geometry"]]

        self.sjoin_point_to_line = gpd.GeoDataFrame(sjoin_points, geometry="geometry")
        
#        if find_node:
#            
#            snapped_points["link_geom"] = 
#            wn_points["node_geom"] = wn_points.geometry
#            sjoin_points = points.sjoin_nearest(wn_points, how="left", max_distance=tolerance)
#            sjoin_points.geometry = sjoin_points["node_geom"]
#    #        sjoin_points.drop(columns=["node_geom", "type", "initial_quality", "base_demand",
#            sjoin_points = sjoin_points[["index_right", "geometry"]]
#            sjoin_points = sjoin_points.rename(columns={"index_right":"node"})
#            self.sjoin_points = sjoin_points
            
                

    def snap_to_point(self, points, tolerance, wn_points='junctions'):
        """
        Returns new points with coordinates snapped to the nearest lines.

        Parameters
        ----------
        points : GeoPandas GeoDataFrame
            A pandas.DataFrame object with a 'geometry' column populated by 
            'POINT' geometries.
        tolerance : float, optional
            the maximum allowable distance (in the line coordinate system) 
            between a point and nearby line to move the point to the line.
        wn_points : str or GeoPandas GeoDataFrame
            A pandas.DataFrame object with a 'geometry' column populated by 
            'LINESTRING' or 'MULTILINESTRING' geometries.
        """   
        if wn_points=='junctions':
            wn_points = self.junctions

#        # determine how far to look around each point for lines
#        bbox = points.bounds + [-tolerance, -tolerance, tolerance, tolerance]       
#        # determine which links are close to each point
#        hits = bbox.apply(lambda row: list(wn_points.loc[list(wn_points.sindex.intersection(row))]['name']), axis=1)        
#        closest = pd.DataFrame({
#            # index of points table
#            "valve": np.repeat(hits.index, hits.apply(len)),
#            # ordinal position of link - access via iloc later
#            "name": np.concatenate(hits.values)
#            })
#        # Join back to the links on line_i; we use reset_index() to 
#        # give us the ordinal position of each line
#        closest = pd.merge(closest,wn_points, on="name")
#        closest = closest.rename(columns={"name":"node"})
#        # Join back to the original points to get their geometry
#        # rename the point geometry as "point"
#        closest = closest.join(points.geometry.rename("points"), on="valve")
#        # Convert back to a GeoDataFrame, so we can do spatial ops
#        closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=wn_points.crs)    
#        # Calculate distance between the point and nearby links
#        closest["snap_dist"] = closest.geometry.distance(gpd.GeoSeries(closest.points, crs=wn_points.crs))
#        # Sort on ascending snap distance, so that closest goes to top
#        closest = closest.sort_values(by=["snap_dist"])        
#        # group by the index of the points and take the first, which is the closest line
#        closest = closest.groupby("valve").first()        
#        # construct a GeoDataFrame of the closest nodes
#        closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=wn_points.crs)
#        snapped_points = gpd.GeoDataFrame(data=closest.node,geometry=closest.geometry, crs=wn_points.crs)
#        self.closest = closest
#        self.snapped_point_to_point = snapped_points 
        
        wn_points["node_geom"] = wn_points.geometry
#        points = points.to_crs(wn_points.crs)
        sjoin_points = points.sjoin_nearest(wn_points, how="left", max_distance=tolerance)
        sjoin_points.geometry = sjoin_points["node_geom"]
        wn_points.drop("node_geom", inplace=True, axis=1)
#        sjoin_points.drop(columns=["node_geom", "type", "initial_quality", "base_demand",
        # sjoin_points = sjoin_points[["index_right", "geometry"]]
        sjoin_points = sjoin_points.rename(columns={"name":"node"})
        sjoin_points = sjoin_points[["node", "geometry", "elevation"]]
        self.sjoin_point_to_point = gpd.GeoDataFrame(sjoin_points, geometry="geometry")

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
                prefix + "_pipes" + suffix + extension, driver=driver,index=True
            )
        if len(self.pumps) > 0:
            self.pumps.to_file(
                prefix + "_pumps" + suffix + extension, driver=driver,
            )
        if len(self.valves) > 0:
            self.valves.to_file(
                prefix + "_valves" + suffix + extension, driver=driver,
            )
#        if len(self.snapped_point_to_line) > 0:
#            self.snapped_point_to_line.to_file(
#                prefix + "_snapped_points_to_line" + suffix + extension, driver=driver,
#            )
#        if len(self.snapped_point_to_point) > 0:
#            self.snapped_point_to_point.to_file(
#                prefix + "_snapped_points_to_point" + suffix + extension, driver=driver,
#            )

def snap_points_to_points(points1, points2, tolerance):
    
    isinstance(points1, gpd.GeoDataFrame)
    assert(points1['geometry'].geom_type).isin(['Point']).all()
    isinstance(points2, gpd.GeoDataFrame)
    assert(points2['geometry'].geom_type).isin(['Point']).all()
    
    points2["node_geom"] = points2.geometry
    sjoin_points = points1.sjoin_nearest(points2, how="left", max_distance=tolerance)
    sjoin_points.geometry = sjoin_points["node_geom"]
    points2.drop("node_geom", inplace=True, axis=1)
    sjoin_points = sjoin_points.rename(columns={"name":"node"})
    sjoin_points = sjoin_points[["node", "geometry", "elevation"]]
    snapped_points1 = gpd.GeoDataFrame(sjoin_points, geometry="geometry")    
    return snapped_points1
    
def snap_points_to_lines(points1, lines, tolerance):
    """
    Returns new points with coordinates snapped to the nearest lines.

    Parameters
    ----------
    points : GeoPandas GeoDataFrame
        A pandas.DataFrame object with a 'geometry' column populated by 
        'POINT' geometries.
    lines : str or GeoPandas GeoDataFrame
        A pandas.DataFrame object with a 'geometry' column populated by 
        'LINESTRING' or 'MULTILINESTRING' geometries.
    tolerance : float, optional
        the maximum allowable distance (in the line coordinate system) 
        between a point and nearby line to move the point to the line.
    """   

    # determine how far to look around each point for lines
    bbox = points.bounds + [-tolerance, -tolerance, tolerance, tolerance]       
    # determine which links are close to each point
    hits = bbox.apply(lambda row: list(lines.loc[list(lines.sindex.intersection(row))]['name']), axis=1)        
    closest = pd.DataFrame({
        # index of points table
        "valve": np.repeat(hits.index, hits.apply(len)),
        # name of link
        "name": np.concatenate(hits.values)
        })
    # Merge the closest dataframe with the lines dataframe on the line names
    closest = pd.merge(closest,lines, on="name")
    # rename the line "name" column header to "link"
    closest = closest.rename(columns={"name":"link"})
    # Join back to the original points to get their geometry
    # rename the point geometry as "point"
    closest = closest.join(points.geometry.rename("points"), on="valve")
    # Convert back to a GeoDataFrame, so we can do spatial ops
    closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=lines.crs)    
    # Calculate distance between the point and nearby links
    closest["snap_dist"] = closest.geometry.distance(gpd.GeoSeries(closest.points, crs=lines.crs))
    # Sort on ascending snap distance, so that closest goes to top
    closest = closest.sort_values(by=["snap_dist"])        
    # group by the index of the points and take the first, which is the closest line
    closest = closest.groupby("valve").first()        
    # construct a GeoDataFrame of the closest lines
    closest = gpd.GeoDataFrame(closest, geometry="geometry", crs=lines.crs)
    # position of nearest point from start of the line
    pos = closest.geometry.project(gpd.GeoSeries(closest.points))        
    # get new point location geometry
    snapped_lines = closest.geometry.interpolate(pos)
    closest_node = closest.geometry.project(gpd.GeoSeries(closest.points), normalize=True)
    snapped_lines = gpd.GeoDataFrame(data=closest.link,geometry=snapped_points, crs=lines.crs)
    
#    sjoin_points = points.sjoin_nearest(lines, how="left", max_distance=tolerance)
#    sjoin_points = sjoin_points.rename(columns={"name":"link"})
#    sjoin_points = gpd.GeoDataFrame(sjoin_points, geometry="geometry")
#    sjoin_points["node"] = 0
#    sjoin_points["snapped_geom"] = 0
##    for point in sjoin_points.index:
#    for point in range(90):
#        points_link = sjoin_points.loc[point].link
#        
#        pt_coord = sjoin_points.loc[point].geometry
#        link = lines.loc[lines['name'] == points_link]
#        linestring = link.geometry
#        snapped_to_line = linestring.interpolate(linestring.project(pt_coord)).values[0]
#        norm_distance = linestring.project(pt_coord, normalized=True).values[0]
#        
#        if norm_distance < 0.5:
#            sjoin_points["node"].loc[point] = link.start_node.values[0]
#        else:
#            sjoin_points["node"].loc[point] = link.end_node.values[0]
#        sjoin_points["snapped_geom"].loc[point] = snapped_to_line
#        print('point:', point, '\tnew coord: ', str(snapped_to_line), '\tdistance:', str(norm_distance))
        
        
#        sjoin_points.geometry = sjoin_points["node_geom"]
#        sjoin_points.drop(columns=["node_geom", "type", "initial_quality", "base_demand",
    
    
#        sjoin_points["link"] = sjoin_points["index_right"]
#        if find_node:    
#            sjoin_points = sjoin_points[["index_right", "start_node", "end_node", "geometry"]]
#            # find nearest node to the point (between the start and end nodes for the link)
#            for row in sjoin_points:
#                link_name = sjoin_points.loc[row]['link']
#                link = self._wn.get_link(link_name)
#                start_node_coordinate = link.start_node.coordinates
#                end_node_coordinate = link.end_node.coordinates
            
    # else:
    #     sjoin_points = sjoin_points[["index_right", "geometry"]]

#    snapped_lines = gpd.GeoDataFrame(sjoin_points, geometry="snapped_geom")
    
#        if find_node:
#            +
#            snapped_points["link_geom"] = 
#            wn_points["node_geom"] = wn_points.geometry
#            sjoin_points = points.sjoin_nearest(wn_points, how="left", max_distance=tolerance)
#            sjoin_points.geometry = sjoin_points["node_geom"]
#    #        sjoin_points.drop(columns=["node_geom", "type", "initial_quality", "base_demand",
#            sjoin_points = sjoin_points[["index_right", "geometry"]]
#            sjoin_points = sjoin_points.rename(columns={"index_right":"node"})
#            self.sjoin_points = sjoin_points
               
    return snapped_lines

def point_projection(point, line):
    distance = line.distance(point)
    point_on_line = line.interpolate(line.project(point))

    return point_on_line, distance

if __name__ == "__main__":
    # Use Net3
    import wntr
    import matplotlib.pyplot as plt
    plt.close('all')
    
    inp_file = '../../examples/networks/Net3.inp'
    wn = wntr.network.WaterNetworkModel(inp_file)
    
    # Create GIS network
    wn_gis = WaterNetworkGIS(wn)
    
#    """ Generate valves, move them slightly off the pipes, save as geojson """
#    # generate a valve layer
#    valve_layer = wntr.network.generate_valve_layer(wn)
#    
#    # adjust valves so they are moved off the pipes in random directions
#    valve_coordinates = []
#    for valve_name, (pipe_name, node_name) in valve_layer.iterrows():
#        pipe = wn.get_link(pipe_name)
#        if node_name == pipe.start_node_name:
#            start_node = pipe.start_node

#            end_node = pipe.end_node
#        elif node_name == pipe.end_node_name:
#            start_node = pipe.end_node
#            end_node = pipe.start_node
#        else:
#            print("Not valid")
#            continue
#        x0 = start_node.coordinates[0]
#        dx = end_node.coordinates[0] - x0
#        y0 = start_node.coordinates[1]
#        dy = end_node.coordinates[1] - y0
#        valve_coordinates.append((x0 + dx * 0.1 + 0.5*(np.random.random() - 0.5), y0 + dy * 0.1 + 0.5*(np.random.random() - 0.5)))
#    valve_coordinates = np.array(valve_coordinates)
#    geometry = [Point(xy) for xy in zip(valve_coordinates[:,0], valve_coordinates[:,1])]
#    off_valves = gpd.GeoDataFrame(geometry=geometry)
#    off_valves.to_file("Net3_off_valves.geojson")
    
    # Load off-centered valves from geojson
    off_valves = gpd.read_file("Net3_off_valves.geojson") # off-centered valves
    
    # Snap valves onto pipes using new function
#    wn_gis.snap_to_line(off_valves, tolerance=1.0)
    snapped_pts = snap_points_to_points(off_valves, wn_gis.junctions, 1.0)
    snapped_lines = snap_points_to_lines(off_valves, wn_gis.pipes, 1.0)
#    wn_gis.snap_to_point(off_valves, tolerance=1.0)
    
#    # Valves snapped to the nearest pipes
##    new_valves = wn_gis.snapped_point_to_line
##    new_junctions = wn_gis.snapped_point_to_point
##    sj_pts = wn_gis.sjoin_point_to_point
##    sj_pt_l = wn_gis.sjoin_point_to_line
#    
#    # Plot results    
#    ax = wn_gis.pipes.plot()
#    off_valves.plot(color="r",ax=ax)
##    new_valves.plot(color="g",ax=ax)
##    new_junctions.plot(color="k",ax=ax)
##    sj_pt_l.plot(color="y",ax=ax)
#    snapped_pts.plot(color="k",ax=ax)
#    snapped_lines.plot(color="b",ax=ax)
##    
##    wn_gis.write(prefix='Net3')
#    
##    pipes = gpd.read_file("Net3_pipes.geojson")
#    
