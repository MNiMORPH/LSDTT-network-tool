import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
from scipy.optimize import curve_fit
import geopandas as gpd
from shapely.geometry import LineString
#plt.ion()

window = 1000 # meters per "reach"

rp = pd.read_csv('/Users/Shanti/Desktop/Fall_2020/LSDTT-network/LSDTT-network/ww_everything_newDTB.csv', index_col='node')
#rp = pd.read_csv('/home/andy/Desktop/Eel_River_Network_testing/Eel_River_DEM_MChiSegmented.csv')
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
for _receiver_node in rp['receiver_node']:
    #_receiver_node = rp.loc[_node, 'receiver_node']
    try:
        _receiver_source_key = rp.loc[_receiver_node, 'source_key']
    except:
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
confluence_downstream_nodes = list(set(list(rp['receiver_node']
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
    _x = rp.loc[_node, 'E_UTM']
    _y = rp.loc[_node, 'N_UTM']
    confluences.append([_x, _y])
confluences = np.array(confluences)

# Create a set of river mouth locations
mouths = []
for _node in mouth_nodes:
    _x = rp.loc[_node, 'E_UTM']
    _y = rp.loc[_node, 'N_UTM']
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
    segment_nodes.append(rp.loc[segment_nodes[-1], 'receiver_node'])
    while segment_nodes[-1] not in termination_nodes:
        segment_nodes.append(rp.loc[segment_nodes[-1], 'receiver_node'])
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
dfsegs.insert(len(dfsegs.columns), 'slope', None)
dfsegs.insert(len(dfsegs.columns), 'drainage_area_km2', None)
dfsegs.insert(len(dfsegs.columns), 'chi', None)
dfsegs.insert(len(dfsegs.columns), 'depth_to_bedrock_m', None)
for i in range(len(segments)):
    segment = segments[i]
    dfsegs['slope'][i] = (np.max(segment['z']) - np.min(segment['z'])) / \
                         ( np.max(segment['flow_distance']) \
                           - np.min(segment['flow_distance']) )
    dfsegs['drainage_area_km2'][i] = np.mean(segment['drainage_area'])/1E6
    dfsegs['chi'][i] = np.mean(segment['chi'])
    # These are going to be particular to this case
    dfsegs['depth_to_bedrock_m'][i] = np.mean(segment['depth_to_bedrock'])
    #dfsegs['bedrock_lithology'] = np.mean(segment['depth_to_bedrock'])

# Create a set of LineString objects
stream_lines = []
for segment in segments:
    stream_lines.append( LineString(
                            segment.loc[:, ('lon', 'lat', 'z')].values ) )

# Now convert to geopandas
gdf_segs = gpd.GeoDataFrame( dfsegs, geometry=stream_lines )

# Save to GeoPackage
gdf_segs.to_file('whitewater_river_segments.gpkg', driver="GPKG")

print("Done!")

"""
# Create the lines for the shapefile
sf_lines = []
for segment in segments:
    _tmparr = segment.loc[:, ('lon', 'lat', 'z')].values
    _tmplist = []
    for row in _tmparr:
        _tmplist.append(list(row))
    sf_lines.append( _tmplist )

# Now write the results to a shapefile
sf = shapefile.Writer('ww-lines')
sf.shapeType = shapefile.POLYLINEZ # 13; POLYLINE=3
sf.field('id', 'N')
sf.field('toseg', 'N')
sf.field('slope', 'N', decimal=7)
sf.field('drainage_area_km2', 'N', decimal=6)
sf.field('chi', 'N', decimal=3)
# Specific to this data set
sf.field('depth_to_bedrock_m', 'N', decimal=1)
for i in range(len(dfsegs)):
    sf.record( id = dfsegs['id'][i],
              toseg = dfsegs['toseg'][i],
              slope = dfsegs['slope'][i],
              drainage_area_km2 = dfsegs['drainage_area_km2'][i],
              chi = dfsegs['chi'][i],
              depth_to_bedrock_m = dfsegs['depth_to_bedrock_m'][i] )
sf.linez(sf_lines[i])
sf.close()
"""


'''
# Export the points (mouths, heads, confluences)

# Create DataFrames of only these nodes
_df_mouths = rp.loc[mouth_nodes, :]
_df_heads = rp.loc[channel_head_nodes, :]
_df_confluences = rp.loc[confluence_downstream_nodes, :]
# But these don't have the extra info in them. So:
# START HERE
_pdout = []
# for

# Add in a "type" parameter
_df_mouths['network_node_type'] = 'mouth'
_df_heads['network_node_type'] = 'head'
_df_confluences['network_node_type'] = 'confluence'

# All nodes in network
_df_NetworkNodes = pd.concat([_df_heads, _df_confluences, _df_mouths])

gdf_NetworkNodes = geopandas.GeoDataFrame( _df_NetworkNodes,
                                           geometry=geopandas.points_from_xy(
                                                _df_NetworkNodes.lon,
                                                _df_NetworkNodes.lat) )

# Save to shapefile -- some field names will be truncated
gdf_NetworkNodes.to_file('whitewater_river_nodes')




# Export for Landlab NetworkSedimentTransporter

# Create a geoDataFrame with the minimum required data
NST_nodes = gdf_NetworkNodes.loc[:, [ 'receiver_node',
                                      'lon', 'lat', 'z',
                                      'drainage_area', 'geometry'] ]

# Add NST_nodes.index as the node ID

# Build the





'''

plt.figure()
for segment in segments:
    plt.plot(segment['flow_distance'], segment['z'], 'k-')


plt.figure()
for segment in segments:
    plt.plot(segment['E_UTM'], segment['N_UTM'])

plt.plot(confluences[:,0], confluences[:,1], 'bo')
plt.plot(mouths[:,0], mouths[:,1], 'ro')
plt.show()












for i in range(1):
    segment = rp[rp['source_key'] == i]
    plt.plot(segment.flow_distance, segment.segmented_elevation)





#Generating the geopackage to begin path selection
print('Now I will create a geopackage to select segments for a path.')

#Creating df to be used to select segment for path
dfsegsselect= pd.DataFrame ({'segment_ID':segment_ids, 'toseg':toseg})

# Create a set of LineString objects to be used for selection
stream_lines_select = []
for segment in segments:
    stream_lines_select.append( LineString(
                            segment.loc[:, ('lon', 'lat', 'z')].values ) )

gdf_segsselect = gpd.GeoDataFrame( dfsegsselect, geometry=stream_lines_select )

# Save to GeoPackage
gdf_segsselect.to_file('segs_select.gpkg', driver="GPKG")

print('Your geopackage is ready!')
print('Open in GIS to select your starter segment_ID.')





#Adding in Peter's changes (with some tweaks)
input_segment_id = 2789

#Find out if the input segment is in the segments dataframe
input_segment_id_found = False
for seg_id in dfsegs['id']:
    if seg_id == input_segment_id:
        input_segment_id_found = True
        print("Segment ID found.")
#We'll probably want this to raise an exception so that it doesn't continue with the pathmaking if the given ID doesn't exist
# for right now, though, we'll just print a message
if not input_segment_id_found:
    print("Error: No segment with the given ID")


#End Peter edits, begin attempts to generate path

#convert input to int
input_segment_id= int(input_segment_id)

#Look up user input seg id, create column is_input w/true and false
dfsegs['is_input'] = np.where(dfsegs['id']== input_segment_id, True, False)

#Create new df called dfpath that is populated by all the true values.
dfpath = dfsegs[dfsegs['is_input'] == True]

dfpath.head()

input_toseg = input_segment_id
while input_toseg != -1:
    #find relevant toseg
    input_toseg=dfpath.loc[dfpath['id']== input_segment_id, 'toseg']
    #convert to int
    input_toseg=int(input_toseg)
    #query dfsegs to find the segment with the same id as toseg
    dfsegs['is_input'] = np.where(dfsegs['id']== input_toseg, True, False)
    #take this line ad append it to dfpath
    dfpath = dfpath.append(dfsegs[dfsegs['is_input'] == True])
    input_segment_id = input_toseg


dfpath

#This is currently working to create the dfpath
#Working now to pull relevant elevation, lat/long information into dfpath
