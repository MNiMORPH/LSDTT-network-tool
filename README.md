# LSDTT-network-tool
Builds a vectorized drainage network from LSDTopoTools outputs, divided at tributary junctions. Uses: analysis, plotting, GIS, model input.

# Guide 
Before the lsdtt-network-tool can be used, we must create some files with the original LSDTopoTools. We will begin this guide at the very beginning, assuming that you have a DEM of your area of interest and would like to create some map view and long profile plots of the channels. 

There are two tools that you will use in order to generate plots from your DEM. The first is the lsdtt-chi-mapping tool within LSDTopoTools, and the second is this one--the LSDTT-network-tool. Along the way, we will explain what the tool does, the neccesary (and optional) inputs, the outputs you will receive, and we will follow an example workflow from beginning to end to show how to structure commands. 

### Section 1: Using The `lsdtt-chi-mapping` Tool: Extracting Channels From Your DEM 
LSDTopoTools is a program with many tools that are able to extract a range of data from elevation data. The `lsdtt-chi-mapping` tool can be used to create channel networks and record various parameters along each channel, such as elevation, flow distance, drainage area, chi, and more. 

#### Inputs
* A digital elevation model (DEM) in the the ENVI .bil format of your area of interest.
  * If you have a DEM in a different format, you can use `gdal_tranlate` with the flag `-of ENVI` to convert to the correct format.  
* A parameter file
  * We will go through what needs to be included in this file. It must be a plain text file (not a word or google document).

#### Outputs
* *_MChiSegmented.csv
* *_chi_data_map.csv
* *_hs.bil

#### Workflow

##### Step 1: Fill nulls in your your DEM #####
   * There are definitely many ways to do this, but we will suggest two: the  the 'Fill nodata' tool in the GDAL package of qgis and the 'r.fillnulls' tool in the Grass package of qgis.  

##### Step 2: Write a parameter file #####
   * In order to write this file you will need to be able to edit a plain text file,which have some variation depending on your DEM and what outputs you are interested in, but there a few lines that everyone will need. The first few lines of your parameter file should include the location and naming information for the files that you are inputting and that will be outputted. For our example, the first few lines look like:
   ```
read path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
write path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
read fname: CascadeRiver
write fname: CascadeRiver

channel heads fname: NULL
   ```
   * As you can see, we have a read path and a write path, which tell the computer where to find the files that we want it to use, the read filename (`read fname`), which are the prefix that we want the computer look for at the beginning of the names of input files and the write filename (`write fname`) which is the prefix we want the computer to attach to the beginning of the name of all the files that it outputs. Below those there is the channel heads fname, which would be a file (along with its full path if not local) which contains the locations of the the channel heads in the area of interest. If you do not have one, write NULL. 

   * Next, in your parameter file is information about how the computer will process the input data. For our example, this looks like:
   ```
# Parameter for filling the DEM 
min_slope_for_fill: 0.0001

# Parameters for selecting channels and basins
threshold_contributing_pixels: 10000
minimum_basin_size_pixels: 100000
maximum_basin_size_pixels: 6000000
test_drainage_boundaries: false
# Use network tool to select largest complete basin via "--basin_key"
find_largest_complete_basins: false
find_complete_basins_in_window: false

# The data that you want printed to file
write_hillshade: true
print_basin_raster: false
print_chi_data_maps: true
print_basic_M_chi_map_to_csv: false
print_segmented_M_chi_map_to_csv: true
use_extended_channel_data: true


# Chi analysis options
m_over_n: 0.5
A_0: 1

   ```
* First is a parameter that is used for filling the DEM. Next there is a series of parameters that the computer will use to select basins and locate channels. Adjusting these will affect the size of basins and the starting locations of rivers. In this example, we are using area-threshold extraction, but there are a number of algorithms available in this program to extract basins and channels. If you are interested in more information about what they are and how to use them, visit the [LSDTopoTools documentation page](https://lsdtopotools.github.io/LSDTT_documentation/). Next, there are some instructions to tell the computer what data we want it to print. For creating long profiles, you must include `print_chi_data_maps: true`, `print_segmented_M_chi_map_to_csv: true`, and  `use_extended_channel_data: true`. Finally, there are some parameters for the chi analysis. 
 
* Save the parameter with a helpful name followed by `.param` in the same folder as your DEM. For our example the parameter file was named `LSDTT_Chi_Analysis.param`. Now that we have a parameter file, we can actually process the data. 

##### Step 3: Navigate to the folder that contains your DEM and your parameter file #####
* This simplifies the command you write greatly, because you do not have to include the full path to the parameter file.

##### Step 4: Ask the computer to run the lsdtt-chi-mapping tool on your data #####
* Now that you are in the right folder, this is the easy part. Type the command: 
```
lsdtt-chi-mapping name-of-you-parameter-file
```
* For our example, the command looked like:
```
lsdtt-chi-mapping LSDTT_chi_analysis.param
```
This will probably take a bit of time. Running our example data (~110 Mb) on our relatively powerful lab computer (which certainly has more horsepower than a most laptops) takes a few minutes. 

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
