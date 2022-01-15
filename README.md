# LSDTT-network-tool
Builds a vectorized drainage network from LSDTopoTools outputs, divided at tributary junctions. Uses: analysis, plotting, GIS, model input.

# Guide 
This tool has two parts, the first builds a network of lines and points, and the second creates long profile plots. 

## Initial step: build the channel network using lsdtt-network-tool.py

lsdtt-network-tool.py creates a geopackage containing a channel networkmade of line segments from the points outputted by the chi-mapping tool. In other words, it creates a network of lines that show the channels generated during the chi mapping. These lines can be easily imported into your favorite GIS software. 

### Inputs
_Necessary inputs:_

* `file_input`: The *_MChiSegmented.csv output from LSDTT2

* `file_output`: The filename for the output geodatabase(s)


_Optional inputs:_

* `--basin_key=BASIN_KEY`: adding this flag allows you to select a single basin for which to generate a network. If the `--basin_key` flag is not used, then all channels generated during chi-mapping will be included in the geopackage

* `-n` (`--node_export`): adding this flag tells the program to export all nodes (in addition to all line segments) to a geopackage. Including this flag is necessary if you are to use lsdtt-channel-plotter.py.


### Outputs

* file_output.gpkg

* file_output_nodes.gpkg (only with use of -n / --node_export flag)

### Example workflow
 
## Final step: generate plots of the network and the channel long profile using lsdtt-channel-plotter.py




# Goals for Network Tool
## Inputs
### Input chi analysis output from LSDTT
  * LSDTT outputs will include the `source_key`, `receiver_node`, and `node_ID`.
  * Working to see if we can get these updates to LSDTT, hoping to be able to    link the network tool with chi, z, etc. data.

## Tool
### Initial tool to build the channel network.
  * The first half of the code is currently doing this.
  * Currently working to update channel network code to include new inputs from LSDTT-chi tool.

### Once network is built, generate plots of the network and the channel long profile
  * Capability to select a `node_ID` that the code will walk down to generate a channel long profile.
    * This will make it possible to make channel profiles for mutiple branches, etc.

### Planning to use `argparse` to make the tool much easier to work with.

## Future expansion goals
### Pairing `LSDTT_terraces` with channel long profile outputs to generate plot with both.
### qGIS plugin.
