import wntr
from wntr.utils.libraries import DemandPatternLibrary

DPL = DemandPatternLibrary()
print(DPL.library.keys())

# Plot patterns
DPL.plot_patterns() # plot all patterns in the library
DPL.plot_patterns(names=['Net1 Pattern 1', 'Net2 Pattern 1', 'Net3 Pattern 1'])

# Create new patterns based on Net2 Pattern 1
multipliers = DPL.resample_multipliers('Net2 Pattern 1', 3*24*3600)
print(multipliers)

DPL.copy_pattern('Net2 Pattern 1', 'Net2 Pattern 1b')
DPL.library['Net2 Pattern 1b']['start_clocktime'] = 0
DPL.library['Net2 Pattern 1b']['pattern_timestep'] = 3600
multipliers = DPL.resample_multipliers('Net2 Pattern 1b', 3*24*3600)
print(multipliers)

DPL.copy_pattern('Net2 Pattern 1', 'Net2 Pattern 1c')
DPL.library['Net2 Pattern 1c']['start_clocktime'] = 0
DPL.library['Net2 Pattern 1c']['pattern_timestep'] = 3600
DPL.library['Net2 Pattern 1c']['wrap'] = False
multipliers = DPL.resample_multipliers('Net2 Pattern 1c', 3*24*3600)
print(multipliers)
DPL.plot_patterns(names=['Net2 Pattern 1b', 'Net2 Pattern 1c', 'Net2 Pattern 1'])

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
DPL.combine_patterns(['Pulse', 'Gaussian', 'Triangular'], normalize=True, name='Combined')
DPL.plot_patterns(names=['Pulse', 'Pulse_invert', 'Gaussian', 'Triangular', 'Combined'])

# Copy pattern and apply noise
DPL.copy_pattern('Gaussian', 'Gaussian_with_noise')
DPL.apply_noise('Gaussian_with_noise', 0.1, normalize=True)
DPL.plot_patterns(names=['Gaussian', 'Gaussian_with_noise'])

DPL.write_json('New_demand_pattern_library.json')

# Create a water network model
wn = wntr.network.WaterNetworkModel('networks/Net3.inp')

# Get demands associated with a junction
junction = wn.get_node('15')
print(junction.demand_timeseries_list)

# Modify the base value and pattern of the original demand
junction.demand_timeseries_list[0].base_value = 6e-5
junction.demand_timeseries_list[0].pattern_name = '1'
junction.demand_timeseries_list[0].category = 'A'

# Add a new pattern from the pattern library, then add a demand
pattern = DPL.to_Pattern('Pulse')
wn.add_pattern('Pulse', pattern)
junction.add_demand(base=5e-5, pattern_name='Pulse', category='B')
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


