#! /usr/bin/python3

import argparse
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import geopandas as gpd
from shapely.geometry import LineString

# Create possible command line arguments
parser = argparse.ArgumentParser(description='build a vectorized drainage network from LSDTopoTools outputs, divided at tributary junctions.')
parser.add_argument("file_input", help="LSDTopoTools csv output used to build the drainage network", type=str)
parser.add_argument("file_output", help="Filename for the output geopackage", type=str)
parser.add_argument("--chi", "-c", action="store_true", help="include chi in the output geodatabase")
parser.add_argument("--drainage_area", "-da", action="store_true", help="include drainage area in the output geodatabase")
parser.add_argument("--elevation", "-e", action="store_true", help="include average, minimum, and maximum elevation in the output geodatabase")
parser.add_argument("--slope", "-s", action="store_true", help="include slope in the output geodatabase")

# Parse file input and output names.
# If the output file isn't specified as a geopackage, add the .gpkg file extension
# TODO: More verification to make sure input and output filenames are valid
# TODO: Provide the user with the option to output a single file with both the information in the output and segs_select.gkpg

args = parser.parse_args()
file_input = args.file_input
file_output = args.file_output
if file_output[-5:] != '.gpkg':
    file_output += '.gpkg'

# Read the LSDTopoTools river chi profile inputs, indexing by the 
# node index
rp = pd.read_csv(file_input, index_col='NI', na_filter=False)
# The "source key" sets the ID for each segment -- section of channel between
# tributary junctions.
segment_ids = np.array(list(set(rp['source_key'])))

# Get the source key for all receiver nodes
# This will show the upstream limit(s) of confluences, and provide the
# node IDs of these confluences.
receiver_nodes_at_mouths = []
rp.insert(len(rp.columns), 'receiver_source_key', None)
#for _node in rp.index:
# IMPORTANT FOR EFFICIENCY: MINIMIZE THE NUMBER OF TIMES YOU UPDATE THE
# DATAFRAME

_tmplist = []
for _node in rp.index:
    _receiver_node = rp.loc[_node, 'receiver_NI']
    if _receiver_node in rp.index and _node != _receiver_node:
        _receiver_source_key = rp.loc[_receiver_node, 'source_key']
    else:
        print("Found mouth node. Offmap receiver node ID: "
                + str(_receiver_node))
        _receiver_source_key = -1
        receiver_nodes_at_mouths.append(_receiver_node)
    _tmplist.append(_receiver_source_key)
rp['receiver_source_key'] = _tmplist

# In the case of the downstream-most one, no node with this ID will exist
mouth_nodes = list(rp[rp['receiver_source_key'] == -1].index)

# Next, identify these confluences by places where the receiver_source_key
# differs from the source_key
confluence_downstream_nodes = list(set(list(rp['receiver_NI']
                                                  [rp['source_key'] !=
                                                  rp['receiver_source_key']])))
# Remove river mouths
# Inefficient but should be relatively few points at this step.
confluence_downstream_nodes = np.array(confluence_downstream_nodes)
for _receiver_node_at_mouth in receiver_nodes_at_mouths:
    confluence_downstream_nodes = confluence_downstream_nodes\
                                    [confluence_downstream_nodes
                                     != _receiver_node_at_mouth]

# Create a set of confluence locations
confluences = []
for _node in confluence_downstream_nodes:
    _x = rp.loc[_node, 'longitude']
    _y = rp.loc[_node, 'latitude']
    confluences.append([_x, _y])
confluences = np.array(confluences)

# Create a set of river mouth locations
mouths = []
for _node in mouth_nodes:
    _x = rp.loc[_node, 'longitude']
    _y = rp.loc[_node, 'latitude']
    mouths.append([_x, _y])
mouths = np.array(mouths)

# Obtain channel-head locations
# They are in another file, but whatever.... reduce data dependencies
channel_head_nodes = []
source_keys = list(set(list(rp['source_key'])))
for _source_key in source_keys:
    channel_head_nodes.append( rp.index[rp['source_key'] == _source_key][0] )
channel_head_nodes = np.array(channel_head_nodes)

# Create a list of segment sources
# This includes all channel heads (true "sources") and confluences
source_nodes = np.hstack(( channel_head_nodes, confluence_downstream_nodes ))

# Create a list of segment terminations
# This includes all confluence and mouth nodes
termination_nodes = np.hstack(( confluence_downstream_nodes, mouth_nodes ))

# Create a list of lists of node IDs going down each segment in the network
# Each segment will include as its downstream-most cell the upstream-most
# node from the next tributary junction.
# This is duplicitive, but helpful for network dynamics and plotting
# line segments that represent the river attributes.
segments_nodes = []
for _source_node in source_nodes:
    segment_nodes = [_source_node]
    segment_nodes.append(rp.loc[segment_nodes[-1], 'receiver_NI'])
    while segment_nodes[-1] not in termination_nodes:
        segment_nodes.append(rp.loc[segment_nodes[-1], 'receiver_NI'])
    segments_nodes.append(segment_nodes)

# Next, reconstruct the data table elements for each of these points
# within its specific segment in the network
segments = []
for segment_nodes in segments_nodes:
    segments.append( rp.loc[segment_nodes, :] )

# Apply an arbitrary ID in order
_id = 0
segment_ids = []
for segment in segments:
    segment_ids.append(_id)
    segment['segment_id'] = _id
    _id += 1
segment_ids = np.array(segment_ids)

# Obtain correlative ID numbers from the source nodes
internal_segment_ids = []
for segment in segments:
    internal_segment_ids.append(segment.index[0])
internal_segment_ids = np.array(internal_segment_ids)

# Also record which segment they send their flow to
internal_receiver_segment_ids = []
for segment in segments:
    internal_receiver_segment_ids.append( segment.index[-1] )
internal_receiver_segment_ids = np.array(internal_receiver_segment_ids)

# To-segment IDs
toseg = []
for i in range(len(internal_segment_ids)):
    toseg_bool = (internal_receiver_segment_ids[i] == internal_segment_ids)
    if np.sum(toseg_bool) > 1:
        print(i)
        print(np.sum(toseg_bool))
        print("ERROR! NETWORK IS BRANCHING.")
    elif np.sum(toseg_bool) == 0:
        print(i)
        print(np.sum(toseg_bool))
        print("Channel mouth; segment ID -1.")
        toseg.append(-1)
    else:
        toseg.append(int(segment_ids[toseg_bool]))
toseg = np.array(toseg)

# Unnecessary, but why not? Makes life easier.
# Especially once I use these to create the nodes!
for i in range(len(segments)):
    segment = segments[i]
    segment['toseg'] = internal_receiver_segment_ids[i] # = toseg
    _id += 1

# Now we have the full set of points that can be written to file.
# But how about the GIS lines?
# Let's get more information in each segment.
# And let's add it to its own DataFrame


dfsegs = pd.DataFrame({'id': segment_ids, 'toseg': toseg})
dfsegs.insert(len(dfsegs.columns), 'lat', None)
dfsegs.insert(len(dfsegs.columns), 'lon', None)

# Add additional columns according to the provided command line arguments

if args.slope:
    dfsegs.insert(len(dfsegs.columns), 'slope', None)
if args.elevation:
    dfsegs.insert(len(dfsegs.columns), 'max_elev', None)
    dfsegs.insert(len(dfsegs.columns), 'min_elev', None)
    dfsegs.insert(len(dfsegs.columns), 'average_elev', None)
if args.drainage_area:
    dfsegs.insert(len(dfsegs.columns), 'drainage_area_km2', None)
if args.chi:
    dfsegs.insert(len(dfsegs.columns), 'chi', None)
#dfsegs.insert(len(dfsegs.columns), 'depth_to_bedrock_m', None)
for i in range(len(segments)):
    segment = segments[i]
    if args.slope:
        dfsegs['slope'][i] = (np.max(segment['elevation']) - np.min(segment['elevation'])) / \
                         ( np.max(segment['flow_distance']) \
                           - np.min(segment['flow_distance']) )
    if args.elevation:
        dfsegs['average_elev'][i] = (np.max(segment['elevation']) + np.min(segment['elevation'])) / 2
        dfsegs['max_elev'][i] = (np.max(segment['elevation']))
        dfsegs['min_elev'][i] = (np.min(segment['elevation']))
    if args.drainage_area:
        dfsegs['drainage_area_km2'][i] = np.mean(segment['drainage_area'])/1E6
    if args.chi:
        dfsegs['chi'][i] = np.mean(segment['chi'])
    # These are going to be particular to this case
    #dfsegs['depth_to_bedrock_m'][i] = np.mean(segment['depth_to_bedrock'])
    #dfsegs['bedrock_lithology'] = np.mean(segment['depth_to_bedrock'])



# Create a set of LineString objects
stream_lines = []
for segment in segments:
    stream_lines.append( LineString(
                            segment.loc[:, ('longitude', 'latitude', 'elevation')].values ) )

# Now convert to geopandas
gdf_segs = gpd.GeoDataFrame( dfsegs, geometry=stream_lines )

# Save to GeoPackage
gdf_segs.to_file(file_output, driver="GPKG")

print("Done!")

#Generating the geopackage to begin path selection
print('Now I will create a geopackage to select segments for a path.')

#Creating df to be used to select segment for path
dfsegsselect= pd.DataFrame ({'segment_ID':segment_ids, 'toseg':toseg})

# Create a set of LineString objects to be used for selection
stream_lines_select = []
for segment in segments:
    stream_lines_select.append( LineString(
                            segment.loc[:, ('longitude', 'latitude', 'elevation')].values ) )

gdf_segsselect = gpd.GeoDataFrame( dfsegsselect, geometry=stream_lines_select )

# Save to GeoPackage
gdf_segsselect.to_file('segs_select.gpkg', driver="GPKG")

print('Your geopackage is ready!')
print('Open in GIS to select your starter segment_ID.')


# Export nodes for use of plotting
dfnodes = pd.concat(segments)
dfnodes['network_node_type'] = ""
#for mouth in mouth_nodes:
#   dfnodes.loc[mouth]['network_node_type'] = 'mouth'
gdf_NetworkNodes = gpd.GeoDataFrame( dfnodes, geometry=gpd.points_from_xy(dfnodes.longitude, dfnodes.latitude) )
gdf_NetworkNodes.to_file('output_nodes.gpkg', driver="GPKG")
print('Node shapefile is ready!')