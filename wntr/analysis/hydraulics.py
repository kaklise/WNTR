import wntr
import numpy as np
import pandas as pd



def pipe_criticality(wn, min_diameter_in, pressure_threshold = 14.06, nominal_pressure = 17.57, start_time = "24:00:00", end_time = "72:00:00",\
    demand_multiplier = 1.):
#initialize water network for PDD simulation    
    wn.options.time.duration = _parse_value(end_time)
    wn.options.hydraulic.demand_multiplier = demand_multiplier 
    for name, node in wn.nodes():
        node.nominal_pressure = nominal_pressure  
        
#collect list of pipes above diameter threshold        
    critical_pipes = wn.query_link_attribute('diameter', np.greater_equal, min_diameter_in*0.0254, link_type=wntr.network.model.Pipe)    
    critical_pipes = list(critical_pipes.keys())
#perform initial simulation with no changes to the network
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
    results = sim.run_sim()
    temp = results.node['pressure'].min()
    temp = temp[temp < pressure_threshold]
    summary = {}
    summary['Original'] = list(temp.index)

    #print("wn.inpfile_name:  ", wn.inpfile_name)
    inp_file = wn.inpfile_name

#perform analysis for each critical pipe and save nodes with pressure below threshold in summary dict
    for pipe_name in critical_pipes:
        wn = wntr.network.WaterNetworkModel(inp_file)
        print(pipe_name)
        try:
            pipe = wn.get_link(pipe_name)
        
            act = wntr.network.controls.ControlAction(pipe, 'status', wntr.network.LinkStatus.Closed)
            cond = wntr.network.controls.SimTimeCondition(wn, '=', start_time)
            ctrl = wntr.network.controls.Control(cond, act)
            wn.add_control('close pipe ' + pipe_name, ctrl)
          
            sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
            results = sim.run_sim(solver_options={'MAXITER':500})

            temp = results.node['pressure'].min()
            temp = temp[temp < pressure_threshold]
            #print ("temp", temp)
            summary[pipe_name] = list(temp.index) 
            #print ("summary element", summary[pipe_name])
            
            wn._discard_control('close pipe ' + pipe_name)
            wn.reset_initial_values()
        except Exception as e:
            summary[pipe_name] = e
            print('   Failed')
            
#extract original case results for comparison    
    orig = summary['Original']
    del summary['Original']
#extract population and number of nodes impacted. record failed sims
    pop = wntr.metrics.population(wn)
    summary_len = {}
    summary_pop = {}
    failed_sim = {}
    for key, val in summary.items():
        if type(val) is list:
            summary[key] = list(set(val) - set(orig))
            summary_len[key] = len(set(val) - set(orig))
            summary_pop[key] = 0
            for node in summary[key]:
                summary_pop[key] = summary_pop[key] + pop[node]                
        else:
            failed_sim[key] = val
    print ("Original: \n", orig)
    print ("summary_len: \n", summary_len)
    print ("summary_pop: \n", summary_pop)
    print ("failed_sim: \n", failed_sim)

#generate and save graphics 
    cmap = wntr.graphics.color.custom_colormap(numcolors=2, colors=['gray','gray'], name='custom')
    fig_x = 6.3
    fig_y = 10
    fig, ax = plt.subplots(1,1,figsize=(fig_x, fig_y))
    
    wntr.graphics.plot_network(wn, link_attribute='length', node_size=0, link_cmap=cmap, add_colorbar=False, ax=ax)
    wntr.graphics.plot_network(wn, link_attribute=summary_len, node_size=0, link_width=2,title='Number of nodes impacted by low pressure conditions\nfor each pipe closure', ax=ax)
    plt.savefig('nodes_impacted.png')
    
    fig, ax = plt.subplots(1,1,figsize=(fig_x, fig_y))
    wntr.graphics.plot_network(wn, link_attribute='length', node_size=0, link_cmap=cmap, add_colorbar=False, ax=ax)
    wntr.graphics.plot_network(wn, link_attribute=summary_pop, node_size=0, link_width=2,title='Number of people impacted by low pressure conditions\nfor each pipe closure', ax=ax)
    plt.savefig('pop_impacted.png')
    return summary

def connectivity(wn, hdf_file = "hydraulic_connectivity.hdf"):
# Simulate hydraulics and save hyd file
    sim = wntr.sim.EpanetSimulator(wn)
    sim.run_sim(save_hyd = True)
# Simulate WQ trace for all nodes    
    for name in wn.junction_name_list:
        print(name)
        wn.options.quality.mode = 'TRACE'
        wn.options.quality.trace_node = name
        results = sim.run_sim(use_hyd = True)
        qual = results.node['quality']
        qual.to_hdf(hdf_file, "trace_junction" + str(name), mode = 'a')
        
    return "success"
    