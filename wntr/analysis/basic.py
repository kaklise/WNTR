import wntr
import pandas as pd
import matplotlib.pylab as plt
import numpy as np

def basics(wn):
    # Network plot and basic properties
    fig_x = 6.3
    fig_y = 10
    fig, ax = plt.subplots(1,1,figsize=(fig_x, fig_y))
    wntr.graphics.plot_network(wn, node_size=5, title = str(wn.inpfile_name), ax=ax)
    
    print(wn.num_junctions)
    print(wn.num_pipes)
    
    # Pipe diameter, node elevation, pipe roughness
    fig, (ax1, ax2, ax3) = plt.subplots(1,3,figsize=(fig_x*3, fig_y))
    diameter = wn.query_link_attribute('diameter')
    print ("diameter link query type:", type(diameter))
    diameter_in = pd.Series(diameter)*3.28084*12
    elevation = wn.query_node_attribute('elevation')
    print ("elevation node query type:", type(elevation))
    elevation_ft = pd.Series(elevation)*3.28084
    wntr.graphics.plot_network(wn, link_attribute=diameter_in, node_size=0, 
                               link_width=1.5, link_range=(6,36), title='Pipe diameter (inch)', ax=ax1)
    wntr.graphics.plot_network(wn, link_attribute='roughness', node_size=0, 
                               link_width=1.5, title='Pipe Roughness', ax=ax2)
    wntr.graphics.plot_network(wn, node_attribute=elevation_ft, node_size=15, 
                               title='Node elevation (ft)', node_range=(0,300), ax=ax3)
    
    # average expected demand and population
    fig, (ax1, ax2) = plt.subplots(1,2,figsize=(fig_x*2, fig_y))
    ave_expected_demand = wntr.metrics.hydraulic.average_expected_demand(wn)
    ave_expected_demand_gpm = ave_expected_demand*15850.3
    R=120*4.3813e-8
    pop = ave_expected_demand/R
    pop = pop[pop > 0]
    
    wntr.graphics.plot_network(wn, node_attribute=np.log(ave_expected_demand_gpm), 
                               node_range=[-2,6], node_size=15, title='Average expected demand (gpm, log scale)', ax=ax1)                    
    wntr.graphics.plot_network(wn, node_attribute=np.log(pop), 
                               node_range=[0,8], node_size=15, title='Population (log scale)', ax=ax2)
    
    print('Average expected demand (MGD): ', str(ave_expected_demand_gpm.sum()*24*60/1e6)) # convert to MGD
    print('Population: ', str(pop.sum()))
    
    pipe_volume = 0
    for name, pipe in wn.pipes():
        pipe_volume = pipe_volume + np.pi*pow(pipe.diameter/2,2) * pipe.length
    
    tank_volume = 0
    for name, tank in wn.tanks():
        tank_volume = tank_volume + np.pi*pow(tank.diameter/2,2) * (tank.max_level - tank.min_level)
                           
    capacity = pipe_volume + tank_volume
    print('Capacity: ', str(capacity*264.172/1e6)) # million gallons
