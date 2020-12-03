import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
from scipy.optimize import curve_fit
import geopandas as gpd
from shapely.geometry import LineString
#plt.ion()

window = 1000 # meters per "reach"

#rp = pd.read_csv('/Users/Shanti/Desktop/Fall_2020/LSDTT-network/LSDTT-network/ww_everything_newDTB.csv', index_col='node')
rp = pd.read_csv('zum_chi_chi_data_map.csv', index_col='NI', na_filter=False)
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
dfsegs.insert(len(dfsegs.columns), 'slope', None)
dfsegs.insert(len(dfsegs.columns), 'max_elev', None)
dfsegs.insert(len(dfsegs.columns), 'min_elev', None)
dfsegs.insert(len(dfsegs.columns), 'average_elev', None)
dfsegs.insert(len(dfsegs.columns), 'drainage_area_km2', None)
dfsegs.insert(len(dfsegs.columns), 'chi', None)
#dfsegs.insert(len(dfsegs.columns), 'depth_to_bedrock_m', None)
for i in range(len(segments)):
    segment = segments[i]
    dfsegs['slope'][i] = (np.max(segment['elevation']) - np.min(segment['elevation'])) / \
                         ( np.max(segment['flow_distance']) \
                           - np.min(segment['flow_distance']) )
    dfsegs['average_elev'][i] = (np.max(segment['elevation']) + np.min(segment['elevation'])) / 2
    dfsegs['max_elev'][i] = (np.max(segment['elevation']))
    dfsegs['min_elev'][i] = (np.min(segment['elevation']))
    dfsegs['drainage_area_km2'][i] = np.mean(segment['drainage_area'])/1E6
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
gdf_segs.to_file('whitewater_river_segments.gpkg', driver="GPKG")

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





#Input selected segment_ID. This will be the start of the path.
input_segment_id = 155

river_name = "Zumbro River"

#Find out if the input segment is in the segments dataframe.
input_segment_id_found = False
for seg_id in dfsegs['id']:
    if seg_id == input_segment_id:
        input_segment_id_found = True
        print("Segment ID found.")

#We'll probably want this to raise an exception so that it doesn't continue with the pathmaking if the given ID doesn't exist
# for right now, though, we'll just print a message

if not input_segment_id_found:
    print("Error: No segment with the given ID")


#Begin to generate path.
#convert input to int
input_segment_id= int(input_segment_id)

#Look up user input seg id, create column is_input w/true and false
dfsegs['is_input'] = np.where(dfsegs['id']== input_segment_id, True, False)

#Create new df called dfpath that is populated by all the true values.
dfpath = dfsegs[dfsegs['is_input'] == True]

#Create the path
#Set input_toseg to the input_segment_id
#Does this generate a duplicate of the first segment?
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

#Now have a df that has all the relevant segments, in order moving down path.

#Begin pulling required nodes from segments
#Create list of relevant segments
queried_segments = []
for seg_id in dfpath['id']:
    queried_segments.append(seg_id)

#Creat list of df entries for relevant nodes in queried_segments
path_nodes=[]
for _id in queried_segments:
    path_nodes.append( segments[_id] )

#Create a df with relevant nodes in path
dfpath_nodes = pd.concat(path_nodes, ignore_index=True)

dfpath_nodes

# Build Plots
# Profile of entire network (selected path in black)
plt.figure()
for segment in segments:
    plt.plot((segment['flow_distance']/1000), segment['elevation'], color= 'gray', linewidth=1)
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.xlabel('Downchannel distance [km]')
plt.ylabel('Elevation [m]')
plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'],'k-', linewidth=4)
plt.gca().invert_xaxis()

plt.savefig("AllChannelLongProfile", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

# Map view of network (selected path in black)
plt.figure()
for segment in segments:
    plt.plot(segment['longitude'], segment['latitude'], color= 'grey')

#plt.plot(confluences[:,0], confluences[:,1], 'bo')
plt.plot(mouths[:,0], mouths[:,1], color= 'grey', linewidth= 1)
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot(dfpath_nodes['longitude'], dfpath_nodes['latitude'], 'k-', linewidth= 6)
plt.xlabel('Longitude')
plt.ylabel('Latitude')

plt.savefig("NetworkMap", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

plt.figure()


# Map view of the selected path
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot(dfpath_nodes['longitude'], dfpath_nodes['latitude'], 'k-', linewidth= 5)
plt.xlabel('Longitude')
plt.ylabel('Latitude')


plt.savefig("PathMap", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

plt.figure()


# Long profile of the selected path
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], 'k-', linewidth= 3)
plt.xlabel('Downchannel distance [km]')
plt.ylabel('Elevation [m]')
plt.gca().invert_xaxis()

plt.savefig("PathChannelLongProfile", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

plt.figure()

