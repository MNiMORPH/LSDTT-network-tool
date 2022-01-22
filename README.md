# LSDTT-network-tool
Builds a vectorized drainage network from LSDTopoTools outputs, divided at tributary junctions. Uses: analysis, plotting, GIS, model input.

# Guide 
Before the lsdtt-network-tool can be used, we must create some files with the original LSDTopoTools. We will begin this guide at the very beginning, assuming that you have a DEM of your area of interest and would like to create some map view and long profile plots of the channels. 

There are two tools that you will use in order to generate plots from your DEM. The first is the lsdtt-chi-mapping tool within LSDTopoTools, and the second is this one--the LSDTT-network-tool. Along the way, we will explain what the tool does, the neccesary (and optional) inputs, the outputs you will receive, and we will follow an example workflow from beginning to end to show how to structure commands. 

------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Part 1: Using The `lsdtt-chi-mapping` Tool: Extracting Channels From Your DEM 
LSDTopoTools is a program with many tools that are able to extract a range of data from elevation data. The `lsdtt-chi-mapping` tool can be used to create channel networks and record various parameters along each channel, such as elevation, flow distance, drainage area, chi, and more. 

#### Inputs
* A digital elevation model (DEM) in the the ENVI .bil format of your area of interest.
  * If you have a DEM in a different format, you can use `gdal_tranlate` with the flag `-of ENVI` to convert to the correct format.  
* A parameter file
  * We will go through what needs to be included in this file. It must be a plain text file (not a word or google document).

#### Outputs
* _Neccesary outputs_
  * *_MChiSegmented.csv
  * *_chi_data_map.csv
* _Optional outputs_
  * *_hs.bil (this one prints a hillshade raster and is nice for making good looking figures!)
  * There are many other outputs possible,and which outputs you get will depend on what you include in your parameter file. A complete list can be found in the [LSDTopoTools User Guide to Chi Analysis](https://lsdtopotools.github.io/LSDTT_documentation/LSDTT_chi_analysis.html). 

#### Workflow

##### Step 1: Fill nulls in your your DEM #####
   * There are definitely many ways to do this, but we will suggest two: the  the 'Fill nodata' tool in the GDAL package of qgis and the 'r.fillnulls' tool in the Grass package of qgis.  

##### Step 2: Write a parameter file #####
   * In order to write this file you will need to be able to edit a plain text file, which requires a code editor. There are many programs out there that do this, but Visual Studio Code and Sublime are two popular options. 
   * Each parameter file is unique to the project you are working on, because it is essentially the instructions you are giving the computer. Variations will be made depending on your DEM and what outputs you are interested in. The first few lines of your parameter file should include the location and naming information for the files that you are inputting and that will be outputted. All parameter files need these lines. For our example, the first few lines look like:
   ```
read path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
write path: /home/josie/LSDTopoTools/Northshore_Data/CascadeRiver
read fname: CascadeRiver
write fname: CascadeRiver

channel heads fname: NULL
   ```
   * As you can see, we have a read path and a write path, which tell the computer where to find the files that we want it to use, the read filename (`read fname`), which is the prefix that we want the computer look for at the beginning input file names and the write filename (`write fname`) which is the prefix we want the computer to attach to the beginning of the name of all output file names. Below those, there is a line indicating whether the computer should look for a channel heads location file. If you have one write the file name (include the full path to the file if the file is not in the same location as the DEM and parameter file). If you do not have one, inclulde the line and write NULL. 

   * Next is information about how the computer will process the input data. For our example, this looks like:
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
* This will probably take a bit of time. Running our example data (~110 Mb) on our relatively powerful lab computer (which has 4 to 6 times more horsepower than a most laptops) takes a few minutes. If all goes well, then its time to move on to getting this data cleaned up to make nice plots!

----------------------------------------------------------------------------------------------------------------------------------------------------------------

## Part 2: Using The LSDTT-network-tool: Converting The Chi Map Data Into Easily Readable Plots 

There are two main steps in this section: the first builds a network of lines and points that can be easily entered into a GIS program of your choice, and the second creates long profile plots. This tool is really for visualizing data that you have already created using the LSDTopoTools program. 

### Initial step: Build the channel network using lsdtt-network-tool.py

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

#### Workflow

##### Step 1: Get node data and chi data in one file

* Unfortunately, the extended data is placed only in the *_chi_data_map.csv, which does not contain all of the information needed. So, we need to copy 2 columns, 'NI' and 'receiver_NI', from the *_chi_data_map.csv file and paste them into the *_MChiSegmented.csv file. Luckily, these two sheets contain the same points and they are in the same order, so you can simply copy & paste. Once these columns are in the proper file, we must rename them.'NI' becomes 'index_node' and  'receiver_NI' becomes 'receiver_node'

##### Step 2: Choose which basin you would like to print geopackages for (optional)
* This step is optional, but if you are trying to highlight the network in one basin it is very helpful to pick a basin **before** you print geopackages. Processing will also go quicker if you do this. 
* In order to do this, we must look at the channels that we extracted. To do this: 
  1. Open qgis and import *_MChiSegmented.csv
  2. In the geoprocessing toolbox, find the 'Create points layer from table' tool and double click
      - In the 'Input layer' box, select your csv
      - In the 'X field' box, select longitude
      - In the 'Y field' box, select lattitude
      - Make sure the 'target CRS' box says 'ESPG:4326: WGS 84'
      - Leave the rest as it is and run the tool
      - Using the 'identify features' tool click on a channel that you are interested in. In the identify results box on the right, you will find the 'basin_key' for that channels network. 

##### Step 3: Use the network tool to print line (and point) network geopackage(s)

* Now that we have our basin_key and our data is organized, we can create our channel network geopackage(s). The command will looks something like the following:
 ```
 python /home/josie/LSDTopoTools/LSDTT-network-tool/lsdtt-network-tool.py CascadeRiver_MChiSegmented.csv CascadeRiver_network.gpkg --basin_key=6 -n 
 ```
* First, you tell the computer to use the network-tool, this includes telling it to use python, and then the location of the program and its name. this is followed by the `file_input` which is the name of the file you want it to use, then the `file output` which is what you would like to name the geopackage(s). Next, we provide the `basin_key` and tell the `-n`/`--print_nodes` flag (optional). 
* Run the command, then we are ready for the next step!
 
 
### Final step: generate plots of the network and the channel long profile using lsdtt-channel-plotter.py


#### Inputs 
_Neccesary Inputs_
* *.gpkg
* *_nodes.gpkg

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
