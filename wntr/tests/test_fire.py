# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 15:45:18 2019

@author: PHassett
"""

#from nose.tools import *
import unittest
import unittest.mock
from os.path import abspath, dirname, join, isfile
from os import remove

testdir = dirname(abspath(str(__file__)))
datadir = join(testdir, 'networks_for_testing')
netdir = join(testdir, '..','..','examples','networks')

class TestFireMethods(unittest.TestCase):
    def setUp(self):
        import wntr
        self.wntr = wntr
        self.wn = self.wntr.network.WaterNetworkModel(join(netdir, 'Net3.inp'))
        self.mock_fire_params = unittest.mock.Mock(fire_flow_demand = 1500,
                 fire_start = '24:00:00',
                 fire_stop = '26:00:00', 
                 p_thresh = 14.06, 
                 p_nom = 17.57,
                 demand_mult = 1
                 )
        
    def test_fire_analysis_parameters(self):
        fire_params = self.wntr.analysis.fire.fire_analysis_parameters()
        expected_params = [1500, '24:00:00', '26:00:00', 14.06, 17.57, 1] 
        params = [fire_params.fire_flow_demand, 
                  fire_params.fire_start,
                  fire_params.fire_stop, 
                  fire_params.p_thresh,
                  fire_params.p_nom,
                  fire_params.demand_mult
                  ]
        self.assertListEqual(expected_params, params, \
                        msg = 'fire parameters do not match default values.')
        
    def test_totalWSA(self):
        self.wn.options.time.duration = 129600 # 36 hrs
        sim = self.wntr.sim.WNTRSimulator(self.wn, mode = 'PDD')
        results = sim.run_sim()
        wsa = self.wntr.analysis.totalWSA(self.wn, results, 86400, 129600)
        total_demand = 0
        expected_demand = 0
        for junc in self.wn.junction_name_list:
            total_demand += sum(results.node['demand'].loc[86400:129600, junc])
            expected_demand += sum(self.wntr.metrics.expected_demand(self.wn).loc[86400:129600,junc])
        expected_wsa = total_demand/expected_demand
        self.assertAlmostEqual(expected_wsa, wsa, "WSA doesn't match expected value.")
    
    def test_PDDinitialize(self):
        self.wntr.analysis.PDDinitialize(self.wn, 129600)
        self.assertEqual(self.wn.options.time.duration, 129600)
        self.assertEqual(self.wn.options.hydraulic.demand_multiplier, 1)
        for name, node in self.wn.nodes():
            self.assertEqual(node.nominal_pressure, 17.57)
            self.assertEqual(node.minimum_pressure, 14.06)
        
    def test_fire_node_sim(self):       
        node_choice = '159' #arbitrary selection
#run fire_node_sim function
        results = self.wntr.analysis.fire_node_sim(self.wn, node_choice, self.mock_fire_params)
        pressures = results.node['pressure']
        flow = results.link['flowrate']

#initialize water network for PDD simulation            
        wn2 = self.wntr.network.WaterNetworkModel(join(netdir, 'Net3.inp'))
        wn2.options.time.duration = 26 * 3600
        wn2.options.hydraulic.demand_multiplier = 1
        node = self.wn.get_node(node_choice)
        for name, node in wn2.nodes():
            node.nominal_pressure = 17.57
            node.minimum_pressure = 14.06
            
#add firefighting demand pattern to the desired node
        fire_flow_demand = 1500 / (60*264.17) #convert from gpm to m3/s
        fire_flow_pattern = self.wntr.network.elements.Pattern.binary_pattern('fire_flow', 24*3600, 26*3600, 
                            wn2.options.time.pattern_timestep, duration = 26*3600)
        wn2.add_pattern('fire_flow', fire_flow_pattern)
        node = wn2.get_node(node_choice)
        node.add_demand(fire_flow_demand, fire_flow_pattern, category = 'fire')
    
#run sim and return results    
        sim = self.wntr.sim.WNTRSimulator(wn2, mode = 'PDD')
        expected_results = sim.run_sim(solver_options = {'MAXITER' :500})
        expected_pressures = expected_results.node['pressure']
        expected_flow = expected_results.link['flowrate']
#compare results        
        pressures = pressures.to_dict()
        expected_pressures = expected_pressures.to_dict()
        self.assertDictEqual(pressures, expected_pressures,
        "Sim pressures for fire_node_sim do not match expected values")        
        flow = flow.to_dict()
        expected_flow = expected_flow.to_dict()
        self.assertDictEqual(flow, expected_flow,
        "Sim flowrates for fire_node_sim do not match expected values")

#test exception handling        
        node_choice = '13' #invalid node name
        with self.assertRaises(Exception) as cm:
            result = self.wntr.analysis.fire_node_sim(self.wn, node_choice, self.mock_fire_params)
        self.assertEqual("The given node name is not in the wn.node_name_list.", str(cm.exception))   

    def test_fire_node_criticality(self):
        firenodes = ['15', '35', '105', '123']
#call method        
        fire_criticality_results = self.wntr.analysis.fire_node_criticality(self.wn, firenodes, self.mock_fire_params)
#replicate process
        summary = {}        
        for node_name in firenodes:
            wn = self.wntr.network.WaterNetworkModel(self.wn.inpfile_name)
#initialize water network for PDD simulation    
            wn.options.time.duration = 93600
            wn.options.hydraulic.demand_multiplier = self.mock_fire_params.demand_mult 
            for name, node in wn.nodes():
                node.nominal_pressure = self.mock_fire_params.p_nom  
                node.minimum_pressure = self.mock_fire_params.p_thresh
#add firefighting demand pattern to the desired node
            fire_flow_demand = self.mock_fire_params.fire_flow_demand / (60*264.17) #convert from gpm to m3/s
            fire_flow_pattern = self.wntr.network.elements.Pattern.binary_pattern('fire_flow',86400,\
                           93600, self.wn.options.time.pattern_timestep, duration = 93600)
            wn.add_pattern('fire_flow', fire_flow_pattern)
            nodeobj = wn.get_node(node_name)
            nodeobj.add_demand(fire_flow_demand, fire_flow_pattern, category = 'fire')
#run sim and return results    
            sim = self.wntr.sim.WNTRSimulator(wn, mode = 'PDD')
            results = sim.run_sim(solver_options = {'MAXITER' :500})
            temp = results.node['pressure'].min()
            temp = temp[temp < self.mock_fire_params.p_thresh]
            summary[node_name] = list(temp.index)
            nodeobj.demand_timeseries_list.remove_category('fire')#remove added demands    
            wn.reset_initial_values()
        fire_criticality_dict = dict()
        for node in firenodes:            
            fire_criticality_dict[node] = fire_criticality_results.get(node)[0]
#compare results 
        self.assertDictEqual(summary,fire_criticality_dict)
#assert raises exception for invalid nodes
        fire_nodes = ["13"]  #invalid node name
        with self.assertRaises(Exception) as cm:
            fire_criticality = self.wntr.analysis.fire_node_criticality(self.wn, fire_nodes, self.mock_fire_params)
        exceptmsg = "('The given node', '13', 'is not in the wn.node_name_list.')"
        self.assertEqual(exceptmsg, str(cm.exception))   
#test that exception is raised on simulation failure
        wn2 = self.wntr.network.WaterNetworkModel(join(datadir,"Net1crash.inp"))
        fire_nodes = ["10"]
        self.mock_fire_params.fire_flow_demand = 5000
        self.assertRaises(Exception, self.wntr.analysis.fire_node_criticality(wn2, 
                                fire_nodes, self.mock_fire_params, hdf_file = 'fire_criticality.hdf')) 
#test that hdf file is created
        hdf_file = join(testdir, 'fire_criticality.hdf')
        exists = isfile(hdf_file)
        self.assertTrue(exists, "fire_criticality.hdf exists is not true.")
        remove(join(testdir, 'fire_criticality.hdf'))
#assert raises exception for invalid file name        
        with self.assertRaises(Exception) as cm:
            fire_criticality = self.wntr.analysis.fire_node_criticality(wn2, 
                                fire_nodes, self.mock_fire_params, hdf_file = "fireresults")
        exceptmsg = 'The given hdf file name is invalid. Must be hdf5 compatible.'
        self.assertEqual(exceptmsg, str(cm.exception))           
        
if __name__ == '__main__':
    unittest.main()
    