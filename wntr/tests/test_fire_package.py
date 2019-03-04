# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 15:45:18 2019

@author: PHassett
"""

#from nose.tools import *
import unittest.mock
from os.path import abspath, dirname, join



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
        #node = a_node
        #results = wntr.analysis.fire_node_sim(self.wn, node, fire_params)
        print (mock_fire_params)
        pass


if __name__ == '__main__':
    unittest.main()
     
    