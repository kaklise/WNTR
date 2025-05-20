"""
The wntr.stormwater.io module contains methods to 
read and write stormwater and wastewater network models.
"""
import logging
import pandas as pd
import networkx as nx

try:
    import epaswmm.output
    import swmmio
    has_swmm = True
except ModuleNotFoundError:
    has_swmm = False

from wntr.sim import SimulationResults
from wntr.extensions.stormwater.gis import StormWaterNetworkGIS
import wntr.extensions.stormwater

logger = logging.getLogger(__name__)


def to_graph(swn, node_weight=None, link_weight=None, modify_direction=False):
    """
    Convert a StormWaterNetworkModel into a NetworkX MultiDiGraph
    
    Parameters
    ----------
    swn : StormWaterNetworkModel
        Storm water network model
    node_weight :  dict or pandas Series (optional)
        Node weights
    link_weight : dict or pandas Series (optional)
        Link weights
    modify_direction : bool (optional)
        If True, then if the link weight is negative, the link start and 
        end node are switched and the abs(weight) is assigned to the link
        (this is useful when weighting graphs by flowrate). If False, link 
        direction and weight are not changed.
         
    Returns
    -------
    NetworkX MultiDiGraph
    
    """
    # Note, this function could use "G = swn._swmmio_model.network" but that would 
    # require an additional write/read of the inp file to capture model 
    # updates
    
    G = nx.MultiDiGraph()

    for name in swn.node_name_list:
        node = swn.get_node(name)
        G.add_node(name)
        coords = (swn.coordinates.loc[name, 'X'], swn.coordinates.loc[name, 'Y'])
        nx.set_node_attributes(G, name="pos", values={name: coords})
        nx.set_node_attributes(G, name="type", values={name: node.node_type})

        if node_weight is not None:
            try:  # weight nodes
                value = node_weight[name]
                nx.set_node_attributes(G, name="weight", values={name: value})
            except:
                pass

    for name in swn.link_name_list:
        link = swn.get_link(name)
        start_node = link.start_node_name
        end_node = link.end_node_name
        G.add_edge(start_node, end_node, key=name)
        nx.set_edge_attributes(G, name="type", values={(start_node, end_node, name): link.link_type})

        if link_weight is not None:
            try:  # weight links
                value = link_weight[name]
                if modify_direction and value < 0:  # change the direction of the link and value
                    G.remove_edge(start_node, end_node, name)
                    G.add_edge(end_node, start_node, name)
                    nx.set_edge_attributes(G, name="type", values={(end_node, start_node, name): link.link_type})
                    nx.set_edge_attributes(G, name="weight", values={(end_node, start_node, name): -value})
                else:
                    nx.set_edge_attributes(G, name="weight", values={(start_node, end_node, name): value})
            except:
                pass
    
    return G

def to_gis(swn, crs=None):
    """
    Convert a StormWaterNetworkModel into GeoDataFrames
    
    Parameters
    ----------
    swn : WaterNetworkModel
        Water network model
    crs : str, optional
        Coordinate reference system, by default None

    Returns
    -------
    StormWaterNetworkGIS object that contains GeoDataFrames
        
    """
    # Create geodataframes
    gis_data = StormWaterNetworkGIS()
    gis_data._create_gis(swn, crs)
    return gis_data

def write_inpfile(swn, filename):
    """
    Write the StormWaterNetworkModel to an EPANET INP file
    
    Parameters
    ----------
    swn : WaterNetworkModel
        Water network model
    filename : string
       Name of the inp file
    
    """
    for sec in swn.section_names:
        df = getattr(swn, sec)
        setattr(swn._swmmio_model.inp, sec, df)
            
    swn._swmmio_model.inp.save(filename)

def read_inpfile(filename):
    """
    Create a StormWaterNetworkModel from an SWMM INP file
    
    Parameters
    ----------
    filename : string
       Name of the inp file
       
    Returns
    -------
    StormWaterNetworkModel
    
    """
    swn = wntr.stormwater.network.StormWaterNetworkModel(filename)

    return swn

def read_rptfile(filename):
    """
    Read a SWMM summary report file
    
    Parameters
    ----------
    filename : string
       Name of the SWMM summary report file
    
    Returns
    -------
    dict
    
    """
    if not has_swmm:
        raise ModuleNotFoundError('swmmio is required')
        
    report = {}
    
    rpt_sections = swmmio.utils.text.get_rpt_sections_details(filename)
    
    for section in rpt_sections: 
        try:
            data = swmmio.utils.dataframes.dataframe_from_rpt(filename, section)
            if data.shape[0] > 0:
                section_name = section.upper().replace(' ', '_')
                report[section_name] = data
        except:
            pass

    return report

def read_outfile(filename):
    """
    Read a SWMM binary output file

    Parameters
    ----------
    filename : string
       Name of the SWMM binary output file
    
    Returns
    -------
    SimulationResults
    
    """
    if not has_swmm:
        raise ModuleNotFoundError('epaswmm is required')
    
    results = SimulationResults()
    
    # Node results = INVERT_DEPTH, HYDRAULIC_HEAD, PONDED_VOLUME, 
    # LATERAL_INFLOW, TOTAL_INFLOW, FLOODING_LOSSES, POLLUT_CONC_0
    results.node = {}
    
    # Link results = FLOW_RATE, FLOW_DEPTH, FLOW_VELOCITY, FLOW_VOLUME, 
    # CAPACITY, POLLUT_CONC_0
    results.link = {}
    
    # Subcatchment results = RAINFALL, SNOW_DEPTH, EVAP_LOSS, INFIL_LOSS, 
    # RUNOFF_RATE, GW_OUTFLOW_RATE, GW_TABLE_ELEV, SOIL_MOISTURE, 
    # POLLUT_CONC_0
    results.subcatchment = {}
    
    # System results = AIR_TEMP, RAINFALL, SNOW_DEPTH, EVAP_INFIL_LOSS, 
    # RUNOFF_FLOW, DRY_WEATHER_INFLOW, GW_INFLOW, RDII_INFLOW, DIRECT_INFLOW,
    # TOTAL_LATERAL_INFLOW, FLOOD_LOSSES, OUTFALL_FLOWS, VOLUME_STORED, 
    # EVAP_RATE
    results.system = {}
    
    swmm_output = epaswmm.output.Output(output_file=filename)
    times = swmm_output.times
    
    for attribute in epaswmm.output.NodeAttribute:
        temp = {}
        for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.NODE):
            ts = swmm_output.get_node_timeseries(element_index=name, attribute=attribute)
            temp[name] = ts.values()
        results.node[attribute.name] = pd.DataFrame(data=temp, index=times)
        
    for attribute in epaswmm.output.LinkAttribute:
        temp = {}
        for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.LINK):
            ts = swmm_output.get_link_timeseries(element_index=name, attribute=attribute)
            temp[name] = ts.values()
        results.link[attribute.name] = pd.DataFrame(data=temp, index=times)
        
    for attribute in epaswmm.output.SubcatchAttribute:
        temp = {}
        for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.SUBCATCHMENT):
            ts = swmm_output.get_subcatchment_timeseries(element_index=name, attribute=attribute)
            temp[name] = ts.values()
        results.subcatchment[attribute.name] = pd.DataFrame(data=temp, index=times)
    
    #temp = {}
    for attribute in epaswmm.output.SystemAttribute:
        ts = swmm_output.get_system_timeseries(attribute=attribute)
        #temp[attribute.name] = ts.values()
        results.system[attribute.name] = pd.Series(data=ts.values(), index=times)
    
    return results

def write_geojson(swn, prefix: str, crs=None):
    """
    Write the StormWaterNetworkModel to a set of GeoJSON files, one file for each
    network element.

    Parameters
    ----------
    swn : wntr StormWaterNetworkModel
        Storm water network model
    prefix : str
        File prefix
    crs : str, optional
        Coordinate reference system, by default None
        
    """
    swn_gis = swn.to_gis(crs)
    swn_gis.write_geojson(prefix=prefix)
