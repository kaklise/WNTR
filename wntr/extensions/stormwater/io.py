"""
The wntr.stormwater.io module contains methods to 
read and write stormwater and wastewater network models.
"""
import logging
import pandas as pd
import networkx as nx
import numpy as np

try:
    from openswmm.engine import OutputReader, OutNodeVar, OutLinkVar, OutSubcatchVar, OutSystemVar
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
    
    # Fix to read version number from an OPENSWMM RPT file
    with open(filename, 'r') as file:
        data = file.read()
    data = data.replace("OPENSWMM ENGINE - VERSION", 
                        "STORM WATER MANAGEMENT MODEL - VERSION")
    with open(filename, 'w') as file:
        file.write(data)       
            
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
        raise ModuleNotFoundError('openswmm.engine is required')
    
    results = SimulationResults()
    
    # Node results = DEPTH, HEAD, VOLUME, 
    # LATERAL_INFLOW, TOTAL_INFLOW, OVERFLOW , POLLUT_BASE
    results.node = {}
    
    # Link results = FLOW, DEPTH, VELOCITY, VOLUME, 
    # CAPACITY, POLLUT_BASE
    results.link = {}
    
    # Subcatchment results = RAINFALL, SNOW_DEPTH, EVAP, INFIL, 
    # RUNOFF, GW_FLOW, GW_ELEV , SOIL_MOIST, POLLUT_BASE
    results.subcatchment = {}
    
    # System results = TEMPERATURE, RAINFALL, SNOW_DEPTH, EVAP, INFIL, RUNOFF,
    # DW_INFLOW, GW_INFLOW, LAT_INFLOW, FLOODING, OUTFLOW, STORAGE, 
    # EVAP_TOTAL, PET
    results.system = {}
    
    with OutputReader(filename) as out:
        
        T = out.get_period_count()
        N = out.get_node_count()
        L = out.get_link_count()
        S = out.get_subcatch_count()
        
        node_name_list = [out.get_node_id(i) for i in range(N)]
        link_name_list = [out.get_link_id(i) for i in range(L)]
        subcatchment_name_list = [out.get_subcatch_id(i) for i in range(S)]
        
        start_date = out.get_start_date() # start date as a Julian date value
        report_step = out.get_report_step() # time step in seconds
        timesteps = [i*report_step for i in range(T)]
        timesteps = pd.to_datetime(timesteps, unit='s')
        
        # Node attributes
        for attribute in OutNodeVar:
            temp = np.empty((T, N), dtype=np.float32)
            for t in range(T):
                try:
                    temp[t] = out.get_node_result(t, attribute)
                except:
                    pass
            df = pd.DataFrame(data=temp, columns=node_name_list, index=timesteps)
            results.node[attribute.name] = df
        
        # Link attributes
        for attribute in OutLinkVar:
            temp = np.empty((T, L), dtype=np.float32)
            for t in range(T):
                try:
                    temp[t] = out.get_link_result(t, attribute)
                except:
                    pass
            df = pd.DataFrame(data=temp, columns=link_name_list, index=timesteps)
            results.link[attribute.name] = df
        
        # Subcatchment attributes
        for attribute in OutSubcatchVar:
            temp = np.empty((T, S), dtype=np.float32)
            for t in range(T):
                try:
                    temp[t] = out.get_subcatch_result(t, attribute)
                except:
                    pass
            df = pd.DataFrame(data=temp, columns=subcatchment_name_list, index=timesteps)
            results.subcatchment[attribute.name] = df
        
        # System attributes
        for attribute in OutSystemVar:
            temp = np.empty((T), dtype=np.float32)
            for t in range(T):
                try:
                    temp[t] = out.get_system_result(t, attribute)
                except:
                    pass
            df = pd.Series(data=temp, index=timesteps)
            results.system[attribute.name] = df


    # swmm_output = epaswmm.output.Output(output_file=filename)
    # times = swmm_output.times
    
    # for attribute in epaswmm.output.NodeAttribute:
    #     temp = {}
    #     for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.NODE):
    #         ts = swmm_output.get_node_timeseries(element_index=name, attribute=attribute)
    #         temp[name] = ts.values()
    #     results.node[attribute.name] = pd.DataFrame(data=temp, index=times)
        
    # for attribute in epaswmm.output.LinkAttribute:
    #     temp = {}
    #     for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.LINK):
    #         ts = swmm_output.get_link_timeseries(element_index=name, attribute=attribute)
    #         temp[name] = ts.values()
    #     results.link[attribute.name] = pd.DataFrame(data=temp, index=times)
        
    # for attribute in epaswmm.output.SubcatchAttribute:
    #     temp = {}
    #     for name in swmm_output.get_element_names(element_type=epaswmm.output.ElementType.SUBCATCHMENT):
    #         ts = swmm_output.get_subcatchment_timeseries(element_index=name, attribute=attribute)
    #         temp[name] = ts.values()
    #     results.subcatchment[attribute.name] = pd.DataFrame(data=temp, index=times)
    
    # #temp = {}
    # for attribute in epaswmm.output.SystemAttribute:
    #     ts = swmm_output.get_system_timeseries(attribute=attribute)
    #     #temp[attribute.name] = ts.values()
    #     results.system[attribute.name] = pd.Series(data=ts.values(), index=times)

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
