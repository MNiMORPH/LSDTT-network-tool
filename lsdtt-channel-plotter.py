#! /usr/bin/python3

import argparse
import pandas as pd
import geopandas as gpd
import numpy as np
from matplotlib import pyplot as plt
import sys

##########
# PARSER #
##########

# INPUT
parser = argparse.ArgumentParser(description='Plot channel long profile and/or map view, optionally higlighting a channel starting from a provided segment id.')
parser.add_argument("segments", help="Path to geopackage file with segments (output from lsdtt-network-tool)", type=str)
parser.add_argument("nodes", help="Path to geopackage file with nodes (output from lsdtt-network-tool)", type=str)
parser.add_argument("--id", help="segment id (see attribute table) of the upstream-most segment of the flow path to plot and/or highlight", type=int)
parser.add_argument("--outbase", help="Base name for the output plots; can include full path, and otherwise will be assumed to be local; an underscore will be appended to the end of this", type=str)
parser.add_argument("--outfmt", help="File-extension-coded format for the output plots; if not set, plots may be displayed but not saved; defaults to 'png'", type=str, default='png')
#parser.add_argument("river_name", help="name of the river (used for title of plots)", type=str)

# OUTPUT
# Starting with just two long-profile plots
# Flags for plots
parser.add_argument("-p", "--lp", help="Flag: Plot long profile starting from ID", action="store_true")
parser.add_argument("-a", "--lp_all", help="Flag: Plot long profile of all streams", action="store_true")
parser.add_argument("-c", "--lp_combined", help="Flag: Plot long profiles of all streams with the portion starting from ID highlighted", action="store_true")
parser.add_argument("-k", "--ksn", help="Flag: Plot ksn on long profile", action="store_true")
parser.add_argument("-s", "--show", help="Flag: Display plot(s) on screen", action="store_true")
# Flag for selected channel output
parser.add_argument("-g", "--geopackage", help="Flag: Export geopackage of selected channel for plotting in GIS", action="store_true")

# PARSE
args = parser.parse_args()

# Standard arguments
#Input selected segment_ID. This will be the start of the path.
input_segment_id = args.id
input_segments = args.segments
input_nodes = args.nodes
#river_name = args.river_name
outbase = args.outbase
outfmt = args.outfmt

# Flags
_plot_selected_lp = args.lp
_plot_all_lps = args.lp_all
_plot_combined = args.lp_combined
_plot_ksn = args.ksn
_plot_show = args.show
_write_geopackage = args.geopackage

"""
input_segments = 'GooseberryNetworkTest20211117_6.gpkg'
input_nodes = 'GooseberryNetworkTest20211117_6_nodes.gpkg'
input_segment_id = 236
river_name = 'Gooseberry'

outbase='plot_tmp'
outfmt = 'png'
_plot_selected_lp = True
_plot_all_lps = True
_plot_combined = False
_plot_ksn = False
_plot_show = True
_write_geopackage = True
"""

##############################
# CHECK FOR FLAG CONSISTENCY #
##############################

if _plot_selected_lp:
    if input_segment_id is None:
        print('For --lp, --id is required')
        sys.exit(2)
if _plot_combined:
    if input_segment_id is None:
        print('For --lp-combined, --id is required')
        sys.exit(2)

if _write_geopackage:
    if input_segment_id is None:
        print('For --geopackage, --id is required')
        sys.exit(2)
    if outbase is None:
        print('For --geopackage, --outbase is required')
        sys.exit(2)

if _plot_selected_lp or _plot_all_lps or _plot_combined:
    if input_nodes is None:
        print('For any plotting request, a node-input file is required')
        sys.exit(2)

##############
# READ INPUT #
##############

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
queried_segments_idx = []
for seg_id in dfpath['id']:
    queried_segments.append(seg_id)
    queried_segments_idx.append(dfsegs.index[dfsegs['id'] == seg_id][0])

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


#####################
# Geopackage output #
#####################

if _write_geopackage:
    path_selected = dfsegs.loc[queried_segments_idx]
    path_selected.to_file(outbase+'_SelectedChannel.gpkg', driver="GPKG")

#########
# Plots #
#########

# Only one (selected) long profile
if _plot_selected_lp:
    plt.figure(figsize=(9,5))
    if _plot_ksn:
        plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], '.5', linewidth=4)
        sc = plt.scatter((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], c=np.log10(dfpath_nodes['m_chi']), cmap='magma', s=16, zorder=999999)
        cbar = plt.colorbar(sc)
        cbar.set_label(label='log$_{10} (k_{sn})$', fontsize=16)
    else:
        plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], 'k-', linewidth=4)
    plt.gca().invert_xaxis()
    plt.xlabel('Upchannel distance [km]', fontsize=16)
    plt.ylabel('Elevation [m]', fontsize=16)
    plt.tight_layout()
    if outbase is not None:
        plt.savefig(outbase+'_LongProfile.'+outfmt, dpi=300,
                facecolor='w', edgecolor='w',
                orientation='portrait', transparent=False)

# All long profiles with selected one highlighted
if _plot_combined:
    plt.figure(figsize=(9,5))
    for seg, nodes_segs in dfnodes.groupby('segment_id'):
        plt.plot((nodes_segs['flow_distance']/1000), nodes_segs['elevation'],
                  color='gray', linewidth=1)
    #plt.title(river_name, fontdict=None, loc='center', pad=None)
    plt.xlabel('Upchannel distance [km]')
    plt.ylabel('Elevation [m]')
    #plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'],'k-', linewidth=4)
    
    #plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], 'k-', linewidth= 3)
    if _plot_ksn:
        sc = plt.scatter((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], c=np.log10(dfpath_nodes['m_chi']), cmap='magma', s=16, zorder=999999)#0)
        cbar = plt.colorbar(sc, label='log$_{10} (k_{sn})$')#, fontsize=16)
        cbar.set_label(label='log$_{10} (k_{sn})$', fontsize=16)
    else:
        plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], 'k-', linewidth=4, zorder=999999)#0)
    plt.gca().invert_xaxis()
    plt.xlabel('Upchannel distance [km]', fontsize=16)
    plt.ylabel('Elevation [m]', fontsize=16)
    plt.tight_layout()
    if outbase is not None:
        plt.savefig(outbase+'_LongProfiles_AllWithHighlight.'+outfmt, dpi=300,
                facecolor='w', edgecolor='w',
                orientation='portrait', transparent=False)

# All long profiles
if _plot_all_lps:
    plt.figure(figsize=(9,5))
    for seg, nodes_segs in dfnodes.groupby('segment_id'):
        plt.plot((nodes_segs['flow_distance']/1000), nodes_segs['elevation'],
        color= 'gray', linewidth=1)
    if _plot_ksn:
        # First, find full range of ksn
        _ksn_max = -1E16
        _ksn_min = 1E16
        for seg, nodes_segs in dfnodes.groupby('segment_id'):
            _ksn_max = np.max((_ksn_max, np.max(nodes_segs['m_chi'])))
            _ksn_min = np.min((_ksn_min, np.min(nodes_segs['m_chi'])))
        # Then plot
        for seg, nodes_segs in dfnodes.groupby('segment_id'):
            sc = plt.scatter((nodes_segs['flow_distance']/1000), nodes_segs['elevation'],
                               c=np.log10(nodes_segs['m_chi']), cmap='magma', s=1,
                               vmax=np.log10(_ksn_max), vmin=np.log10(_ksn_min),
                               zorder=999999)
        cbar = plt.colorbar(sc, label='log$_{10} (k_{sn})$')#, fontsize=16)
        cbar.set_label(label='log$_{10} (k_{sn})$', fontsize=16)
    plt.gca().invert_xaxis()
    plt.xlabel('Upchannel distance [km]', fontsize=16)
    plt.ylabel('Elevation [m]', fontsize=16)
    plt.tight_layout()
    if outbase is not None:
        plt.savefig(outbase+'_LongProfiles_All.'+outfmt, dpi=300,
                facecolor='w', edgecolor='w',
                orientation='portrait', transparent=False)

"""
# Profile of entire network (selected path in black)
plt.figure()
for seg, nodes_segs in dfnodes.groupby('segment_id'):
    plt.plot((nodes_segs['flow_distance']/1000), nodes_segs['elevation'], color= 'gray', linewidth=1)
#plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.xlabel('Upchannel distance [km]')
plt.ylabel('Elevation [m]')
plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'],'k-', linewidth=4)
plt.gca().invert_xaxis()

plt.savefig("AllChannelLongProfile", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
"""

if _plot_show:
    plt.show()


"""
# Map view of network (selected path in black)
plt.figure()
for seg, nodes_segs in dfnodes.groupby('segment_id'):
    plt.plot(nodes_segs['longitude'], nodes_segs['latitude'], color= 'grey')

#plt.plot(confluences[:,0], confluences[:,1], 'bo')
#plt.plot(mouths[:,0], mouths[:,1], color= 'grey', linewidth= 1)
#plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot(dfpath_nodes['longitude'], dfpath_nodes['latitude'], 'k-', linewidth= 6)
plt.xlabel('Longitude')
plt.ylabel('Latitude')

plt.savefig("NetworkMap", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
"""

"""
plt.figure()
# Map view of the selected path
#plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot(dfpath_nodes['longitude'], dfpath_nodes['latitude'], 'k-', linewidth= 5)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.savefig("PathMap", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
"""

"""
# Long profile of the selected path
plt.figure()
#plt.title(river_name, fontdict=None, loc='center', pad=None)
plt.plot((dfpath_nodes['flow_distance']/1000), dfpath_nodes['elevation'], 'k-', linewidth= 3)
plt.xlabel('Upchannel distance [km]')
plt.ylabel('Elevation [m]')
plt.gca().invert_xaxis()

plt.savefig("PathChannelLongProfile", dpi=300, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None, metadata=None)
"""

