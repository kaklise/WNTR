import wntr
from wntr.sim.solvers import PyomoSolver

# Create a water network model
inp_file = 'networks/Net1.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.hydraulic.demand_model = 'DD' # DD or PDD

# Create a WNTR steady state algebraic hydaulic model (this methods is used within the WNTRSimulator) 
model, updater = wntr.sim.hydraulics.create_hydraulic_model(wn, HW_approx='piecewise')
# Extract the jacobian and residuals
model.set_structure()
r = model.evaluate_residuals(labeled=True)
J = model.evaluate_jacobian(labeled=True)
print(J)
print()
print(r)

# Create a Pyomo steady state algebraic hydaulic model
pyomo_model, pyomo_map = wntr.sim.hydraulics.convert_hydraulic_model_to_pyomo(model)
print(pyomo_model.pprint())


### Compare the Newton and Pyomo Solvers

# Solve using the NewtonSolver
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.time.duration = 24*3600
sim = wntr.sim.WNTRSimulator(wn)
results1 = sim.run_sim(HW_approx=HW_approx) # solver defaults to NewtonSolver

# Solve using Pyomo and ipopt (PyomoSolver)
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.time.duration = 24*3600
sim = wntr.sim.WNTRSimulator(wn)
results2 = sim.run_sim(HW_approx=HW_approx, solver=PyomoSolver, solver_options={'tee': False})

# Compare results
head_sim = results1.node['head'].loc[6*3600, wn.junction_name_list]
flow_sim = results1.link['flowrate'].loc[6*3600,:]
wntr.graphics.plot_network(wn, head_sim, flow_sim, title='NewtonSolver')

head_opt = results2.node['head'].loc[6*3600, wn.junction_name_list]
flow_opt = results2.link['flowrate'].loc[6*3600,:]
wntr.graphics.plot_network(wn, head_opt, flow_opt, title='PyomoSolver')

results1.node['head'].plot(title='NewtonSolver')
results2.node['head'].plot(title='PyomoSolver')

results1.link['flowrate'].plot(title='NewtonSolver')
results2.link['flowrate'].plot(title='PyomoSolver')
