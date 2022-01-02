#! /usr/bin/python3

import argparse
import pandas as pd
import geopandas as gpd
import numpy as np
from matplotlib import pyplot as plt

##########
# PARSER #
##########

# INPUT
parser = argparse.ArgumentParser(description='Plot channel long profile and/or map view, optionally higlighting a channel starting from a provided segment id.')
parser.add_argument("segments", help="Path to geopackage file with segments (output from lsdtt-network-tool)", type=str)
parser.add_argument("nodes", help="Path to geopackage file with nodes (output from lsdtt-network-tool)", type=str)
parser.add_argument("--id", help="segment id (see attribute table) of the upstream-most segment of the flow path to plot and/or highlight", type=int)
#parser.add_argument("river_name", help="name of the river (used for title of plots)", type=str)

# OUTPUT
# Starting with just two long-profile plots
parser.add_argument("--lp", help="long profile starting from ID", type=int)
parser.add_argument("--lp-all", help="long profile of all streams, with (optionally) the portion starting from ID highlighted", type=int)


args = parser.parse_args()
#Input selected segment_ID. This will be the start of the path.
input_segment_id = args.id
input_segments = args.segments
input_nodes = args.nodes
#river_name = args.river_name

"""
input_segments = 'GooseberryNetworkTest20211117_6.gpkg'
input_nodes = 'GooseberryNetworkTest20211117_6_nodes.gpkg'
input_segment_id = 236
river_name = 'Gooseberry'
"""

dfsegs = gpd.read_file(input_segments)
dfnodes = gpd.read_file(input_nodes)

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
#print(dfpath)

#Now have a df that has all the relevant segments, in order moving down path.

#Begin pulling required nodes from segments
#Create list of relevant segments
queried_segments = []
for seg_id in dfpath['id']:
    queried_segments.append(seg_id)

#Create list of df entries for relevant nodes in queried_segments
"""
# Approach querying the network
path_nodes=[]
for _id in queried_segments:
    _seg = dfsegs.geometry[dfsegs['id'] == _id]
    _xyz = np.array(_seg[_seg.index[0]].coords[:])
    _
"""
    
# Approach with nodes already printed
path_nodes=[]
for _id in queried_segments:
    path_nodes.append(dfnodes[dfnodes['segment_id'] == _id] )

#Create a df with relevant nodes in path
dfpath_nodes = pd.concat(path_nodes, ignore_index=True)

#dfpath_nodes



plt.figure()
for seg, nodes_segs in dfnodes.groupby('segment_id'):
    plt.plot((nodes_segs['flow_distance']/1000), nodes_segs['elevation'], color= 'gray', linewidth=1)
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.xlabel('Downchannel distance [km]')
plt.ylabel('Elevation [m]')
#plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'],'k-', linewidth=4)
plt.scatter((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], c=np.log10(dfpath_nodes['m_chi']), cmap='magma')
plt.gca().invert_xaxis()
plt.show()


# Build Plots
# Profile of entire network (selected path in black)
plt.figure()
for seg, nodes_segs in dfnodes.groupby('segment_id'):
    plt.plot((nodes_segs['flow_distance']/1000), nodes_segs['elevation'], color= 'gray', linewidth=1)
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
for seg, nodes_segs in dfnodes.groupby('segment_id'):
    plt.plot(nodes_segs['longitude'], nodes_segs['latitude'], color= 'grey')

#plt.plot(confluences[:,0], confluences[:,1], 'bo')
#plt.plot(mouths[:,0], mouths[:,1], color= 'grey', linewidth= 1)
plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot(dfpath_nodes['longitude'], dfpath_nodes['latitude'], 'k-', linewidth= 6)
plt.xlabel('Longitude')
plt.ylabel('Latitude')

plt.savefig("NetworkMap", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)

plt.figure()

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
