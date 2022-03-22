import sys
import unittest
import warnings
import os
from os.path import abspath, dirname, isfile, join

import numpy as np
import pandas as pd
import networkx as nx
import wntr
from pandas.testing import assert_frame_equal, assert_series_equal

try:
    from shapely.geometry import LineString, Point, Polygon, shape
    has_shapely = True
except ModuleNotFoundError:
    has_shapely = False

try:
    import geopandas as gpd
    has_geopandas = True
except ModuleNotFoundError:
    gpd = None
    has_geopandas = False
    
testdir = dirname(abspath(str(__file__)))
datadir = join(testdir, "networks_for_testing")
ex_datadir = join(testdir, "..", "..", "examples", "networks")


class TestGIS(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        import wntr

        self.wntr = wntr

        inp_file = join(ex_datadir, "Net1.inp")
        self.wn = self.wntr.network.WaterNetworkModel(inp_file)
        sim = wntr.sim.EpanetSimulator(self.wn)
        self.results = sim.run_sim()
        self.gis_data = self.wntr.gis.wn_to_gis(self.wn)
        
        polygon_pts = [[(25,80), (65,80), (65,60), (25,60)],
                       [(25,60), (80,60), (80,30), (25,30)],
                       [(40,50), (60,65), (60,15), (40,15)]]
        polygon_data = []
        for i, pts in enumerate(polygon_pts):
            geometry = Polygon(pts)
            polygon_data.append({'name': str(i+1), 
                                 'value': (i+1)*10,
                                 'geometry': geometry.convex_hull})
            
        df = pd.DataFrame(polygon_data)
        df.set_index("name", inplace=True)
        self.polygons = gpd.GeoDataFrame(df, crs=None)

        points = [(52,71), (75,40), (27,37)]
        point_data = []
        for i, pts in enumerate(points):
            geometry = Point(pts)
            point_data.append({'geometry': geometry})
            
        df = pd.DataFrame(point_data)
        self.points = gpd.GeoDataFrame(df, crs=None)
        
    @classmethod
    def tearDownClass(self):
        pass
    
    def test_wn_to_gis(self):
        # Check type
        isinstance(self.gis_data.junctions, gpd.GeoDataFrame)
        isinstance(self.gis_data.tanks, gpd.GeoDataFrame)
        isinstance(self.gis_data.reservoirs, gpd.GeoDataFrame)
        isinstance(self.gis_data.pipes, gpd.GeoDataFrame)
        isinstance(self.gis_data.pumps, gpd.GeoDataFrame)
        isinstance(self.gis_data.valves, gpd.GeoDataFrame)
        
        # Check size
        assert self.gis_data.junctions.shape[0] == self.wn.num_junctions
        assert self.gis_data.tanks.shape[0] == self.wn.num_tanks
        assert self.gis_data.reservoirs.shape[0] == self.wn.num_reservoirs
        assert self.gis_data.pipes.shape[0] == self.wn.num_pipes
        assert self.gis_data.pumps.shape[0] == self.wn.num_pumps
        assert self.gis_data.valves.shape[0] == self.wn.num_valves
        
        # Check minimal set of attributes
        assert set(['type', 'elevation', 'geometry']).issubset(self.gis_data.junctions.columns)
        assert set(['type', 'elevation', 'geometry']).issubset(self.gis_data.tanks.columns)
        assert set(['type', 'elevation', 'geometry']).issubset(self.gis_data.reservoirs.columns)
        assert set(['type', 'start_node_name', 'end_node_name', 'geometry']).issubset(self.gis_data.pipes.columns)
        assert set(['type', 'start_node_name', 'end_node_name', 'geometry']).issubset(self.gis_data.pumps.columns)
        #assert set(['type', 'start_node_name', 'end_node_name', 'geometry']).issubset(self.gis_data.valves.columns) # Net1 has no valves
        
    def test_gis_to_wn(self):
        
        wn2 = wntr.gis.gis_to_wn(self.gis_data)
        G1 = self.wn.get_graph()
        G2 = wn2.get_graph()
        
        assert nx.is_isomorphic(G1, G2)
                         
    def test_intersect_points_with_polygons(self):
        
        stats = wntr.gis.intersect(self.gis_data.junctions, self.polygons, 'value')
        
        # Junction 22 intersects poly2 val=20, intersects poly3 val=30
        # weighted mean = (1*20+0.5*30)/2 = 17.5
        expected = pd.Series({'intersections': ['2','3'], 'values': [20,30]})
        expected['n'] = len(expected['values'])
        expected['sum'] = float(sum(expected['values']))
        expected['min'] = float(min(expected['values']))
        expected['max'] = float(max(expected['values']))
        expected['mean'] = expected['sum']/expected['n']
        expected = expected.reindex(stats.columns)
        
        assert_series_equal(stats.loc['22',:], expected, check_dtype=False, check_names=False)
        
        # Junction 31: no intersections
        expected = pd.Series({'intersections': [], 'values': [], 'n': 0, 
                              'sum': np.nan, 'min': np.nan, 'max': np.nan,
                              'mean': np.nan, })
        
        assert_series_equal(stats.loc['31',:], expected, check_dtype=False, check_names=False)
        
    def test_intersect_lines_with_polygons(self):
        
        bv = 0
        stats = wntr.gis.intersect(self.gis_data.pipes, self.polygons, 'value', True, bv)
        print(stats)

        ax = self.polygons.plot(column='value', alpha=0.5)
        ax = wntr.graphics.plot_network(self.wn, ax=ax)
        
        # Pipe 22 intersects poly2 100%, val=20, intersects poly3 50%, val=30
        expected_weighted_mean = 20*1+30*0.5
        expected = pd.Series({'intersections': ['3','2'], 'values': [30,20], 'weighted_mean': expected_weighted_mean})
        expected['n'] = len(expected['values'])
        expected['sum'] = float(sum(expected['values']))
        expected['min'] = float(min(expected['values']))
        expected['max'] = float(max(expected['values']))
        expected['mean'] = expected['sum']/expected['n']
        expected = expected.reindex(stats.columns)
        
        assert_series_equal(stats.loc['22',:], expected, check_dtype=False, check_names=False)
        
        # Pipe 31: no intersections
        expected = pd.Series({'intersections': ['BACKGROUND'], 'values': [bv],
                              'n': 1, 'sum': bv, 'min': bv, 'max': bv,
                              'mean': bv, 'weighted_mean': bv})
        
        assert_series_equal(stats.loc['31',:], expected, check_dtype=False, check_names=False)
        
        # Pipe 122
        self.assertEqual(stats.loc['122','intersections'], ['BACKGROUND', '3', '2'])
        # total length = 30
        expected_weighted_mean = bv*(5/30) + 30*(25/30) + 20*(10/30)
        self.assertEqual(stats.loc['122','weighted_mean'], expected_weighted_mean)
        
    
    def test_intersect_polygons_with_lines(self):
        
        stats = wntr.gis.intersect(self.polygons, self.gis_data.pipes)
        
        expected = pd.DataFrame([{'intersections': ['10', '111', '11', '110', '112', '12'], 'n': 6},
                                 {'intersections': ['111', '112', '121', '21', '122', '22', '113'], 'n': 7},
                                 {'intersections': ['112', '21', '122', '22'], 'n': 4}])
        expected.index=['1', '2', '3']
        
        assert_frame_equal(stats, expected, check_dtype=False)
        
    def test_add_attributes_and_write(self):
        
        self.gis_data.add_node_attributes(self.results.node['pressure'].loc[3600,:], 'Pressure_1hr')
        self.gis_data.add_link_attributes(self.results.link['flowrate'].loc[3600,:], 'Flowrate_1hr')
       
        assert 'Pressure_1hr' in self.gis_data.junctions.columns
        assert 'Pressure_1hr' in self.gis_data.tanks.columns
        assert 'Pressure_1hr' in self.gis_data.reservoirs.columns
        assert 'Flowrate_1hr' in self.gis_data.pipes.columns
        assert 'Flowrate_1hr' in self.gis_data.pumps.columns
        assert 'Flowrate_1hr' not in self.gis_data.valves.columns # Net1 has no valves
    
    def test_write(self):
        prefix = 'temp_Net1'
        components = ['junctions', 'tanks', 'reservoirs', 'pipes', 'pumps', 'valves']
        for component in components:
            filename = abspath(join(testdir, prefix+'_'+component+'.geojson'))
            if isfile(filename):
                os.remove(filename)
            
        self.gis_data.write(prefix)

        for component in components:
            if component == 'valves':
                continue # Net1 has no valves
            filename = abspath(join(testdir, prefix+'_'+component+'.geojson'))
            self.assertTrue(isfile(filename))

    def test_snap_points_to_points(self):
        
        snapped_points = wntr.gis.snap(self.points, self.gis_data.junctions, tolerance=5.0)        
        # distance = np.sqrt(2)*2, 5, np.sqrt(2)*3
        expected = pd.DataFrame([{'node': '12', 'snap_distance': 2.23607, 'geometry': Point([50.0,70.0])},
                                 {'node': '23', 'snap_distance': 5.0,      'geometry': Point([70.0,40.0])},
                                 {'node': '21', 'snap_distance': 4.242641, 'geometry': Point([30.0,40.0])}])
        
        assert_frame_equal(pd.DataFrame(snapped_points), expected, check_dtype=False)
        

    def test_snap_points_to_lines(self):
        
        snapped_points = wntr.gis.snap(self.points, self.gis_data.pipes, tolerance=5.0)
        
        # distance = 1,5,3
        expected = pd.DataFrame([{'link': '12', 'node': '12', 'snap_distance': 1, 'line_position': 0.1, 'geometry': Point([52.0,70.0])},
                                 {'link':  '22', 'node': '23', 'snap_distance': 5.0, 'line_position': 1.0, 'geometry': Point([70.0,40.0])},
                                 {'link': '121', 'node': '21', 'snap_distance': 3.0, 'line_position': 0.1, 'geometry': Point([30.0,37.0])}])
        
        assert_frame_equal(pd.DataFrame(snapped_points), expected, check_dtype=False)

if __name__ == "__main__":
    unittest.main()