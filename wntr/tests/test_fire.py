# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 15:45:18 2019

@author: PHassett
"""

#from nose.tools import *
import unittest
import unittest.mock
from os.path import abspath, dirname, join
import pandas as pd


testdir = dirname(abspath(str(__file__)))
datadir = join(testdir, 'networks_for_testing')
netdir = join(testdir, '..','..','examples','networks')

class TestFireMethods(unittest.TestCase):
    def setUp(self):
        import wntr
        self.wntr = wntr
        self.wn = self.wntr.network.WaterNetworkModel(join(netdir, 'net3.inp'))
        
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

    def test_PDDinitialize(self):
        pass
    
    def test_fire_node_sim(self):
        
        mock_fire_params = unittest.mock.Mock(fire_flow_demand = 1500,
                 fire_start = '24:00:00',
                 fire_stop = '26:00:00', 
                 p_thresh = 14.06, 
                 p_nom = 17.57,
                 demand_mult = 1
                 )        

        node_choice = '159' #arbitrary selection
#run fire_node_sim function
        results = self.wntr.analysis.fire_node_sim(self.wn, node_choice, mock_fire_params)
        pressures = results.node['pressure']
        flow = results.link['flowrate']

#initialize water network for PDD simulation            
        wn2 = self.wntr.network.WaterNetworkModel(join(netdir, 'net3.inp'))
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
            result = self.wntr.analysis.fire_node_sim(self.wn, node_choice, mock_fire_params)
        self.assertEqual("The given node name is not in the wn.node_name_list.", str(cm.exception))   

    def test_fire_node_criticality(self):
        mock_fire_params = unittest.mock.Mock(fire_flow_demand = 1500,
                 fire_start = '24:00:00',
                 fire_stop = '26:00:00', 
                 p_thresh = 14.06, 
                 p_nom = 17.57,
                 demand_mult = 1
                 )        
        
        pass
        
        
        
if __name__ == '__main__':
    unittest.main()
     
    