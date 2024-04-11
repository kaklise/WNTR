import wntr
from wntr.library import DemandPatternLibrary

DPL = DemandPatternLibrary()
print(DPL.entry_name_list)

DPL.normalize_pattern('Net1_1')

# Plot patterns
DPL.plot_patterns() # plot all patterns in the library
DPL.plot_patterns(names=['Net1_1', 'Net2_1', 'Net3_1'])

DPL.add_combined_pattern(names=['Net1_1', 'Net2_1'], duration=3*24*3600, name='Combo_1')
DPL.plot_patterns(names=['Net1_1', 'Net2_1', 'Combo_1'])
                           
# Create new patterns based on Net2 Pattern 1
DPL.copy_pattern('Net2_1', 'Net2_1_resampled')
multipliers = DPL.resample_multipliers('Net2_1_resampled', duration=3*24*3600,
                                       pattern_timestep=7200, start_clocktime=0)

print(multipliers)
DPL.plot_patterns(names=['Net2_1', 'Net2_1_resampled'])

# Filter patterns by category
reidential_patterns = DPL.filter_by_category('Residential')
commercial_patterns = DPL.filter_by_category('Commercial')
indistrial_patterns = DPL.filter_by_category('Industrial')
none_patterns = DPL.filter_by_category(None)

# Convert to a WNTR Pattern object
pattern = DPL.to_Pattern('Constant')

# Convert to a Pandas Series and change time parameters, this could be used to 
# update the pattern or create a new pattern
series_1 = DPL.to_Series('Constant')
series_24 = DPL.to_Series('Constant', duration=24*3600)

# Add pulse, gaussian, and traingular patterns to the libary
DPL.add_pulse_pattern([3*3600,6*3600,14*3600,20*3600], normalize=True, name='Pulse')
DPL.add_pulse_pattern([3*3600,6*3600,14*3600,20*3600], invert=True, normalize=True, name='Pulse_invert')
DPL.add_gaussian_pattern(12*3600, 5*3600, normalize=True, name='Gaussian')
DPL.add_triangular_pattern(2*3600, 12*3600, 18*3600, normalize=True, name='Triangular')
DPL.add_combined_pattern(['Pulse', 'Gaussian', 'Triangular'], normalize=True, name='Combined')
DPL.plot_patterns(names=['Pulse', 'Pulse_invert', 'Gaussian', 'Triangular', 'Combined'])

# Copy pattern and apply noise
DPL.copy_pattern('Gaussian', 'Gaussian_with_noise')
DPL.apply_noise('Gaussian_with_noise', 0.1, normalize=True)
DPL.plot_patterns(names=['Gaussian', 'Gaussian_with_noise'])

DPL.write_json('New_demand_pattern_library.json')

# Create a water network model
wn = wntr.network.WaterNetworkModel('networks/Net1.inp')

# Get demands associated with a junction
junction = wn.get_node('11')
print(junction.demand_timeseries_list)

# Modify the base value and pattern of the original demand
junction.demand_timeseries_list[0].base_value = 6e-5
junction.demand_timeseries_list[0].pattern_name = '1'
junction.demand_timeseries_list[0].category = 'A'

# Add a new pattern from the pattern library, then add a demand
print(wn.options.time.pattern_timestep, wn.options.time.start_clocktime)
pattern = DPL.to_Pattern('Net2_1_resampled')
wn.add_pattern('Net2_1_resample', pattern)
junction.add_demand(base=5e-5, pattern_name='Net2_1_resample', category='B')
print(junction.demand_timeseries_list)

# Add another pattern from a list, then add a demand
wn.add_pattern('New', [1,1,1,0,0,0,1,0,0.5,0.5,0.5,1])
junction.add_demand(base=2e-5, pattern_name='New', category='C')
print(junction.demand_timeseries_list)

# Simulate hydraulics
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()

# Plot results on the network
pressure_at_5hr = results.node['pressure'].loc[5*3600, :]
wntr.graphics.plot_network(wn, node_attribute=pressure_at_5hr, node_size=30, 
                        title='Pressure at 5 hours')

print(wn.pattern_name_list)


