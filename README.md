# LSDTT-network-tool
Builds a vectorized drainage network from LSDTopoTools outputs, divided at tributary junctions. Uses: analysis, plotting, GIS, model input.

# Guide 
Before the lsdtt-network-tool can be used, we must create some files with the original LSDTopoTools. We will begin this guide at the very beginning, assuming that you have a DEM of your area of interest and would like to create some map view and long profile plots of the channels. 

There are two tools that you will use in order to generate plots from your DEM. The first is the lsdtt-chi-mapping tool within LSDTopoTools, and the second is this one--the LSDTT-network-tool. Along the way, we will explain what the tool does, the neccesary (and optional) inputs, the outputs you will receive, and we will follow an example workflow from beginning to end to show how to structure commands. 

## Section 1: Using The `lsdtt-chi-mapping` Tool: Extracting Channels From Your DEM 
LSDTopoTools is a program with many tools that are able to extract a range of data from elevation data. The `lsdtt-chi-mapping` tool can be used to create channel networks and record various parameters along each channel, such as elevation, flow distance, drainage area, chi, and more. 

#### Inputs

#### Outputs

#### Workflow

Step 1: Fill nulls in your your DEM
* There are definitely many ways to do this, but we will suggest two: the 'r.fillnulls' tool in the Grass package of qgis and the 'Fill nodata' tool in the GDAL package of qgis.  

Step 2: write a parameter file
* Now this will have some variation depending on what your DEM is of and what outputs you are interested in, but there some portions that everyone will need. The first few lines of your parameter file should include the location and naming information for the files that you are inputting and that will be outputted. For our example this looks like:
```
read path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
write path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
read fname: CascadeRiver
write fname: CascadeRiver
channel heads fname: NULL
```
* Next, you need information about how the computer will process the data you give it. For our example, this looks like:
```
# Parameter for filling the DEM
min_slope_for_fill: 0.0001

# Parameters for selecting channels and basins
threshold_contributing_pixels: 10000
connected_components_threshold: 100
print_area_threshold_channels: true
print_wiener_channels: false
print_pelletier_channels: false
print_dreich_channels: false

write_hillshade: true
print_stream_order_raster: true

surface_fitting_radius: 2
```
* Now that we have a parameter file, we can actually process the data. 

Step 3: Navigate to the folder that contains your DEM and your parameter file

Step 4: Ask the computer to run the lsdtt-chi-mapping tool on your data


## Section 2: Using The LSDTT-network-tool: Converting The Chi Map Data Into Easily Readable Plots 

There are two main steps in this section: the first builds a network of lines and points that can be easily entered into a GIS program of your choice, and the second creates long profile plots. This tool is really for visualizing data that you have already created using the LSDTopoTools program. 

### Initial step: build the channel network using lsdtt-network-tool.py

lsdtt-network-tool.py creates a geopackage containing a channel networkmade of line segments from the points outputted by the chi-mapping tool. In other words, it creates a network of lines that show the channels generated during the chi mapping. These lines can be easily imported into your favorite GIS software. 

#### Inputs
_Necessary inputs:_

* `file_input`: The *_MChiSegmented.csv output from LSDTT2

* `file_output`: The filename for the output geodatabase(s)


_Optional inputs:_

* `--basin_key=BASIN_KEY`: adding this flag allows you to select a single basin for which to generate a network. If the `--basin_key` flag is not used, then all channels generated during chi-mapping will be included in the geopackage.
  * how do I know what the BASIN_KEY is for the channel I am interested in?

* `-n` (`--node_export`): adding this flag tells the program to export all nodes (in addition to all line segments) to a geopackage. Including this flag is necessary if you are to use lsdtt-channel-plotter.py.


#### Outputs

* file_output.gpkg

* file_output_nodes.gpkg (only with use of `-n` / `--node_export` flag)

#### Example workflow
 
 ```
 python /home/josie/LSDTopoTools/LSDTT-network-tool/lsdtt-network-tool.py CascadeRiver_MChiSegmented.csv CascadeRiver_network.gpkg -n --basin_key=6
 ```
 
### Final step: generate plots of the network and the channel long profile using lsdtt-channel-plotter.py


#### Inputs 
_Neccesary Inputs_
* asdf
* asdf

_Optional Inputs_
* asdf
* asdf

#### Example workflow

```
python /home/josie/LSDTopoTools/LSDTT-network-tool/lsdtt-channel-plotter.py CascadeRiver_network.gpkg CascadeRiver_network_nodes.gpkg --id=0 --outbase=CascadeRiver --outfmt=svg -packsg
```

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
