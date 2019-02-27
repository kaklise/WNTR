# -*- coding: utf-8 -*-
"""
Created on Mon Feb 11 15:47:29 2019

@author: PHassett
"""

import wntr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class fire_analysis(object):
    """
    fire_sim class
    
    Parameters
    ----------
    wn - water network model object
    
    

    """
    def __init__(self, fire_flow_demand = 1500, fire_start = '24:00:00', fire_stop = '26:00:00',\
    p_thresh = 14.06, p_nom = 17.57, demand_mult = 1):
        self.fire_flow_demand = fire_flow_demand
        self.fire_start = fire_start
        self.fire_stop = fire_stop
        self.p_thresh = p_thresh
        self.p_nom = p_nom
        self.demand_mult = demand_mult
      
def _parse_value(value):
    try:
        v = float(value)
        return v
    except ValueError:
        value = value.upper()
        if value == 'CLOSED':
            return 0
        if value == 'OPEN':
            return 1
        if value == 'ACTIVE':
            return np.nan
        PM = 0
        words = value.split()
        if len(words) > 1:
            if words[1] == 'PM':
                PM = 86400 / 2
        hms = words[0].split(':')
        v = 0
        if len(hms) > 2:
            v += int(hms[2])
        if len(hms) > 1:
            v += int(hms[1])*60
        if len(hms) > 0:
            v += int(hms[0])*3600
        if int(hms[0]) <= 12:
            v += PM
        return v

def totalWSA(wn, results, start, stop):
#calculate total demand for all junctions over the requested time period
    demand = 0 
    for junc in wn.junction_name_list:
        demand += sum(results.node['demand'].loc[_parse_value(start):_parse_value(stop),junc])
    print("actual demand\n", demand )
#calculate total expected demand for all junctions over the requested time period
    exp_demand = sum(wntr.metrics.expected_demand(wn).loc[_parse_value(start):_parse_value(stop),:].sum())
    print("expected demand\n", exp_demand )
#calculate total WSA
    total_wsa = demand/exp_demand
    print("Total WSA:\n", total_wsa)
#return total WSA
    return total_wsa

def PDDinitialize(wn, duration, p_thresh = 14.06, nom_press = 17.57, demand_mult = 1):
#initialize water network for PDD simulation    
    wn.options.time.duration = _parse_value(duration)
    wn.options.hydraulic.demand_multiplier = demand_mult 
    for name, node in wn.nodes():
        node.nominal_pressure = nom_press  
        node.minimum_pressure = p_thresh

def fire_node_sim(wn, node_name, fire_parameters):

#initialize water network for PDD simulation   
    PDDinitialize(wn, fire_parameters.fire_stop, p_thresh = fire_parameters.p_thresh, \
    nom_press = fire_parameters.p_nom, demand_mult = fire_parameters.demand_mult)

#add firefighting demand pattern to the desired node
    fire_flow_demand = fire_parameters.fire_flow_demand / (60*264.17) #convert from gpm to m3/s
    fire_flow_pattern = wntr.network.elements.Pattern.binary_pattern('fire_flow',_parse_value(fire_parameters.fire_start),\
    _parse_value(fire_parameters.fire_stop), wn.options.time.pattern_timestep, duration = _parse_value(fire_parameters.fire_stop))
    wn.add_pattern('fire_flow', fire_flow_pattern)
    node = wn.get_node(node_name)
    node.add_demand(fire_flow_demand, fire_flow_pattern, category = 'fire')
    
#run sim and return results    
    sim = wntr.sim.WNTRSimulator(wn, mode = 'PDD')
    results = sim.run_sim(solver_options = {'MAXITER' :500})

    return results
            
def fire_node_criticality(wn, fire_nodes, fire_parameters, hdf_output = False, hdf_file = "fire_criticality.hdf"):

    summary = {}
#run sim for all fire nodes and record results
    for node_name in fire_nodes:
        wn = wntr.network.WaterNetworkModel(wn.inpfile_name)
        try:
            fire_sim = fire_node_sim(wn, node_name, fire_parameters)    
            temp = fire_sim.node['pressure'].min()
            temp = temp[temp < fire_parameters.p_thresh]
            if hdf_output:
                temp.to_hdf(hdf_file, "node"+str(node_name)+"fire_criticality", mode = 'a')
            summary[node_name] = [list(temp.index), totalWSA(wn, fire_sim)]
        except Exception as e:
            temp = e
            if hdf_output:
                temp ={node_name : temp}
                temp.to_hdf(hdf_file, "node"+str(node_name)+"fire_criticality", mode = 'a')
            summary[node_name] = e
            print(' failed')
        node = wn.get_node(node_name)
        node.demand_timeseries_list.remove_category('fire')#remove added demands    
        wn.reset_initial_values()
    
    return summary
    
    