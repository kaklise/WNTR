# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 10:34:50 2019

@author: PHassett
"""
import os
import json
import jinja2
import wntr
from wntr.epanet import FlowUnits


def inp_to_gjson(wn, to_file=False):
    """
    Write a minimal geojson representation of the Water Network.

    Parameters
    ----------
    wn: wntr WaterNetworkModel object
        The network to be make the geojson from
    to_file: Boolean, default=False
        To save the geojson links and nodes as files in the directory of the
        inp file
    Returns
    -------
    geojson_nodes, geojson_links: dict in geojson format
        geojson spatial representation of the WN nodes and links, respectively.
    """
    inp_path = os.path.abspath(wn.name)
    # Translate the nodes to geojson.
    geojson_nodes = {"type": "FeatureColllection",
                     "features": []
                     }
    for name, node in wn.nodes():
        feature = {"type": "Feature",
                   "geometry": {"type": "Point",
                                "coordinates": list(node.coordinates)
                                },
                   "id": name,
                   "properties": {"ID": name,
                                  }
                   }
        if node.node_type == 'Junction':
            feature['properties']["Base Demand (gpm)"] = node.base_demand/FlowUnits.GPM.factor
        else:
            feature['properties']["Base Demand (gpm)"] = node.node_type
        geojson_nodes["features"].append(feature)
    # Translate the links to geojson.
    geojson_links = {"type": "FeatureColllection", "features": []}
    for name, link in wn.links():
        link = wn.get_link(link)
        start = list(link.start_node.coordinates)
        end = list(link.end_node.coordinates)
        feature = {"type": "Feature",
                   "geometry": {"type": "LineString",
                                "coordinates": [start, end]
                                },
                   "id": name,
                   "properties": {"ID": name
                                  }
                   }
        link_type = link.link_type
        if link_type == 'Pump':
            feature['properties']["Pipe Diameter (in)"] = "Pump"
        else:
            feature['properties']["Pipe Diameter (in)"] = round(link.diameter * 39.3701)
        geojson_links["features"].append(feature)
    if to_file:
        # Write out the network to the file.
        json_nodesfile = inp_path.split('.inp')[0] + '_nodes.json'
        with open(json_nodesfile, 'w') as fp:
            json.dump(geojson_nodes, fp)
        json_linksfile = inp_path.split('.inp')[0] + '_links.json'
        with open(json_linksfile, 'w') as fp:
            json.dump(geojson_links, fp)
    return geojson_nodes, geojson_links


def create_leaflet_map(latlong, wn_nodes, wn_links, output='./wn_map.html'):
    '''
    Create a leaflet map of the water network from a geojson representation.

    **Note** This function relies on a jinja2 html template file titled
    "simple_wn_map_template.html" in the same dir as this script.

    jinja2 interaction based on example at:
    https://gist.github.com/wrunk/1317933/d204be62e6001ea21e99ca0a90594200ade2511e

    Parameters
    ----------

    latlong: list
            latitude, longitude of the center of the map

    wn_nodes: dict in geojson format
            A geojson Feature Collection of geometry type Points with a
            "properties" attribute with fields "ID" and "Base Demand (gpm)"

    wn_links: dict in geojson format
            A geojson Feature Collection of geometry type LineString with a
            "properties" attribute with fields "ID" and "Pipe Diameter (in)"

    output: str/path-like object
            output path for the .html file

    '''
    # Capture our current directory.
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(THIS_DIR),
                                trim_blocks=True)

    with open(output, 'w') as fp:
        fp.write(j2_env.get_template('simple_wn_map_template.html').render(
                latlong=latlong,
                nodes_geojson=wn_nodes,
                links_geojson=wn_links)
        )


if __name__ == '__main__':
    # Load the inp file.
    try:
        wn = wntr.network.WaterNetworkModel("../../networks/Net3.inp")
    except FileNotFoundError:
        wn = wntr.network.WaterNetworkModel("../networks/Net3.inp")
    # Morph the WN coordinates based on two known reference points.
    longlat_map = {'Lake': (-106.6851, 35.1344), '219': (-106.5073, 35.0713)}
    wn2 = wntr.morph.convert_node_coordinates_to_longlat(wn, longlat_map)
    # Get the geojson representations of the water network.
    wn_nodes, wn_links = inp_to_gjson(wn2)
    # Chose a point for the center of the map.
    # Note the reversed order of the coordinates to [lat, long].
    center = [35.08, -106.6]
    # Specify an output path/file name
    output_path = '../net3_map.html'
    # Make the map!
    create_leaflet_map(center, wn_nodes, wn_links, output=output_path)
